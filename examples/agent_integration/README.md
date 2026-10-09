# Control Trace Lite — deterministic agent workflow demonstration

Run against an installed `control-trace-lite` package or the adjacent local checkout:

```bash
python agent_integration_demo.py
```

This is a **scripted tool-calling agent workflow**, not a live LLM or a LangGraph integration. It exercises the same four named cases deterministically: normal, skipped review, retry with stale receipts, and ineffective review. The last case **publishes**, showing that successful function return is not evidence of semantic correctness. Direct bypass of `finalize()` is also not prevented.

This demonstration does not establish comparative performance versus hand-written Python checks, a real-world LLM omission rate, or protection against malicious callers.
