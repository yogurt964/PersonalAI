# Memory Design

## 目的

Memoryは、PersonalAIが今後も役立つ情報を保存・参照するための仕組みである。

現在は、ユーザーの名前、好きな食べ物、好み、目標、現在取り組んでいること、プロジェクト情報などを長期記憶として保存する。

Version 0.13では、今後のMemory強化に備えて、保存する情報の構造を少し詳しくした。

## Version 0.13で追加した項目

`memories` テーブルに以下の列を追加した。

| 列名 | 役割 |
|---|---|
| `memory_key` | 同じ記憶を更新するための識別子 |
| `subcategory` | categoryをさらに細かく分けるための分類 |
| `scope` | 記憶の範囲。基本は `global` |
| `confidence` | 記憶の確からしさ。0〜100の整数 |
| `updated_at` | 最後に更新した日時 |
| `expires_at` | 期限がある記憶の期限 |
| `is_active` | 現在有効な記憶かどうか |

既存の `data/personal_ai.db` は削除せず、起動時の `create_database()` で足りない列だけを `ALTER TABLE` で追加する。
同じ列がすでに存在する場合は何もしないため、何度実行しても安全である。

## memory_keyの役割

`memory_key` は、同じ種類の記憶を安全に更新するためのキーである。

例:

- `user_name`: ユーザーの名前
- `favorite_food`: 好きな食べ物
- `main_project`: 現在の中心プロジェクト

`memory_key` がある場合は、`memory_type + scope + memory_key` が同じ記憶を更新する。
これにより、categoryだけで雑に上書きするよりも、どの記憶を更新したいのかが分かりやすくなる。

## categoryによる保存方針

すべてのcategoryを同じように上書きすると、必要な記憶が消える可能性がある。
そのため、Version 0.13ではcategoryを大きく2種類に分ける。

### 1つにまとまりやすいcategory

以下は、同じcategoryの中で基本的に1つへ更新する。

- `name`
- `favorite_food`
- `current_activity`

例:

```text
ユーザーの名前は太郎
```

このような情報は、最新の内容に更新される方が自然である。

### 複数持てるcategory

以下は、memory_keyがない場合、categoryだけでは上書きしない。

- `project`
- `preference`
- `goal`
- `personality`
- `other`
- `knowledge`

例:

```text
ユーザーはPersonalAIを開発している
ユーザーは英語学習にも取り組んでいる
```

どちらも `project` や `goal` に近いが、片方で片方を消してはいけない。
そのため、内容が違う場合は別々の記憶として保存する。
ただし、同じcontentがすでに存在する場合は重複保存しない。

## scopeの考え方

`scope` は記憶の使い道を分けるための範囲である。

- `global`: 全体で使う基本記憶
- `user`: ユーザー本人に関する記憶
- `project`: 特定プロジェクトに関する記憶
- `knowledge`: 知識として使う記憶

現時点では基本値として `global` を使う。
将来的に、プロジェクト単位の記憶や知識ベースを分けるときに活用する。

## Version 0.14のMemoryContext

Version 0.14では、保存済みの長期記憶をLLMへ渡す `MemoryContext` を強化した。

以前は、主に `memory.content` だけを箇条書きで渡していた。
現在は、記憶をカテゴリ別に整理し、重要度や確信度も一緒に渡す。

MemoryContextは以下のような見出しへ記憶を分類する。

- ユーザー情報
- 好み・方針
- プロジェクト
- 現在の作業
- 知識
- その他

分類には、主に `category` と `scope` を使う。

例:

| category / scope | 分類 |
|---|---|
| `name` | ユーザー情報 |
| `favorite_food` | ユーザー情報 |
| `preference` | 好み・方針 |
| `personality` | 好み・方針 |
| `goal` | 好み・方針 |
| `project` | プロジェクト |
| `current_activity` | 現在の作業 |
| `knowledge` | 知識 |
| `scope=user` | ユーザー情報 |
| `scope=project` | プロジェクト |
| `scope=knowledge` | 知識 |

LLMへ渡すときは、各記憶に `importance` と `confidence` を表示する。
`scope` が `global` 以外の場合は、どの範囲の記憶かも表示する。
`memory_key` がある場合は、デバッグしやすいようにkeyも表示する。

例:

```text
【ユーザー情報】
- ユーザーの名前は巧弥。重要度:10 / 確信度:90 / key:user_name
```

`is_active` が `False` の記憶は、LLMへ渡さない。
ただし、古いDBやテスト用オブジェクトで `is_active` が存在しない場合や `None` の場合は、有効な記憶として扱う。

`confidence` が50未満の記憶は、完全には除外しない。
ただし、`低確信` と表示して、LLMが確定情報として扱いすぎないようにする。

MemoryContextが長くなりすぎると回答品質が下がるため、現在は全体で最大20件、各分類で最大5件程度に制限する。

## Version 0.15のMemoryContext確認

Version 0.15では、現在DBに保存されている長期記憶が、実際にどのようなMemoryContextとしてLLMへ渡されるかを確認しやすくした。

確認用スクリプトとして `scripts/show_memory_context.py` を追加した。
このスクリプトは、`get_memories()` で現在DBの長期記憶を取得し、`build_memory_context(memories)` の結果を表示する。

基本的な使い方:

```powershell
venv\Scripts\python.exe -B scripts\show_memory_context.py
```

件数や分類を絞る場合:

```powershell
venv\Scripts\python.exe -B scripts\show_memory_context.py --limit 10
venv\Scripts\python.exe -B scripts\show_memory_context.py --category project
venv\Scripts\python.exe -B scripts\show_memory_context.py --scope user
```

このスクリプトは読み取り専用であり、既存記憶を削除・更新しない。
MemoryContextの表示内容を確認するためのデバッグ補助である。

また、`scripts/check_ver015.py` を追加し、以下を確認できるようにした。

- `build_memory_context` と `get_memories` のimport
- `show_memory_context.py` の存在
- 現在DBの記憶からMemoryContext文字列を作れること
- `show_memory_context.py --limit 5` が実行できること

## Version 0.16のMemory一覧表示

Version 0.16では、現在DBに保存されている長期記憶そのものを、人間が一覧で確認しやすくするために `scripts/list_memories.py` を追加した。

このスクリプトは、記憶を1件ごとのブロック形式で表示する。
表示する主な項目は以下である。

- `id`
- `content`
- `memory_type`
- `category`
- `subcategory`
- `scope`
- `memory_key`
- `importance`
- `confidence`
- `is_active`
- `source`
- `tags`
- `created_at`
- `updated_at`
- `expires_at`

基本的な使い方:

```powershell
venv\Scripts\python.exe -B scripts\list_memories.py
```

絞り込みの例:

```powershell
venv\Scripts\python.exe -B scripts\list_memories.py --limit 20
venv\Scripts\python.exe -B scripts\list_memories.py --category project
venv\Scripts\python.exe -B scripts\list_memories.py --scope user
venv\Scripts\python.exe -B scripts\list_memories.py --include-inactive
venv\Scripts\python.exe -B scripts\list_memories.py --search PersonalAI
```

既定では有効な記憶だけを表示する。
`--include-inactive` を指定した場合だけ、無効な記憶も表示する。
`--search` は、`content`、`category`、`subcategory`、`scope`、`memory_key`、`source`、`tags` を対象にした簡易検索である。

このスクリプトは読み取り専用であり、記憶の削除、更新、無効化、DBリセットは行わない。
記憶の編集・削除・無効化はまだ未実装である。

確認用スクリプトとして `scripts/check_ver016.py` も追加した。
これは `list_memories.py` の存在、基本実行、category絞り込み、inactive表示、search実行を確認する。

## Version 0.17の手動無効化・復元

Version 0.17では、間違った記憶や古い記憶を物理削除せず、手動で無効化・復元できるようにした。

無効化は `is_active=False` にすることで行う。
復元は `is_active=True` に戻すことで行う。
Memoryの `content`、`category`、`memory_key` などは変更しない。

追加した主な関数:

- `get_memory_by_id(memory_id, include_inactive=True)`
- `set_memory_active(memory_id, is_active)`

手動操作用スクリプトとして `scripts/manage_memory_status.py` を追加した。
このスクリプトは、対象Memoryの内容を表示してから、状態変更のpreviewまたはapplyを行う。

無効化のdry-run:

```powershell
venv\Scripts\python.exe -B scripts\manage_memory_status.py --id 1 --deactivate
```

無効化を実際に適用:

```powershell
venv\Scripts\python.exe -B scripts\manage_memory_status.py --id 1 --deactivate --apply
```

復元のdry-run:

```powershell
venv\Scripts\python.exe -B scripts\manage_memory_status.py --id 1 --restore
```

復元を実際に適用:

```powershell
venv\Scripts\python.exe -B scripts\manage_memory_status.py --id 1 --restore --apply
```

安全性のため、`--apply` がない場合は必ずdry-runになり、DBは変更しない。
実際にDBを書き換えるには `--apply` が必要である。

無効化済みのMemoryは、以下で確認できる。

```powershell
venv\Scripts\python.exe -B scripts\list_memories.py --include-inactive
```

この機能は読み取りと状態変更だけを扱う。
Memoryの物理削除、内容編集、一括無効化、自動無効化はまだ未実装である。

確認用スクリプトとして `scripts/check_ver017.py` も追加した。
このスクリプトは `ver017_test` のテストMemoryだけを作成し、dry-run、無効化apply、復元applyを確認したあと、テストデータだけを削除する。

## Version 0.18の無効化MemoryとMemoryContext確認

Version 0.18では、`is_active=False` のMemoryが本当にMemoryContextから除外されることを確認するスクリプトを追加した。

確認用スクリプトは `scripts/check_ver018.py` である。

このスクリプトでは、テスト用Memoryを作成し、以下を確認する。

- active状態では `get_memories(active_only=True)` で取得される
- active状態では `build_memory_context(memories)` に表示される
- `set_memory_active(test_id, False)` 後は `is_active=False` になる
- 無効化後は `get_memories(active_only=True)` に出ない
- 無効化後はMemoryContextにも出ない
- inactiveなMemoryを直接 `build_memory_context([memory])` に渡しても出ない
- `set_memory_active(test_id, True)` 後はMemoryContextに戻る

これにより、Ver0.17で追加した手動無効化・復元が、Ver0.14のMemoryContextに正しく反映されることを確認できる。

テストデータは `source="ver018_test"`、`tags="ver018_test"`、`memory_key="ver018_memory_context_active_test"` のものだけを対象にクリーンアップする。
ユーザーの既存記憶には触れない。

## Version 0.19のPreference記憶

Version 0.19では、好き嫌いを扱うPreference記憶の最小実装を追加した。

追加した補助モジュールは `ai/preference_memory.py` である。
このモジュールは、明確な日本語パターンから以下を抽出する。

- `like`: 好き
- `not_like`: 好きではない / 好きじゃない
- `dislike`: 嫌い

例:

```text
ラーメンが好きです。覚えて
寿司が好きです。覚えて
ラーメンは好きじゃないです。覚えて
寿司は嫌いです。覚えて
```

Preference記憶では、以下の形式の `memory_key` を使う。

```text
preference:food:<target>
```

このため、`ラーメンが好き` と `ラーメンは好きじゃない` は同じ `preference:food:ラーメン` を更新する。
一方で、`ラーメンが好き` と `寿司が好き` は別々のkeyになるため、両方保持できる。

PersonalAI本体では、ユーザー入力に「覚えて」が含まれ、Preferenceが抽出できた場合、Preference記憶を先に保存する。
これにより、好き嫌いの単純文が汎用LLM抽出と重複保存されにくくなる。

記憶確認については、毎回確認しすぎない方針とする。
好きなものが増えたように見える場合は、基本的に追加記憶として扱う。
ただし、「一番好き」「今は」「前は」など更新意図がありそうな場合や、同じ対象に対して好き嫌いが矛盾する場合は、将来的に確認質問を行う。

詳細は `docs/preference_memory.md` にまとめる。

## Version 0.20のPreference確認質問

Version 0.20では、Preference記憶を保存する前に、確認質問が必要かを判断する補助機能を追加した。

追加したモジュールは `ai/preference_confirmation.py` である。

確認しない例:

- `焼き肉が好きです。覚えて`: 好きなものの単純追加
- `ラーメンは好きじゃないです。覚えて`: 明確なnot_like
- `寿司は嫌いです。覚えて`: 明確なdislike

確認候補にする例:

- `一番好きな食べ物は焼き肉です。覚えて`
- `前はカレーが好きだったけど、今は焼き肉が好きです。覚えて`
- `好きな食べ物をカレーから焼き肉に変更して。覚えて`

確認が必要な場合は、Preferenceを保存せず、ユーザーに固定の確認質問を返す。
確認不要の場合は、Ver0.19のPreference保存をそのまま行う。

確認しすぎると会話が重くなるため、毎回質問しない。
将来的には、`confirmation_frequency` や `memory_confirmation_style` をユーザー設定として記憶し、確認頻度を調整できるようにする。

## Version 0.22のPreference確認回答

Version 0.22では、確認質問を出したあと、ユーザーの回答を受けてPreference保存を続行する最小実装を追加した。

PersonalAIは、現在のインスタンス内で1件だけ `pending_preference_confirmation` を保持する。
このpendingはDBには保存しない一時状態であり、アプリを終了すると消える。

確認回答では、以下のactionを扱う。

- `save_primary`: 一番好きとして保存
- `save_addition`: 好きなものの1つとして追加
- `save_change`: 好みの変更として保存
- `cancel`: 保存しない
- `ask_again`: 曖昧なため再確認する

一番好きな食べ物は、通常の `preference:food:<target>` とは分けて、特別な `memory_key` として `preference:food:primary` に保存する。
これは完全な自然言語理解ではなく、明確な返答パターンを扱うための小さな実装である。
ユーザーに影響する大きな操作ではなく、Preference記憶の保存に限定した確認回答処理として扱う。

## Version 0.24の自動忘却dry-run

Version 0.24では、自動忘却の土台としてdry-runを追加した。

これは記憶を自動で削除する機能ではない。
低重要度、低信頼度、一時記憶、test/debug系、期限切れ記憶などを忘却候補として提案するだけである。

高重要度のユーザー情報、Preference、project情報、core方針、安全方針などは候補にしにくくする。

現時点では以下を行わない。

- Memoryの物理削除
- 自動で `is_active=False` にすること
- ユーザー確認なしに記憶を忘れること
- 一括無効化

将来的には、以下の流れを想定する。

```text
候補表示 → ユーザー確認 → is_active=False
```

詳細は `docs/memory_forgetting.md` にまとめる。

## Version 1.1のMemory利用方針

Version 1.1では、Memoryを「使う / 使わない」の二択ではなく、会話内容に応じて使い方の強さを分ける。

Memory利用方針は以下の3段階である。

| memory_usage | 使い方 |
|---|---|
| `minimal` | 通常会話ではMemory情報を控えめに使う |
| `normal` | 関連が強いMemoryだけ使う |
| `detailed` | ユーザーが明示的に記憶参照を求めた場合は詳しく使う |

基本方針:

- 通常会話ではMemory情報を控えめに使う
- ユーザーが明示的に記憶参照を求めた場合は詳しく使う
- Preference情報は、会話と直接関係がある場合だけ使う
- 好きな食べ物などのPreference情報を、単なる挨拶、応援、雑談に毎回混ぜない
- 関係の薄いMemoryを無理に会話へ混ぜない

`minimal` の例:

```text
こんにちは
今日は疲れました
短く応援してください
```

この場合、MemoryContextには通常会話向けの注意を入れる。
Preference情報は原則として前に出さず、挨拶や応援として自然に返答できることを優先する。

`normal` の例:

```text
おすすめを教えて
私に合いそうなものを提案して
前の方針を踏まえて考えて
```

この場合、関連が強いMemoryだけを使う。
食事、好み、選択に直接関係する場合はPreference情報を使ってよいが、関係が薄い場合は使わない。

`detailed` の例:

```text
私について覚えていることを教えて
何を覚えてる？
Memoryを確認したい
```

この場合は、ユーザーが記憶参照を求めているため、保存済みMemoryを分かる範囲で整理して答える。
ただし、記憶にないことは推測で作らない。

判定は `ai/memory_usage_policy.py` の `decide_memory_usage()` で行う。
MemoryContext生成時には、`build_memory_context(memories, memory_usage="normal")` のように利用方針を渡す。
既存呼び出しが壊れないよう、既定値は `normal` とする。

## 現時点でまだ行わないこと

Version 0.20では、明確なPreference更新候補に対する確認質問の最小実装を追加する段階である。

まだ以下は行わない。

- 記憶の編集
- 記憶の削除
- 一括無効化
- 自動無効化
- Preference記憶の本格的な自然言語理解
- 好き嫌い矛盾処理の本格実装
- 短期記憶、長期記憶、知識の完全な分離
- ベクトルDBの導入
- embedding検索
- 外部資料の知識化
- 記憶のユーザー確認フロー
- 期限切れ記憶の自動無効化
- MemoryManagerの本格的な独立クラス化

まずは既存の会話・記憶機能を壊さず、後から拡張しやすい保存構造にする。
