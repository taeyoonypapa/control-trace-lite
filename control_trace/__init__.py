"""Small cooperative-runtime mandatory control guard (not a security sandbox)."""
from __future__ import annotations
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Callable, Any


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class Receipt:
    event_id: str
    control: str
    work_id: str
    revision: str
    contract_digest: str
    attempt: int


class ControlMissing(RuntimeError):
    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__('Mandatory controls missing: ' + ', '.join(missing))


class Guard:
    """Call run() for required checks and finalize() at the publication boundary.

    Assumes cooperative callers; Python code with direct access can bypass this guard.
    """
    def __init__(self, required: list[str] | tuple[str, ...], *, work_id: str = 'default', revision: str = 'r1'):
        if not required or any(not isinstance(c, str) or not c.strip() for c in required):
            raise ValueError('required must contain nonempty control names')
        if len(set(required)) != len(required):
            raise ValueError('duplicate control names')
        self.required = tuple(required)
        self.work_id = work_id
        self.revision = revision
        self.contract_digest = _hash([work_id, revision, sorted(required)])
        self.attempt = 1
        self._events: list[Receipt] = []
        self._state = 'ACTIVE'
        self._retries = 0
        self.alerts: list[dict] = []

    @property
    def state(self) -> str:
        return self._state

    def run(self, control: str, function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if self._state != 'ACTIVE' or control not in self.required:
            raise ValueError('invalid control or closed guard')
        attempt = self.attempt
        result = function(*args, **kwargs)  # Exceptions never create receipts.
        if self._state != 'ACTIVE' or attempt != self.attempt:
            raise RuntimeError('stale control execution')
        self._events.append(Receipt(uuid.uuid4().hex, control, self.work_id,
                                    self.revision, self.contract_digest, attempt))
        return result

    def missing(self) -> list[str]:
        completed = {e.control for e in self._events
                     if e.work_id == self.work_id and e.revision == self.revision
                     and e.contract_digest == self.contract_digest and e.attempt == self.attempt}
        return [name for name in self.required if name not in completed]

    def finalize(self, artifact: Any) -> Any:
        if self._state != 'ACTIVE':
            raise RuntimeError('guard is not active')
        missing = self.missing()
        if missing:
            raise ControlMissing(missing)
        self._state = 'PUBLISHED'
        return artifact

    def retry_or_hold(self) -> str:
        if self._state != 'ACTIVE':
            raise RuntimeError('guard is not active')
        if self._retries >= 1:
            self._state = 'HOLD'
            self.alerts.append({'work_id': self.work_id, 'reason': 'repeated mismatch'})
            return 'HOLD'
        self._retries += 1
        self.attempt += 1
        return 'RETRY'

    def trace(self) -> list[dict]:
        return [vars(event).copy() for event in self._events]
