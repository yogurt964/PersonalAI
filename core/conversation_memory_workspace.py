"""Atomic, bounded companion storage for accepted short memory and usage.

The legacy conversation DB is read-only here. This separate one-row store is
single-user, bound to an explicit source DB path. Never silently repair/reset it.
"""
import json
import sqlite3
from contextlib import closing
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from core.conversation_memory import (
    MemoryScope, SourceRef, StateNote, ShortTermSnapshot, ShortTermMemory, StateConflict,
)
from core.conversation_memory_lifecycle import MemoryIdentity, UsageEvent, UsageLedger
from core.conversation_sources import ConversationSourceReader

MAX_PAYLOAD = 262144


def now_utc():
    return datetime.now(timezone.utc)


def restore_snapshot(data):
    notes = tuple(StateNote(n['key'], n['kind'], n['content'],
                           tuple(SourceRef(**r) for r in n['source_refs']), tuple(n['tags']))
                  for n in data['notes'])
    return ShortTermSnapshot(MemoryScope(**data['scope']), data['dataset_id'],
                             data['version'], data['topic'], notes)


def encode_ledger(ledger):
    return {'identity': asdict(ledger.identity), 'since': ledger.since.isoformat(),
            'history_known': ledger.history_known, 'max_events': ledger.max_events,
            'events': [asdict(e) | {'at': e.at.isoformat()} for e in ledger.events]}


def restore_identity(data):
    return MemoryIdentity(MemoryScope(**data['scope']), data['memory_id'], data['version'])


def restore_ledger(data, *, now):
    ledger = UsageLedger(restore_identity(data['identity']), since=datetime.fromisoformat(data['since']),
                         history_known=data['history_known'], max_events=data['max_events'])
    for item in data['events']:
        event = UsageEvent(restore_identity(item['identity']), item['event_id'], item['turn_id'],
                           item['session_id'], item['kind'], datetime.fromisoformat(item['at']),
                           SourceRef(**item['source']) if item['source'] else None, item['successful'])
        if not ledger.record(event, now=now):
            raise ValueError('duplicate persisted usage event')
    return ledger


class MemoryWorkspace:
    def __init__(self, path, source_path, *, clock=now_utc):
        self.path, self.source_path = Path(path).resolve(), Path(source_path).resolve()
        self.clock = clock
        self.session_id = str(uuid4())
        if self.path == self.source_path or not self.source_path.is_file():
            raise ValueError('separate workspace and existing source DB required')
        if not self.path.parent.is_dir():
            raise ValueError('workspace parent directory must exist')
        exists = self.path.exists()
        # Existing stores must already have our schema; do not adopt arbitrary DBs.
        with closing(sqlite3.connect(str(self.path), timeout=5)) as db:
            with db:
                if not exists:
                    db.execute('CREATE TABLE companion_memory (id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER NOT NULL, payload TEXT NOT NULL)')
                    state = ShortTermSnapshot(MemoryScope('local-user'), str(uuid4()))
                    payload = {'format': 1, 'source_path': str(self.source_path),
                               'state': json.loads(state.to_json()), 'ledgers': {}}
                    db.execute('INSERT INTO companion_memory VALUES (1, 0, ?)', (self._encode(payload),))
        self.refresh()
        # Session-only hopes must never silently become next-session preferences.
        if any(n.kind == 'temporary_preference' for n in self.state.notes) or self.state.topic:
            self.end_topic()

    @staticmethod
    def _encode(payload):
        text = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        if len(text.encode('utf-8')) > MAX_PAYLOAD:
            raise ValueError('workspace full; aggregation required')
        return text

    def _decode(self, text):
        if len(text.encode('utf-8')) > MAX_PAYLOAD:
            raise ValueError('oversized workspace')
        data = json.loads(text)
        if set(data) != {'format', 'source_path', 'state', 'ledgers'} or data['format'] != 1:
            raise ValueError('unsupported workspace format')
        if data['source_path'] != str(self.source_path):
            raise ValueError('workspace bound to another source DB')
        state = restore_snapshot(data['state'])
        if set(data['ledgers']) != {n.key for n in state.notes}:
            raise ValueError('usage identities do not match short memory')
        ledgers = {key: restore_ledger(value, now=self.clock()) for key, value in data['ledgers'].items()}
        for key, ledger in ledgers.items():
            if ledger.identity.scope != state.scope or ledger.identity.memory_id != key:
                raise ValueError('usage scope mismatch')
            if any(e.source is not None and e.source.dataset_id != state.dataset_id for e in ledger.events):
                raise ValueError('usage source dataset mismatch')
        return data, state, ledgers

    def refresh(self):
        with closing(sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True)) as db:
            row = db.execute('SELECT revision, payload FROM companion_memory WHERE id=1').fetchone()
        if row is None or type(row[0]) is not int or row[0] < 0:
            raise ValueError('missing workspace state')
        data, state, ledgers = self._decode(row[1])
        self.revision, self.data, self.state, self.ledgers = row[0], data, state, ledgers
        self.reader = ConversationSourceReader(self.source_path, dataset_id=state.dataset_id, scope=state.scope)

    def _commit(self, state, ledgers):
        payload = {'format': 1, 'source_path': str(self.source_path), 'state': json.loads(state.to_json()),
                   'ledgers': {k: encode_ledger(v) for k, v in ledgers.items()}}
        text = self._encode(payload)
        self._decode(text)  # Fully validate before any write.
        with closing(sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True, timeout=5)) as db:
            with db:
                cursor = db.execute('UPDATE companion_memory SET revision=revision+1, payload=? WHERE id=1 AND revision=?',
                                    (text, self.revision))
                if cursor.rowcount != 1:
                    raise StateConflict('workspace changed; reload before retrying')
        self.revision += 1
        self.data, self.state, self.ledgers = payload, state, ledgers

    def accept(self, proposals, *, expected_version):
        if expected_version != self.state.version:
            raise StateConflict('short memory changed; extract again')
        if not proposals:
            raise ValueError('no candidates selected')
        refs = {r for p in proposals for r in p.note.source_refs}
        batch = self.reader.by_ids([r.message_id for r in refs])
        model = ShortTermMemory.from_snapshot(self.state)
        state = model.apply(expected_version=expected_version, evidence=batch,
                            upserts=tuple(p.note for p in proposals))
        ledgers = {k: restore_ledger(encode_ledger(v), now=self.clock()) for k, v in self.ledgers.items()}
        old = {n.key: n for n in self.state.notes}
        for proposal in proposals:
            note = proposal.note
            # Revisions conservatively separate statistics for changed meanings.
            same = note.key in old and (old[note.key].kind, old[note.key].content) == (note.kind, note.content)
            if not same:
                version = ledgers[note.key].identity.version + 1 if note.key in ledgers else 1
                ledgers[note.key] = UsageLedger(MemoryIdentity(state.scope, note.key, version),
                                               since=self.clock(), history_known=False)
            ledger = ledgers[note.key]
            for ref in note.source_refs:
                if ref.role == 'user':
                    if any(e.kind == 'mention' and (e.source.dataset_id, e.source.message_id) ==
                           (ref.dataset_id, ref.message_id) for e in ledger.events):
                        continue
                    ledger.record(UsageEvent(ledger.identity, f'mention-{ref.message_id}',
                                             f'source-{ref.message_id}', 'source-session-unknown', 'mention',
                                             self.clock(), ref), now=self.clock())
        self._commit(state, ledgers)
        return state

    def end_topic(self):
        state = replace(self.state, version=self.state.version + 1, topic='',
                        notes=tuple(n for n in self.state.notes if n.kind != 'temporary_preference'))
        self._commit(state, {n.key: self.ledgers[n.key] for n in state.notes})

    def record_selection(self, keys, turn_id):
        ledgers = {k: restore_ledger(encode_ledger(v), now=self.clock()) for k, v in self.ledgers.items()}
        changed = False
        for key in keys:
            ledger = ledgers[key]
            changed |= ledger.record(UsageEvent(ledger.identity, turn_id, turn_id, self.session_id,
                                                 'context_selected', self.clock()), now=self.clock())
        if changed:
            self._commit(self.state, ledgers)

    def context(self):
        # Original text is not duplicated. Missing originals remain distinguishable.
        refs = {r for note in self.state.notes for r in note.source_refs}
        ids = sorted({r.message_id for r in refs})
        current = set()
        for offset in range(0, len(ids), 100):
            current.update(s.ref for s in self.reader.by_ids(ids[offset:offset + 100]).sources)
        data = [{'key': n.key, 'kind': n.kind, 'content': n.content,
                 'sources_available_unchanged': all(r in current for r in n.source_refs)} for n in self.state.notes]
        return data
