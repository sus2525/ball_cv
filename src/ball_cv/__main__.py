from __future__ import annotations

import argparse

from ball_cv.doctor import run_doctor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ball-cv")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Verify the Python/CV runtime.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "doctor":
        return run_doctor()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
