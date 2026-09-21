"""Connector contract + reference StubConnector + the contract-test suite.

Every FUTURE connector MUST implement BaseConnector and pass run_contract_suite()
before it can be activated. In Phase 1A no connector is live; only the in-memory
StubConnector exists and all connectors remain labeled "Not Connected".

Contract behaviors enforced: authorization (default-deny), pause blocks execution,
revocation blocks execution, timeout is surfaced without side effects, failure is
surfaced without side effects, every attempt generates an audit record, execution is
idempotent by key (no double-apply), and a safe retry after a transient failure
applies exactly once.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class ConnectorUnauthorized(Exception):
    pass


class ConnectorPaused(Exception):
    pass


class ConnectorRevoked(Exception):
    pass


class ConnectorTimeout(Exception):
    pass


class ConnectorFailure(Exception):
    pass


@dataclass
class ConnectorResult:
    status: str  # "executed" | "replayed"
    detail: str
    idempotent_replay: bool = False


@dataclass
class ConnectorAction:
    name: str
    payload: dict = field(default_factory=dict)
    idempotency_key: str = ""


class BaseConnector(ABC):
    """Interface every connector must implement. Identity/behavior only — no secrets here."""

    name: str = "abstract"
    required_permission: str = "connector:read"

    @abstractmethod
    def authorize(self, granted_permissions: set[str]) -> None:
        """Raise ConnectorUnauthorized unless required_permission is granted (default-deny)."""

    @abstractmethod
    def execute(self, action: ConnectorAction) -> ConnectorResult:
        """Execute an action. Must be idempotent by action.idempotency_key."""

    @abstractmethod
    def pause(self) -> None: ...

    @abstractmethod
    def resume(self) -> None: ...

    @abstractmethod
    def revoke(self) -> None: ...

    @abstractmethod
    def audit_records(self) -> list[dict]: ...


class StubConnector(BaseConnector):
    """In-memory reference connector. NEVER performs any external I/O."""

    name = "stub"
    required_permission = "connector:test"

    def __init__(self):
        self._paused = False
        self._revoked = False
        self._store: dict[str, ConnectorResult] = {}
        self._audit: list[dict] = []
        self.execute_count = 0
        # test knobs
        self.timeout_next = False
        self.fail_next = False

    def authorize(self, granted_permissions: set[str]) -> None:
        if self.required_permission not in granted_permissions:
            self._audit.append({"event": "authorization.denied", "permission": self.required_permission})
            raise ConnectorUnauthorized(self.required_permission)

    def execute(self, action: ConnectorAction) -> ConnectorResult:
        self._audit.append({"event": "execute.attempt", "action": action.name,
                            "key": action.idempotency_key})
        if self._paused:
            self._audit.append({"event": "execute.blocked", "reason": "paused"})
            raise ConnectorPaused()
        if self._revoked:
            self._audit.append({"event": "execute.blocked", "reason": "revoked"})
            raise ConnectorRevoked()

        # Idempotent replay: same key already applied -> no second side effect.
        if action.idempotency_key and action.idempotency_key in self._store:
            prior = self._store[action.idempotency_key]
            self._audit.append({"event": "execute.replayed", "key": action.idempotency_key})
            return ConnectorResult(status="replayed", detail=prior.detail, idempotent_replay=True)

        if self.timeout_next:
            self.timeout_next = False
            self._audit.append({"event": "execute.timeout"})
            raise ConnectorTimeout()

        if self.fail_next:
            self.fail_next = False
            self._audit.append({"event": "execute.failed"})
            raise ConnectorFailure()

        # Apply exactly once.
        self.execute_count += 1
        result = ConnectorResult(status="executed", detail=f"applied:{action.name}")
        if action.idempotency_key:
            self._store[action.idempotency_key] = result
        self._audit.append({"event": "execute.ok", "key": action.idempotency_key})
        return result

    def pause(self) -> None:
        self._paused = True
        self._audit.append({"event": "pause"})

    def resume(self) -> None:
        self._paused = False
        self._audit.append({"event": "resume"})

    def revoke(self) -> None:
        self._revoked = True
        self._audit.append({"event": "revoke"})

    def audit_records(self) -> list[dict]:
        return list(self._audit)


def run_contract_suite(factory) -> list[dict]:
    """Run every contract check against a fresh connector from `factory()`.
    Returns a list of {check, passed, detail}. Used by CI and the /connectors endpoint.
    """
    results: list[dict] = []

    def record(check, passed, detail=""):
        results.append({"check": check, "passed": bool(passed), "detail": detail})

    granted = {"connector:test"}

    # 1. authorization: default-deny
    c = factory()
    try:
        c.authorize(set())  # empty grants
        record("authorization_default_deny", False, "authorize() did not raise on empty grants")
    except ConnectorUnauthorized:
        record("authorization_default_deny", True)
    # authorized path works
    c.authorize(granted)

    # 2. pause blocks execution
    c = factory(); c.authorize(granted); c.pause()
    try:
        c.execute(ConnectorAction("a", {}, "k1"))
        record("pause_blocks_execution", False)
    except ConnectorPaused:
        record("pause_blocks_execution", c.execute_count == 0, f"execute_count={c.execute_count}")

    # 3. revocation blocks execution
    c = factory(); c.authorize(granted); c.revoke()
    try:
        c.execute(ConnectorAction("a", {}, "k1"))
        record("revocation_blocks_execution", False)
    except ConnectorRevoked:
        record("revocation_blocks_execution", c.execute_count == 0)

    # 4. timeout surfaced, no side effect
    c = factory(); c.authorize(granted); c.timeout_next = True
    try:
        c.execute(ConnectorAction("a", {}, "k1"))
        record("timeout_no_side_effect", False)
    except ConnectorTimeout:
        record("timeout_no_side_effect", c.execute_count == 0)

    # 5. failure surfaced, no side effect
    c = factory(); c.authorize(granted); c.fail_next = True
    try:
        c.execute(ConnectorAction("a", {}, "k1"))
        record("failure_no_side_effect", False)
    except ConnectorFailure:
        record("failure_no_side_effect", c.execute_count == 0)

    # 6. audit generated for attempts
    c = factory(); c.authorize(granted)
    c.execute(ConnectorAction("a", {}, "k1"))
    record("audit_generated", any(r["event"].startswith("execute") for r in c.audit_records()))

    # 7. idempotency: same key twice -> one side effect + replay
    c = factory(); c.authorize(granted)
    r1 = c.execute(ConnectorAction("a", {}, "same-key"))
    r2 = c.execute(ConnectorAction("a", {}, "same-key"))
    record("idempotent_by_key", c.execute_count == 1 and r2.idempotent_replay and not r1.idempotent_replay,
           f"execute_count={c.execute_count}")

    # 8. safe retry: transient failure then retry same key applies once
    c = factory(); c.authorize(granted); c.fail_next = True
    try:
        c.execute(ConnectorAction("a", {}, "retry-key"))
    except ConnectorFailure:
        pass
    c.execute(ConnectorAction("a", {}, "retry-key"))  # retry
    c.execute(ConnectorAction("a", {}, "retry-key"))  # duplicate retry -> replay
    record("safe_retry_applies_once", c.execute_count == 1, f"execute_count={c.execute_count}")

    return results
