"""Qwen（ローカルモデル）が、Stage 2のLLMフォールバック分類タスク
（core/capability_manager.pyの_ask_llm_for_capability_label、
core/web_search_intent.pyの_ask_llm_needs_web_search）で
実際にどれくらいの正解率を出せるかを実測するベンチマークです。

これはscripts/check_verXXXX.pyとは違い、実際のQwen（Ollama、ローカル・無料）を
呼び出します。チェックスクリプトの一覧（run_ver2_checks.py）には含めません
（自動チェックは実LLM呼び出しをしない方針のため）。

正解ラベルはこのファイル内で人手により定義しています。テストケースは、
既存のキーワードリスト（core/reading_keywords.py等）でも判定できてしまう
「わかりやすい」表現をあえて避け、キーワードでは拾えない言い換え表現を中心に
選んでいます（Stage 2のLLMフォールバックが実際に呼ばれる場面を想定するため）。

実行方法:
    venv\\Scripts\\python.exe -B scripts\\benchmark_capability_classification.py

Ollamaでqwen3:8bが起動している必要があります。テストケース数に応じて、
実行に数分かかる場合があります。
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


# (発言, 正解ラベル, キーワードだけでも判定できてしまうか)
# needs_keyword=Trueのケースは「わかりやすい」対照群として少数だけ含める。
# needs_keyword=Falseのケースが、Stage 2のLLMフォールバックが実際に問われる場面。
CAPABILITY_TEST_CASES = [
    # --- web_read_required ---
    ("さっき送ったリンクの内容、確認してもらえる？", "web_read_required", False),
    ("あそこに書いてあった話、詳しく知りたいんだけど", "web_read_required", False),
    ("http://example.com にある情報を教えて", "web_read_required", True),

    # --- youtube_read_required ---
    ("さっきシェアした動画、中身どんな感じか教えて", "youtube_read_required", False),
    ("あの配信で何を話してたか知りたい", "youtube_read_required", False),
    ("https://youtu.be/dQw4w9WgXcQ の内容を要約して", "youtube_read_required", True),

    # --- pdf_read_required ---
    ("添付した書類、中身を見てもらえる？", "pdf_read_required", False),
    ("この論文ファイルに何が書いてあるか知りたい", "pdf_read_required", False),
    ("report.pdf を読んで要約して", "pdf_read_required", True),

    # --- image_read_required ---
    ("さっきの写真に何が写ってるか知りたい", "image_read_required", False),
    ("このスクショの内容を説明して", "image_read_required", False),
    ("photo.png を解析して", "image_read_required", True),

    # --- file_read_required ---
    ("デスクトップに置いてあるメモの中身を確認して", "file_read_required", False),
    ("そのテキストファイル、何が書いてあるか教えて", "file_read_required", True),

    # --- document_creation_required ---
    ("会議の議事録を作ってほしい", "document_creation_required", False),
    ("見積書を作成してもらえる？", "document_creation_required", False),
    ("Wordで文書を作って", "document_creation_required", True),

    # --- pc_operation_required ---
    ("デスクトップのアイコンを整理しておいて", "pc_operation_required", False),
    ("このアプリを閉じておいて", "pc_operation_required", False),
    ("PowerShellで実行して", "pc_operation_required", True),

    # --- external_api_required ---
    ("天気予報のAPIから情報を取ってきて", "external_api_required", True),
    ("この外部サービスとAPI連携して", "external_api_required", True),

    # --- openai_required（高精度モデルが必要そうな専門的判断） ---
    ("この契約書の法的リスクを厳密に判定して", "openai_required", True),
    ("この症状について医学的に正確な診断をして", "openai_required", True),

    # --- none（通常会話、特別な能力は不要） ---
    ("今日は疲れました", "none", False),
    ("最近ハマってることある？", "none", False),
    ("ラーメンとうどん、どっちが好き？", "none", False),
    ("簡単な自己紹介をして", "none", False),
    ("週末におすすめの過ごし方ある？", "none", False),
]


# (発言, 正解: Web検索が必要か, キーワードだけでも判定できてしまうか)
WEB_SEARCH_TEST_CASES = [
    ("私の街で今開催中の変わったイベントある？", True, False),
    ("この会社の最新の株主総会はいつ開かれた？", True, False),
    ("今シーズンの流行色は何色？", True, False),
    ("今日の東京の天気を教えて", True, True),
    ("こんにちは、元気ですか", False, False),
    ("フェルマーの最終定理について解説して", False, False),
    ("あなたの名前は何ですか", False, False),
    ("1+1は何ですか", False, False),
]


def run_capability_benchmark():
    from core.capability_manager import CapabilityManager, _LLM_CAPABILITY_LABELS
    from ai.llm import ask_llm

    cm = CapabilityManager()

    print("=" * 70)
    print("capability_manager: Qwen分類ベンチマーク")
    print("=" * 70)

    results = []
    for text, expected, needs_keyword in CAPABILITY_TEST_CASES:
        start = time.time()
        labels = ", ".join(_LLM_CAPABILITY_LABELS)
        prompt = (
            "次のユーザーの発言を読んで、必要そうな能力を1つだけ選んでください。\n"
            f"選択肢: {labels}\n"
            "どれにも当てはまらない、または通常の会話で答えられる場合は none と答えてください。\n"
            "説明や記号は付けず、必ずこの中の1つの単語だけで答えてください。\n\n"
            f"発言: {text}"
        )
        raw_response = ask_llm([{"role": "user", "content": prompt}])
        actual = cm._parse_capability_label(raw_response)
        elapsed = time.time() - start
        correct = actual == expected
        results.append((text, expected, actual, correct, needs_keyword, raw_response))
        status = "OK" if correct else "NG"
        tag = "(keyword-obvious)" if needs_keyword else "(keyword-blind)"
        print(f"[{status}] {tag} expected={expected} actual={actual} ({elapsed:.1f}s) :: {text}")
        if not correct:
            print(f"       raw_response: {raw_response!r}")

    return results


def run_web_search_benchmark():
    from core.web_search_intent import _ask_llm_needs_web_search
    from ai.llm import ask_llm

    print()
    print("=" * 70)
    print("web_search_intent: Qwen yes/no判定ベンチマーク")
    print("=" * 70)

    results = []
    for text, expected, needs_keyword in WEB_SEARCH_TEST_CASES:
        start = time.time()
        actual = _ask_llm_needs_web_search(text, ask_llm)
        elapsed = time.time() - start
        correct = actual == expected
        results.append((text, expected, actual, correct, needs_keyword))
        status = "OK" if correct else "NG"
        tag = "(keyword-obvious)" if needs_keyword else "(keyword-blind)"
        print(f"[{status}] {tag} expected={expected} actual={actual} ({elapsed:.1f}s) :: {text}")

    return results


def summarize(label, results):
    total = len(results)
    correct = sum(1 for r in results if r[3])
    accuracy = (correct / total * 100) if total else 0.0

    blind_results = [r for r in results if not r[4]]
    blind_total = len(blind_results)
    blind_correct = sum(1 for r in blind_results if r[3])
    blind_accuracy = (blind_correct / blind_total * 100) if blind_total else 0.0

    print()
    print(f"--- {label} summary ---")
    print(f"Overall:        {correct}/{total} = {accuracy:.1f}%")
    print(f"Keyword-blind:  {blind_correct}/{blind_total} = {blind_accuracy:.1f}% "
          f"(the cases Stage 2's LLM fallback actually exists for)")

    if results:
        print("Misclassifications:")
        any_wrong = False
        for row in results:
            text, expected, actual, correct = row[0], row[1], row[2], row[3]
            if not correct:
                any_wrong = True
                print(f"  - expected={expected} actual={actual} :: {text}")
        if not any_wrong:
            print("  (none)")

    print()
    if blind_accuracy >= 95:
        print(f"[PASS] {label}: keyword-blind accuracy meets the 95% target.")
    else:
        print(f"[FAIL] {label}: keyword-blind accuracy is below the 95% target.")

    return blind_accuracy


def main():
    capability_results = run_capability_benchmark()
    web_search_results = run_web_search_benchmark()

    cap_accuracy = summarize("capability_manager classification", capability_results)
    search_accuracy = summarize("web_search_intent yes/no", web_search_results)

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    print(f"capability_manager keyword-blind accuracy: {cap_accuracy:.1f}%")
    print(f"web_search_intent keyword-blind accuracy:  {search_accuracy:.1f}%")


if __name__ == "__main__":
    main()
