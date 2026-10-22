"""Synthetic lifecycle demo; no DB, API, saving or forgetting execution."""
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.conversation_memory import ConversationSource, MemoryScope
from core.conversation_memory_lifecycle import (
    LifecycleMemory, LifecyclePolicy, MemoryIdentity, UsageEvent, UsageLedger, evaluate_lifecycle,
)


def main():
    now = datetime(2026, 10, 22, tzinfo=timezone.utc)
    start = now - timedelta(days=120)
    identity = MemoryIdentity(MemoryScope("fictional-owner", "fictional-project"), "sample", 1)
    base = LifecycleMemory(identity, "short", start, start, 2, True, True, True)
    policy = LifecyclePolicy("demo-only-1", 30, 2, 3, 8, 3, 90)
    labels = {"retain": "保持", "hold": "保留", "review": "要確認",
              "promote_candidate": "繰り上げ候補", "forget_candidate": "忘却候補"}
    print("架空データのみ。DB・APIは使わず、保存・繰り上げ・忘却を実行しません。")
    print("実験値: 集計30日 / 2セッションで中期候補・3で長期候補 / 重要度8以上")
    print("実験値: 重要度3以下かつ90日未利用で忘却候補。製品の確定設定ではありません。")
    scenarios = [
        ("同じ発言を3回処理", base, "repeat", True),
        ("別セッションで3回言及", base, "independent", True),
        ("検索だけを3回実行", base, "retrieved", True),
        ("回答の根拠として利用", base, "used_as_evidence", True),
        ("一度の重要な決定", replace(base, importance=9), "none", True),
        ("未使用の重要プロジェクト情報", replace(base, layer="project", project_core=True), "none", True),
        ("未解決の課題", replace(base, unresolved=True), "none", True),
        ("履歴が不明な旧記憶", base, "none", False),
        ("期限切れだが明示保存済み", replace(base, explicit_save=True, expires_at=now), "none", True),
    ]
    for name, memory, pattern, known in scenarios:
        ledger = UsageLedger(identity, since=start, history_known=known)
        if pattern != "none":
            for n in range(1, 4):
                num = 1 if pattern == "repeat" else n
                kind = "mention" if pattern in ("repeat", "independent") else pattern
                source = ConversationSource.from_row("synthetic", num, "user", "架空の要点").ref if kind == "mention" else None
                event = UsageEvent(identity, f"e{num}", f"t{num}", f"s{num}", kind,
                                   now - timedelta(days=num), source)
                ledger.record(event, now=now)
        proposal = evaluate_lifecycle(memory, ledger, policy, now=now)
        stats = ledger.summary(now=now, window_days=policy.window_days)
        counts = stats["window_counts"]
        print(f"\n{name}: {labels[proposal.action]} {proposal.target_layer}")
        print(f"  言及={counts['mention']} / 独立セッション={counts['mention_sessions']} / "
              f"検索={counts['retrieved']} / 根拠利用={counts['used_as_evidence']} / 理由={proposal.reason}")
    print("\n判定だけ完了。実際の記憶は変更していません。")


if __name__ == "__main__":
    main()
