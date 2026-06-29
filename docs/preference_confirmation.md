# Preference Confirmation

## 目的

Preference Confirmationは、Preference記憶を保存する前に、ユーザーへ確認質問すべきかを判断するための補助機能である。

Version 0.20では、完全な自然言語理解ではなく、明確なパターンに対する最小実装として追加した。

## 追加したモジュール

`ai/preference_confirmation.py` に以下を追加した。

```python
analyze_preference_confirmation(
    text: str,
    existing_memories=None,
    confirmation_frequency: str = "normal",
) -> dict
```

戻り値の例:

```python
{
    "should_ask": True,
    "reason": "primary_preference_update",
    "question": "焼き肉を一番好きな食べ物として記憶しますか？それとも、好きな食べ物の1つとして追加しますか？",
    "default_action": "ask_before_save",
}
```

確認不要の場合:

```python
{
    "should_ask": False,
    "reason": "simple_addition",
    "question": "",
    "default_action": "save_without_question",
}
```

## 確認しないケース

### 好きなものの単純追加

入力例:

```text
焼き肉が好きです。覚えて
```

期待:

```text
should_ask=False
reason=simple_addition
```

好きなものが増えたように見える場合は、基本的に追加記憶として扱う。
毎回確認すると会話が重くなるため、単純な追加では確認しない。

### 明確なnot_like / dislike

入力例:

```text
ラーメンは好きじゃないです。覚えて
寿司は嫌いです。覚えて
```

期待:

```text
should_ask=False
reason=explicit_negative_preference
```

明確に好きではない、嫌いと言っている場合は曖昧ではないため、確認せず更新してよい。

## 確認してよいケース

### 一番好き

入力例:

```text
一番好きな食べ物は焼き肉です。覚えて
```

期待:

```text
should_ask=True
reason=primary_preference_update
```

これは、単なる好きなものの追加なのか、一番好きなものの更新なのかが曖昧である。

質問例:

```text
焼き肉を一番好きな食べ物として記憶しますか？
それとも、好きな食べ物の1つとして追加しますか？
```

### 今は / 前は

入力例:

```text
前はカレーが好きだったけど、今は焼き肉が好きです。覚えて
```

期待:

```text
should_ask=True
reason=temporal_preference_change
```

これは時間による好みの変化を含む可能性がある。

質問例:

```text
カレーは古い好みとして扱い、今は焼き肉が好きとして更新しますか？
```

### 変更

入力例:

```text
好きな食べ物をカレーから焼き肉に変更して。覚えて
```

期待:

```text
should_ask=True
reason=preference_change_request
```

これは変更意図があるため、既存の好き記憶をどう扱うか確認する。

質問例:

```text
好きな食べ物をカレーから焼き肉に変更し、カレーの好き記憶を使わないようにしますか？
```

## confirmation_frequency

将来的に、ユーザーとの会話から確認頻度を調整できるようにする。

想定値:

```text
low
normal
high
```

Version 0.20の最小方針:

- `low`: よほど明確に曖昧な場合だけ確認
- `normal`: 一番好き / 今は / 前は / 変更 で確認
- `high`: Preference更新っぽい場合はやや積極的に確認

現時点では `normal` を中心に扱う。

## PersonalAI本体での扱い

PersonalAI本体では、Preference保存前に `analyze_preference_confirmation()` を呼ぶ。

`should_ask=True` の場合は、Preferenceを保存せず、固定の確認質問を返す。

`should_ask=False` の場合は、Ver0.19と同じようにPreference記憶を保存する。

これにより、以下は今まで通り保存する。

```text
ラーメンが好きです。覚えて
寿司が好きです。覚えて
ラーメンは好きじゃないです。覚えて
寿司は嫌いです。覚えて
```

一方で、以下は保存前に確認質問を返す。

```text
一番好きな食べ物は焼き肉です。覚えて
前はカレーが好きだったけど、今は焼き肉が好きです。覚えて
好きな食べ物をカレーから焼き肉に変更して。覚えて
```

## まだ実装しないこと

Version 0.20では、以下はまだ実装しない。

- 完全な自然言語理解
- LLMによる高度な矛盾判定
- Preference以外の複雑な矛盾処理
- 自動忘却の実行
- 一括無効化
- Memoryの物理削除
- OpenAI接続
- ベクトルDB
- Embedding検索
- GUI
- Web / PDF / YouTube読み取り
