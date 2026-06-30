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

## Version 0.22の確認回答処理

Version 0.22では、確認質問を出したあと、ユーザーの回答を受けてPreference保存を続行する最小実装を追加した。

PersonalAIは、現在のインスタンス内で1件だけ保留中のPreference確認を保持する。

```python
self.pending_preference_confirmation = None
```

保留情報はDBには保存しない。
アプリを終了すると消える一時状態である。
この処理は、ユーザーに影響する大きな操作ではなく、Preference記憶の保存に限定した確認回答処理である。

保留情報の例:

```python
{
    "type": "preference_confirmation",
    "original_text": "一番好きな食べ物は焼き肉です。覚えて",
    "reason": "primary_preference_update",
    "target": "焼き肉",
    "domain": "food",
    "question": "焼き肉を一番好きな食べ物として記憶しますか？それとも、好きな食べ物の1つとして追加しますか？",
}
```

追加した主な関数:

- `resolve_preference_confirmation_answer(answer_text, pending)`
- `save_resolved_preference_confirmation(pending, resolution, source="user", tags="preference")`

`resolve_preference_confirmation_answer()` は、ユーザーの回答を以下のactionへ分類する。

| action | 意味 |
|---|---|
| `save_primary` | 一番好きとして保存 |
| `save_addition` | 好きなものの1つとして追加 |
| `save_change` | 好みの変更として保存 |
| `cancel` | 保存しない |
| `ask_again` | 曖昧なので再確認 |

## 回答パターン

### save_primary

```text
一番好きとして記憶して
一番でいい
一番好き
最優先で記憶
```

`preference:food:primary` を使って、一番好きな食べ物として保存する。

### save_addition

```text
好きなものの1つとして追加して
追加で
追加して
両方好き
それも好き
```

通常のlikeとして `preference:food:<target>` に保存する。

### save_change

```text
変更して
更新して
今はそれで
今は焼き肉
カレーから焼き肉にして
```

新しい対象を現在の好みとして保存し、可能であれば古い対象を `food_past_like` として更新する。

### cancel

```text
記憶しないで
キャンセル
やっぱりいい
保存しないで
取り消して
```

Preference記憶は保存せず、pendingをクリアする。

### ask_again

```text
わからない
どっちでも
任せる
```

pendingを残し、もう一度確認する。

## 保存方針

`save_primary` では、以下の特別なmemory_keyを使う。

```text
preference:food:primary
```

これは「一番好きな食べ物」を表すkeyであり、通常の `preference:food:焼き肉` とは分けて扱う。

`save_addition` では、通常のlikeとして保存する。

`save_change` では、新しい対象を現在のlikeとして保存し、古い対象がある場合は、現在の好みとしては優先しない記憶へ更新する。

## まだ実装しないこと

Version 0.22では、以下はまだ実装しない。

- 完全な自然言語理解
- LLMによる高度な矛盾判定
- Preference以外の複雑な矛盾処理
- 長期的なpending状態のDB保存
- 複数の同時保留タスク管理
- 複雑な時系列Preference推論
- 自動忘却の実行
- 一括無効化
- Memoryの物理削除
- OpenAI接続
- ベクトルDB
- Embedding検索
- GUI
- Web / PDF / YouTube読み取り
