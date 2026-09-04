"""Tiny terminal helpers + the banner and shared copy text.

Every printed line goes through `c()`/`say()`, which strips terminal control
characters from the *text* first: profiles, bios, and post captions are
attacker-controlled (any public Instagram user), and a crafted bio must not
be able to inject ANSI escape sequences into the operator's terminal.
"""

from __future__ import annotations

import re
import sys

BANNER = r"""██╗       ███╗   ██╗███████╗████████╗ █████╗   ██████╗  ██████╗  █████╗ ██╗  ██╗
██║       ████╗  ██║██╔════╝╚══██╔══╝██╔══██╗  ██╔════╝ ██╔═══██╗██╔══██╗██║ ██╔╝
██║       ██╔██╗ ██║███████╗   ██║   ███████║  ██║      ██║   ██║███████║█████╔╝
██║       ██║╚██╗██║╚════██║   ██║   ██╔══██║  ██║      ██║   ██║██╔══██║██╔═██╗
██║       ██║ ╚████║███████║   ██║   ██║  ██║  ╚██████╗ ╚██████╔╝██║  ██║██║  ██╗
╚═╝       ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
        stealth instagram recon -- public data, human touch"""

NOTES = """\
Will collect (public data only, logged-out):
  - profile: bio, stats, verification, business category, contact info
  - recent posts: captions, hashtags, mentions, likes/comments, geotags
  - media: profile picture + post images (videos optional)
  - social graph: follower/following COUNTS always; usernames best-effort
    (Instagram login-walls these for logged-out visitors -- configure a
    burner login via the Login menu option to unlock them)
  - contact info: public email/phone (business profiles) + bio/caption scans

Cautions:
  - Private accounts return almost nothing. That's Instagram, not a bug.
  - Use a residential proxy (config.toml) for real-world stealth; datacenter
    IPs are blocked instantly by Instagram.
  - Keep volume low: single targets, spaced-out runs. This is recon, not a
    firehose.
  - Public data, but scraping technically violates Instagram's ToS. Your call.
"""

ANSI = {"green": 32, "cyan": 36, "yellow": 33, "red": 31, "dim": 2, "bold": 1,
        "magenta": 95, "gold": 93}

# C0 control chars + DEL (keep \n and \t). Strips ESC sequences, bells, etc.
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def c(text: str, *styles: str) -> str:
    text = _CONTROL_RE.sub("", text)
    if not sys.stdout.isatty():
        return text
    codes = ";".join(str(ANSI[s]) for s in styles if s in ANSI)
    return f"\x1b[{codes}m{text}\x1b[0m" if codes else text


def say(msg: str, *styles: str) -> None:
    print(c(msg, *styles))


def section(n: int, total: int, msg: str) -> None:
    say(f"\n[{n}/{total}] {msg}", "cyan", "bold")


def say_banner() -> None:
    """Print the banner: purple ASCII letters, yellow tagline."""
    lines = BANNER.splitlines()
    for line in lines[:-1]:
        say(line, "magenta", "bold")
    say(lines[-1], "gold", "bold")
