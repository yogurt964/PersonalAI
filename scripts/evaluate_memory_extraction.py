"""Synthetic extraction quality evaluation. Default preview makes no model calls."""
import argparse
import json
import sys
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.conversation_api import (
    PreflightError, estimate_reserve, make_client, usage_cost, validate_budget,
)
from core.conversation_memory import (
    ConversationSource, MemoryScope, ShortTermMemory, SourceBatch, StateNote, WorkingTurn,
)
from core.conversation_memory_extraction import build_extraction_messages, extract_memory_proposals


def evaluation_cases():
    definitions = [
        ("一時的な希望", [("user", "普段は質問してくれていいけど、今日は質問せずに聞いてて。")],
         "今日だけの希望をtemporary_preferenceに分ける。恒久的な質問嫌いにしない。"),
        ("否定と未決定", [("user", "週末の予定はまだ決めていない。旅行に行くとは言っていないよ。")],
         "予定は未決定として保持し、旅行へ行く予定を作らない。否定を落とさない。"),
        ("AIの未採用提案", [("assistant", "来月から毎朝走るのはどう？"),
                            ("user", "それはまだ決めない。今日は候補を出しただけだよ。")],
         "毎朝走ることをユーザーの決定や習慣として保存しない。具体的な案を残すならAI発言1とユーザー発言2の両方を引用する。"),
        ("好みの訂正", [("user", "以前は甘いコーヒーが好きだった。"),
                        ("user", "今は甘くないコーヒーのほうが好き。昔の好みと区別してね。")],
         "過去と現在の好みを区別する。既存キーcoffeeを更新候補に使い、逆の好みを併存させない。"),
        ("プロジェクトの正確な条件", [("user", "試作アプリの待ち時間は最大2.5秒、保存期間は14日。"
                                          "これは決定済み。自動削除を有効にするかはまだ未決定。")],
         "2.5秒・14日・決定済みという条件を保持する。自動削除は未決定と分離する。"),
        ("保存不要の相づち", [("user", "うん、ありがとう。")],
         "新しい事実や性格を作らず、原則candidatesを空にする。"),
    ]
    for index, (name, messages, criterion) in enumerate(definitions, 1):
        scope = MemoryScope("synthetic-evaluation", f"case-{index}")
        dataset = f"synthetic-case-{index}"
        sources = tuple(ConversationSource.from_row(dataset, n, role, content,
                        f"2026-10-22T09:0{n}:00+09:00")
                        for n, (role, content) in enumerate(messages, 1))
        batch = SourceBatch(scope, dataset, sources)
        memory = ShortTermMemory(scope, dataset)
        if index == 4:
            memory.apply(expected_version=0, evidence=batch, upserts=(
                StateNote("coffee", "user_fact", "甘いコーヒーが好き", (sources[0].ref,), ("飲み物",)),))
        turn = WorkingTurn(f"evaluation-{index}", sources[-1].content, memory.snapshot, batch)
        yield index, name, criterion, turn


def request_for(messages):
    return {"model": "gpt-6.1-sol", "instructions": messages[0]["content"], "input": messages[1:],
            "reasoning": {"effort": "low"}, "max_output_tokens": 2048,
            "store": False, "service_tier": "default"}


def make_plan(selected_cases=None):
    if selected_cases is not None:
        if (not selected_cases or any(type(i) is not int or i not in range(1, 7)
                                      for i in selected_cases)):
            raise PreflightError("ケースは1〜6から選んでください。")
    plan = []
    for index, name, criterion, turn in evaluation_cases():
        if selected_cases is not None and index not in selected_cases:
            continue
        request = request_for(build_extraction_messages(turn))
        plan.append({"case": index, "name": name, "criterion": criterion, "turn": turn,
                     "request": request, "reserve": estimate_reserve(request)})
    return plan


def run_evaluation(*, execute=False, engine="openai", approved_budget=None,
                   selected_cases=None, client_factory=None, local_factory=None):
    if engine not in ("openai", "ollama"):
        raise PreflightError("engineはopenaiまたはollamaです。")
    plan = make_plan(selected_cases)
    total = sum((item["reserve"] for item in plan), Decimal(0))
    print(f"架空データのみ / {len(plan)}ケース / engine={engine}", flush=True)
    print("DBの読み書き・記憶保存なし。形式と出典の検証を行い、意味の合否は人が確認します。", flush=True)
    if engine == "openai":
        print(f"全件の予算用見積額: ${total:.4f}（実請求額や厳密な請求上限ではありません）", flush=True)
    if not execute:
        print("事前表示のみ。APIキー・モデル・DBへアクセスしません。")
        for item in plan:
            print(f"\n{item['case']}: {item['name']}\n確認点: {item['criterion']}")
            for source in item["turn"].evidence.sources:
                print(f"  {source.ref.message_id} / {source.ref.role}: {source.content}")
        return 0
    budget = None
    if engine == "openai":
        budget = validate_budget(approved_budget)
        if total > budget:
            raise PreflightError("全件の見積額が承認予算を超えるため、APIを呼びません。")
    client, local = None, None
    spent = Decimal(0)
    try:
        if engine == "openai":
            client = (client_factory or make_client)()
        else:
            if local_factory is None:
                from core.conversation_session import LocalModel
                local_factory = LocalModel
            local = local_factory()
        for item in plan:
            print(f"\n=== {item['case']}: {item['name']} ===", flush=True)
            print("確認点:", item["criterion"], flush=True)
            for source in item["turn"].evidence.sources:
                print(f"原文 {source.ref.message_id} / {source.ref.role}: {source.content}", flush=True)
            stats = {}

            def model(messages):
                nonlocal spent
                if engine == "ollama":
                    raw = local(messages, think=True, json_mode=True)
                else:
                    request = request_for(messages)
                    reserve = estimate_reserve(request)
                    if spent + reserve > budget:
                        raise PreflightError("残り予算不足")
                    spent += reserve
                    response = client.responses.create(**request)
                    cost = usage_cost(response, request["model"])
                    if cost is not None:
                        spent += cost - reserve
                    stats["usage_estimate_usd"] = str(cost) if cost is not None else None
                    if getattr(response, "status", None) != "completed":
                        raise RuntimeError("incomplete response")
                    raw = getattr(response, "output_text", None)
                if isinstance(raw, str):
                    stats["raw_preview"] = raw[:2048]
                    stats["raw_preview_truncated"] = len(raw) > 2048
                return raw

            started = perf_counter()
            result = extract_memory_proposals(item["turn"], model=model)
            print(f"秒数: {perf_counter() - started:.2f} / 形式・出典検証: {result.status}", flush=True)
            if result.status != "proposed":
                if result.status == "invalid_response" and "raw_preview" in stats:
                    print("未検証のモデル出力（診断用・保存しません）:",
                          stats["raw_preview"], flush=True)
                    if stats["raw_preview_truncated"]:
                        print("診断表示は先頭2048文字まで。", flush=True)
                print("評価を停止。自動再試行や保存はしません。", flush=True)
                return 1
            print(json.dumps([asdict(p) for p in result.proposals], ensure_ascii=False, indent=2), flush=True)
            print("意味の評価: 未判定（原文・確認点と比較してください）", flush=True)
            if "usage_estimate_usd" in stats:
                print("今回の使用額見積:", stats["usage_estimate_usd"], flush=True)
        return 0
    finally:
        if client is not None:
            print(f"\n使用額見積（不明時は確保額を維持）: ${spent:.4f}", flush=True)
            print("実請求額はAPI側で確認してください。", flush=True)
            client.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=("openai", "ollama"), default="openai")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approved-budget-usd")
    parser.add_argument("--cases", nargs="+", type=int, choices=range(1, 7))
    args = parser.parse_args(argv)
    try:
        return run_evaluation(execute=args.execute, engine=args.engine,
                              approved_budget=args.approved_budget_usd, selected_cases=args.cases)
    except Exception as error:
        print(str(error) if isinstance(error, PreflightError)
              else f"評価を停止しました（{type(error).__name__}）。自動再試行はしません。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
