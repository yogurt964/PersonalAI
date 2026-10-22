"""Offline synthetic lifecycle checks; no database, model or network."""
import sys
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.conversation_memory import ConversationSource, MemoryScope
from core.conversation_memory_lifecycle import (
    LifecycleMemory, LifecyclePolicy, MemoryIdentity, UsageEvent, UsageLedger, evaluate_lifecycle,
)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.now = self.start + timedelta(days=120)
        self.identity = MemoryIdentity(MemoryScope("synthetic", "project-a"), "note-1", 1)
        self.memory = LifecycleMemory(self.identity, "short", self.start, self.start, 2, True, True, True)
        self.policy = LifecyclePolicy("experiment-1", 30, 2, 3, 8, 3, 90)
        self.ledger = UsageLedger(self.identity, since=self.start, history_known=True)

    def event(self, n=1, kind="mention", **changes):
        source = ConversationSource.from_row("fixture", n, "user", "架空の発言").ref if kind == "mention" else None
        event = UsageEvent(self.identity, f"event-{n}", f"turn-{n}", f"session-{n}", kind,
                           self.now - timedelta(days=n), source)
        return replace(event, **changes)

    def evaluate(self, **changes):
        return evaluate_lifecycle(replace(self.memory, **changes), self.ledger, self.policy, now=self.now)

    def test_retry_same_event_turn_and_source_not_double_counted(self):
        event = self.event()
        self.assertTrue(self.ledger.record(event, now=self.now))
        for duplicate in (event, replace(event, event_id="retry"),
                          replace(event, event_id="other", turn_id="other", session_id="other")):
            self.assertFalse(self.ledger.record(duplicate, now=self.now))
        self.assertEqual(self.ledger.summary(now=self.now, window_days=30)["window_counts"]["mention"], 1)

    def test_conflicting_event_id_is_rejected(self):
        self.ledger.record(self.event(), now=self.now)
        with self.assertRaises(ValueError):
            self.ledger.record(self.event(2, event_id="event-1"), now=self.now)
        self.assertEqual(len(self.ledger.events), 1)

    def test_assistant_repetition_is_not_a_mention(self):
        ref = ConversationSource.from_row("fixture", 1, "assistant", "復唱").ref
        with self.assertRaises(ValueError):
            self.event(source=ref)

    def test_same_session_mentions_do_not_promote(self):
        for n in range(1, 5):
            self.ledger.record(self.event(n, session_id="same"), now=self.now)
        self.assertEqual(self.evaluate().action, "retain")

    def test_two_sessions_medium_three_long(self):
        for n in (1, 2):
            self.ledger.record(self.event(n), now=self.now)
        self.assertEqual(self.evaluate().target_layer, "medium")
        self.ledger.record(self.event(3), now=self.now)
        self.assertEqual(self.evaluate().target_layer, "long")
        self.assertEqual(self.memory.layer, "short")

    def test_window_excludes_old_mentions(self):
        for n in (1, 2, 3):
            self.ledger.record(self.event(n, at=self.start + timedelta(days=n)), now=self.now)
        self.assertEqual(self.evaluate().action, "forget_candidate")
        stats = self.ledger.summary(now=self.now, window_days=30)
        self.assertEqual(stats["total_counts"]["mention"], 3)
        self.assertEqual(stats["window_counts"]["mention"], 0)

    def test_idle_boundary_and_recent_update(self):
        for age, expected in ((89, "retain"), (90, "forget_candidate")):
            result = evaluate_lifecycle(self.memory, self.ledger, self.policy,
                                        now=self.start + timedelta(days=age))
            self.assertEqual(result.action, expected)
        self.assertEqual(self.evaluate(updated_at=self.now).action, "retain")

    def test_retrieval_and_selection_neither_promote_nor_renew(self):
        for n, kind in enumerate(("retrieved", "context_selected", "retrieved"), 1):
            self.ledger.record(self.event(n, kind), now=self.now)
        self.assertEqual(self.evaluate().reason, "low_importance_and_idle")

    def test_successful_evidence_use_renews_but_does_not_promote(self):
        self.ledger.record(self.event(kind="used_as_evidence"), now=self.now)
        self.assertEqual(self.evaluate().action, "retain")
        self.assertEqual(self.ledger.summary(now=self.now, window_days=30)["window_counts"]["mention"], 0)

    def test_failed_use_not_counted(self):
        self.assertFalse(self.ledger.record(self.event(kind="used_as_evidence", successful=False), now=self.now))
        self.assertEqual(self.evaluate().action, "forget_candidate")

    def test_important_once_and_explicit_can_skip_layers(self):
        self.assertEqual(self.evaluate(importance=8).target_layer, "long")
        self.assertEqual(self.evaluate(explicit_save=True).target_layer, "long")
        self.assertNotEqual(self.evaluate(durable=False, explicit_save=True).action, "promote_candidate")

    def test_promotion_requires_reviewed_evidence_and_no_conflict(self):
        self.assertNotEqual(self.evaluate(evidence_reviewed=False, importance=9).action, "promote_candidate")
        self.assertEqual(self.evaluate(conflict=True, importance=9).action, "review")
        self.assertEqual(self.evaluate(storage_allowed=False, importance=9).action, "hold")

    def test_project_protection_and_project_target(self):
        self.assertEqual(self.evaluate(project_core=True).target_layer, "project")
        self.assertEqual(self.evaluate(project_core=True, layer="project").action, "retain")
        self.assertEqual(self.evaluate(project_core=True, expires_at=self.start).action, "review")

    def test_unresolved_and_pinned_are_protected(self):
        for flags in ({"pinned": True}, {"unresolved": True}):
            self.assertEqual(self.evaluate(**flags).action, "retain")
            self.assertEqual(self.evaluate(**flags, expires_at=self.start).action, "review")

    def test_expiry_before_promotion_and_explicit_review(self):
        self.assertEqual(self.evaluate(expires_at=self.now).reason, "expired")
        self.assertEqual(self.evaluate(explicit_save=True, expires_at=self.now).action, "review")
        self.assertEqual(self.evaluate(explicit_save=True, durable=False).action, "review")

    def test_unknown_history_is_not_zero_usage(self):
        self.ledger = UsageLedger(self.identity, since=self.start, history_known=False)
        self.assertEqual(self.evaluate().reason, "incomplete_usage_history")
        self.ledger = UsageLedger(self.identity, since=self.start + timedelta(days=1), history_known=True)
        self.assertEqual(self.evaluate().reason, "incomplete_usage_history")

    def test_negative_feedback_holds_even_high_frequency(self):
        for n in (1, 2, 3):
            self.ledger.record(self.event(n), now=self.now)
        self.ledger.record(self.event(4, "feedback_negative"), now=self.now)
        self.assertEqual(self.evaluate().action, "review")

    def test_scope_memory_and_version_mismatches_rejected(self):
        for identity in (replace(self.identity, version=2), replace(self.identity, memory_id="another"),
                         replace(self.identity, scope=MemoryScope("other"))):
            with self.assertRaises(ValueError):
                self.ledger.record(self.event(identity=identity), now=self.now)
            with self.assertRaises(ValueError):
                self.evaluate(identity=identity)

    def test_capacity_rejects_new_event_without_eviction(self):
        self.ledger = UsageLedger(self.identity, since=self.start, history_known=True, max_events=1)
        self.ledger.record(self.event(), now=self.now)
        with self.assertRaises(ValueError):
            self.ledger.record(self.event(2), now=self.now)
        self.assertFalse(self.ledger.record(self.event(), now=self.now))
        self.assertEqual(len(self.ledger.events), 1)

    def test_invalid_times_and_thresholds_rejected(self):
        for at in (self.now.replace(tzinfo=None), self.now + timedelta(days=1), self.start - timedelta(days=1)):
            with self.assertRaises(ValueError):
                self.ledger.record(self.event(at=at), now=self.now)
        with self.assertRaises(ValueError):
            replace(self.policy, forget_at_most=8)
        with self.assertRaises(ValueError):
            replace(self.memory, importance=True)

    def test_repeatable_proposal_bound_to_input_and_changes(self):
        first = self.evaluate()
        self.assertEqual(first, self.evaluate())
        self.assertTrue(first.dry_run)
        self.assertNotEqual(first.input_digest, self.evaluate(updated_at=self.now).input_digest)
        self.ledger.record(self.event(), now=self.now)
        self.assertNotEqual(first.input_digest, self.evaluate().input_digest)


if __name__ == "__main__":
    unittest.main()
