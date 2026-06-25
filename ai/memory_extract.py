import json
from ollama import chat


def extract_memories(user_input):
    prompt = f"""
以下のユーザー発言から、今後も役立つ長期記憶を複数抽出してください。

保存すべき例:
- 名前
- 好き嫌い
- 目標
- 現在取り組んでいること
- 性格や希望
- 継続中のプロジェクト

保存しない例:
- あいさつ
- 一時的な雑談
- その場限りの質問
- ユーザーが質問しているだけの内容
- 「〜を尋ねています」「〜について聞いています」のような発言内容の説明

重要:
- 「私」はユーザーを指します。
- content は必ず「ユーザーは〜」「ユーザーの〜」の形にしてください。
- content は「ユーザーについて長期的に覚えるべき事実」だけにしてください。
- 質問内容の要約は保存しないでください。
- 文章は短く、自然で完全な日本語にしてください。
- 未完成な文を保存しないでください。
- 好きな食べ物なら「ユーザーの好きな食べ物は〇〇」の形にしてください。
- 必ずJSON配列だけで返してください。
- 保存する内容がない場合は [] を返してください。

category は記憶の種類を英語で表してください。

category例:
- name
- favorite_food
- current_activity
- goal
- preference
- project
- personality
- other

形式:
[
  {{
    "content": "ユーザーの名前は巧弥で、読み方はたくや",
    "memory_type": "user_profile",
    "category": "name",
    "importance": 10,
    "source": "user",
    "tags": "名前"
  }},
  {{
    "content": "ユーザーの好きな食べ物はカレー",
    "memory_type": "user_profile",
    "category": "favorite_food",
    "importance": 8,
    "source": "user",
    "tags": "好み,食事"
  }}
]

ユーザー発言:
{user_input}
"""

    response = chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    text = response.message.content.strip()

    try:
        data = json.loads(text)

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []