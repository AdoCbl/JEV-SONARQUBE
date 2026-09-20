"""Check C++ code against SonarQube rules using the TypeSafe AI API."""
import asyncio
import sys
import time

from typesafe_sdk import TypeSafeAPIError

from checker.cache import cached_check
from checker.config import CPP_FILE, EXAMPLE_GROUND_TRUTH, load_api_key, load_code, load_rules
from checker.report import print_run

SEP = "─" * 66


async def _main() -> None:
    api_key = load_api_key()
    rules   = load_rules()
    code    = load_code()

    n_violated = sum(EXAMPLE_GROUND_TRUTH.values())
    print(
        f"{CPP_FILE}  ·  {len(rules)} rules  ·  "
        f"ground truth: {n_violated} violated / {len(rules) - n_violated} clean"
    )
    print(SEP)

    t0 = time.perf_counter()
    result, was_cached = await cached_check(code, rules, api_key)
    wall_ms = (time.perf_counter() - t0) * 1000

    print_run(result, EXAMPLE_GROUND_TRUTH, wall_ms=wall_ms, cached=was_cached)
    sys.exit(len(result.violations))


def main() -> None:
    try:
        asyncio.run(_main())
    except TypeSafeAPIError as err:
        sys.exit(f"TypeSafe API error ({err.status}): {err}")


if __name__ == "__main__":
    main()

