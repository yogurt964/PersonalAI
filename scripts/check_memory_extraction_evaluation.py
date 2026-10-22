"""Offline tests for synthetic extraction evaluation and its execution gates."""
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_memory_extraction import main, make_plan, run_evaluation, PreflightError


class Client:
    def __init__(self, raw='{"candidates":[]}', status="completed", failure=None, usage=True):
        self.raw, self.status, self.failure, self.usage = raw, status, failure, usage
        self.calls, self.closed, self.responses = [], False, self

    def create(self, **request):
        self.calls.append(request)
        if self.failure:
            raise self.failure
        return SimpleNamespace(status=self.status, output_text=self.raw,
            usage=SimpleNamespace(input_tokens=100, output_tokens=20) if self.usage else None)

    def close(self):
        self.closed = True


class EvaluationTests(unittest.TestCase):
    def test_default_preview_has_six_cases_and_opens_no_clients_or_db(self):
        with patch("scripts.evaluate_memory_extraction.make_client", side_effect=AssertionError):
            with patch("sqlite3.connect", side_effect=AssertionError):
                with redirect_stdout(StringIO()):
                    self.assertEqual(main([]), 0)
        self.assertEqual(len(make_plan()), 6)

    def test_missing_or_insufficient_budget_stops_before_key_access(self):
        for budget in (None, "0.0001", "NaN", "0", "0.51"):
            with self.subTest(budget=budget), redirect_stdout(StringIO()):
                with self.assertRaises(PreflightError):
                    run_evaluation(execute=True, approved_budget=budget,
                                   client_factory=lambda: self.fail("key access"))

    def test_synthetic_payload_uses_fixed_limits_and_no_tools(self):
        client = Client()
        with patch("sqlite3.connect", side_effect=AssertionError), redirect_stdout(StringIO()):
            self.assertEqual(run_evaluation(execute=True, approved_budget="0.50",
                             client_factory=lambda: client), 0)
        self.assertEqual(len(client.calls), 6)
        for request in client.calls:
            self.assertEqual(request["model"], "gpt-6.1-sol")
            self.assertEqual(request["max_output_tokens"], 2048)
            self.assertIs(request["store"], False)
            self.assertNotIn("tools", request)
        self.assertTrue(client.closed)

    def test_failure_incomplete_and_invalid_output_stop_after_one_attempt(self):
        clients = [Client(failure=RuntimeError("secret")), Client(status="incomplete"),
                   Client(raw="invalid JSON")]
        for client in clients:
            output = StringIO()
            with self.subTest(client=client), redirect_stdout(output):
                result = run_evaluation(execute=True, approved_budget="0.50", client_factory=lambda: client)
            self.assertEqual(result, 1)
            self.assertEqual(len(client.calls), 1)
            self.assertTrue(client.closed)
            self.assertNotIn("secret", output.getvalue())

    def test_unknown_usage_retains_reserved_amount(self):
        client = Client(usage=False)
        output = StringIO()
        plan = make_plan([1])
        with redirect_stdout(output):
            run_evaluation(execute=True, approved_budget="0.50", selected_cases=[1],
                           client_factory=lambda: client)
        self.assertIn(f"${plan[0]['reserve']:.4f}", output.getvalue())

    def test_local_mode_calls_only_explicit_local_factory(self):
        local = Mock(return_value='{"candidates":[]}')
        with patch("scripts.evaluate_memory_extraction.make_client", side_effect=AssertionError):
            with redirect_stdout(StringIO()):
                self.assertEqual(run_evaluation(execute=True, engine="ollama", selected_cases=[1],
                                               local_factory=lambda: local), 0)
        local.assert_called_once()
        self.assertEqual(local.call_args.kwargs, {"think": True, "json_mode": True})

    def test_correction_case_includes_old_state_and_new_user_source(self):
        plan = make_plan([4])[0]
        turn = plan["turn"]
        self.assertEqual(turn.state.notes[0].key, "coffee")
        self.assertIn("甘くない", turn.evidence.sources[-1].content)
        self.assertEqual(turn.state.version, 1)

    def test_structure_success_does_not_mark_meaning_as_passed(self):
        output = StringIO()
        with redirect_stdout(output):
            run_evaluation(execute=True, approved_budget="0.50", selected_cases=[5],
                           client_factory=Client)
        self.assertIn("意味の評価: 未判定", output.getvalue())


if __name__ == "__main__":
    unittest.main()
