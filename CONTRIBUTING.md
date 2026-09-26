# Contributing to InstaCloak

Contributions are welcome — bug reports, parser fixes, and features alike.
This tool scrapes a site that rotates its markup constantly, so parser
maintenance is the highest-value contribution anyone can make.

Read [ETHICS.md](ETHICS.md) first. Changes that widen the tool's scope beyond
public data, or that weaken its no-fabrication guarantees, will not be merged.

## Quick contribution loop

```bash
git clone https://github.com/Ahmad170412/InstaCloak.git
cd InstaCloak
python3.11 -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

Before you open a pull request:

```bash
python tests/test_instacloak.py   # 29 offline tests, no network needed
```

That suite is the whole quality gate — it runs in about a second and CI runs
the same command across Linux, macOS, and Windows.

## Where to make changes

Each concern owns one module, so keep the fix where it belongs:

| Symptom | Change lives in |
|---|---|
| Profile fields missing or wrong | `instacloak/profile.py` |
| Post fields missing or wrong | `instacloak/post.py` |
| Carousel/media candidates wrong | `instacloak/fetch.py` |
| A field is buried in an unknown blob | `instacloak/jsonutil.py` |
| Walled/skipped labeling is wrong | `instacloak/report.py` |

Instagram's JSON shapes change every few weeks. When a run silently loses
fields, that is a parser-shape problem, not a browser problem — see
[How the data is sourced](README.md#how-the-data-is-sourced-2026-realities).

## Guidelines

1. **Add a test with every parser change.** Fixtures live at the top of
   `tests/test_instacloak.py`. Use fabricated data only — never paste real
   account data, emails, or handles into a fixture.
2. **Never commit credentials.** `config.toml` is gitignored. Use
   `config.example.toml` as the template and env vars for anything secret.
3. **Keep it offline-testable.** Parsing and normalization must not require a
   browser or network. If a change needs a live page to verify, it belongs in a
   different layer.
4. **Preserve the no-fabrication rule.** If data is unavailable or walled, say
   so. Never synthesize plausible-looking values.
5. **Match the surrounding style.** Type hints on public functions, `say()` for
   terminal output, no new dependencies without discussion.

## Submitting

1. Fork the repository
2. Create a branch: `git checkout -b fix/carousel-candidates`
3. Make your change, with tests
4. Run `python tests/test_instacloak.py` and confirm it passes
5. Open a pull request against `main`, describing what broke and how you verified the fix

## Reporting a bug

Open an issue with the target's profile URL shape, the command you ran, and the
relevant part of `report.json` (with the username redacted if you prefer).
If the parser is the problem, `output/<username>/raw_profile.json` is usually
the fastest diagnosis — attach a trimmed excerpt with personal fields removed.

## Code of conduct

Be accurate and be reasonable. Disagree with the code, not the person. Assume
good faith, especially in a domain where people are often on the defensive
about their own footprint.
