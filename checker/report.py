"""Format and print rule-check results and sync/async comparison."""
from dataclasses import dataclass

from checker.config import VIOLATION_THRESHOLD
from checker.engine import CheckResult


@dataclass(frozen=True)
class EvalMetrics:
    tp: int
    fp: int
    fn: int
    tn: int
    precision: float
    recall: float
    accuracy: float
    f1: float


def _eval(result: CheckResult, ground_truth: dict[str, bool]) -> EvalMetrics:
    tp = fp = fn = tn = 0
    violated = {r.rule.key for r in result.violations}
    for key, actual in ground_truth.items():
        predicted = key in violated
        if actual and predicted:
            tp += 1
        elif actual and not predicted:
            fn += 1
        elif not actual and predicted:
            fp += 1
        else:
            tn += 1
    n = len(ground_truth)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec  = tp / (tp + fn) if tp + fn else 0.0
    acc  = (tp + tn) / n  if n       else 0.0
    f1   = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return EvalMetrics(tp=tp, fp=fp, fn=fn, tn=tn,
                       precision=prec, recall=rec, accuracy=acc, f1=f1)


def _tok(m) -> str:
    def f(n: int | None) -> str:
        return f"{n:,}" if n is not None else "n/a"
    return f"{f(m.total_tokens)} ({f(m.input_tokens)} in + {f(m.output_tokens)} out)"


def _print_header(result: CheckResult, wall_ms: float, cached: bool) -> None:
    m = result.metrics
    source = "cache hit" if cached else f"{m.model}"
    print(f"  {source}  ·  {wall_ms:.0f} ms  ·  {_tok(m)}\n")


def _print_violations(result: CheckResult) -> None:
    if result.violations:
        print(f"  VIOLATIONS ({len(result.violations)}):")
        for r in result.violations:
            print(f"    [{r.rule.severity:8}] {r.rule.key}  {r.rule.name}  (p={r.prob:.2f})")
    else:
        print("  No violations above threshold.")
    if result.uncertain:
        print(f"\n  UNCERTAIN ({len(result.uncertain)}):")
        for r in result.uncertain:
            print(f"    [{r.rule.severity:8}] {r.rule.key}  {r.rule.name}  (p={r.prob:.2f})")
    print()


def _print_per_rule(result: CheckResult, ground_truth: dict[str, bool]) -> None:
    violated = {r.rule.key for r in result.violations}
    print("  Verdict per rule:")
    for key in sorted(ground_truth):
        prob    = result.all_probs.get(key)
        p_str   = f"p={prob:.2f}" if prob is not None else "p=n/a"
        pred    = key in violated
        actual  = ground_truth[key]
        label   = ("TP" if pred and actual else
                   "TN" if not pred and not actual else
                   "FP" if pred and not actual else "FN")
        mark    = "✓" if label in ("TP", "TN") else "✗"
        verdict = "violated" if pred else "clean   "
        note    = ("  ← FP: actually clean"    if label == "FP" else
                   "  ← FN: actually violated" if label == "FN" else "")
        print(f"    {key:<12}  {p_str}  {verdict}  {label} {mark}{note}")
    print()


def print_run(
    result: CheckResult,
    ground_truth: dict[str, bool],
    wall_ms: float = 0.0,
    cached: bool = False,
) -> None:
    """Print API metrics, violations, per-rule verdict table, and accuracy summary."""
    _print_header(result, wall_ms, cached)
    # _print_violations(result)
    _print_per_rule(result, ground_truth)
    m = _eval(result, ground_truth)
    print(
        f"  Precision {m.precision:.1%}  ·  Recall {m.recall:.1%}"
        f"  ·  Accuracy {m.accuracy:.1%}  ·  F1 {m.f1:.1%}"
    )


