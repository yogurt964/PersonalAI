"""Run from the project root: python conversation_app.py."""
import os
from pathlib import Path

from core.conversation_session import ConversationSession


def main():
    os.chdir(Path(__file__).resolve().parent)
    from database.models import create_database
    Path("data").mkdir(exist_ok=True)
    create_database()
    ai = ConversationSession()
    mode = "auto"
    print("PersonalAI 会話版0.1 / 終了: /exit / 推論: /mode auto|fast|deep")
    print("記憶保存: /remember 内容 / 記憶一覧: /memories（会話履歴は既存DBに保存）")
    while True:
        try:
            user = input("あなた > ").strip()
            if not user:
                continue
            if user == "/exit":
                break
            if user.startswith("/mode "):
                candidate = user[6:].strip()
                if candidate not in ("auto", "fast", "deep"):
                    print("auto / fast / deepを指定してください。")
                    continue
                mode = candidate
                print(f"推論: {mode}")
                continue
            if user.startswith("/remember "):
                content = user[10:].strip()
                if not content or len(content) > 2000:
                    print("記憶は1〜2000文字にしてください。")
                    continue
                result = ai.store.remember(content)
                print("記憶を保存しました。" if result else "新しい記憶は保存されませんでした。")
                continue
            if user == "/memories":
                memories = ai.store.memories()
                for memory in memories:
                    print(f"{memory.id}: {memory.content}")
                if not memories:
                    print("有効な記憶はありません。")
                continue
            if user.startswith("/"):
                print("コマンド: /exit /mode auto|fast|deep /remember 内容 /memories")
                continue
            print("PersonalAI > " + ai.reply(user, mode=mode))
        except (EOFError, KeyboardInterrupt):
            print("\n終了します。")
            break
        except Exception as error:
            print(f"応答を完了できませんでした（{type(error).__name__}）。")
            print("Ollamaの起動とqwen3:8bの導入、設定ファイル、DBへの書き込み権限を確認してください。")


if __name__ == "__main__":
    main()
