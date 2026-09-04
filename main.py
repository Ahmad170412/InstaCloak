#!/usr/bin/env python3
"""Compatibility entry point — the real code lives in the `instacloak` package.

Run either `python3 main.py` (this wrapper) or `python3 -m instacloak`.
"""
from instacloak.cli import main

if __name__ == "__main__":
    main()
