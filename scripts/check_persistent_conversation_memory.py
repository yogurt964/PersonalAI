"""End-to-end tests with temporary databases and fake API; never production data."""
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing, redirect_stdout
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.conversation_memory_workspace import MemoryWorkspace, MAX_PAYLOAD
from core.conversation_memory import StateConflict
from core.conversation_api_memory import MemoryApiSession
from core.conversation_api import PreflightError
from conversation_api_app import main


class FakeStore:
    def __init__(self, path):
        self.path = path

    def history(self):
        with closing(sqlite3.connect(self.path)) as db:
            return [{'role': role, 'content': text} for role, text in db.execute(
                'SELECT role, content FROM conversations ORDER BY id DESC LIMIT 20').fetchall()[::-1]]

    def memories(self):
        return []

    def save_turn(self, user, answer):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executemany('INSERT INTO conversations(role,content,created_at) VALUES (?,?,?)',
                           [(role, text, '2026-10-22T00:00:00+00:00') for role, text in (('user', user), ('assistant', answer))])


class FakeClient:
    def __init__(self, outputs):
        self.outputs, self.calls, self.responses = list(outputs), [], self
        self.closed = False

    def create(self, **request):
        self.calls.append(request)
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return SimpleNamespace(status='completed', output_text=output,
                               usage=SimpleNamespace(input_tokens=100, output_tokens=20))

    def close(self):
        self.closed = True


def candidate(kind='open_question', key='weekend', text='週末の予定は未決定。', source=1):
    return {'key': key, 'kind': kind, 'content': text, 'tags': [],
            'evidence': [{'source_id': source, 'quote': text}]}


def extraction(*items):
    return json.dumps({'candidates': items}, ensure_ascii=False)


class PersistentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source, self.path = self.root / 'legacy.db', self.root / 'short.sqlite3'
        with closing(sqlite3.connect(self.source)) as db, db:
            db.execute('CREATE TABLE conversations(id INTEGER PRIMARY KEY,role TEXT,content TEXT,created_at TEXT)')
        self.store = FakeStore(self.source)
        self.clock = lambda: datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
        self.store.save_turn('週末の予定は未決定。', '了解。')
        self.workspace = self.open()

    def tearDown(self):
        self.tmp.cleanup()

    def open(self):
        return MemoryWorkspace(self.path, self.source, clock=self.clock)

    def session(self, client, workspace=None, budget='0.50'):
        return MemoryApiSession(budget, allow_saved_context=True, store=self.store,
                                workspace=workspace or self.workspace, client_factory=lambda: client)

    def adopt(self):
        ai = self.session(FakeClient([extraction(candidate())]))
        ai.extract_candidates()
        ai.accept_candidates([1])
        return ai

    def test_full_conversation_extraction_accept_restart_context_usage(self):
        client = FakeClient(['まだ決めてないんだね。', extraction(candidate()), '覚えているよ。'])
        ai = self.session(client)
        ai.reply('週末の予定は未決定。')
        self.assertEqual(len(client.calls), 1)  # No hidden automatic extraction.
        ai.extract_candidates()
        self.assertEqual(ai.workspace.state.notes, ())  # Proposal alone is never adopted.
        ai.accept_candidates([1])
        ai.reply('予定の話を続けよう')
        ai.close()
        reopened = self.open()
        self.assertEqual(reopened.state.notes[0].content, '週末の予定は未決定。')
        counts = reopened.ledgers['weekend'].summary(now=self.clock(), window_days=30)['total_counts']
        self.assertEqual(counts['mention'], 1)
        self.assertEqual(counts['context_selected'], 1)
        self.assertEqual(counts['used_as_evidence'], 0)
        second_client = FakeClient(['続けよう。'])
        second = self.session(second_client, reopened)
        second.reply('前の相談は？')
        self.assertIn('採用済み短期記憶', second_client.calls[0]['instructions'])
        self.assertIn('入力履歴の先頭6件は今回の起動より前', second_client.calls[0]['instructions'])
        self.assertIn('週末の予定は未決定。', second_client.calls[0]['instructions'])
        self.assertEqual(ai.spent, Decimal('0.0024'))  # Extraction shares the response budget.
        self.assertEqual(second.pending, None)

    def test_temporary_preference_cleared_on_restart_unresolved_retained(self):
        self.store.save_turn('今日は質問なし。', 'わかった。')
        ai = self.session(FakeClient([extraction(candidate(), candidate('temporary_preference', 'today', '今日は質問なし。', 3))]))
        ai.extract_candidates()
        ai.accept_candidates([1, 2])
        self.assertEqual(len(ai.workspace.state.notes), 2)
        restarted = self.open()
        self.assertEqual([n.key for n in restarted.state.notes], ['weekend'])
        self.assertEqual(set(restarted.ledgers), {'weekend'})

    def test_explicit_topic_end_and_usage_commands(self):
        ai = self.adopt()
        self.assertIn('weekend', ai.memory_command('/short-memory'))
        self.assertIn('文脈選択=0', ai.memory_command('/memory-usage'))
        ai.memory_command('/end-topic')
        self.assertEqual(len(ai.workspace.state.notes), 1)
        self.assertIsNone(ai.pending)

    def test_budget_before_client_and_no_state_change(self):
        client = FakeClient([])
        ai = self.session(client, budget='0.00001')
        with self.assertRaises(PreflightError):
            ai.extract_candidates()
        self.assertEqual(client.calls, [])
        self.assertEqual(ai.spent, 0)
        self.assertEqual(self.open().state.notes, ())

    def test_failed_extraction_no_adoption_no_retry_and_reservation_kept(self):
        client = FakeClient([RuntimeError('private failure')])
        ai = self.session(client)
        with self.assertRaises(PreflightError) as error:
            ai.extract_candidates()
        self.assertNotIn('private failure', str(error.exception))
        with self.assertRaises(PreflightError):
            ai.extract_candidates()
        self.assertEqual(len(client.calls), 1)
        self.assertGreater(ai.spent, 0)
        self.assertEqual(self.open().state.notes, ())

    def test_malformed_extraction_keeps_prior_state(self):
        self.adopt()
        ai = self.session(FakeClient(['not json']))
        with self.assertRaises(PreflightError):
            ai.extract_candidates()
        self.assertEqual(len(self.open().state.notes), 1)

    def test_changed_source_blocks_adoption(self):
        ai = self.session(FakeClient([extraction(candidate())]))
        ai.extract_candidates()
        with closing(sqlite3.connect(self.source)) as db, db:
            db.execute("UPDATE conversations SET content='訂正済み' WHERE id=1")
        with self.assertRaises(ValueError):
            ai.accept_candidates([1])
        self.assertEqual(self.open().state.notes, ())

    def test_missing_original_retains_summary_but_marks_unavailable(self):
        self.adopt()
        with closing(sqlite3.connect(self.source)) as db, db:
            db.execute('DELETE FROM conversations WHERE id=1')  # Synthetic fixture only.
        restarted = self.open()
        self.assertFalse(restarted.context()[0]['sources_available_unchanged'])
        self.assertEqual(restarted.state.notes[0].content, '週末の予定は未決定。')

    def test_concurrent_writer_cannot_overwrite_state_or_counts(self):
        other = self.open()
        self.adopt()
        with self.assertRaises(StateConflict):
            other.end_topic()
        self.assertEqual(len(self.open().state.notes), 1)

    def test_state_changed_after_extraction_rejects_old_candidate(self):
        ai = self.session(FakeClient([extraction(candidate())]))
        ai.extract_candidates()
        ai.workspace.end_topic()
        with self.assertRaises(StateConflict):
            ai.accept_candidates([1])

    def test_duplicate_adoption_does_not_inflate_mentions(self):
        ai = self.adopt()
        ai._client = FakeClient([extraction(candidate())])
        ai.extract_candidates()
        ai.accept_candidates([1])
        counts = self.open().ledgers['weekend'].summary(now=self.clock(), window_days=30)['total_counts']
        self.assertEqual(counts['mention'], 1)

    def test_workspace_write_failure_keeps_prior_snapshot(self):
        ai = self.session(FakeClient([extraction(candidate())]))
        ai.extract_candidates()
        with patch.object(self.workspace, '_commit', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                ai.accept_candidates([1])
        self.assertEqual(self.workspace.state.notes, ())
        self.assertEqual(self.open().state.notes, ())

    def test_sql_transaction_abort_does_not_partially_update(self):
        ai = self.session(FakeClient([extraction(candidate())]))
        ai.extract_candidates()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TRIGGER fail_update BEFORE UPDATE ON companion_memory BEGIN SELECT RAISE(ABORT, 'fixture write failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            ai.accept_candidates([1])
        self.assertEqual(self.workspace.state.notes, ())
        self.assertEqual(self.open().state.notes, ())

    def test_cli_commands_extract_accept_reply_and_exit(self):
        data = self.root / 'data'
        data.mkdir()
        legacy = data / 'personal_ai.db'
        legacy.write_bytes(self.source.read_bytes())
        client = FakeClient([extraction(candidate()), '続けよう。'])
        previous, change = Path.cwd(), os.chdir
        output = StringIO()
        try:
            with patch('conversation_api_app.os.chdir', side_effect=lambda _path: change(self.root)), \
                 patch('core.conversation_session.LegacyStore', side_effect=lambda: FakeStore(legacy)), \
                 patch('core.conversation_api.make_client', return_value=client), \
                 patch('builtins.input', side_effect=['/extract-memory', '/accept-memory 1', '/short-memory',
                                                      '続きを話そう', '/memory-usage', '/exit']), \
                 redirect_stdout(output):
                self.assertEqual(main(['--execute', '--allow-saved-context', '--enable-short-memory',
                                       '--approved-budget-usd', '0.25']), 0)
        finally:
            change(previous)
        self.assertTrue(client.closed)
        self.assertEqual(len(client.calls), 2)
        self.assertIn('採用済み短期記憶を保存しました', output.getvalue())
        self.assertIn('文脈選択=1', output.getvalue())
        reopened = MemoryWorkspace(data / 'conversation_memory.sqlite3', legacy)
        self.assertEqual(len(reopened.state.notes), 1)

    def test_stats_failure_does_not_hide_saved_answer(self):
        ai = self.adopt()
        ai._client = FakeClient(['会話は成功'])
        with patch.object(self.workspace, 'record_selection', side_effect=OSError('disk full')):
            self.assertEqual(ai.reply('続けよう'), '会話は成功')
        self.assertIn('利用統計', ai.memory_warning)
        self.assertFalse(ai.failed)
        self.assertEqual(self.store.history()[-1]['content'], '会話は成功')

    def test_source_db_untouched_by_memory_operations(self):
        before = self.source.read_bytes()
        ai = self.adopt()
        ai.memory_command('/memory-usage')
        self.open()
        self.assertEqual(self.source.read_bytes(), before)

    def test_source_path_binding_and_corruption_fail_closed(self):
        other = self.root / 'other.db'
        other.write_bytes(self.source.read_bytes())
        with self.assertRaises(ValueError):
            MemoryWorkspace(self.path, other)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE companion_memory SET payload='broken' WHERE id=1")
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.open()
        self.assertEqual(self.path.read_bytes(), before)

    def test_payload_cap_and_invalid_candidate_number(self):
        with self.assertRaises(ValueError):
            self.workspace._encode({'text': 'x' * MAX_PAYLOAD})
        ai = self.session(FakeClient([extraction(candidate())]))
        ai.extract_candidates()
        for selection in ([], [0], [1, 1], [True]):
            with self.assertRaises(PreflightError):
                ai.accept_candidates(selection)
        self.assertEqual(self.open().state.notes, ())

    def test_preview_never_opens_db_or_client(self):
        with patch('sqlite3.connect', side_effect=AssertionError('no DB')), redirect_stdout(StringIO()):
            self.assertEqual(main(['--enable-short-memory']), 0)
            self.assertEqual(main(['--execute', '--enable-short-memory', '--approved-budget-usd', '0.25']), 1)


if __name__ == '__main__':
    unittest.main()
