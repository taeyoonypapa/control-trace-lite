# Control Trace Lite

**Did your AI agent complete every required check before returning its answer?**

Control Trace Lite is a small, model-agnostic Python library that checks whether mandatory control functions have recorded completion receipts **in the current execution attempt**.

It detects missing receipts before `finalize()` returns an artifact. It does **not** prove that a control was correct, or prevent an application from bypassing the guard.

**Status:** Early public research prototype · Python 3.10+ · MIT License · No model API required

## See the failure in action

Imagine an agent workflow that must validate evidence and review an answer before publication.

What happens if the review step is skipped? What if a retry incorrectly relies on receipts from an earlier attempt?

The [deterministic agent workflow demo](examples/agent_integration/README.md) exercises four cases:

| Scenario | Result | What it demonstrates |
|---|---|---|
| Normal workflow | PUBLISHED | Required receipts are present |
| Skipped review | BLOCKED | A missing receipt prevents `finalize()` |
| Retry with stale receipts | BLOCKED | Previous-attempt receipts do not satisfy current requirements |
| Ineffective review | PUBLISHED | A receipt does not prove semantic correctness |

This is a **scripted workflow**, not a live LLM experiment.

Run it locally:

```bash
python -m pip install -e .
python examples/agent_integration/agent_integration_demo.py
```

## Quick start

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

Remove the `guard.run("review", review_result)` call to simulate a missing control receipt. `finalize()` then raises `ControlMissing`.

**Important:** The application must call `finalize()` at its actual publication boundary. The library cannot enforce this automatically.

## How it works

- `run(name, callable, ...)` records completion after a function returns normally. Exceptions do not produce completion receipts.
- `finalize(artifact)` checks whether every required control has a receipt from the current attempt.
- `retry_or_hold()` advances to a new attempt on its first call, invalidating earlier receipts; a second call enters HOLD and records a local alert.
- `trace()` returns diagnostic records, not cryptographic proof.

## What it does not guarantee

- **No semantic verification:** A function returning normally can be ineffective or incorrect, even if it returns `False`.
- **No automatic publication enforcement:** Application code can bypass `finalize()`.
- **No tamper resistance:** This is a cooperative, in-memory runtime guard, not a security boundary.
- **No durable history:** Records are lost when the process ends.
- **No concurrency guarantee:** The current implementation is not thread-safe.
- **No measured LLM performance:** The included tests and demo do not establish real-world omission rates or superiority over hand-written Python checks.

## Why explore this?

A simple Python condition can also detect missing steps. Control Trace Lite explores whether a reusable, attempt-scoped receipt mechanism is useful when workflows contain retries, multiple mandatory checks, and explicit output boundaries.

That practical value remains an open research question.

## Help us find unexpected cases

We welcome independently reproducible examples involving:

- Missing mandatory control receipts
- Retry or attempt-boundary errors
- Ineffective controls that still produce receipts
- Direct publication-boundary bypasses
- Unexpected false positives or false negatives

Use the [unexpected-case issue template](.github/ISSUE_TEMPLATE/unexpected-case.yml).

Please include the smallest reproducible example, expected versus observed behavior, and relevant runtime information. Do not include secrets or private agent data.

Reports are unverified until independently examined.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python examples/quickstart.py
python examples/agent_integration/agent_integration_demo.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance.

## License

MIT. See [LICENSE](LICENSE).
