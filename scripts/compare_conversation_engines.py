"""Preview synthetic API comparisons by default; paid execution is explicit."""
import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.diagnose_conversation_context import adaptation_scenarios, minimal_messages

# Conservative short-context rate allowances, USD per million tokens. These
# exceed or match the official standard-rate pages reviewed on 2026-10-22.
# Refresh before future experiments; this is not an account billing limit.
# https://developers.openai.com/api/docs/pricing
# https://developers.openai.com/api/docs/models/gpt-6-luna
# https://developers.openai.com/api/docs/models/gpt-6.1-sol
RATE_ALLOWANCES = {
    "gpt-6-luna": (Decimal("0.20"), Decimal("1.00")),
    "gpt-6.1-sol": (Decimal("4.00"), Decimal("20.00")),
}
MAX_OUTPUT_TOKENS = 2048
MAX_RUN_BUDGET = Decimal("0.50")


class PreflightError(ValueError):
    """Only these local, fixed messages are safe to show verbatim."""


def make_plan(selected_cases=None):
    plan = []
    for index, (name, criterion, history, preferences, question) in enumerate(adaptation_scenarios(), 1):
        if selected_cases is not None and index not in selected_cases:
            continue
        messages = minimal_messages(history, preferences, question)
        # UTF-8 bytes plus generous framing allowance: an estimate, not a
        # tokenizer or a provider-side hard spend limit.
        input_allowance = (sum(len(m["content"].encode("utf-8")) for m in messages)
                           + 256 * len(messages) + 1024)
        for model, (input_rate, output_rate) in RATE_ALLOWANCES.items():
            reserve = (input_allowance * input_rate + MAX_OUTPUT_TOKENS * output_rate) / 1_000_000
            plan.append({
                "case": index, "name": name, "criterion": criterion,
                "reserve_usd": str(reserve),
                "request": {
                    "model": model,
                    "instructions": messages[0]["content"],
                    "input": messages[1:],
                    "reasoning": {"effort": "low"},
                    "max_output_tokens": MAX_OUTPUT_TOKENS,
                    "store": False,
                    "service_tier": "default",
                },
            })
    return plan


def make_client():
    # Reuse the existing key loader. Do not load .env or print credentials.
    from ai.openai_client import get_api_key
    from openai import OpenAI
    import httpx
    return OpenAI(
        api_key=get_api_key(), base_url="https://api.openai.com/v1",
        timeout=90, max_retries=0,
        http_client=httpx.Client(trust_env=False, follow_redirects=False),
    )


def run_comparison(*, execute=False, approved_budget=None, selected_cases=None, client_factory=None):
    plan = make_plan(selected_cases)
    total_reserve = sum((Decimal(item["reserve_usd"]) for item in plan), Decimal(0))
    print(f"架空データ限定 / {len(plan)}リクエスト / 予算用の見積額=${total_reserve:.4f}")
    print("実DBを読み書きせず、通常アプリの設定も変更しません。")
    if not execute:
        print("事前表示のみ。キー取得・API呼び出し・課金は行いません。")
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if approved_budget is None:
        raise PreflightError("実行には承認済みの今回予算を指定してください。")
    budget = Decimal(str(approved_budget))
    if not budget.is_finite() or not Decimal(0) < budget <= MAX_RUN_BUDGET:
        raise PreflightError("今回予算は0より大きく0.50 USD以下で指定してください。")
    if total_reserve > budget:
        raise PreflightError("実行前の見積額が今回予算を超えるため、APIを呼びません。")
    # Only construct a credential-bearing client after preflight has passed.
    client = (client_factory or make_client)()
    charged_reserve = Decimal(0)
    try:
        for item in plan:
            charged_reserve += Decimal(item["reserve_usd"])
            print(f"\n=== {item['name']} / {item['request']['model']} ===", flush=True)
            print("確認点:", item["criterion"], flush=True)
            started = perf_counter()
            response = client.responses.create(**item["request"])
            print("秒数:", round(perf_counter() - started, 2), flush=True)
            usage = getattr(response, "usage", None)
            print("入力トークン:", getattr(usage, "input_tokens", None),
                  "/ 出力トークン（推論含む）:", getattr(usage, "output_tokens", None), flush=True)
            text = getattr(response, "output_text", "")
            if getattr(response, "status", None) != "completed" or not isinstance(text, str) or not text.strip():
                raise RuntimeError("回答未完了または空のため停止。自動再試行はしません。")
            print("返答:", text.strip(), flush=True)
    finally:
        print(f"\n実行を試みたリクエストの予算用見積額: ${charged_reserve:.4f}", flush=True)
        print("見積額は実請求額ではありません。実請求はAPI側で確認してください。", flush=True)
        client.close()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", nargs="+", type=int, choices=range(1, 7))
    parser.add_argument("--execute", action="store_true", help="承認後のみ指定する有料実行")
    parser.add_argument("--approved-budget-usd", help="事前に承認した今回予算（最大0.50 USD）")
    args = parser.parse_args(argv)
    try:
        return run_comparison(execute=args.execute, approved_budget=args.approved_budget_usd,
                              selected_cases=args.cases)
    except Exception as error:
        # Exceptions from providers can contain request details; do not dump them.
        if isinstance(error, PreflightError):
            print(str(error))
        else:
            print(f"比較を停止しました（{type(error).__name__}）。自動再試行はしません。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
