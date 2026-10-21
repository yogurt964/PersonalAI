"""Offline checks for paid comparison controls; no key or real API is used."""
import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.compare_conversation_engines import (
    make_plan, run_comparison, PreflightError, main,
)
from scripts.diagnose_conversation_context import adaptation_scenarios, minimal_messages


class Client:
    def __init__(self, status="completed", failure=None):
        self.responses = self
        self.calls = []
        self.status, self.failure, self.closed = status, failure, False

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.failure:
            raise self.failure
        return SimpleNamespace(status=self.status, output_text="試験の返答",
                               usage=SimpleNamespace(input_tokens=220, output_tokens=40))

    def close(self):
        self.closed = True


class ComparisonTests(unittest.TestCase):
    def test_preview_never_loads_key_opens_database_or_creates_client(self):
        with patch("scripts.compare_conversation_engines.make_client", side_effect=AssertionError):
            with patch("sqlite3.connect", side_effect=AssertionError):
                with redirect_stdout(StringIO()):
                    self.assertEqual(main([]), 0)
        self.assertEqual(len(make_plan()), 12)

    def test_budget_rejection_precedes_client_creation(self):
        for budget in (None, "0", "-1", "0.0001", "NaN", "Infinity", "0.51"):
            with self.subTest(budget=budget):
                with patch("scripts.compare_conversation_engines.make_client", side_effect=AssertionError):
                    with redirect_stdout(StringIO()):
                        with self.assertRaises(PreflightError):
                            run_comparison(execute=True, approved_budget=budget)

    def test_actual_payload_matches_local_minimal_test_and_enforces_limits(self):
        client = Client()
        with patch("sqlite3.connect", side_effect=AssertionError):
            with redirect_stdout(StringIO()):
                run_comparison(execute=True, approved_budget="0.50", selected_cases=[2],
                               client_factory=lambda: client)
        self.assertEqual(len(client.calls), 2)
        _, _, history, preferences, question = list(adaptation_scenarios())[1]
        expected = minimal_messages(history, preferences, question)
        for request in client.calls:
            self.assertEqual(request["instructions"], expected[0]["content"])
            self.assertEqual(request["input"], expected[1:])
            self.assertEqual(request["max_output_tokens"], 2048)
            self.assertEqual(request["reasoning"], {"effort": "low"})
            self.assertIs(request["store"], False)
            self.assertNotIn("tools", request)
        self.assertTrue(client.closed)

    def test_failure_or_incomplete_response_stops_without_retry(self):
        for client in (Client(status="incomplete"), Client(failure=ConnectionError("private detail"))):
            with self.subTest(status=client.status, failure=client.failure):
                with redirect_stdout(StringIO()):
                    with self.assertRaises((RuntimeError, ConnectionError)):
                        run_comparison(execute=True, approved_budget="0.50", client_factory=lambda: client)
                self.assertEqual(len(client.calls), 1)
                self.assertTrue(client.closed)

    def test_provider_value_error_is_not_printed(self):
        output = StringIO()
        client = Client(failure=ValueError("sensitive provider detail"))
        with patch("scripts.compare_conversation_engines.make_client", return_value=client):
            with redirect_stdout(output):
                self.assertEqual(main(["--execute", "--approved-budget-usd", "0.50"]), 1)
        self.assertNotIn("sensitive provider detail", output.getvalue())


if __name__ == "__main__":
    unittest.main()
