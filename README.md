# InstaCloak

**The Instagram recon tool that walks the real site like a human — and writes everything down.**

Classic OSINT tools (Osintgram et al.) hammer Instagram's private API from a
headless bot until the platform notices. InstaCloak does something they can't:
it drives the *actual Instagram website* inside
[CloakBrowser](https://github.com/CloakHQ/cloakbrowser)'s stealth Chromium,
doing exactly what a curious human does — open a profile, scroll a bit, click
into posts, read captions — but systematically, with every scrap of public
intel recorded into a structured report.

**V1 = logged-out, public-data only, single target.** No credentials, no
burner accounts, the lowest possible ban risk. And unlike the spooky tools
that vanish into the shadows, this browser opens *in front of you* so you can
watch it work, live, like your own personal recon assistant with perfect
recall.

---

## Why you should use this

**Because every other option makes you choose between getting caught, getting
nothing, or getting lied to.** InstaCloak is the tool that refuses all three:

- **Zero account, zero risk.** It runs logged-out on public data. No burner to
  burn, no credentials to leak, nothing to lose when a platform changes its
  mind. If you want *more* later, the burner-login path is one menu option
  away — not a whole different tool.
- **It shows you the work.** The browser opens on your screen and you watch it
  scroll, click, and read like a person. Every run is auditable, every finding
  traceable. No black box that hands you a dossier and expects trust.
- **It never makes things up.** When Instagram login-walls a follower list,
  the report says `login-walled` — it does not quietly invent twelve "followers"
  from the suggestion pool and call it intelligence. Tools that fabricate data
  are worse than tools that return nothing; this one has honesty built in.
- **It turns raw pages into actual intel.** Not a dump of JSON you'll never
  read — a synthesized report: engagement realism that flags fake followers,
  mention and hashtag networks that expose partnerships, contact details with
  the exact source they came from, account-state signals (memorialized,
  suspended, freshly-created) that classic tools never surface.
- **It looks human because it moves like one.** Jittered pacing, dwell time,
  warm-up scrolls, a persistent per-target footprint that grows more believable
  with every run. The stealth premise isn't a trick — it's behaving like the
  person the platform assumes you are.
- **It fits your workflow.** One command, full report. JSON for your tools,
  markdown for your eyes, a cron-friendly flag mode (`-u target --headless -y`)
  that runs unattended, and reports that land in tidy per-target directories.
- **It's open source, MIT-licensed, and scoped on purpose.** Read the code,
  keep it forever, and know exactly where the lines are — public data only,
  no private-account bypass, no mass contact harvesting.

---

## What it collects

Everything Instagram shows the public, pulled clean and organized:

| Data | V1 (logged-out) | V1 (burner login, menu 2) |
|---|---|---|
| Profile: bio, name, verification, counts, propic URL | Yes | — |
| Extra metadata: pronouns, badges, highlights, last-reel date, memorialized… | Yes | — |
| Business contact email/phone (business profiles) | Yes, via profile API | — |
| Recent posts: captions, hashtags, mentions, likes/comments, timestamps | Yes | — |
| Geotags / locations | Yes | — |
| Media downloads (post images; carousels fully) | Yes | + stories |
| Followers/following **counts** | Yes | — |
| Followers/following **lists** | Partial — usually login-walled (counts only) | Yes, full lists |
| Stories | No — login-walled | Best-effort (24h window) |
| Tagged users, commenters | Yes (as embedded in post data) | Deeper comment crawl |
| Email/phone scans of bio + captions | Yes | Follower contacts (planned) |

Hard platform limits (no tool can beat these): private-account content.
Logged-out follower lists / current stories are login-walled; configure a
burner login (menu 2, or `INSTACLOAK_LOGIN=1` + username/password env vars)
to unlock them.

## Why it doesn't get caught

- **A real browser, not a scraper.** CloakBrowser is Chromium patched at the
  C++ level — canvas, WebGL, audio, TLS, automation signals. Requests are made
  by the browser itself (`fetch` from the page), never by raw HTTP libraries
  that fingerprint like a bot screaming into the void.
- **The human touch is the whole point.** Humanized mouse curves, jittered
  delays between every action, warm-up scrolls, dwell time on posts. Nothing
  runs on fixed timers, because humans don't.
- **A persistent footprint per target.** Each target gets its own profile
  directory (`profiles/<username>/`) — cookies, history and cache accumulate
  across runs, so the "person" behind the browser looks increasingly real the
  longer you use it.
- **IP hardening (your side).** Point it at a **residential** proxy and
  `geoip` matches timezone/locale/WebRTC to the exit IP. Datacenter IPs are
  blocked by Instagram in seconds — the tool *will* run without a proxy, but
  from a clean residential connection it runs dramatically better.

## Requirements

- Python 3.11+ (uses `tomllib`)
- ~200MB disk for the CloakBrowser Chromium binary (auto-downloaded on first run)
- macOS / Linux / Windows
- Optional: a residential proxy + `cloakbrowser login` free license key for the
  latest binary (see [cloakbrowser.dev/free](https://cloakbrowser.dev/free))

## Quickstart

```bash
python3.11 -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# optional, one-time: CloakBrowser license for the latest stealth build
# cloakbrowser login

python3 main.py                    # interactive: banner → menu → OSINT → username → y/N
# (same thing: python3 -m instacloak)
```

## Project layout

The code is a package, not one file — each concern has its own module, so a
change to (say) parsing never touches the browser logic:

```
main.py                  thin wrapper → instacloak.cli
instacloak/
├── cli.py               argument parsing, menu, command runners (main())
├── engine.py            run orchestration: launch → profile → posts → report
├── config.py            config.toml + env loading; burner-login config writer
├── session.py           CloakBrowser launch (persistent per-target profiles)
├── auth.py              burner login state machine + challenge handling
├── human.py             jittered timing, mouse curves, scrolls, popups
├── jsonutil.py          digging into Instagram's embedded JSON (pure)
├── fetch.py             in-page fetch + media downloads (all via the browser)
├── profile.py           profile extraction + normalization (modern + legacy)
├── post.py              post extraction + normalization + post-page visits
├── stories.py           logged-in story tray scrape
├── social.py            followers/following modal (login-wall detection)
├── contacts.py          email/phone/hashtag/mention scanning (pure)
├── report.py            report assembly + summary printing
└── ui.py                ANSI colors, banner, shared printing helpers
tests/test_instacloak.py  offline parser/extraction tests
```

Instagram's JSON shapes rotate every few weeks; when a run silently loses
fields, the fix lives in `profile.py`/`post.py` (shape → schema mapping) or
`jsonutil.py` (blob digging) — not scattered through a 1,700-line file.

Optionally install as a real CLI: `pip install -e .` then run `instacloak`.

First launch downloads the stealth Chromium binary (~200MB) — that's normal.

### Flags

```bash
python3 main.py -u instagram -y        # skip prompts
python3 main.py --headless -u natgeo -y   # fully non-interactive (cron/CI)
python3 main.py --headless             # no visible window (menu still asks)

> **Piped/CI stdin**: the menu is interactive-only. A run whose stdin isn't a
> TTY and that has no `-u` exits with a usage hint — always pass `-u` (plus
> `-y` to auto-save `report.md`) for scripted runs.

> **Login mode**: interactive OSINT runs ask *logged out vs logged in (burner)*
> **only when burner credentials are configured** (default: logged out).
> Scripted runs (`-y`/CI) skip the question and use the config as-is.
python3 main.py --max-posts 6          # deep-visit N recent posts
python3 main.py --no-media             # skip downloads
python3 main.py --no-followers         # skip the (usually walled) list attempt
python3 main.py --deep                 # HD profile pic + highlight story covers
python3 main.py -u natgeo -y --mode login   # force burner session in scripts
python3 main.py -u natgeo -y --mode logout  # force logged-out (ignore config login)
```

### Configuration

Copy `config.example.toml` → `config.toml` and adjust. Highlights:

```toml
[instacloak]
headless = false        # watch the browser work
max_posts = 12          # recent posts to deep-visit
min_delay = 1.2         # humanized pacing between actions
max_delay = 3.5

[proxy]                 # bring your own residential proxy (sticky session)
enabled = true
url = "http://user:pass@host:port"
```

Environment overrides: `INSTACLOAK_PROXY`, `INSTACLOAK_OUTPUT_DIR`,
`INSTACLOAK_PROFILES_DIR`, `INSTACLOAK_HEADLESS=1`,
`CLOAKBROWSER_LICENSE_KEY`.

## Output

```
output/<username>/
├── report.json        # everything: profile, posts, contacts, hashtags, media…
├── report.md          # readable markdown export (offered as y/N after each run)
├── raw_profile.json   # the untouched profile node (debugging)
└── media/             # downloaded images (named by shortcode)
```

After the terminal summary, you're asked `Save markdown report (report.md)? [y/N]`
— answer `y` to also get the human-readable `report.md`. Non-interactive runs
with `-y` (cron/CI) auto-save it; plain piped runs keep the default (no).

## How the data is sourced (2026 realities)

- **Profile**: the `web_profile_info` API (via in-page fetch with the browser's
  own TLS/cookies) for the richest data incl. business contact fields; falls
  back to the profile page's embedded JSON (`xig_user_by_username` node) when
  the API is throttled (commonly: datacenter IPs → HTTP 401 "wait a few
  minutes").
- **Posts**: post pages embed their full JSON (code, caption, like/comment
  counts, media candidates, usertags, location). No GraphQL `doc_id` chasing —
  those rotate every 2–4 weeks and break raw scrapers.
- **Social graph**: follower/following **counts** come with the profile;
  **lists** require the modal, which logged-out Instagram login-walls. When
  walled we say so and record counts only — no fabricated data, ever.
- Because structure changes over time, parsers handle both modern and legacy
  shapes. Run the offline suite after Instagram updates break something:

```bash
./venv/bin/python tests/test_instacloak.py   # 29 tests, no network needed
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `profile unavailable (api_unavailable)` | API throttled your IP. Use a residential proxy; retry later. |
| Followers show `login-walled` | Normal for logged-out. Configure a burner login (menu 2) to collect lists. |
| Launch error about license/binary | `cloakbrowser login`, or set `CLOAKBROWSER_LICENSE_KEY`; check the ~200MB binary can download. |
| Empty posts after a site change | Run `tests/test_instacloak.py`; if fixtures fail, Instagram changed its JSON again — update the parsers in `instacloak/profile.py` / `post.py`. |

## Roadmap

**Shipped in V1 (1.0.0):**

- [x] **Burner-account login** — menu 2 saves credentials to `config.toml`;
      logged-in runs share one persistent burner profile and unlock full
      follower/following lists + best-effort stories. Challenges pause and wait
      for you to solve them in the visible window.
- [x] Refactor into a package: `instacloak/` library (`python3 -m instacloak`) + installable `instacloak` CLI (`pip install -e .`).

**Next up — V1.1:**

- [ ] **Auto-footprint mode** (menu 3) — the browser scrolls Reels / related
      profiles by itself between runs to grow a believable browsing history
      before a target engagement.

**Later — V1.2+:**

- [ ] **Follower contact mining** — walk follower usernames → bios/captions to
      surface emails/phones (Osintgram parity).

## Legal / ethics

InstaCloak only touches **public** data — the same pages any human can open.
Scraping public pages still technically violates Instagram's Terms of Service.
Keep volume low (single targets, spaced-out runs), use your own infrastructure,
and don't point it at private accounts. What you do with it is on you.

**Read [ETHICS.md](ETHICS.md) before using this tool** — it defines the
project's scope, the lines it will not cross, and your legal obligations.
