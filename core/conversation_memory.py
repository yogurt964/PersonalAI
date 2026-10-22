"""Bounded, in-process memory contracts. No extraction, API or persistent writes."""
import hashlib
import json
from dataclasses import asdict, dataclass, replace


def checked_text(value, name, max_bytes, *, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ValueError(f"{name} must be text")
    if len(value.encode("utf-8")) > max_bytes:
        raise ValueError(f"{name} exceeds {max_bytes} UTF-8 bytes")


def positive_id(value):
    if type(value) is not int or value <= 0:
        raise ValueError("message_id must be a positive integer")


@dataclass(frozen=True)
class MemoryScope:
    owner_id: str
    project_id: str = ""

    def __post_init__(self):
        checked_text(self.owner_id, "owner_id", 128)
        checked_text(self.project_id, "project_id", 128, allow_empty=True)


@dataclass(frozen=True)
class SourceRef:
    dataset_id: str
    message_id: int
    role: str
    content_digest: str

    def __post_init__(self):
        checked_text(self.dataset_id, "dataset_id", 128)
        positive_id(self.message_id)
        if self.role not in ("user", "assistant"):
            raise ValueError("unsupported source role")
        if (not isinstance(self.content_digest, str) or len(self.content_digest) != 64
                or any(c not in "0123456789abcdef" for c in self.content_digest)):
            raise ValueError("invalid source digest")


@dataclass(frozen=True)
class ConversationSource:
    ref: SourceRef
    content: str
    created_at: str | None = None

    def __post_init__(self):
        if not isinstance(self.ref, SourceRef):
            raise ValueError("source reference required")
        checked_text(self.content, "source content", 65536)
        if hashlib.sha256(self.content.encode("utf-8")).hexdigest() != self.ref.content_digest:
            raise ValueError("source content does not match reference")
        if self.created_at is not None:
            checked_text(self.created_at, "created_at", 128, allow_empty=True)

    @classmethod
    def from_row(cls, dataset_id, message_id, role, content, created_at=None):
        checked_text(content, "source content", 65536)
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return cls(SourceRef(dataset_id, message_id, role, digest), content, created_at)


@dataclass(frozen=True)
class SourceBatch:
    scope: MemoryScope
    dataset_id: str
    sources: tuple[ConversationSource, ...]
    missing_ids: tuple[int, ...] = ()
    has_older: bool = False

    def __post_init__(self):
        if not isinstance(self.scope, MemoryScope):
            raise ValueError("scope required")
        checked_text(self.dataset_id, "dataset_id", 128)
        if type(self.sources) is not tuple or len(self.sources) > 100:
            raise ValueError("sources must be a tuple of at most 100 messages")
        if any(not isinstance(s, ConversationSource) or s.ref.dataset_id != self.dataset_id
               for s in self.sources):
            raise ValueError("source dataset mismatch")
        ids = [s.ref.message_id for s in self.sources]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate source IDs")
        if type(self.missing_ids) is not tuple or len(self.missing_ids) > 100:
            raise ValueError("invalid missing IDs")
        for message_id in self.missing_ids:
            positive_id(message_id)
        if set(ids) & set(self.missing_ids) or type(self.has_older) is not bool:
            raise ValueError("invalid batch metadata")


NOTE_KINDS = {"user_fact", "inference", "goal", "open_question",
              "temporary_preference", "decision"}


@dataclass(frozen=True)
class StateNote:
    key: str
    kind: str
    content: str
    source_refs: tuple[SourceRef, ...]
    tags: tuple[str, ...] = ()

    def __post_init__(self):
        checked_text(self.key, "note key", 128)
        checked_text(self.content, "note content", 1024)
        if self.kind not in NOTE_KINDS:
            raise ValueError("unknown note kind")
        if (type(self.source_refs) is not tuple or not 1 <= len(self.source_refs) <= 8
                or any(not isinstance(r, SourceRef) for r in self.source_refs)):
            raise ValueError("one to eight source references required")
        if len(set(self.source_refs)) != len(self.source_refs):
            raise ValueError("duplicate source reference")
        if self.kind in ("user_fact", "temporary_preference"):
            if any(r.role != "user" for r in self.source_refs):
                raise ValueError("user fact/preference requires user-authored sources")
        if type(self.tags) is not tuple or len(self.tags) > 8:
            raise ValueError("at most eight tags required")
        for tag in self.tags:
            checked_text(tag, "tag", 64)
        if len(set(self.tags)) != len(self.tags):
            raise ValueError("duplicate tag")


@dataclass(frozen=True)
class ShortTermSnapshot:
    scope: MemoryScope
    dataset_id: str
    version: int = 0
    topic: str = ""
    notes: tuple[StateNote, ...] = ()

    def __post_init__(self):
        if not isinstance(self.scope, MemoryScope):
            raise ValueError("scope required")
        checked_text(self.dataset_id, "dataset_id", 128)
        checked_text(self.topic, "topic", 256, allow_empty=True)
        if type(self.version) is not int or self.version < 0:
            raise ValueError("invalid state version")
        if (type(self.notes) is not tuple or len(self.notes) > 16
                or any(not isinstance(n, StateNote) for n in self.notes)):
            raise ValueError("at most sixteen notes required")
        if len({n.key for n in self.notes}) != len(self.notes):
            raise ValueError("duplicate note key")
        if any(r.dataset_id != self.dataset_id for n in self.notes for r in n.source_refs):
            raise ValueError("note dataset mismatch")
        if len(self.to_json().encode("utf-8")) > 8192:
            raise ValueError("short-term state exceeds 8192 UTF-8 bytes")

    def to_json(self):
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))


class StateConflict(ValueError):
    pass


class ShortTermMemory:
    """Explicit updates only; does not infer facts or write long-term memories."""
    def __init__(self, scope, dataset_id):
        self._snapshot = ShortTermSnapshot(scope, dataset_id)

    @classmethod
    def from_snapshot(cls, snapshot):
        if not isinstance(snapshot, ShortTermSnapshot):
            raise ValueError("validated snapshot required")
        memory = cls(snapshot.scope, snapshot.dataset_id)
        memory._snapshot = snapshot
        return memory

    @property
    def snapshot(self):
        return self._snapshot

    def _check_version(self, expected_version):
        if type(expected_version) is not int or expected_version != self._snapshot.version:
            raise StateConflict("state changed; reload before applying update")

    def apply(self, *, expected_version, evidence, upserts=(), remove_keys=(), topic=None):
        self._check_version(expected_version)
        current = self._snapshot
        if (not isinstance(evidence, SourceBatch) or evidence.scope != current.scope
                or evidence.dataset_id != current.dataset_id):
            raise ValueError("evidence scope/dataset mismatch")
        if type(upserts) is not tuple or any(not isinstance(n, StateNote) for n in upserts):
            raise ValueError("upserts must be a tuple of notes")
        if type(remove_keys) is not tuple:
            raise ValueError("remove_keys must be a tuple")
        for key in remove_keys:
            checked_text(key, "remove key", 128)
        keys = [n.key for n in upserts]
        if len(set(keys)) != len(keys) or set(keys) & set(remove_keys):
            raise ValueError("ambiguous update")
        allowed = {s.ref for s in evidence.sources}
        if any(ref not in allowed for note in upserts for ref in note.source_refs):
            raise ValueError("new notes must cite available, unchanged sources")
        notes = {n.key: n for n in current.notes}
        if any(key not in notes for key in remove_keys):
            raise ValueError("cannot remove unknown note")
        for key in remove_keys:
            del notes[key]
        for note in upserts:
            notes[note.key] = note
        candidate = replace(current, version=current.version + 1,
                            topic=current.topic if topic is None else topic,
                            notes=tuple(notes.values()))
        # Validation above completes before state is replaced: failure is atomic.
        self._snapshot = candidate
        return candidate

    def end_topic(self, *, expected_version):
        self._check_version(expected_version)
        current = self._snapshot
        self._snapshot = replace(current, version=current.version + 1, topic="",
                                 notes=tuple(n for n in current.notes
                                             if n.kind != "temporary_preference"))
        return self._snapshot


@dataclass(frozen=True)
class WorkingTurn:
    turn_id: str
    user_input: str
    state: ShortTermSnapshot
    evidence: SourceBatch

    def __post_init__(self):
        checked_text(self.turn_id, "turn_id", 128)
        checked_text(self.user_input, "user_input", 48000)
        if not isinstance(self.state, ShortTermSnapshot) or not isinstance(self.evidence, SourceBatch):
            raise ValueError("state and evidence required")
        if (self.state.scope != self.evidence.scope
                or self.state.dataset_id != self.evidence.dataset_id):
            raise ValueError("working context scope mismatch")
