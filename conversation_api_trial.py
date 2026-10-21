"""Ephemeral API conversation trial; only start after budget/data approval."""
import argparse

from core.conversation_api import ApiTrialSession, PreflightError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approved-budget-usd")
    args = parser.parse_args(argv)
    if not args.execute:
        print("API会話の試用。今回予算と、新しく入力する会話のAPI送信を承認後に実行してください。")
        print("送信対象は今回入力した発言・試用中の好み・直近の試用会話のみ。既存DBは利用しません。")
        return 0
    try:
        ai = ApiTrialSession(args.approved_budget_usd)
    except PreflightError as error:
        print(error)
        return 1
    print("PersonalAI API試用 / gpt-6.1-sol / 終了: /exit / 予算: /budget / 好み: /preference 内容")
    print("入力した会話と好みをOpenAI APIに送信します。試用会話は保存せず、終了後に消えます。")
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
            if user.startswith("/preference "):
                try:
                    ai.set_preference(user[len("/preference "):])
                    print("この試用中の好みを設定しました。次の発言からAPIにも渡します。")
                except PreflightError as error:
                    print(error)
                continue
            if user.startswith("/"):
                print("コマンド: /exit /budget /preference 内容")
                continue
            try:
                print("PersonalAI > " + ai.reply(user))
            except PreflightError as error:
                print(error)
                break
            except Exception as error:
                print(f"応答を停止しました（{type(error).__name__}）。自動再試行はしません。")
                return 1
    except (EOFError, KeyboardInterrupt):
        print("\n終了します。")
    finally:
        ai.close()
        print(f"この試用の使用額の見積: ${ai.spent:.4f}（実請求額はAPI側で確認してください）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
