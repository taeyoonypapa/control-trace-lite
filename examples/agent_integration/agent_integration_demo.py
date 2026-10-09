"""Deterministic tool-calling agent workflow demo. No LLM API is used."""
from __future__ import annotations
import json
import sys
from pathlib import Path

# Use the published package when installed; otherwise use the adjacent local checkout.
try:
    from control_trace import Guard, ControlMissing
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'control-trace-lite'))
    from control_trace import Guard, ControlMissing


def lookup(query: str) -> dict:
    return {'query': query, 'value': 42, 'source': 'local_fixture'}


def verify_evidence(result: dict) -> bool:
    if result.get('source') != 'local_fixture':
        raise ValueError('untrusted evidence')
    return True


def review_answer(answer: dict) -> bool:
    if answer.get('answer') != 42:
        raise ValueError('invalid answer')
    return True


def run_case(case: str) -> dict:
    guard = Guard(['verify_evidence', 'review_answer'], work_id=case)
    data = lookup('meaning of life')
    answer = {'answer': data['value']}

    if case == 'normal':
        guard.run('verify_evidence', verify_evidence, data)
        guard.run('review_answer', review_answer, answer)
    elif case == 'skipped_review':
        guard.run('verify_evidence', verify_evidence, data)
    elif case == 'retry_stale':
        guard.run('verify_evidence', verify_evidence, data)
        guard.run('review_answer', review_answer, answer)
        assert guard.retry_or_hold() == 'RETRY'
        guard.run('verify_evidence', verify_evidence, data)
    elif case == 'ineffective_review':
        guard.run('verify_evidence', verify_evidence, data)
        guard.run('review_answer', lambda _: True, answer)  # Returns normally without checking.
    else:
        raise ValueError(case)

    try:
        artifact = guard.finalize(answer)
        return {'case': case, 'outcome': 'PUBLISHED', 'artifact': artifact,
                'receipt_count': len(guard.trace()), 'attempt': guard.attempt}
    except ControlMissing as error:
        return {'case': case, 'outcome': 'BLOCKED', 'missing': error.missing,
                'receipt_count': len(guard.trace()), 'attempt': guard.attempt}


def main() -> None:
    outcomes = [run_case(x) for x in ('normal', 'skipped_review', 'retry_stale', 'ineffective_review')]
    assert [x['outcome'] for x in outcomes] == ['PUBLISHED', 'BLOCKED', 'BLOCKED', 'PUBLISHED']
    assert outcomes[1]['missing'] == ['review_answer']
    assert outcomes[2]['missing'] == ['review_answer']
    print(json.dumps(outcomes, indent=2))
    print('ASSERTIONS PASSED: 4 deterministic agent-workflow scenarios')


if __name__ == '__main__':
    main()
