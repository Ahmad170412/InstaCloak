"""Burner-account login: state probing, the login flow, challenge handling.

The burner session is optional (menu 2 / config `[login]` / env vars). It
unlocks full follower/following lists and stories. Every failure degrades to
logged-out instead of crashing the run.
"""

from __future__ import annotations

import random
import re
import time

from .human import human_delay
from .ui import say

LOGIN_URL = "https://www.instagram.com/accounts/login/"
HOME_URL = "https://www.instagram.com/"
CHALLENGE_RE = re.compile(
    r"(?i)(confirmation code|enter the code|challenge required|we need to make sure "
    r"it's you|suspicious activity|we\'ve sent a code|add another device|verify it's you)")


def _login_state(page) -> dict:
    """DOM probe of the current auth state."""
    try:
        return page.evaluate("""() => {
            const visible = (el) => !!el && el.offsetParent !== null;
            const loginCtas = [...document.querySelectorAll(
                'a[href*="/accounts/login"], a[href*="/accounts/signup"]')]
                .filter(visible).length;
            const home = !!document.querySelector('svg[aria-label="Home"]');
            const avatar = !!document.querySelector('nav svg[aria-label="Profile"], ' +
                'nav img[alt], [aria-label="Profile"]');
            const inbox = !!document.querySelector('a[href*="/direct/inbox"]');
            return {loginCtas, home, avatar, inbox};
        }""")
    except Exception:  # noqa: BLE001
        return {}


def login_needed(state: dict) -> bool:
    """Pure decision: does this session still need the login flow?"""
    if not state:
        return True  # couldn't probe -> attempt login (harmless if already in)
    return bool(state.get("loginCtas")) or not (state.get("home")
                                                or state.get("avatar")
                                                or state.get("inbox"))


def _click_not_now(page) -> None:
    """Dismiss 'Save your login info?' / 'Save your password?' prompts."""
    try:
        for _ in range(3):
            clicked = page.evaluate("""() => {
                const btns = [...document.querySelectorAll('button, div[role="button"]')];
                const b = btns.find(el => (el.innerText || '').trim().toLowerCase() === 'not now');
                if (b) { b.click(); return true; }
                return false;
            }""")
            if not clicked:
                break
            page.wait_for_timeout(1200)
    except Exception:  # noqa: BLE001
        pass


def ensure_login(page, cfg: dict, username: str) -> bool:
    """Make sure the burner session is logged in. Returns True if logged in."""
    user, pw = cfg.get("login_username", ""), cfg.get("login_password", "")
    if not (cfg.get("login_enabled") and user and pw):
        return False

    # 1) already logged in? (persistent session from a previous run)
    try:
        page.goto(HOME_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
    except Exception:  # noqa: BLE001
        pass
    if not login_needed(_login_state(page)):
        say(f"  already logged in as @{user}", "green")
        return True

    # 2) perform the login
    say(f"  logging in as @{user} ...", "magenta")
    try:
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
        human_delay(cfg, 1.5, 3.0)
    except Exception:  # noqa: BLE001
        pass
    try:
        try:
            page.wait_for_selector('input[name="username"]', timeout=15000)
        except Exception:  # noqa: BLE001 - page may bounce/redirect; retry once
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector('input[name="username"]', timeout=20000)
        page.type('input[name="username"]', user, delay=random.uniform(35, 80))
        human_delay(cfg, 0.4, 0.9)
        page.type('input[name="password"]', pw, delay=random.uniform(35, 80))
        human_delay(cfg, 0.4, 0.9)
        page.click('button[type="submit"]')
    except Exception as exc:  # noqa: BLE001
        say(f"  login form interaction failed: {exc}", "yellow")
        return False

    # 3) wait for completion (feed, challenge, or failure)
    deadline = time.time() + 45
    challenge = False
    while time.time() < deadline:
        page.wait_for_timeout(2500)
        try:
            body = (page.evaluate("() => document.body ? document.body.innerText : ''") or "")
        except Exception:  # noqa: BLE001
            body = ""
        if not login_needed(_login_state(page)):
            _click_not_now(page)
            say(f"  logged in as @{user}", "green")
            return True
        if CHALLENGE_RE.search(body):
            challenge = True
            break
    if challenge:
        say("  Instagram is challenging this login (verification code / suspicious activity).", "yellow")
        say("  Complete it in the browser window -- you have 120 seconds.", "yellow")
        deadline = time.time() + 120
        while time.time() < deadline:
            page.wait_for_timeout(3000)
            if not login_needed(_login_state(page)):
                _click_not_now(page)
                say(f"  logged in as @{user}", "green")
                return True
        say("  challenge not completed in time; continuing logged-out.", "yellow")
        return False
    say("  login did not complete; continuing logged-out.", "yellow")
    return False
