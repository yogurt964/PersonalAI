"""Bounded usage accounting and pure lifecycle proposals. No DB/API or execution.

Caller supplies trusted IDs, scope and reviewed metadata. This is not an auth or
semantic-verification boundary. Thresholds must be supplied explicitly.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import hashlib
import json

from core.conversation_memory import MemoryScope, SourceRef, checked_text


def integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"invalid {name}")


def aware(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("timezone-aware datetime required")


@dataclass(frozen=True)
class MemoryIdentity:
    scope: MemoryScope
    memory_id: str
    version: int

    def __post_init__(self):
        if not isinstance(self.scope, MemoryScope):
            raise ValueError("scope required")
        checked_text(self.memory_id, "memory ID", 128)
        integer(self.version, "version", 0, 2**63 - 1)


@dataclass(frozen=True)
class UsageEvent:
    identity: MemoryIdentity
    event_id: str
    turn_id: str
    session_id: str
    kind: str
    at: datetime
    source: SourceRef | None = None
    successful: bool = True

    def __post_init__(self):
        if not isinstance(self.identity, MemoryIdentity):
            raise ValueError("identity required")
        for name in ("event_id", "turn_id", "session_id"):
            checked_text(getattr(self, name), name, 128)
        if self.kind not in ("mention", "retrieved", "context_selected", "used_as_evidence",
                             "feedback_positive", "feedback_negative"):
            raise ValueError("unknown event kind")
        aware(self.at)
        if type(self.successful) is not bool:
            raise ValueError("successful must be bool")
        if self.kind == "mention":
            if not isinstance(self.source, SourceRef) or self.source.role != "user":
                raise ValueError("mention requires a user source")
        elif self.source is not None:
            raise ValueError("source is only for mention events")


class UsageLedger:
    """One immutable memory version; bounded IDs prevent retry inflation.

    Full ledgers reject new events, never evict deduplication IDs. Persistence,
    cross-version migration and aggregate compaction are intentionally absent.
    """
    def __init__(self, identity, *, since, history_known, max_events=512):
        if not isinstance(identity, MemoryIdentity) or type(history_known) is not bool:
            raise ValueError("identity and explicit history completeness required")
        aware(since)
        integer(max_events, "max events", 1, 4096)
        self.identity, self.since = identity, since
        self.history_known, self.max_events = history_known, max_events
        self._events = []

    @property
    def events(self):
        return tuple(self._events)

    def record(self, event, *, now):
        aware(now)
        if not isinstance(event, UsageEvent) or event.identity != self.identity:
            raise ValueError("event scope, memory ID or version mismatch")
        if not self.since <= event.at <= now:
            raise ValueError("event outside observed time range")
        for old in self._events:
            if old.event_id == event.event_id:
                if old != event:
                    raise ValueError("event ID reused with different data")
                return False
            if (old.turn_id, old.kind) == (event.turn_id, event.kind):
                return False
            if event.kind == old.kind == "mention" and (
                old.source.dataset_id, old.source.message_id
            ) == (event.source.dataset_id, event.source.message_id):
                return False
        if not event.successful:
            return False
        if len(self._events) >= self.max_events:
            raise ValueError("usage ledger full; aggregation required")
        self._events.append(event)
        return True

    def summary(self, *, now, window_days):
        aware(now)
        integer(window_days, "window days", 1, 36500)
        if now < self.since or any(e.at > now for e in self._events):
            raise ValueError("evaluation precedes observed events")
        recent = [e for e in self._events if e.at >= now - timedelta(days=window_days)]
        kinds = (
            "mention", "retrieved", "context_selected", "used_as_evidence",
            "feedback_positive", "feedback_negative")
        counts = {kind: sum(e.kind == kind for e in recent) for kind in kinds}
        totals = {kind: sum(e.kind == kind for e in self._events) for kind in kinds}
        counts["mention_sessions"] = len({e.session_id for e in recent if e.kind == "mention"})
        # Background retrieval/selection cannot renew a memory's lifetime.
        uses = [e.at for e in self._events if e.kind in ("mention", "used_as_evidence", "feedback_positive")]
        return {"window_counts": counts, "total_counts": totals, "total_events": len(self._events),
                "last_use": max(uses) if uses else None,
                "negative_feedback": any(e.kind == "feedback_negative" for e in self._events)}


@dataclass(frozen=True)
class LifecycleMemory:
    identity: MemoryIdentity
    layer: str
    created_at: datetime
    updated_at: datetime
    importance: int
    durable: bool
    evidence_reviewed: bool
    storage_allowed: bool
    conflict: bool = False
    pinned: bool = False
    unresolved: bool = False
    project_core: bool = False
    explicit_save: bool = False
    expires_at: datetime | None = None

    def __post_init__(self):
        if not isinstance(self.identity, MemoryIdentity):
            raise ValueError("identity required")
        if self.layer not in ("temporary", "short", "medium", "long", "project"):
            raise ValueError("unknown layer")
        aware(self.created_at)
        aware(self.updated_at)
        if self.updated_at < self.created_at:
            raise ValueError("updated before creation")
        if self.expires_at is not None:
            aware(self.expires_at)
        integer(self.importance, "importance", 0, 10)
        for name in ("durable", "evidence_reviewed", "storage_allowed", "conflict", "pinned",
                     "unresolved", "project_core", "explicit_save"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be bool")
        if self.project_core and not self.identity.scope.project_id:
            raise ValueError("project core requires project scope")


@dataclass(frozen=True)
class LifecyclePolicy:
    version: str
    window_days: int
    medium_sessions: int
    long_sessions: int
    important_at: int
    forget_at_most: int
    idle_days: int

    def __post_init__(self):
        checked_text(self.version, "policy version", 128)
        for name in ("window_days", "idle_days"):
            integer(getattr(self, name), name, 1, 36500)
        integer(self.medium_sessions, "medium sessions", 2, 4096)
        integer(self.long_sessions, "long sessions", self.medium_sessions, 4096)
        integer(self.important_at, "important threshold", 1, 10)
        integer(self.forget_at_most, "forget threshold", 0, self.important_at - 1)


@dataclass(frozen=True)
class LifecycleProposal:
    identity: MemoryIdentity
    action: str
    target_layer: str
    reason: str
    policy_version: str
    input_digest: str
    dry_run: bool = True


def evaluate_lifecycle(memory, ledger, policy, *, now):
    """Return a repeatable proposal, never save/promote/archive/delete anything."""
    if not isinstance(memory, LifecycleMemory) or not isinstance(policy, LifecyclePolicy):
        raise ValueError("memory and policy required")
    if not isinstance(ledger, UsageLedger) or memory.identity != ledger.identity:
        raise ValueError("ledger identity mismatch")
    aware(now)
    if memory.updated_at > now or ledger.since < memory.created_at:
        raise ValueError("inconsistent timeline")
    stats = ledger.summary(now=now, window_days=policy.window_days)
    payload = {"memory": asdict(memory), "policy": asdict(policy), "now": now,
               "events": [asdict(e) for e in ledger.events], "since": ledger.since,
               "history_known": ledger.history_known}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str,
                                      separators=(",", ":")).encode()).hexdigest()

    def result(action, reason, target=""):
        return LifecycleProposal(memory.identity, action, target, reason, policy.version, digest)

    if not memory.storage_allowed:
        return result("hold", "storage_not_allowed")
    if memory.conflict or stats["negative_feedback"]:
        return result("review", "conflict_or_negative_feedback")
    protected = memory.pinned or memory.unresolved or memory.project_core or memory.importance >= policy.important_at
    expired = memory.expires_at is not None and memory.expires_at <= now
    if expired:
        if protected or memory.explicit_save:
            return result("review", "expired_protected_or_explicit")
        return result("forget_candidate", "expired")
    if memory.evidence_reviewed and memory.durable and memory.layer not in ("long", "project"):
        if memory.project_core:
            return result("promote_candidate", "project_core", "project")
        if memory.explicit_save or memory.importance >= policy.important_at:
            return result("promote_candidate", "explicit_or_important", "long")
        sessions = stats["window_counts"]["mention_sessions"]
        if sessions >= policy.long_sessions:
            return result("promote_candidate", "independent_sessions", "long")
        if sessions >= policy.medium_sessions and memory.layer in ("temporary", "short"):
            return result("promote_candidate", "repeated_topic", "medium")
    if protected:
        return result("retain", "protected")
    if not ledger.history_known or ledger.since > memory.created_at:
        return result("hold", "incomplete_usage_history")
    last_use = max(memory.updated_at, stats["last_use"] or memory.created_at)
    if memory.importance <= policy.forget_at_most and now - last_use >= timedelta(days=policy.idle_days):
        if memory.explicit_save:
            return result("review", "idle_explicit_save")
        return result("forget_candidate", "low_importance_and_idle")
    return result("retain", "no_lifecycle_change")
