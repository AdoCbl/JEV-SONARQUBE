"""Rule-check engine using AsyncTypeSafeClient.

All rules are sent in a single batched system_one call so questions
run in parallel on the model side.
"""
from dataclasses import dataclass

from typesafe_sdk import AsyncTypeSafeClient, Noul, SystemOneResponse

from checker.config import Rule, UNCERTAIN_LOW, VIOLATION_THRESHOLD
from checker.diagnostics import RequestMetrics, timed_call


@dataclass
class RuleResult:
    rule: Rule
    prob: float


@dataclass
class CheckResult:
    violations: list[RuleResult]   # prob >= VIOLATION_THRESHOLD, sorted desc
    uncertain: list[RuleResult]    # UNCERTAIN_LOW <= prob < VIOLATION_THRESHOLD
    metrics: RequestMetrics
    all_probs: dict[str, float]    # rule.key → noul probability


def _build_questions(rules: list[Rule]) -> dict:
    return {
        rule.key: Noul(
            instructions=(
                f"{rule.name}: {rule.description} "
                "Does the provided C++ code violate this rule?"
            )
        )
        for rule in rules
    }


def _classify(
    response: SystemOneResponse,
    rules: list[Rule],
    metrics: RequestMetrics,
) -> CheckResult:
    all_probs: dict[str, float] = {}
    violations: list[RuleResult] = []
    uncertain: list[RuleResult] = []

    for rule in rules:
        if rule.key not in response.nouls:
            continue
        prob = response.nouls[rule.key].noul
        all_probs[rule.key] = prob
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


async def check(code: str, rules: list[Rule], api_key: str) -> CheckResult:
    """Single batched request; all rule questions run in parallel on the model side."""
    questions = _build_questions(rules)
    async with AsyncTypeSafeClient(api_key=api_key) as client:
        response, metrics = await timed_call(
            client, state={"cpp_code": code}, questions=questions
        )
    return _classify(response, rules, metrics)

