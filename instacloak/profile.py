"""Profile extraction + normalization (modern 2026+ and legacy GraphQL shapes).

The richest source is the `web_profile_info` API, fetched from inside the
browser (real TLS). When Instagram throttles that (datacenter IPs get a 401),
we fall back to the profile page's embedded JSON (`xig_user_by_username` node,
or older `_sharedData` GraphQL shapes).

`norm_profile` maps whatever node shape we got onto one stable, documented
report schema — Instagram's key names rotate, the report's don't.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from .fetch import INSTAGRAM_APP_ID, fetch_json
from .jsonutil import deep_find, extract_json_blobs, first as _first, iter_dicts

PROFILE_API = "https://i.instagram.com/api/v1/users/web_profile_info/?username={u}"
PROFILE_API_FALLBACK = "https://www.instagram.com/api/v1/users/web_profile_info/?username={u}"


def get_profile(page, username: str) -> tuple[dict | None, str]:
    """Fetch profile data via the web_profile_info endpoint.

    Returns (user_node, source) or (None, reason). This endpoint works
    logged-out from clean IPs; throttled/datacenter IPs get a 401 and we
    fall back to the embedded page JSON.
    """
    headers = {"x-ig-app-id": INSTAGRAM_APP_ID, "Accept": "application/json"}
    for url in (PROFILE_API.format(u=username), PROFILE_API_FALLBACK.format(u=username)):
        data = fetch_json(page, url, headers)
        if data:
            user = ((data.get("data") or {}).get("user")) or None
            if user is not None:
                return user, "web_profile_info"
            if user is None and "data" in data:
                return None, "not_found"
    return None, "api_unavailable"


def find_user_in_blobs(blobs: list, username: str) -> dict | None:
    """Find a profile node inside Instagram's embedded JSON blobs.

    Modern (2026+) logged-out pages embed it under `xig_user_by_username`;
    older pages used `_sharedData`/`__additionalDataLoaded` GraphQL shapes.
    """
    for blob in blobs:
        for d in iter_dicts(blob):
            inner = d.get("xig_user_by_username")
            if isinstance(inner, dict) and inner.get("username", "").lower() == username.lower():
                return inner
    for blob in blobs:
        node = deep_find(blob, "edge_followed_by", "edge_owner_to_timeline_media")
        if node is None:
            node = deep_find(blob, "biography", "edge_followed_by")
        if node and node.get("username", "").lower() == username.lower():
            return node
    return None


def profile_from_embedded(page, username: str) -> dict | None:
    try:
        html = page.content()
    except Exception:  # noqa: BLE001
        return None
    return find_user_in_blobs(extract_json_blobs(html), username)


def _count(node: dict, modern_key: str, legacy_edge: str) -> int | None:
    v = node.get(modern_key)
    if v is None:
        v = (node.get(legacy_edge) or {}).get("count")
    return v


def _external_link(node: dict) -> str | None:
    ext = node.get("external_url")
    if ext:
        return ext
    for bl in node.get("bio_links") or []:
        if isinstance(bl, dict) and bl.get("url"):
            return bl["url"]
    return None


def _hd_propic_url(url: str | None) -> str | None:
    """Try to upgrade the profile pic CDN URL to the highest size."""
    if not url:
        return url
    return re.sub(r"s\d+x\d+", "s640x640", url)


def _bio_links(node: dict) -> list:
    """Bio links with display titles + pinned flag (not just raw URLs)."""
    out = []
    for bl in node.get("bio_links") or []:
        if isinstance(bl, dict) and (bl.get("url") or bl.get("lynx_url")):
            out.append({
                "url": bl.get("url") or bl.get("lynx_url"),
                "title": bl.get("title") or "",
                "is_pinned": bool(bl.get("is_pinned")),
            })
    return out


def _badge_names(node: dict) -> list:
    """Account badges (e.g. 'new' on freshly-created accounts)."""
    out = []
    for b in node.get("account_badges") or []:
        if isinstance(b, str):
            out.append(b)
        elif isinstance(b, dict) and b.get("badge"):
            out.append(b["badge"])
    return out


def _highlights(node: dict) -> list:
    """Highlight story titles + covers (public logged-out)."""
    conn = node.get("lox_highlights_connection") or {}
    out = []
    for e in (conn.get("edges") or []):
        n = (e or {}).get("node") or {}
        if n.get("title"):
            out.append({
                "id": n.get("id"),
                "title": n.get("title"),
                "cover_url": n.get("cover_media_cropped_thumbnail_url"),
            })
    return out


def _linked_fb(node: dict) -> dict | None:
    """Linked Facebook Page info, when present."""
    info = node.get("linked_fb_info")
    if not isinstance(info, dict) or not info:
        return None
    return {k: info[k] for k in ("id", "name", "url") if info.get(k)}


def _related_profiles(node: dict) -> list:
    """Similar accounts Instagram itself includes (node or API shapes)."""
    rel = node.get("related_profiles")
    out = []
    if isinstance(rel, list):
        for r in rel:
            if isinstance(r, dict):
                u = r.get("username") or r.get("id")
                if u:
                    out.append(u)
    elif isinstance(rel, dict):
        for e in (rel.get("edges") or []):
            n = (e or {}).get("node") or {}
            u = n.get("username") or n.get("id")
            if u:
                out.append(u)
    return out


_CONTACT_KEYS = ("public_email", "public_phone_number", "business_email",
                 "business_phone_number", "contact_phone_number")


def _tri_known(node: dict, *keys: str) -> bool | None:
    """bool when the node serves any of `keys`, None when the shape is stripped.

    Logged-out page JSON often omits professional/contact fields entirely; on
    such nodes we must say "unknown" rather than a lying False.
    """
    if not any(k in node for k in keys):
        return None
    return any(bool(node.get(k)) for k in keys)


def _contact_exposed(node: dict, is_business: bool | None) -> bool | None:
    """Does the account display a public business contact button?

    True  -> a public email/phone/contact field is present on the profile
    False -> definitively no button (explicitly a non-business, or the node
             served empty contact fields on a professional account)
    None  -> not determinable from this node (stripped logged-out shape)
    """
    vals = [node.get(k) for k in _CONTACT_KEYS if k in node]
    if any(v for v in vals if v):
        return True
    if node.get("should_show_public_contacts") is not None:
        return bool(node["should_show_public_contacts"])
    if is_business is False:
        return False
    if is_business is True:
        # professional node that carried no contact payload at all -> ambiguous
        return False if any(k in node for k in _CONTACT_KEYS) else None
    return None


def norm_profile(node: dict) -> dict:
    media = node.get("edge_owner_to_timeline_media") or {}
    is_business = _tri_known(node, "is_business_account", "is_business")
    lr = node.get("latest_reel_media")
    try:
        last_reel = (datetime.fromtimestamp(lr, timezone.utc).isoformat()
                     if isinstance(lr, (int, float)) else None)
    except (OverflowError, OSError, ValueError):
        last_reel = None
    return {
        "id": _first(node.get("id"), node.get("pk")),
        "username": node.get("username"),
        "full_name": node.get("full_name"),
        "biography": node.get("biography"),
        "external_url": _external_link(node),
        "bio_links": _bio_links(node),
        "pronouns": node.get("pronouns") or [],
        "account_badges": _badge_names(node),
        "is_joined_recently": node.get("is_joined_recently"),
        "is_memorialized": bool(node.get("is_memorialized")),
        "is_coppa_enforced": bool(node.get("is_coppa_enforced")),
        "is_unpublished": bool(node.get("is_unpublished")),
        "has_any_clips": bool(node.get("has_any_clips")),
        "text_post_app_badge": {
            "shown": bool(node.get("show_text_post_app_badge")),
            "label": node.get("text_post_app_badge_label"),
        },
        "last_reel_at": last_reel,
        "highlights": _highlights(node),
        "linked_fb_page": _linked_fb(node),
        "related_profiles": _related_profiles(node),
        "is_private": bool(node.get("is_private")),
        "is_verified": bool(node.get("is_verified")),
        "is_business": is_business,
        "business_category": _first(node.get("business_category_name"),
                                    node.get("category_name")),
        "business_email": _first(node.get("business_email"), node.get("public_email")),
        "business_phone_number": _first(node.get("business_phone_number"),
                                        node.get("public_phone_number")),
        "business_contact_exposed": _contact_exposed(node, is_business),
        "profile_pic_url": _first(node.get("profile_pic_url_hd"),
                                  node.get("profile_pic_url")),
        "counts": {
            "followers": _count(node, "follower_count", "edge_followed_by"),
            "following": _count(node, "following_count", "edge_follow"),
            "posts": _count(node, "all_media_count", "edge_owner_to_timeline_media"),
        },
        "post_page_info": media.get("page_info"),
        "recent_posts": [e.get("node") or {} for e in (media.get("edges") or [])],
    }
