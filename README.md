# JEV-SONARQUBE

Check C++ source files against SonarQube rules using the [TypeSafe AI](https://docs.typesafe.ai) System One (Jev) API. Each rule becomes one `Noul` question; all questions are sent in a single batched `system_one` call and run in parallel on the model side. Results are cached to disk so repeated runs on unchanged code are instant.

## Setup

```bash
uv sync
cp secrets.toml.example secrets.toml   # add your TypeSafe API key
```

## Run

```bash
uv run python main.py
```

Example output:

```
examples/example.cpp  ·  10 rules  ·  ground truth: 6 violated / 4 clean
──────────────────────────────────────────────────────────────────
  jev-latest  ·  542 ms  ·  1,842 (1,796 in + 46 out)

  Verdict per rule:
    cpp:S1001   p=0.95   violated   TP ✓
    cpp:S1128   p=0.07   clean      TN ✓
    cpp:S2185   p=0.04   clean      TN ✓
    ...

  Precision 100.0%  ·  Recall 100.0%  ·  Accuracy 100.0%  ·  F1 100.0%
```

Second run (cache hit):

```
  cache hit  ·  2 ms  ·  1,842 (1,796 in + 46 out)
```

Delete `.checker_cache.json` to force a fresh API call.

## How it works

1. Load rules from `sq_rules/sq_cpp_rules.json` and source from `examples/example.cpp`
2. Check cache (`SHA-256` of code + rule descriptions) — return immediately on hit
3. On miss: one `Noul` question per rule → single `system_one` call → cache result
4. Classify: p ≥ 0.60 → violation · 0.40–0.60 → uncertain
5. Evaluate against `EXAMPLE_GROUND_TRUTH` → precision / recall / accuracy / F1

## Extending

- **Add rules** — append to `sq_rules/sq_cpp_rules.json` (`key`, `name`, `description`, `severity`, `type`)
- **Check a different file** — change `CPP_FILE` and `EXAMPLE_GROUND_TRUTH` in `checker/config.py`
- **Tune thresholds** — adjust `VIOLATION_THRESHOLD` / `UNCERTAIN_LOW` in `checker/config.py`

