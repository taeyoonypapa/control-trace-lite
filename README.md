# Control Trace Lite

A tiny, model-agnostic Python guard that checks whether mandatory control functions completed **in the current attempt** before an artifact is returned by `finalize()`.

**Status:** research prototype, v0.1. Python 3.10+, standard library at runtime. No model API or external service required.

## Quick start

```bash
python -m pip install -e .
python examples/quickstart.py
python -m unittest discover -s tests -v
```

```python
from control_trace import Guard, ControlMissing

def validate_data():
    return True

def review_result():
    return True

guard = Guard(required=["validate", "review"])
guard.run("validate", validate_data)
guard.run("review", review_result)
artifact = guard.finalize({"answer": 42})
print(artifact)
```

To see omission detection, remove `guard.run("review", review_result)` and run again. `finalize()` raises `ControlMissing`.


The caller must wire `finalize()` to the **actual publication boundary**. Calling `finalize()` is not an enforcement guarantee if other code can publish directly.

## Behavior

- `run(name, callable, ...)` records a unique completion event **after normal function return**. Exceptions do not create receipts.
- `finalize(artifact)` returns the artifact only if all named controls have receipts from the current attempt; otherwise raises `ControlMissing` with the missing control names.
- `retry_or_hold()` invalidates the current attempt's receipts on first call; a second call sets `HOLD` and adds a local alert record.
- `trace()` returns diagnostic records, not cryptographic proof of control correctness.

## Limitations and research questions

- **Cooperative runtime only.** A caller can bypass the guard and publish directly; there is no sandbox or tamper resistance.
- A function returning normally is not evidence that its *semantic* check was adequate. Users must implement and test their control functions.
- In-memory only: receipts, alerts and retries are lost on process restart. No actor handoff or durable replay support in this minimal release.
- Not thread-safe, not an external side-effect transaction system, and not a security boundary.
- No real LLM omission-rate measurements are included. Unit tests verify programmed scenarios, not autonomous model behavior.
- Future research: independent LLM episodes, false positives/negatives, reliable publication-boundary integrations, persistent execution lineage.

## What this does NOT guarantee

This library detects missing receipts **only when the application calls `finalize()` at its actual output boundary**. It cannot force an arbitrary LLM agent to use the guard, prove that a control was semantically correct, or prevent a caller from directly publishing. A successful test suite is not evidence of a measured real-world LLM omission rate.

## Contributions

Please submit a reproducible test case, expected/observed result, and runtime information with each issue or pull request. Avoid including private prompts, credentials, or proprietary agent data.

## License

MIT. See [LICENSE](LICENSE).

## Open research and community cases

This is an **early public research prototype**, not a completed empirical study. We publish the minimal runnable implementation and known limitations now so others can identify unexpected cases. We do **not** claim that all scenarios have been tested, that external cases will be submitted, or that missing receipts always mean a control was omitted.

Please use the [unexpected-case issue template](.github/ISSUE_TEMPLATE/unexpected-case.yml) for independently reproducible counterexamples. Cases are initially **unverified reports**; maintainers should distinguish *actual omission*, *missing observation*, *ineffective control with a receipt*, and *publication-boundary bypass*. Do not treat a reported case as verified until its evidence is checked. A passing guard test only supports receipt-completeness behavior, not semantic correctness.
