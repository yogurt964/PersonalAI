r"""Compare context variants locally; never save replies or alter the database.

Run from PowerShell: .\venv\Scripts\python.exe scripts\diagnose_conversation_context.py
All cases use the same question, policy, model, seed and thinking setting.
One sample per case is diagnostic evidence, not a quality benchmark.
"""
import argparse
import hashlib
import sqlite3
import sys
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai.memory_context import build_memory_context
from core.conversation_session import BOUNDARY, POLICY_PATH, bounded_history


def read_snapshot(path):
    # mode=ro also prevents accidentally creating a new database.
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT 20"
        ).fetchall()
        memories = db.execute(
            "SELECT * FROM memories WHERE is_active = 1 "
            "ORDER BY importance DESC, updated_at DESC, created_at DESC LIMIT 20"
        ).fetchall()
    history = bounded_history([dict(row) for row in reversed(rows)])
    return history, [SimpleNamespace(**dict(row)) for row in memories]


def cases(history, memories, policy, question):
    for name, turns, facts in (
        ("A: 通常の履歴＋長期記憶", history, memories),
        ("B: 長期記憶なし（履歴は同じ）", history, []),
        ("C: 過去のAI返答なし（ユーザー発言＋長期記憶）",
         [item for item in history if item["role"] == "user"], memories),
    ):
        system = "\n\n".join((
            BOUNDARY,
            build_memory_context(facts, memory_usage="detailed"),
            "【今回の返答に適用する会話方針】\n" + policy,
        ))
        yield name, [
            {"role": "system", "content": system},
            *turns,
            {"role": "user", "content": question},
        ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", default="俺が疲れた理由覚えてる？")
    args = parser.parse_args()
    history, memories = read_snapshot(ROOT / "data" / "personal_ai.db")
    policy = POLICY_PATH.read_text(encoding="utf-8")
    from ollama import Client
    client = Client(host="http://127.0.0.1:11434", timeout=180, trust_env=False)
    print("ローカル診断：DBは読み取り専用。診断の返答は保存しません。", flush=True)
    print(f"履歴={len(history)}件 / 長期記憶={len(memories)}件 / "
          f"方針SHA256={hashlib.sha256(policy.encode()).hexdigest()[:12]}")
    print(f"共通条件: think=True / seed=42 / memory=detailed / 質問={args.question}")
    for name, messages in cases(history, memories, policy, args.question):
        print(f"\n{name} / 入力文字数={sum(len(m['content']) for m in messages)}", flush=True)
        started = perf_counter()
        try:
            result = client.chat(model="qwen3:8b", messages=messages,
                                 think=True, options={"seed": 42})
        except Exception as error:
            print(f"実行失敗: {type(error).__name__}。Ollamaの状態を確認してください。")
            return 1
        print("返答:", result.message.content)
        print("秒数:", round(perf_counter() - started, 2),
              "/ 推論文字数:", len(getattr(result.message, "thinking", "") or ""),
              "/ 入力トークン数:", getattr(result, "prompt_eval_count", None), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
