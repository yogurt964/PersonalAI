"""Memory foundation checks: temporary SQLite and explicit synthetic notes only."""
import sqlite3
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.conversation_memory import (
    ConversationSource, MemoryScope, ShortTermMemory, SourceBatch,
    StateConflict, StateNote, WorkingTurn,
)
from core.conversation_sources import ConversationSourceReader


class MemoryFoundationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "会話 #1.db"
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("CREATE TABLE conversations "
                               "(id INTEGER PRIMARY KEY, role TEXT, content TEXT, created_at TEXT)")
            connection.executemany("INSERT INTO conversations VALUES (?, ?, ?, ?)", [
                (1, "user", "今日は質問せずに聞いてほしい", "2026-10-22T09:00:00"),
                (2, "assistant", "分かったよ", "2026-10-22T09:00:01"),
                (3, "user", "週末の予定はまだ決めていない", "2026-10-22T09:01:00"),
            ])
        self.scope = MemoryScope("synthetic-owner", "synthetic-project")
        self.reader = ConversationSourceReader(self.path, dataset_id="synthetic-db", scope=self.scope)
        self.batch = self.reader.recent()
        self.memory = ShortTermMemory(self.scope, "synthetic-db")

    def note(self, key="weekend", kind="open_question", content="週末の予定は未決定"):
        return StateNote(key, kind, content, (self.batch.sources[-1].ref,), ("予定",))

    def test_id_readback_preserves_original_roles_dates_and_order(self):
        self.assertEqual([s.ref.message_id for s in self.batch.sources], [1, 2, 3])
        self.assertEqual([s.ref.role for s in self.batch.sources], ["user", "assistant", "user"])
        self.assertEqual(self.reader.by_ids([3, 1, 3]).sources,
                         (self.batch.sources[0], self.batch.sources[2]))
        self.assertEqual(self.batch.sources[0].created_at, "2026-10-22T09:00:00")
        self.assertFalse(self.batch.has_older)

    def test_reading_is_read_only_and_does_not_change_database(self):
        before = self.path.read_bytes()
        self.reader.recent(1)
        self.reader.by_ids([1, 500])
        with self.assertRaises(sqlite3.OperationalError):
            self.reader._read("DELETE FROM conversations", ())
        self.assertEqual(self.path.read_bytes(), before)

    def test_missing_database_is_not_created(self):
        missing = Path(self.tmp.name) / "missing.db"
        reader = ConversationSourceReader(missing, dataset_id="missing", scope=self.scope)
        with self.assertRaises(sqlite3.OperationalError):
            reader.recent()
        self.assertFalse(missing.exists())

    def test_limit_and_missing_sources_are_reported_without_invention(self):
        limited = self.reader.recent(2)
        self.assertTrue(limited.has_older)
        self.assertEqual([s.ref.message_id for s in limited.sources], [2, 3])
        result = self.reader.by_ids([3, 500])
        self.assertEqual(result.missing_ids, (500,))
        self.assertEqual(len(result.sources), 1)
        with self.assertRaises(ValueError):
            self.reader.by_ids([True])
        with self.assertRaises(ValueError):
            self.reader.recent(0)

    def test_short_state_cites_sources_without_copying_original(self):
        state = self.memory.apply(expected_version=0, evidence=self.batch,
                                  upserts=(self.note(),), topic="予定の相談")
        self.assertEqual(state.version, 1)
        self.assertEqual(state.notes[0].source_refs[0], self.batch.sources[2].ref)
        self.assertNotIn(self.batch.sources[2].content, state.to_json())
        self.assertIn("週末の予定は未決定", state.to_json())

    def test_stale_update_cannot_overwrite_a_newer_decision(self):
        before = self.memory.apply(expected_version=0, evidence=self.batch, upserts=(self.note(),))
        with self.assertRaises(StateConflict):
            self.memory.apply(expected_version=0, evidence=self.batch,
                              upserts=(self.note(content="予定は決まった"),))
        self.assertIs(self.memory.snapshot, before)

    def test_oversized_note_and_state_fail_without_truncation_or_partial_update(self):
        with self.assertRaises(ValueError):
            self.note(content="あ" * 342)  # More than 1024 UTF-8 bytes.
        before = self.memory.snapshot
        notes = tuple(self.note(key=str(i), content="あ" * 300) for i in range(8))
        with self.assertRaises(ValueError):
            self.memory.apply(expected_version=0, evidence=self.batch, upserts=notes)
        self.assertIs(self.memory.snapshot, before)

    def test_scope_and_dataset_mismatch_are_rejected(self):
        for batch in (
            replace(self.batch, scope=MemoryScope("another-owner", "synthetic-project")),
            replace(self.batch, scope=MemoryScope("synthetic-owner", "another-project")),
            SourceBatch(self.scope, "another-db", ()),
        ):
            with self.subTest(scope=batch.scope, dataset=batch.dataset_id):
                with self.assertRaises(ValueError):
                    self.memory.apply(expected_version=0, evidence=batch, upserts=(self.note(),))
        self.assertEqual(self.memory.snapshot.version, 0)

    def test_missing_or_changed_source_cannot_support_a_new_note(self):
        missing = self.reader.by_ids([1])
        with self.assertRaises(ValueError):
            self.memory.apply(expected_version=0, evidence=missing, upserts=(self.note(),))
        changed_source = ConversationSource.from_row("synthetic-db", 3, "user", "別の内容")
        changed = SourceBatch(self.scope, "synthetic-db", (changed_source,))
        with self.assertRaises(ValueError):
            self.memory.apply(expected_version=0, evidence=changed, upserts=(self.note(),))
        self.assertEqual(self.memory.snapshot.version, 0)

    def test_ai_reply_is_not_accepted_as_a_user_fact(self):
        for kind in ("user_fact", "temporary_preference"):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                StateNote("claim", kind, "ユーザーの好み", (self.batch.sources[1].ref,))
        # Interpretation is allowed only as a separately marked type; this is
        # not semantic verification that the interpretation is correct.
        inference = StateNote("guess", "inference", "仮説", (self.batch.sources[1].ref,))
        self.memory.apply(expected_version=0, evidence=self.batch, upserts=(inference,))
        self.assertEqual(self.memory.snapshot.notes[0].kind, "inference")

    def test_explicit_topic_end_clears_temporary_preference_but_keeps_unresolved_goal(self):
        preference = StateNote("questions", "temporary_preference", "今は質問なし",
                               (self.batch.sources[0].ref,))
        self.memory.apply(expected_version=0, evidence=self.batch,
                          upserts=(preference, self.note()), topic="近況")
        final = self.memory.end_topic(expected_version=1)
        self.assertEqual([n.key for n in final.notes], ["weekend"])
        self.assertEqual(final.topic, "")
        self.assertEqual(len(self.reader.recent().sources), 3)

    def test_updates_replace_keys_and_explicit_removal_does_not_grow_state(self):
        self.memory.apply(expected_version=0, evidence=self.batch, upserts=(self.note(),))
        result = self.memory.apply(expected_version=1, evidence=self.batch,
                                   upserts=(self.note(content="予定を検討中"),))
        self.assertEqual(len(result.notes), 1)
        removed = self.memory.apply(expected_version=2, evidence=self.batch, remove_keys=("weekend",))
        self.assertEqual(removed.notes, ())

    def test_working_turn_is_immutable_and_cannot_change_prior_snapshot(self):
        turn = WorkingTurn("turn-1", "続けよう", self.memory.snapshot, self.batch)
        self.memory.apply(expected_version=0, evidence=self.batch, upserts=(self.note(),))
        self.assertEqual(turn.state.version, 0)
        self.assertEqual(turn.state.notes, ())
        with self.assertRaises(FrozenInstanceError):
            turn.user_input = "changed"
        with self.assertRaises(ValueError):
            WorkingTurn("turn-2", "続けよう", self.memory.snapshot,
                        replace(self.batch, scope=MemoryScope("other")))

    def test_long_raw_source_does_not_grow_short_state(self):
        source = ConversationSource.from_row("synthetic-db", 4, "user", "詳細" * 5000)
        batch = SourceBatch(self.scope, "synthetic-db", (source,))
        note = StateNote("brief", "goal", "条件を整理する", (source.ref,))
        result = self.memory.apply(expected_version=0, evidence=batch, upserts=(note,))
        self.assertLess(len(result.to_json().encode("utf-8")), 1024)
        self.assertEqual(len(note.source_refs[0].content_digest), 64)

    def test_retained_note_survives_missing_original_without_fabricating_readback(self):
        state = self.memory.apply(expected_version=0, evidence=self.batch, upserts=(self.note(),))
        # Simulate retention on this test's disposable DB only. The production
        # adapter deliberately has no delete operation.
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("DELETE FROM conversations WHERE id = 3")
        readback = self.reader.by_ids([3])
        self.assertEqual(readback.sources, ())
        self.assertEqual(readback.missing_ids, (3,))
        self.assertIs(self.memory.snapshot, state)
        self.assertEqual(state.notes[0].content, "週末の予定は未決定")


if __name__ == "__main__":
    unittest.main()
