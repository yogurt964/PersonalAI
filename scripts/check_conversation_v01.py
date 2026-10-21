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
        for messages, options in model.calls[:2]:
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

    def test_quoted_false_from_live_trace_still_runs_editor(self):
        model = Model({"importance": "low", "complexity": "low", "memory": "normal",
                       "recall_user_fact": "false",
                       "evidence": ["バイトが忙しかったんだよね。"]},
                      answer="昨日より楽だったんだね。何かあったら話してね。")
        self.store.save_turn("バイトが忙しかったんだよね。", "お疲れ様")
        ai = ConversationSession(model=model)
        ai.reply("今日は昨日より楽だった")
        self.assertFalse(ai.last_decision.fallback)
        self.assertFalse(ai.last_decision.think)
        self.assertIs(ai.last_decision.recall_user_fact, False)
        self.assertEqual(len(model.calls), 3)
        self.assertFalse(model.calls[1][1]["think"])

    def test_quoted_true_preserves_recall_and_invalid_values_fall_back(self):
        history = [{"role": "user", "content": "バイトが忙しかった"}]
        for value in (True, "true", " TRUE "):
            with self.subTest(value=value):
                route = {"importance": "low", "complexity": "low", "memory": "detailed",
                         "recall_user_fact": value, "evidence": [history[0]["content"]]}
                decision = ConversationSession(model=Model(route)).decide(history, "覚えてる？")
                self.assertFalse(decision.fallback)
                self.assertIs(decision.recall_user_fact, True)
                self.assertEqual(decision.evidence, (history[0]["content"],))
        for value in ("no", "", None, 0, 1, [], {}):
            with self.subTest(invalid=value):
                route = {"importance": "low", "complexity": "low", "memory": "normal",
                         "recall_user_fact": value, "evidence": []}
                decision = ConversationSession(model=Model(route)).decide(history, "続き")
                self.assertTrue(decision.fallback)
                self.assertTrue(decision.think)

    def test_empty_answer_does_not_save_partial_turn(self):
        with self.assertRaises(ValueError):
            ConversationSession(model=Model(answer=" ")).reply("こんにちは")
        self.assertEqual(self.store.history(), [])

    def test_explicit_memory_reused_and_inactive_excluded(self):
        from database.memory_manager import set_memory_active
        self.assertTrue(self.store.remember("好きな色は青"))
        model = Model({"importance": "low", "complexity": "low", "memory": "detailed"})
        ConversationSession(model=model).reply("好きな色を覚えてる？")
        self.assertIn("好きな色は青", model.calls[1][0][0]["content"])
        set_memory_active(self.store.memories()[0].id, False)
        ConversationSession(model=model).reply("覚えてる？")
        self.assertNotIn("好きな色は青", model.calls[-2][0][0]["content"])

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
        messages = model.calls[1][0]
        systems = [m for m in messages if m["role"] == "system"]
        self.assertEqual(len(systems), 1)
        self.assertIn(BOUNDARY, systems[0]["content"])
        self.assertIn(ai.policy_path.read_text(encoding="utf-8"), systems[0]["content"])
        self.assertIn("【長期記憶】", systems[0]["content"])
        self.assertEqual(messages[-1]["content"], "疲れた理由を覚えてる？")
        self.assertEqual(messages[1]["content"], "バイトが忙しかった")

    def test_recall_uses_only_verified_user_evidence(self):
        self.store.save_turn("バイトが忙しかった", "睡眠不足だったんだね")
        model = Model({"importance": "low", "complexity": "low", "memory": "detailed",
                       "recall_user_fact": True,
                       "evidence": ["睡眠不足だったんだね", "架空の発言", "バイトが忙しかった"]})
        ai = ConversationSession(model=model)
        ai.reply("疲れた理由覚えてる？")
        self.assertEqual(ai.last_decision.evidence, ("バイトが忙しかった",))
        messages = model.calls[-1][0]
        self.assertEqual([m["role"] for m in messages], ["system", "user"])
        self.assertIn("バイトが忙しかった", messages[0]["content"])
        self.assertNotIn("睡眠不足だったんだね", messages[0]["content"])
        self.assertNotIn("架空の発言", messages[0]["content"])

    def test_recall_without_evidence_does_not_replay_assistant(self):
        self.store.save_turn("こんにちは", "あなたはパン屋で働いている")
        model = Model({"importance": "low", "complexity": "low", "memory": "detailed",
                       "recall_user_fact": True, "evidence": []})
        ai = ConversationSession(model=model)
        ai.reply("俺のバイト覚えてる？")
        self.assertEqual(ai.last_decision.evidence, ())
        self.assertNotIn("パン屋", str(model.calls[-1][0]))
        self.assertIn("根拠が不足", model.calls[-1][0][0]["content"])

    def test_closing_edit_is_independent_and_only_final_answer_is_saved(self):
        self.store.save_turn("バイトが忙しかった", "過去の定型返答")
        draft = "昨日より楽だったんだね。無理せず、しっかり休んでね。"
        class EditorModel(Model):
            def __call__(self, messages, **kwargs):
                result = super().__call__(messages, **kwargs)
                return "お、今日は少し余裕あったんだね。" if len(self.calls) == 3 else result
        model = EditorModel(answer=draft)
        ai = ConversationSession(model=model)
        final = ai.reply("今日は昨日より楽だった")
        self.assertEqual(len(model.calls), 3)
        edit_messages = model.calls[-1][0]
        self.assertEqual(len(edit_messages), 2)
        self.assertNotIn("過去の定型返答", str(edit_messages))
        self.assertEqual(json.loads(edit_messages[-1]["content"])["draft_reply"], draft)
        self.assertEqual(self.store.history()[-1]["content"], final)
        self.assertNotEqual(final, draft)

    def test_paraphrase_without_closing_is_edited_with_user_context(self):
        self.store.save_turn("今日は昨日より楽だった", "過去のAIの話し方")
        draft = "明日はまた忙しそうなんだね。"
        model = Model(answer=draft)
        ConversationSession(model=model).reply("でも明日は忙しそうなんだよな")
        self.assertEqual(len(model.calls), 3)
        payload = json.loads(model.calls[-1][0][-1]["content"])
        self.assertEqual(payload["user_context"], ["今日は昨日より楽だった"])
        self.assertEqual(payload["draft_reply"], draft)
        self.assertNotIn("過去のAIの話し方", str(model.calls[-1][0]))

    def test_failed_edit_does_not_save_draft(self):
        class FailedEditor(Model):
            def __call__(self, messages, **kwargs):
                result = super().__call__(messages, **kwargs)
                if len(self.calls) == 3:
                    raise ConnectionError("editor offline")
                return result
        with self.assertRaises(ConnectionError):
            ConversationSession(model=FailedEditor(answer="何かあったら話してね")).reply("今日は楽だった")
        self.assertEqual(self.store.history(), [])

    def test_high_importance_answer_skips_casual_edit(self):
        model = Model({"importance": "high", "complexity": "low", "memory": "normal"},
                      answer="無理せず休んでください")
        ConversationSession(model=model).reply("体調について相談したい")
        self.assertEqual(len(model.calls), 2)

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
