"""Entry point: argument parsing, the interactive menu, and the command runners.

`python3 -m instacloak` and the root `main.py` wrapper both land here. The
menu offers OSINT / Login (burner) / Footprint / Exit; passing `-u` skips the
menu and runs OSINT directly (flag overrides merge into the loaded config).
"""

from __future__ import annotations

import argparse
import getpass
import sys

from . import __version__
from .auth import ensure_login
from .config import load_config, save_login_config
from .engine import collect, output_dir
from .report import print_summary, write_markdown
from .session import open_session
from .ui import ANSI, NOTES, c, say, say_banner

MENU = """\
  {yellow}1{reset}  {yellow}OSINT{reset}
  {yellow}2{reset}  {yellow}Login (burner){reset}
  {yellow}3{reset}  {yellow}Footprint{reset}
  {yellow}4{reset}  {yellow}Exit{reset}
"""


def cli_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="InstaCloak - stealth Instagram OSINT via a humanized browser",
    )
    p.add_argument("-u", "--username", help="target Instagram username (skips prompt)")
    p.add_argument("-y", "--yes", action="store_true", help="skip y/N confirmation")
    p.add_argument("--config", default=None, help="path to config.toml")
    p.add_argument("--headless", action="store_true", help="run without a visible window")
    p.add_argument("--max-posts", type=int, default=None, help="override max posts to visit")
    p.add_argument("--no-media", action="store_true", help="don't download media")
    p.add_argument("--no-followers", action="store_true", help="skip follower/following attempt")
    p.add_argument("--deep", action="store_true",
                   help="extra logged-out data: HD profile pic + highlight story covers")
    p.add_argument("--version", action="version", version=f"InstaCloak {__version__}")
    return p.parse_args()


def show_menu() -> str:
    """Display the main menu and return the user's choice."""
    if sys.stdout.isatty():
        yellow_code = f"\x1b[{ANSI['yellow']}m"
        reset = "\x1b[0m"
    else:
        yellow_code = reset = ""

    say_banner()
    say(f"\n  InstaCloak v{__version__}", "gold")
    say(MENU.format(yellow=yellow_code, reset=reset))

    try:
        choice = input(c("  > ", "bold")).strip()
    except (EOFError, KeyboardInterrupt):
        choice = "4"
    return choice


def run_osint(cfg: dict, args) -> None:
    """Run the OSINT collection flow."""
    username = args.username
    if not username:
        try:
            username = input(c("  target username: ", "bold")).strip().lstrip("@").lower()
        except EOFError:
            say("\n  no target given — aborting.", "yellow")
            return
        if not username:
            say("  no target.", "yellow")
            return

    say(f"\n  Target: @{username}\n", "bold")
    say(NOTES)
    if not args.yes:
        try:
            ok = input(c("\n  Proceed? [y/N] ", "bold")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            say("\n  aborted.", "yellow")
            return
        if ok not in ("y", "yes"):
            say("  aborted.", "yellow")
            return

    try:
        report = collect(cfg, username)
        print_summary(report)
        _offer_markdown_export(cfg, report, args)
    except KeyboardInterrupt:
        say("\n  interrupted by user.", "yellow")
    except Exception as exc:  # noqa: BLE001
        say(f"\n  unexpected error: {exc.__class__.__name__}: {exc}", "red")
        say("  re-run with a residential proxy (config.toml) if this looks "
            "like an Instagram block, or check the traceback above.", "yellow")
        raise


def _offer_markdown_export(cfg: dict, report: dict, args) -> None:
    """Ask whether to also write report.md next to report.json.

    Interactive runs get a y/N prompt. Non-interactive runs with -y (cron/CI)
    auto-save so the markdown is always produced; a plain piped run without -y
    keeps the default (no).
    """
    if args.yes:
        save_md = True
    elif sys.stdin.isatty():
        try:
            ans = input(c("\n  Save markdown report (report.md)? [y/N] ", "bold")).strip().lower()
            save_md = ans in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            save_md = False
    else:
        save_md = False
    if save_md:
        try:
            md_path = write_markdown(report, output_dir(cfg, report["target"]))
            say(f"  markdown: {c(str(md_path), 'green')}")
        except Exception as exc:  # noqa: BLE001 - export must never crash the run
            say(f"  could not write markdown report: {exc}", "yellow")


def run_login(cfg: dict, args) -> None:
    """Configure the burner-account login (saved to config.toml)."""
    say("\n  Burner login — full follower/following lists + stories require a", "bold")
    say("  logged-in session. NEVER use your primary account.", "bold")
    say("  Credentials are saved to config.toml (chmod 600) or use the env vars\n")
    who = cfg.get("login_username") or "none"
    say(f"  current: {'enabled' if cfg.get('login_enabled') else 'disabled'} (@{who})\n")
    try:
        ok = input(c("  Configure burner login? [y/N] ", "bold")).strip().lower()
    except (EOFError, KeyboardInterrupt):
        say("  aborted.", "yellow")
        return
    if ok not in ("y", "yes"):
        say("  leaving login config unchanged.", "yellow")
        return
    user = input(c("  burner username: ", "bold")).strip()
    pw = getpass.getpass(c("  burner password: ", "bold")).strip()
    if not user or not pw:
        say("  empty values -- aborting.", "yellow")
        return
    path = save_login_config(args.config or "config.toml", user, pw, enabled=True)
    say(f"  saved to {c(path, 'green')}")
    cfg["login_enabled"], cfg["login_username"], cfg["login_password"] = True, user, pw
    try:
        test = input(c("  Test the login now (opens a visible browser)? [y/N] ", "bold")).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return
    if test in ("y", "yes"):
        ctx = open_session(cfg, "login_test")
        page = ctx.new_page()
        try:
            ok_login = ensure_login(page, cfg, "login_test")
            say("  login test: " + ("OK" if ok_login else "FAILED"),
                "green" if ok_login else "red")
        finally:
            try:
                ctx.close()
            except Exception:  # noqa: BLE001
                pass


def run_footprint() -> None:
    """Placeholder for footprint / auto-scroll mode."""
    say("\n  [coming soon] Footprint mode — self-driven Reels-scroll auto-footprint\n", "yellow")


def main() -> None:
    args = cli_args()

    # Non-interactive stdin without a target: the menu can't read input, so a
    # piped/CI run would spin uselessly (or EOF-traceback mid-flow). Abort with
    # a usage hint instead of the banner/menu dance.
    if not args.username and not sys.stdin.isatty():
        say("\n  non-interactive input detected (no TTY). Pass a target as a flag:", "yellow")
        say("    python3 main.py -u <username> [--headless] [-y] [--deep]\n", "gold")
        return

    cfg = load_config(args.config)

    if args.headless:
        cfg["headless"] = True
    if args.max_posts is not None:
        cfg["max_posts"] = args.max_posts
    if args.no_media:
        cfg["download_media"] = False
    if args.no_followers:
        cfg["attempt_followers"] = False
    if args.deep:
        cfg["deep"] = True

    # Direct mode: if -u is passed, skip menu and run OSINT directly
    if args.username:
        run_osint(cfg, args)
        return

    # Interactive menu loop
    try:
        while True:
            choice = show_menu()
            if choice == "1":
                run_osint(cfg, args)
            elif choice == "2":
                run_login(cfg, args)
            elif choice == "3":
                run_footprint()
            elif choice == "4":
                say("\n  goodbye.\n", "gold")
                break
            else:
                say("  invalid choice.", "yellow")
    except KeyboardInterrupt:
        say("\n\n  goodbye.\n", "gold")
