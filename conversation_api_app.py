"""API conversation with explicitly approved legacy history and memories."""
import argparse
import os
from pathlib import Path

from core.conversation_api import SavedApiSession, PreflightError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-saved-context", action="store_true")
    parser.add_argument("--approved-budget-usd")
    args = parser.parse_args(argv)
    if not args.execute:
        print("API会話版の確認画面。API呼び出しやDBへのアクセスは行いません。")
        print("実行時に送るもの: 現在の入力、直近20件・16000文字以内の履歴、有効な長期記憶の上位20件以内。")
        print("会話方針と、この起動中に設定した好みも送ります。実行前に送信範囲と今回予算を承認してください。")
        print("会話の成功した入力・返答は既存DBへ保存し、/rememberで明示した長期記憶を保存します。")
        return 0
    try:
        ai = SavedApiSession(args.approved_budget_usd, allow_saved_context=args.allow_saved_context)
    except PreflightError as error:
        print(error)
        return 1
    os.chdir(Path(__file__).resolve().parent)
    if not Path("data/personal_ai.db").is_file():
        print("既存DBが見つかりません。DBは作成・初期化していません。")
        return 1
    print("PersonalAI API会話版0.1候補 / gpt-6.1-sol / 終了: /exit / 予算: /budget")
    print("保存済みの会話履歴・長期記憶と新しい会話をOpenAI APIへ送信します。")
    print("記憶保存: /remember 内容 / 一覧: /memories / 今回の好み: /preference 内容")
    print(f"今回予算: ${ai.budget:.2f}（見積額で制御。API側の厳密な請求上限ではありません）")
    try:
        while True:
            user = input("あなた > ").strip()
            if not user:
                continue
            if user == "/exit":
                break
            if user == "/budget":
                print(f"使用額の見積: ${ai.spent:.4f} / 残り: ${ai.remaining:.4f}")
                continue
            try:
                if user.startswith("/preference "):
                    ai.set_preference(user[len("/preference "):])
                    print("この起動中の好みを設定しました。次の発言からAPIにも渡します。")
                elif user.startswith("/remember "):
                    saved = ai.remember(user[len("/remember "):])
                    print("記憶を保存しました。" if saved else "新しい記憶は保存されませんでした。")
                elif user == "/memories":
                    memories = ai.store.memories()
                    for memory in memories:
                        print(f"{memory.id}: {memory.content}")
                    if not memories:
                        print("有効な記憶はありません。")
                elif user.startswith("/"):
                    print("コマンド: /exit /budget /remember 内容 /memories /preference 内容")
                else:
                    print("PersonalAI > " + ai.reply(user))
            except PreflightError as error:
                print(error)
                if user.startswith("/"):
                    continue
                break
            except Exception as error:
                print(f"処理を停止しました（{type(error).__name__}）。自動再試行はしません。")
                return 1
    except (EOFError, KeyboardInterrupt):
        print("\n終了します。")
    finally:
        ai.close()
        print(f"今回の使用額の見積: ${ai.spent:.4f}（実請求額はAPI側で確認してください）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
