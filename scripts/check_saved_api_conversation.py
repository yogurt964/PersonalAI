"""Saved-context API checks using temporary SQLite and a fake API only."""
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.conversation_api import SavedApiSession, PreflightError
from core.conversation_session import LegacyStore
from database.models import Base
from scripts.check_conversation_api_trial import Client
from conversation_api_app import main


class SavedConversationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = create_engine("sqlite:///" + str(Path(self.tmp.name) / "test.db"))
        Base.metadata.create_all(self.engine)
        factory = sessionmaker(bind=self.engine)
        self.patches = [patch(name, factory) for name in (
            "database.models.SessionLocal", "database.chat_history.SessionLocal",
            "database.memory_manager.SessionLocal")]
        for item in self.patches:
            item.start()
        self.store = LegacyStore()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.engine.dispose()
        self.tmp.cleanup()

    def session(self, client):
        return SavedApiSession("0.25", allow_saved_context=True, store=self.store,
                               client_factory=lambda: client)

    def test_consent_and_preview_gate_database_and_credentials(self):
        store = Mock()
        with self.assertRaises(PreflightError):
            SavedApiSession("0.25", store=store)
        self.assertEqual(store.mock_calls, [])
        with patch("sqlite3.connect", side_effect=AssertionError("DB must not open")):
            with patch("core.conversation_api.make_client", side_effect=AssertionError):
                with redirect_stdout(StringIO()):
                    self.assertEqual(main([]), 0)
                    self.assertEqual(main(["--execute", "--approved-budget-usd", "0.25"]), 1)

    def test_history_and_explicit_memory_survive_session_restart(self):
        first = self.session(Client())
        self.assertTrue(first.remember("テスト用の色は青"))
        first.reply("作業の続きを相談したい")
        first.close()
        client = Client()
        second = self.session(client)
        second.reply("覚えてる？")
        request = client.calls[0]
        self.assertIn("テスト用の色は青", request["instructions"])
        self.assertEqual(request["input"][0], {"role": "user", "content": "作業の続きを相談したい"})
        self.assertEqual([m["role"] for m in request["input"]], ["user", "assistant", "user"])
        self.assertEqual(len(self.store.history()), 4)
        self.assertEqual(second.spent, Decimal("0.0008"))
        self.assertIs(request["store"], False)
        self.assertNotIn("tools", request)

    def test_inactive_memory_is_not_sent(self):
        from database.memory_manager import set_memory_active
        self.store.remember("有効なテスト情報")
        self.store.remember("無効化したテスト情報")
        for memory in self.store.memories():
            if memory.content == "無効化したテスト情報":
                set_memory_active(memory.id, False)
        client = Client()
        self.session(client).reply("こんにちは")
        self.assertIn("有効なテスト情報", client.calls[0]["instructions"])
        self.assertNotIn("無効化したテスト情報", str(client.calls))

    def test_model_failure_does_not_save_partial_turn(self):
        self.store.save_turn("既存の発言", "既存の返答")
        before = self.store.history()
        client = Client(failure=ConnectionError("offline"))
        ai = self.session(client)
        with self.assertRaises(ConnectionError):
            ai.reply("新しい発言")
        self.assertEqual(self.store.history(), before)
        self.assertGreater(ai.spent, 0)
        with self.assertRaises(PreflightError):
            ai.reply("再送")
        self.assertEqual(len(client.calls), 1)

    def test_save_failure_stops_session_after_accounting_for_paid_reply(self):
        self.store.save_turn("既存の発言", "既存の返答")
        client = Client()
        ai = self.session(client)
        with patch.object(self.store, "save_turn", side_effect=RuntimeError("save failed")):
            with self.assertRaises(RuntimeError):
                ai.reply("新しい発言")
        self.assertTrue(ai.failed)
        self.assertEqual(ai.spent, Decimal("0.0008"))
        self.assertEqual(len(self.store.history()), 2)
        self.assertEqual(ai.history, [])
        with self.assertRaises(PreflightError):
            ai.reply("再送")
        self.assertEqual(len(client.calls), 1)

    def test_missing_existing_database_is_not_initialized(self):
        with patch("conversation_api_app.os.chdir"):
            with patch("conversation_api_app.Path.is_file", return_value=False):
                with patch("sqlite3.connect", side_effect=AssertionError("DB must not open")):
                    with redirect_stdout(StringIO()):
                        self.assertEqual(main(["--execute", "--allow-saved-context",
                                               "--approved-budget-usd", "0.25"]), 1)


if __name__ == "__main__":
    unittest.main()
