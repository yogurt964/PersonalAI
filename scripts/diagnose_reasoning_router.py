"""Run synthetic local routing cases; never read a DB or call a paid API."""
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.conversation_reasoning import LocalReasoningRouter


def main():
    cases = [
        ("雑談", [], "今日はちょっと疲れた", "low"),
        ("複数条件の相談の続き", [
            {"role": "user", "content": "個人用AIの構成を、プライバシー・費用・応答速度の3条件で比較したい"},
            {"role": "assistant", "content": "その3条件で構成を比較しよう。"},
        ], "それならどれがいい？", "mediumまたはhigh"),
        ("重大かつ複雑な相談", [], "仕事を辞めて進学するか迷ってる。貯金と学費、生活費、就職を含めて比較して判断したい", "high"),
        ("強い負担・聞き役", [], "家族のことでかなりつらい。今は話を聞いてほしい", "mediumまたはhigh"),
        ("単純な計算", [], "3×4は？答えだけ教えて", "low"),
    ]
    router = LocalReasoningRouter()
    print("ローカルの推論分類だけを確認します。架空データのみ。DB・有料APIは使いません。", flush=True)
    for name, history, user, expected in cases:
        started = perf_counter()
        choice = router.classify(history, user)
        print(f"\n{name} / 目安={expected} / 秒数={perf_counter() - started:.2f}", flush=True)
        print("入力:", user)
        print(json.dumps(asdict(choice), ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
