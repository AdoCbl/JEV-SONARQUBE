"""Disk-backed result cache keyed on SHA-256(code + rules).

Eliminates redundant API calls when inputs are unchanged.
Cache misses call the API and persist the result; hits skip the network entirely.
"""
import hashlib
import json
from pathlib import Path

from checker.config import Rule, UNCERTAIN_LOW, VIOLATION_THRESHOLD
from checker.diagnostics import RequestMetrics
from checker.engine import CheckResult, RuleResult, check

CACHE_FILE = Path(".checker_cache.json")


def _key(code: str, rules: list[Rule]) -> str:
    # include rule descriptions so changing a rule definition invalidates the cache
    payload = code + json.dumps(
        [{"key": r.key, "description": r.description} for r in rules], sort_keys=True
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _to_entry(result: CheckResult) -> dict:
    return {
        "all_probs":    result.all_probs,
        "model":        result.metrics.model,
        "request_id":   result.metrics.request_id,
        "latency_ms":   result.metrics.latency_ms,
        "input_tokens": result.metrics.input_tokens,
        "output_tokens": result.metrics.output_tokens,
    }


def _from_entry(entry: dict, rules: list[Rule]) -> CheckResult:
    all_probs: dict[str, float] = entry["all_probs"]
    metrics = RequestMetrics(
        latency_ms=entry["latency_ms"],
        model=entry["model"],
        request_id=entry["request_id"],
        input_tokens=entry["input_tokens"],
        output_tokens=entry["output_tokens"],
    )
    violations, uncertain = [], []
    for rule in rules:
        prob = all_probs.get(rule.key)
        if prob is None:
            continue
        if prob >= VIOLATION_THRESHOLD:
            violations.append(RuleResult(rule, prob))
        elif prob >= UNCERTAIN_LOW:
            uncertain.append(RuleResult(rule, prob))
    return CheckResult(
        violations=sorted(violations, key=lambda r: -r.prob),
        uncertain=sorted(uncertain, key=lambda r: -r.prob),
        metrics=metrics,
        all_probs=all_probs,
    )


def _load() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(store: dict) -> None:
    try:
        CACHE_FILE.write_text(json.dumps(store, indent=2))
    except OSError:
        pass  # non-fatal; next run will just miss the cache


async def cached_check(
    code: str, rules: list[Rule], api_key: str
) -> tuple[CheckResult, bool]:
    """Return (result, was_cached). Calls the API only on a cache miss."""
    key = _key(code, rules)
    store = _load()
    if key in store:
        return _from_entry(store[key], rules), True

    result = await check(code, rules, api_key)
    store[key] = _to_entry(result)
    _save(store)
    return result, False
