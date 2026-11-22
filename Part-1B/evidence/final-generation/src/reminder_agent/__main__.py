"""Command line entry point: python -m reminder_agent "remind me to ..." """

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import datetime

from .agent import InputError, InvalidModelOutput, interpret, load_system_prompt, safe_result
from .provider import GeminiProvider, ServiceError


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reminder_agent")
    parser.add_argument("text", nargs="?", help="reminder request text")
    parser.add_argument("--now", help="reference time, ISO-8601 with offset (default: system time)")
    parser.add_argument("--list-models", action="store_true", help="list usable model names")
    args = parser.parse_args(argv)
    try:
        provider = GeminiProvider.from_env()
        if args.list_models:
            print("\n".join(provider.list_models()))
            return 0
        if args.text is None:
            parser.error("text is required")
        now = args.now or datetime.now().astimezone().isoformat(timespec="seconds")
        output = interpret(args.text, now, provider, load_system_prompt())
        print(json.dumps(safe_result(output), indent=2, ensure_ascii=False))
    except (ServiceError, InvalidModelOutput, InputError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
