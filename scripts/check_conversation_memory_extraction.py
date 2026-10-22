"""Offline extraction contract checks. Fake model; no paid/local model or DB."""
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.conversation_memory import (
    ConversationSource, MemoryScope, ShortTermMemory, SourceBatch, WorkingTurn,
)
from core.conversation_memory_extraction import extract_memory_proposals


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.scope = MemoryScope("fictional-owner", "fictional-project")
        self.memory = ShortTermMemory(self.scope, "fixture")
        sources = (
            ConversationSource.from_row("fixture", 1, "user", "今は質問せず聞いてて。"),
            ConversationSource.from_row("fixture", 2, "assistant", "週末に出かける案もあるよ。"),
            ConversationSource.from_row("fixture", 3, "user", "まだ予定は決めていない。"),
        )
        self.turn = WorkingTurn("fixture-turn", sources[-1].content, self.memory.snapshot,
                                SourceBatch(self.scope, "fixture", sources))

    def candidate(self, **changes):
        item = {"key": "weekend", "kind": "open_question", "content": "予定は未決定",
                "tags": ["予定"], "evidence": [{"source_id": 3, "quote": "まだ予定は決めていない。"}]}
        item.update(changes)
        return item

    def run_extraction(self, items):
        model = Mock(return_value=json.dumps({"candidates": items}, ensure_ascii=False))
        result = extract_memory_proposals(self.turn, model=model)
        return result, model

    def test_valid_proposals_remain_review_only_and_do_not_modify_state(self):
        result, model = self.run_extraction([self.candidate()])
        self.assertEqual(result.status, "proposed")
        self.assertTrue(result.requires_review)
        self.assertEqual(result.based_on_version, 0)
        self.assertEqual(result.proposals[0].note.source_refs[0], self.turn.evidence.sources[2].ref)
        self.assertEqual(self.memory.snapshot.version, 0)
        self.assertEqual(self.memory.snapshot.notes, ())
        model.assert_called_once()

    def test_temporary_preference_is_a_separate_kind(self):
        item = self.candidate(key="questions", kind="temporary_preference", content="今は質問なし",
                              evidence=[{"source_id": 1, "quote": "今は質問せず聞いてて。"}])
        result, _ = self.run_extraction([item])
        self.assertEqual(result.proposals[0].note.kind, "temporary_preference")
        self.assertTrue(result.requires_review)

    def test_user_fact_cannot_use_assistant_reply_as_its_source(self):
        item = self.candidate(kind="user_fact", content="週末に出かける",
                              evidence=[{"source_id": 2, "quote": "週末に出かける案もあるよ。"}])
        result, _ = self.run_extraction([item])
        self.assertEqual(result.status, "invalid_response")
        self.assertEqual(result.proposals, ())

    def test_missing_source_and_fabricated_quote_reject_the_entire_batch(self):
        for evidence in ([{"source_id": 99, "quote": "未知の情報"}],
                         [{"source_id": 3, "quote": "予定は決まっている"}],
                         [{"source_id": True, "quote": "今は質問せず聞いてて。"}]):
            with self.subTest(evidence=evidence):
                result, _ = self.run_extraction([self.candidate(),
                    self.candidate(key="bad", evidence=evidence)])
                self.assertEqual(result.status, "invalid_response")
                self.assertEqual(result.proposals, ())

    def test_unadopted_proposal_preserves_both_speakers(self):
        result, _ = self.run_extraction([self.candidate(
            content="週末に出かける案は未決定",
            evidence=[{"source_id": 2, "quote": "週末に出かける案もあるよ。"},
                      {"source_id": 3, "quote": "まだ予定は決めていない。"}])])
        self.assertEqual(result.status, "proposed")
        self.assertEqual([r.role for r in result.proposals[0].note.source_refs],
                         ["assistant", "user"])
        self.assertTrue(result.requires_review)

    def test_assistant_only_decision_rejects_whole_batch(self):
        result, _ = self.run_extraction([self.candidate(), self.candidate(
            key="decision", kind="decision",
            evidence=[{"source_id": 2, "quote": "週末に出かける案もあるよ。"}])])
        self.assertEqual(result.status, "invalid_response")
        self.assertEqual(result.proposals, ())

    def test_user_quote_alone_does_not_prove_adoption(self):
        result, _ = self.run_extraction([self.candidate(kind="decision")])
        self.assertEqual(result.status, "proposed")
        self.assertTrue(result.requires_review)
        self.assertEqual(self.memory.snapshot.notes, ())

    def test_missing_antecedent_remains_a_semantic_review_issue(self):
        result, _ = self.run_extraction([self.candidate(content="週末に出かける案は未決定")])
        self.assertEqual(result.status, "proposed")
        self.assertTrue(result.requires_review)
        self.assertEqual(len(result.proposals[0].note.source_refs), 1)

    def test_extra_authority_fields_and_duplicate_candidate_keys_are_rejected(self):
        for items in ([self.candidate(owner_id="other")],
                      [self.candidate(delete=True)],
                      [self.candidate(), self.candidate()]):
            with self.subTest(items=items):
                result, _ = self.run_extraction(items)
                self.assertEqual(result.status, "invalid_response")

    def test_duplicate_json_fields_and_non_json_are_rejected(self):
        for raw in ('{"candidates":[],"candidates":[]}', 'not JSON', '[]', 'null'):
            with self.subTest(raw=raw):
                result = extract_memory_proposals(self.turn, model=Mock(return_value=raw))
                self.assertEqual(result.status, "invalid_response")

    def test_empty_candidates_are_a_valid_result(self):
        result, _ = self.run_extraction([])
        self.assertEqual(result.status, "proposed")
        self.assertEqual(result.proposals, ())

    def test_model_failure_is_not_retried_and_does_not_expose_private_error(self):
        model = Mock(side_effect=RuntimeError("private-key-or-source"))
        result = extract_memory_proposals(self.turn, model=model)
        self.assertEqual(result.status, "model_error")
        self.assertNotIn("private-key-or-source", repr(result))
        model.assert_called_once()
        self.assertEqual(self.memory.snapshot.version, 0)

    def test_source_free_input_does_not_call_a_model(self):
        turn = replace(self.turn, evidence=SourceBatch(self.scope, "fixture", ()))
        model = Mock(side_effect=AssertionError("must not call"))
        result = extract_memory_proposals(turn, model=model)
        self.assertEqual(result.status, "no_sources")
        model.assert_not_called()

    def test_oversized_input_is_rejected_before_model_call(self):
        source = ConversationSource.from_row("fixture", 4, "user", "あ" * 9000)
        turn = replace(self.turn, evidence=SourceBatch(self.scope, "fixture", (source,)))
        model = Mock(side_effect=AssertionError("must not call"))
        with self.assertRaises(ValueError):
            extract_memory_proposals(turn, model=model)
        model.assert_not_called()

    def test_oversized_output_and_notes_are_rejected_without_truncation(self):
        result, _ = self.run_extraction([self.candidate(content="あ" * 342)])
        self.assertEqual(result.status, "invalid_response")
        result = extract_memory_proposals(self.turn, model=Mock(return_value=" " * 32769))
        self.assertEqual(result.status, "invalid_response")

    def test_matching_quote_does_not_claim_semantic_verification(self):
        # A matching quote does NOT prove the summary preserves its meaning.
        # Keep the proposal review-only until semantic evaluation is connected.
        result, _ = self.run_extraction([self.candidate(content="予定は決定済み")])
        self.assertEqual(result.status, "proposed")
        self.assertTrue(result.requires_review)
        self.assertEqual(self.memory.snapshot.notes, ())

    def test_prompt_keeps_source_roles_and_original_negation_as_data(self):
        _, model = self.run_extraction([])
        messages = model.call_args.args[0]
        self.assertEqual([m["role"] for m in messages], ["system", "user"])
        payload = json.loads(messages[1]["content"])
        self.assertEqual(payload["source_messages"][1]["role"], "assistant")
        self.assertEqual(payload["source_messages"][2]["content"], "まだ予定は決めていない。")
        self.assertNotIn("owner_id", payload["state"])

    def test_result_is_bound_to_state_and_request(self):
        first, _ = self.run_extraction([])
        second = extract_memory_proposals(replace(self.turn, user_input="別の入力"),
                                           model=Mock(return_value='{"candidates":[]}'))
        self.assertNotEqual(first.context_digest, second.context_digest)


if __name__ == "__main__":
    unittest.main()
