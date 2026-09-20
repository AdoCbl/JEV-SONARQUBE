"""Load API credentials, SonarQube rules, and C++ source from disk."""
import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

RULES_FILE = Path("sq_rules/sq_cpp_rules.json")
CPP_FILE = Path("examples/example.cpp")
SECRETS_FILE = Path("secrets.toml")

# Noul probability thresholds
VIOLATION_THRESHOLD = 0.60   # p >= threshold → violation
UNCERTAIN_LOW = 0.40         # threshold > p >= uncertain_low → manual review

# Known ground truth for examples/example.cpp — used to compute precision/recall/accuracy.
# True = rule IS violated in that file; False = rule is NOT violated.
EXAMPLE_GROUND_TRUTH: dict[str, bool] = {
    "cpp:S1001": True,   # switch fallthrough
    "cpp:S5509": True,   # switch missing default
    "cpp:S2259": True,   # null pointer dereference
    "cpp:S5025": True,   # raw new[] with no RAII / memory leak
    "cpp:S3432": True,   # printf used
    "cpp:S3584": True,   # buf never freed before main returns
    "cpp:S2185": False,  # divide() guards against zero
    "cpp:S836":  False,  # result declared at point of use
    "cpp:S1128": False,  # no unnecessary includes
    "cpp:S5820": False,  # Base destructor is virtual
}


@dataclass(frozen=True)
class Rule:
    key: str
    name: str
    description: str
    severity: str
    type: str


def load_api_key() -> str:
    if not SECRETS_FILE.exists():
        sys.exit(
            f"{SECRETS_FILE} not found. "
            "Copy secrets.toml.example to secrets.toml and set your API key."
        )
    with SECRETS_FILE.open("rb") as f:
        data = tomllib.load(f)
    key = data.get("typesafe", {}).get("api_key", "")
    if not key or key == "YOUR_API_KEY_HERE":
        sys.exit("Set your TypeSafe API key in secrets.toml under [typesafe] api_key.")
    return key


def load_rules() -> list[Rule]:
    if not RULES_FILE.exists():
        sys.exit(f"Rules file not found: {RULES_FILE}")
    with RULES_FILE.open() as f:
        data = json.load(f)
    raw = data.get("rules")
    if not raw:
        sys.exit(f"No rules found in {RULES_FILE}")
    return [Rule(**r) for r in raw]


def load_code() -> str:
    if not CPP_FILE.exists():
        sys.exit(f"C++ source file not found: {CPP_FILE}")
    return CPP_FILE.read_text()

