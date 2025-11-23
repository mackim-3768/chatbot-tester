from __future__ import annotations

import argparse


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="chatbot-runner", description="Chatbot Test Runner (placeholder)")
    p.add_argument("--version", action="store_true", help="Show version and exit")
    return p


def main(argv: list[str] | None = None) -> None:
    from . import __version__

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"chatbot_tester.runner {__version__}")
        return

    parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()
