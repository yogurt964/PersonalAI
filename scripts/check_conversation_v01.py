"""Offline behavior checks; only temporary SQLite data is written."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.conversation_session import ConversationSession, LegacyStore, bounded_history
from database.models import Base


class Model:
    def __init__(self, route=None, answer="うん、続きから考えよう。"):
        self.route = route or {"importance": "low", "complexity": "low", "memory": "normal"}
        self.answer = answer
        self.calls = []

    def __call__(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        return json.dumps(self.route) if kwargs["json_mode"] else self.answer


class ConversationTests(unittest.TestCase):
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

    def test_followup_survives_restart_and_reaches_both_calls(self):
        first = ConversationSession(model=Model())
        first.reply("AIの設計を一緒に考えたい")
        model = Model()
        ConversationSession(model=model).reply("それの続き")
        for messages, options in model.calls:
            self.assertTrue(any(m["content"] == "AIの設計を一緒に考えたい" for m in messages))
        self.assertEqual(len(self.store.history()), 4)
        self.assertFalse(model.calls[-1][1]["think"])

    def test_important_short_followup_uses_thinking(self):
        model = Model({"importance": "high", "complexity": "low", "memory": "normal"})
        ConversationSession(model=model).reply("どうしよう")
        self.assertTrue(model.calls[-1][1]["think"])

    def test_invalid_classifier_falls_back_to_deep(self):
        model = Model({"importance": "invalid"})
        ai = ConversationSession(model=model)
        ai.reply("考えて")
        self.assertTrue(ai.last_decision.fallback)
        self.assertTrue(model.calls[-1][1]["think"])

    def test_empty_answer_does_not_save_partial_turn(self):
        with self.assertRaises(ValueError):
            ConversationSession(model=Model(answer=" ")).reply("こんにちは")
        self.assertEqual(self.store.history(), [])

    def test_explicit_memory_reused_and_inactive_excluded(self):
        from database.memory_manager import set_memory_active
        self.assertTrue(self.store.remember("好きな色は青"))
        model = Model({"importance": "low", "complexity": "low", "memory": "detailed"})
        ConversationSession(model=model).reply("好きな色を覚えてる？")
        self.assertIn("好きな色は青", model.calls[-1][0][0]["content"])
        set_memory_active(self.store.memories()[0].id, False)
        ConversationSession(model=model).reply("覚えてる？")
        self.assertNotIn("好きな色は青", model.calls[-1][0][0]["content"])

    def test_manual_override_and_policy_reload(self):
        policy = Path(self.tmp.name) / "policy.md"
        policy.write_text("短く答える", encoding="utf-8")
        model = Model()
        ai = ConversationSession(model=model, policy_path=policy)
        ai.reply("こんにちは", mode="deep")
        self.assertTrue(model.calls[-1][1]["think"])
        policy.write_text("詳しく答える", encoding="utf-8")
        ai.reply("こんにちは", mode="fast")
        self.assertIn("詳しく答える", model.calls[-1][0][0]["content"])
        self.assertNotIn("短く答える", model.calls[-1][0][0]["content"])
        self.assertFalse(model.calls[-1][1]["think"])

    def test_single_system_preserves_policy_memory_and_boundaries(self):
        from core.conversation_session import BOUNDARY
        model = Model()
        self.store.save_turn("バイトが忙しかった", "どんなバイトだったの？")
        ai = ConversationSession(model=model)
        ai.reply("疲れた理由を覚えてる？")
        messages = model.calls[-1][0]
        systems = [m for m in messages if m["role"] == "system"]
        self.assertEqual(len(systems), 1)
        self.assertIn(BOUNDARY, systems[0]["content"])
        self.assertIn(ai.policy_path.read_text(encoding="utf-8"), systems[0]["content"])
        self.assertIn("【長期記憶】", systems[0]["content"])
        self.assertEqual(messages[-1]["content"], "疲れた理由を覚えてる？")
        self.assertEqual(messages[1]["content"], "バイトが忙しかった")

    def test_context_limits_and_invalid_input(self):
        history = [{"role": "user", "content": "a" * 1000}] * 100
        self.assertEqual(len(bounded_history(history)), 16)
        model = Model()
        with self.assertRaises(ValueError):
            ConversationSession(model=model).reply(" ")
        self.assertEqual(model.calls, [])

    def test_transport_failure_does_not_save(self):
        def failure(*args, **kwargs):
            raise ConnectionError("offline")
        with self.assertRaises(ConnectionError):
            ConversationSession(model=failure).reply("こんにちは")
        self.assertEqual(self.store.history(), [])


if __name__ == "__main__":
    unittest.main()
