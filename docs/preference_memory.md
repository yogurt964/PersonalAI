# Preference Memory

## 目的

Preference Memoryは、ユーザーの好き嫌いを扱うための長期記憶である。

Version 0.19では、完全な自然言語理解ではなく、明確な日本語パターンに対する最小実装を追加した。

対象にする例:

```text
ラーメンが好きです。覚えて
寿司が好きです。覚えて
ラーメンは好きじゃないです。覚えて
寿司は嫌いです。覚えて
```

## 最小実装の範囲

`ai/preference_memory.py` に以下を追加した。

- `extract_preference_memories(text)`
- `save_preference_memories(text, source="user", tags="preference")`

`extract_preference_memories()` は、明確な好き嫌い表現からPreference候補を作る。

戻り値の主な項目:

- `target`: 好き嫌いの対象
- `domain`: 現時点では基本的に `food`
- `polarity`: `like` / `not_like` / `dislike`
- `content`: Memoryとして保存する文章
- `memory_key`: 同じ対象の現在状態を更新するためのキー
- `category`: `preference`
- `subcategory`: `food_like` / `food_not_like` / `food_dislike`
- `scope`: `user`
- `importance`: 9
- `confidence`: 90

## polarity

Preferenceの状態は、現時点では以下の3つに分ける。

| polarity | 意味 |
|---|---|
| `like` | 好き |
| `not_like` | 好きではない / 好きじゃない |
| `dislike` | 嫌い |

例:

```text
ラーメンが好き → like
ラーメンは好きじゃない → not_like
寿司は嫌い → dislike
```

## memory_key

同じ対象の現在状態を更新できるように、Preference Memoryは以下の形式の `memory_key` を使う。

```text
preference:food:<target>
```

例:

```text
preference:food:ラーメン
preference:food:寿司
```

この設計により、以下のように扱える。

```text
ラーメンが好き
ラーメンは好きじゃない
```

この場合、どちらも `preference:food:ラーメン` を使うため、現在状態が `not_like` に更新される。

一方で、以下は別々の対象である。

```text
ラーメンが好き
寿司が好き
```

この場合は、`preference:food:ラーメン` と `preference:food:寿司` が別キーなので、両方保存される。

## 保存方針

`save_preference_memories()` は、抽出したPreferenceを `save_memory()` で保存する。

保存時の主な値:

```text
memory_type: user_profile
category: preference
scope: user
importance: 9
confidence: 90
```

PersonalAI本体では、ユーザー入力に「覚えて」が含まれ、かつPreferenceが抽出できた場合、Preference記憶として先に保存する。
この場合、汎用LLM記憶抽出には渡さず、好き嫌いの単純文が二重保存されにくいようにする。

## 記憶確認をしすぎない方針

好きなものが増えたように見える場合は、原則として追加記憶にする。

例:

```text
カレーが好きです。覚えて
焼き肉が好きです。覚えて
```

これは基本的に、以下のように扱う。

```text
カレーも焼き肉も好き
```

毎回「追加ですか、変更ですか」と聞くと使いにくいため、確認しすぎない。

## Version 0.20の確認質問判定

Version 0.20では、Preference保存前に確認質問が必要かを判定する `ai/preference_confirmation.py` を追加した。

基本方針は以下である。

- 好きなものの単純追加では確認しない
- 明確な「好きじゃない」「嫌い」は確認せず更新してよい
- 「一番好き」「今は / 前は」「変更」は確認候補にする

PersonalAI本体では、Preference保存前に `analyze_preference_confirmation()` を呼ぶ。
`should_ask=True` の場合は、Preferenceを保存せず、固定の確認質問を返す。
`should_ask=False` の場合は、Ver0.19と同じようにPreference記憶を保存する。

詳細は `docs/preference_confirmation.md` にまとめる。

## Version 0.22の確認回答後保存

Version 0.22では、確認質問後のユーザー回答を扱えるようにした。

現在は、PersonalAIインスタンス内に1件だけ `pending_preference_confirmation` を保持する。
pendingはDBには保存せず、アプリを終了すると消える。

確認回答では、以下を最小限のルールで判定する。

- `save_primary`: 一番好きとして保存
- `save_addition`: 好きなものの1つとして追加
- `save_change`: 好みの変更として保存
- `cancel`: 保存しない
- `ask_again`: 曖昧な回答として再確認する

一番好きな食べ物は `preference:food:primary` に保存する。
通常の好きな食べ物は、これまで通り `preference:food:<target>` を使う。

この処理は完全な自然言語理解ではなく、明確な確認回答パターンだけを扱う。
Web、OpenAI、Vector DB、Embedding検索などは使わない。

## 確認してもよいケース

以下の場合は、追加確認してよい。

- 「一番好き」など、単一の好みを更新している可能性がある
- 「今は」「前は」など、時期の変化がある
- 同じ対象に対して好き/嫌いが矛盾している
- 健康、安全、仕事方針など重要度が高い記憶
- ユーザーが記憶確認を多めにしてほしいと言っている

確認例:

```text
焼き肉も好きな食べ物として追加しますか？
それとも、好きな食べ物をカレーから焼き肉に変更しますか？
```

## 将来の拡張予定

Version 0.19では、基本的に食べ物を対象にした最小実装である。

今後は以下を検討する。

- food以外のdomain
- 「一番好き」「最近好き」「昔は好きだった」などの時系列
- 複数候補を含む1文の抽出
- Preference矛盾の自動検出
- 確認頻度のユーザー設定
- Preference専用のContext表示

将来的には、以下のようなユーザー設定として記憶確認頻度を調整できるようにする。

```text
confirmation_frequency: low / normal / high
memory_confirmation_style: ask_when_ambiguous / ask_often / rarely_ask
```

## まだ実装しないこと

Version 0.19では、以下はまだ実装しない。

- 完全な自然言語理解
- 複雑なPreference抽出
- 自動忘却の本格実行
- 一括無効化
- Memoryの物理削除
- OpenAI接続
- ベクトルDB
- Embedding検索
- GUI
- Web / PDF / YouTube読み取り
