"""Offline reasoning controls: fake local classifier and fake API only."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.conversation_api import ApiTrialSession, PreflightError
from core.conversation_reasoning import LocalReasoningRouter
from scripts.check_conversation_api_trial import Client


class Model:
    def __init__(self, importance="low", complexity="low", *, raw=None, failure=None):
        self.raw = raw if raw is not None else json.dumps({"importance": importance, "complexity": complexity})
        self.failure = failure
        self.calls = []

    def __call__(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        if self.failure:
            raise self.failure
        return self.raw


class ReasoningTests(unittest.TestCase):
    def test_followup_context_reaches_classifier_and_valid_pairs_map_to_effort(self):
        history = [{"role": "user", "content": "3条件で構成を比較したい"},
                   {"role": "assistant", "content": "比較しよう"}]
        for importance, complexity, effort in (("low", "low", "low"), ("high", "low", "medium"),
                                               ("low", "high", "medium"), ("high", "high", "high")):
            with self.subTest(importance=importance, complexity=complexity):
                model = Model(importance, complexity)
                choice = LocalReasoningRouter(model).classify(history, "それなら？")
                self.assertEqual(choice.effort, effort)
                self.assertFalse(choice.fallback)
                messages, options = model.calls[0]
                self.assertEqual(messages[1:-1], history)
                self.assertEqual(messages[-1]["content"], "それなら？")
                self.assertEqual(options, {"think": False, "json_mode": True})

    def test_invalid_classification_or_local_timeout_uses_reported_fallback(self):
        models = [Model(raw=raw) for raw in ("not JSON", "[]", "{}", '{"importance":true,"complexity":"low"}')]
        models.append(Model(failure=TimeoutError("private provider detail")))
        for model in models:
            with self.subTest(raw=model.raw, failure=model.failure):
                choice = LocalReasoningRouter(model).classify([], "相談したい")
                self.assertTrue(choice.fallback)
                self.assertEqual(choice.effort, "medium")
                self.assertEqual(choice.importance, "unknown")
                self.assertNotIn("private provider detail", repr(choice))

    def test_auto_effort_and_output_headroom_are_applied_to_paid_request(self):
        for pair, effort, limit in ((('low', 'low'), 'low', 2048),
                                    (('high', 'low'), 'medium', 4096),
                                    (('high', 'high'), 'high', 4096)):
            with self.subTest(pair=pair):
                client = Client()
                router = LocalReasoningRouter(Model(*pair))
                ai = ApiTrialSession("0.50", mode="auto", router=router, client_factory=lambda: client)
                ai.reply("相談したい")
                self.assertEqual(client.calls[0]["reasoning"], {"effort": effort})
                self.assertEqual(client.calls[0]["max_output_tokens"], limit)
                self.assertEqual(len(client.calls), 1)

    def test_manual_modes_skip_classifier_and_switch_effort(self):
        router = Mock()
        router.classify.side_effect = AssertionError("Must not classify manual modes")
        client = Client()
        ai = ApiTrialSession("0.50", mode="fast", router=router, client_factory=lambda: client)
        ai.reply("こんにちは")
        ai.set_mode("deep")
        ai.reply("じっくり考えたい")
        self.assertEqual([request["reasoning"]["effort"] for request in client.calls], ["low", "high"])
        router.classify.assert_not_called()

    def test_local_classifier_failure_does_not_stop_api_conversation(self):
        client = Client()
        router = LocalReasoningRouter(Model(failure=ConnectionError("offline")))
        ai = ApiTrialSession("0.50", mode="auto", router=router, client_factory=lambda: client)
        self.assertEqual(ai.reply("こんにちは"), "試験の返答")
        self.assertTrue(ai.last_choice.fallback)
        self.assertFalse(ai.failed)
        self.assertEqual(client.calls[0]["reasoning"], {"effort": "medium"})

    def test_deeper_output_budget_is_checked_before_credentials_or_api(self):
        fast_client = Client()
        fast = ApiTrialSession("0.08", mode="fast", client_factory=lambda: fast_client)
        fast.reply("こんにちは")
        self.assertEqual(len(fast_client.calls), 1)
        deep = ApiTrialSession("0.08", mode="deep",
                               client_factory=lambda: self.fail("Must stop before creating client"))
        with self.assertRaises(PreflightError):
            deep.reply("こんにちは")
        self.assertEqual(deep.spent, 0)
        self.assertEqual(deep.history, [])


if __name__ == "__main__":
    unittest.main()
