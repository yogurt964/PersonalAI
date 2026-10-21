"""Offline checks for the ephemeral API trial; no real key, DB, or API."""
import sys
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.conversation_api import ApiTrialSession, PreflightError
from conversation_api_trial import main


class Client:
    def __init__(self, *, usage=True, status="completed", failure=None):
        self.responses = self
        self.calls = []
        self.usage, self.status, self.failure = usage, status, failure
        self.closed = False

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.failure:
            raise self.failure
        return SimpleNamespace(status=self.status, output_text="試験の返答",
                               usage=SimpleNamespace(input_tokens=100, output_tokens=20)
                               if self.usage else None)

    def close(self):
        self.closed = True


class TrialTests(unittest.TestCase):
    def test_preview_and_construction_do_not_create_client(self):
        with patch("core.conversation_api.make_client", side_effect=AssertionError):
            with redirect_stdout(StringIO()):
                self.assertEqual(main([]), 0)
                self.assertEqual(main(["--execute"]), 1)
            ApiTrialSession("0.50").close()

    def test_budget_rejects_before_network_or_key_access(self):
        for budget in ("NaN", "Infinity", "-1", "0", "0.51", "bad"):
            with self.subTest(budget=budget), self.assertRaises(PreflightError):
                ApiTrialSession(budget)
        ai = ApiTrialSession("0.00001", client_factory=lambda: self.fail("Client must not be created"))
        with self.assertRaises(PreflightError):
            ai.reply("こんにちは")
        self.assertEqual(ai.history, [])
        self.assertEqual(ai.spent, 0)

    def test_only_current_trial_context_is_sent_and_usage_is_counted(self):
        client = Client()
        ai = ApiTrialSession("0.50", client_factory=lambda: client)
        ai.set_preference("関心を示してほしい")
        with patch("sqlite3.connect", side_effect=AssertionError("DB must not open")):
            ai.reply("今日は楽だった")
            ai.reply("でも明日は忙しそう。今日は質問なしで聞いてて")
        first, second = client.calls
        self.assertEqual(first["input"], [{"role": "user", "content": "今日は楽だった"}])
        self.assertEqual([m["role"] for m in second["input"]], ["user", "assistant", "user"])
        self.assertEqual(second["input"][0]["content"], "今日は楽だった")
        self.assertIn("関心を示してほしい", second["instructions"])
        self.assertIn("今日は質問なしで", second["input"][-1]["content"])
        self.assertFalse(second["store"])
        self.assertNotIn("tools", second)
        # Conservative Sol rate allowance: 100*4 + 20*20 per million.
        self.assertEqual(ai.spent, Decimal("0.0016"))
        ai.close()
        self.assertTrue(client.closed)

    def test_unknown_usage_keeps_reservation_and_stops_when_exhausted(self):
        client = Client(usage=False)
        ai = ApiTrialSession("0.50", client_factory=lambda: client)
        ai.reply("こんにちは")
        self.assertEqual(ai.spent, ai.last_stats["reserved_usd"])
        ai.budget = ai.spent + Decimal("0.000001")
        with self.assertRaises(PreflightError):
            ai.reply("続けよう")
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(len(ai.history), 2)

    def test_failed_request_keeps_reservation_and_cannot_be_retried(self):
        client = Client(failure=ConnectionError("provider details"))
        ai = ApiTrialSession("0.50", client_factory=lambda: client)
        with self.assertRaises(ConnectionError):
            ai.reply("こんにちは")
        self.assertGreater(ai.spent, 0)
        self.assertEqual(ai.history, [])
        with self.assertRaises(PreflightError):
            ai.reply("もう一度")
        self.assertEqual(len(client.calls), 1)

    def test_incomplete_reply_does_not_enter_conversation_context(self):
        ai = ApiTrialSession("0.50", client_factory=lambda: Client(status="incomplete"))
        with self.assertRaises(RuntimeError):
            ai.reply("こんにちは")
        self.assertEqual(ai.history, [])
        self.assertTrue(ai.failed)
        self.assertEqual(ai.spent, Decimal("0.0008"))

    def test_cli_stops_on_error_and_does_not_print_provider_details(self):
        client = Client(failure=ValueError("sensitive provider detail"))
        output = StringIO()
        with patch("core.conversation_api.make_client", return_value=client):
            with patch("builtins.input", return_value="こんにちは"):
                with redirect_stdout(output):
                    self.assertEqual(main(["--execute", "--approved-budget-usd", "0.50"]), 1)
        self.assertEqual(len(client.calls), 1)
        self.assertTrue(client.closed)
        self.assertNotIn("sensitive provider detail", output.getvalue())


if __name__ == "__main__":
    unittest.main()
