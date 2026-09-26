<div align="center">

<img src="assets/logo.svg" alt="InstaCloak logo" width="320"/>

# InstaCloak

**The Instagram recon tool that walks the real site like a human — and writes everything down.**

It drives the *actual* Instagram website inside a stealth Chromium, doing what a
curious human does — open a profile, scroll, click into posts, read captions —
then synthesizes what it found into a structured report. The browser opens **in
front of you** so you can audit every run.

[![CI](https://github.com/Ahmad170412/InstaCloak/actions/workflows/ci.yml/badge.svg)](https://github.com/Ahmad170412/InstaCloak/actions)
[![Release](https://img.shields.io/github/v/release/Ahmad170412/InstaCloak?color=6366f1&label=release)](https://github.com/Ahmad170412/InstaCloak/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-06b6d4.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[**Quick Start**](#quick-start) · [**Usage**](#usage) · [**Report Bug**](https://github.com/Ahmad170412/InstaCloak/issues) · [**Request Feature**](https://github.com/Ahmad170412/InstaCloak/issues) · [**Ethics**](ETHICS.md)

</div>

---

## Why InstaCloak?

Most Instagram scrapers make you choose between getting caught, getting nothing,
or **getting lied to**. InstaCloak refuses all three:

- **It never fabricates data.** When Instagram login-walls a follower list, the
  report says `login-walled`. It will not quietly invent twelve "followers" from
  the suggestion pool and call it intelligence. A tool that invents data is worse
  than one that returns nothing.
- **Zero credentials required.** V1 runs fully logged-out on public data — no
  burner to burn, nothing to leak, nothing to lose when the platform changes its
  mind. The burner-login path is one menu option away, not a different tool.
- **It shows you the work.** The browser is visible and every finding is
  traceable to the page it came from. No black box handing you a dossier and
  expecting trust.
- **A real browser, not an HTTP client.** Requests are made by the browser
  itself (`fetch` from the page), so TLS, canvas, WebGL, and automation signals
  are the browser's own — not a fingerprint screaming into the void.

Beyond correctness, it reads like a person: jittered pacing, dwell time, warm-up
scrolls, humanized mouse curves, and a **persistent per-target footprint** that
accumulates cookies and history across runs, so the browser looks increasingly
real the longer you use it.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [How the data is sourced](#how-the-data-is-sourced-2026-realities)
- [Troubleshooting](#troubleshooting)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [Repository Structure](#repository-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Start

No API keys, no account, no configuration. Public data only.

```bash
git clone https://github.com/Ahmad170412/InstaCloak.git
cd InstaCloak

python3 -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

python3 main.py
```

You will get a banner, a menu, and a username prompt. First launch downloads the
stealth Chromium binary (~200MB) — that is normal, and it happens once.

Prefer to skip the prompts entirely?

```bash
python3 main.py -u instagram -y
```

> **Scripted runs need `-u`.** The interactive menu requires a TTY. A run with no
> `-u` and a non-TTY stdin exits with a usage hint instead of hanging.

> **Read [ETHICS.md](ETHICS.md) before your first run.** It defines the project's
> scope, the lines it will not cross, and your legal obligations.

---

## Architecture

One pass over a target, in this order:

```text
  launch ──▶ login? ──▶ profile ──▶ stories? ──▶ posts/media ──▶ social graph ──▶ report
    │           │          │            │              │              │            │
CloakBrowser  burner    web_profile  story tray    per-post     followers/    report.json
persistent   session   info API     (24h window)  JSON + media  following      + report.md
profile      (opt.)    + DOM       (opt.)         downloads    modal
             fallback                                          + wall detect
```

Three layers, strictly separated so the fragile parts stay testable:

| Layer | Modules | Depends on |
|---|---|---|
| **Orchestration** | `engine.py`, `cli.py`, `ui.py` | browser |
| **Browser** | `session.py`, `auth.py`, `human.py`, `fetch.py` | browser |
| **Pure logic** | `profile.py`, `post.py`, `stories.py`, `social.py`, `contacts.py`, `jsonutil.py`, `report.py` | nothing |

Everything in the bottom layer is offline-testable, which is why the 29-test
suite runs in about a second with no browser and no network. Instagram rotates
its JSON every few weeks; when a run silently loses fields, the fix lands in the
pure layer, not in a 1,700-line file.

---

## Features

| Feature | Description |
|---|---|
| **Profile intelligence** | Bio, name, pronouns, badges, verification, counts, HD profile pic, last-reel date, memorialized/suspended state |
| **Engagement realism** | Flags likely fake followers by comparing follower count against real interaction volume |
| **Post analysis** | Captions, hashtags, mentions, geotags, like/comment counts, timestamps, carousel expansion |
| **Contact discovery** | Emails, phones, and links scraped from bios and captions, each tagged with the exact source field |
| **Media capture** | Downloads post images and fully-expanded carousels; optional video |
| **Social graph** | Follower/following lists via the modal, with login-wall detection and honest labeling |
| **Stories** | 24-hour story tray scrape when a burner session is active |
| **Dual output** | `report.json` for your tooling, `report.md` for your eyes |
| **Terminal-first UX** | A Rich-rendered summary, a menu-driven CLI, and a fully non-interactive flag mode for cron |
| **Stealth by design** | Humanized mouse curves, jittered delays, persistent per-target browser footprint |

### Coverage by session mode

| Data | V1 (logged-out) | V1 (burner login, menu 2) |
|---|---|---|
| Profile: bio, name, verification, counts, propic URL | Yes | Yes |
| Extra metadata: pronouns, badges, highlights, memorialized… | Yes | Yes |
| Business contact email/phone | Yes, via profile API | Yes |
| Recent posts: captions, hashtags, mentions, geotags, counts | Yes | Yes |
| Media downloads (post images; carousels fully) | Yes | Yes, + stories |
| Followers/following **counts** | Yes | Yes |
| Followers/following **lists** | Partial — usually login-walled | Yes, full lists |
| Stories | No — login-walled | Best-effort (24h window) |
| Tagged users, commenters | Yes (as embedded in post data) | Deeper comment crawl |
| Email/phone scans of bio + captions | Yes | Follower contacts (planned) |

One hard platform limit no tool can beat: **private-account content**. Logged-out
follower lists and current stories are login-walled; configure a burner login to
unlock them.

---

## Installation

### Requirements

- Python **3.11+** (uses `tomllib`)
- macOS, Linux, or Windows
- ~200MB disk for the auto-downloaded Chromium binary

### From source

```bash
git clone https://github.com/Ahmad170412/InstaCloak.git
cd InstaCloak
python3 -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### As an installable CLI

```bash
pip install -e .
instacloak --version
```

This puts an `instacloak` command on your `PATH`. All three entry points are
equivalent:

```bash
python3 main.py
python3 -m instacloak
instacloak
```

### Optional — latest stealth build

CloakBrowser ships a free license key that unlocks the newest stealth binary:

```bash
cloakbrowser login
```

Or set `CLOAKBROWSER_LICENSE_KEY` in your environment. The bundled build works
without it.

---

## Configuration

Every setting is optional — the tool is useful with zero configuration.

### Environment variables

| Variable | Required | Default | Notes |
|---|---|---|---|
| `INSTACLOAK_PROXY` | No | — | Proxy URL; overrides `[proxy].url` in the config file |
| `INSTACLOAK_OUTPUT_DIR` | No | `output` | Where reports and media are written |
| `INSTACLOAK_PROFILES_DIR` | No | `profiles` | Where persistent browser footprints live |
| `INSTACLOAK_HEADLESS` | No | `false` | `1` runs without a visible window |
| `INSTACLOAK_LOGIN` | No | `false` | `1` enables the burner session |
| `INSTACLOAK_LOGIN_USERNAME` | No | — | Burner account username |
| `INSTACLOAK_LOGIN_PASSWORD` | No | — | Burner account password |
| `CLOAKBROWSER_LICENSE_KEY` | No | — | Free key for the latest stealth binary |
| `INSTACLOAK_COLOR` | No | auto | `1` forces color, `0` or `NO_COLOR` disables it |

```bash
# Linux / macOS
export INSTACLOAK_HEADLESS=1
export INSTACLOAK_PROXY="http://user:pass@host:port"

# Windows PowerShell
$env:INSTACLOAK_HEADLESS = "1"
```

### Config file

Copy the template and adjust. It is gitignored, so your credentials stay local.

```bash
cp config.example.toml config.toml
```

```toml
[instacloak]
headless    = false      # watch the browser work
max_posts   = 12          # recent posts to deep-visit
min_delay   = 1.2         # humanized pacing between actions (seconds)
max_delay   = 3.5
download_media = true
attempt_followers = true
deep        = false       # extra logged-out data: HD propic + highlight covers

[proxy]                  # bring your own residential proxy (sticky session)
enabled = true
url     = "http://user:pass@host:port"

[login]                  # burner account — never your primary
enabled  = false
username = ""
password = ""
```

> **Datacenter IPs get blocked in seconds.** A residential proxy plus `geoip`
> timezone/locale matching is the single biggest difference between a clean run
> and a throttled one. The tool runs without a proxy, just far less reliably.

---

## Usage

```bash
python3 main.py                                    # interactive: banner → menu → target → y/N
python3 main.py -u instagram -y                    # skip all prompts
python3 main.py --headless -u instagram -y         # non-interactive, for cron/CI
```

### Flags

| Flag | Effect |
|---|---|
| `-u`, `--username` | Target username; skips the prompt |
| `-y`, `--yes` | Skip the `y/N` confirmation (auto-saves `report.md`) |
| `--headless` | Run without a visible window |
| `--config PATH` | Use a specific `config.toml` |
| `--max-posts N` | Override how many recent posts to deep-visit |
| `--no-media` | Skip media downloads |
| `--no-followers` | Skip the follower/following attempt entirely |
| `--deep` | Extra logged-out data: HD profile pic + highlight story covers |
| `--mode {login,logout}` | Force burner session, or force logged-out |
| `--version` | Print the version and exit |

> **`--no-followers` is not the same as being walled.** Skipped lists are reported
> as `skipped: true` with `walled: false`, because the run never hit a wall. The
> report will not claim a restriction that was not encountered.

### Output

```text
output/<username>/
├── report.json        # everything: profile, posts, contacts, hashtags, media…
├── report.md          # readable markdown export (offered as y/N after each run)
├── raw_profile.json   # the untouched profile node, for debugging
└── media/             # downloaded images, named by shortcode
```

After the terminal summary you are asked `Save markdown report (report.md)? [y/N]`.
Non-interactive runs with `-y` auto-save it; plain piped runs keep the default.

### Burner login

The interactive menu writes burner credentials to `config.toml` for you. For
scripted setups, use env vars:

```bash
export INSTACLOAK_LOGIN=1
export INSTACLOAK_LOGIN_USERNAME="your_burner"
export INSTACLOAK_LOGIN_PASSWORD="your_password"
python3 main.py -u someaccount -y --mode login
```

> **Never use your primary account.** Burners exist precisely so a ban costs you
> nothing. Login challenges pause and wait for you to solve them in the visible
> window.

---

## How the data is sourced (2026 realities)

- **Profile** — the `web_profile_info` API, fetched from inside the page with the
  browser's own TLS and cookies, for the richest data including business contact
  fields. Falls back to the profile page's embedded JSON (`xig_user_by_username`
  node) when the API throttles you, which datacenter IPs hit constantly (HTTP
  401 "wait a few minutes").
- **Posts** — post pages embed their full JSON: code, caption, like and comment
  counts, media candidates, user tags, location. No GraphQL `doc_id` chasing;
  those identifiers rotate every 2–4 weeks and break raw scrapers.
- **Social graph** — follower/following **counts** arrive with the profile;
  **lists** require the modal, which logged-out Instagram login-walls. When walled
  we say so and record counts only.
- **Both shapes handled** — Instagram serves modern and legacy markup depending
  on the account and the surface, so the parsers normalize each into one schema.
  Run the offline suite after an Instagram update breaks something.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `profile unavailable (api_unavailable)` | Your IP is throttled. Use a residential proxy and retry later |
| Followers show `login-walled` | Expected when logged out. Configure a burner login (menu 2) to collect lists |
| Launch error about license or binary | Run `cloakbrowser login`, or set `CLOAKBROWSER_LICENSE_KEY`; confirm the ~200MB binary can download |
| No visible browser window | `headless = true` or `INSTACLOAK_HEADLESS=1` is set — unset it |
| Run exits immediately in a script | The menu needs a TTY. Pass `-u <target>` and `-y` |
| Fields missing after a site change | Run `python tests/test_instacloak.py`; if fixtures fail, Instagram changed its JSON again — update `instacloak/profile.py` / `post.py` |

---

## Testing

The entire suite is offline — no browser, no network, about a second to run:

```bash
python tests/test_instacloak.py
# ALL 29 OFFLINE TESTS PASSED
```

CI runs the same command on Linux, macOS, and Windows across Python 3.11 and
3.13, plus a no-browser entry-point smoke test. Badge at the top tracks it live.

---

## Roadmap

**Shipped in V1 (1.0.0)**

- [x] Burner-account login — unlocks full follower/following lists and best-effort stories
- [x] Package refactor — `instacloak/` library plus an installable `instacloak` CLI
- [x] Rich-rendered terminal UI and run-mode selection
- [x] DOM-profile fallback for API throttles, with honest wall labeling
- [x] Cross-OS CI and a 29-test offline suite

**Next up — V1.1**

- [ ] Auto-footprint mode (menu 3) — the browser scrolls Reels and related profiles between runs to grow a believable history before engaging a target

**Later — V1.2+**

- [ ] Follower contact mining — walk follower usernames to their bios and captions to surface emails and phones (Osintgram parity)

---

## Repository Structure

```text
InstaCloak/
├── main.py                    # thin wrapper → instacloak.cli
├── instacloak/
│   ├── cli.py                 # argument parsing, menu, command runners (main())
│   ├── engine.py              # orchestration: launch → profile → posts → report
│   ├── config.py              # config.toml + env loading; burner-login writer
│   ├── session.py             # CloakBrowser launch, persistent per-target profiles
│   ├── auth.py                # burner login state machine + challenge handling
│   ├── human.py               # jittered timing, mouse curves, scrolls, popups
│   ├── jsonutil.py            # digging into Instagram's embedded JSON (pure)
│   ├── fetch.py               # in-page fetch + media downloads, all via the browser
│   ├── profile.py             # profile extraction + normalization (modern + legacy)
│   ├── post.py                # post extraction + normalization + post-page visits
│   ├── stories.py             # logged-in story tray scrape
│   ├── social.py              # followers/following modal + login-wall detection
│   ├── contacts.py            # email/phone/hashtag/mention scanning (pure)
│   ├── report.py              # report assembly + summary printing
│   └── ui.py                  # Rich console, banner, shared printing helpers
├── tests/
│   └── test_instacloak.py     # 29 offline parser/extraction tests
├── assets/
│   └── logo.svg
├── .github/workflows/ci.yml   # cross-OS, multi-version CI
├── config.example.toml        # template — copy to config.toml
├── CONTRIBUTING.md
├── ETHICS.md                  # read before using this tool
└── LICENSE                    # MIT
```

---

## Contributing

Contributions are welcome, especially parser fixes — Instagram's markup rotates
every few weeks and keeping up is the highest-value work here.

1. Fork the repository
2. Create a branch: `git checkout -b fix/carousel-candidates`
3. Make your change, **with a test**
4. Run the quality gate: `python tests/test_instacloak.py`
5. Open a pull request against `main`

Use fabricated data in fixtures — never paste real account data, emails, or
handles into a test. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## License

MIT — see [LICENSE](LICENSE).

InstaCloak only touches **public** data, the same pages any human can open.
Scraping public pages still technically violates Instagram's Terms of Service.
Keep volume low, use your own infrastructure, and do not point it at private
accounts. What you do with it is on you — see [ETHICS.md](ETHICS.md).
