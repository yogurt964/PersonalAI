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

## 現時点でまだ行わないこと

Version 0.16では、保存済みの長期記憶を一覧で確認できるようにする段階である。

まだ以下は行わない。

- 記憶の編集
- 記憶の削除
- 記憶の無効化
- 短期記憶、長期記憶、知識の完全な分離
- ベクトルDBの導入
- embedding検索
- 外部資料の知識化
- 記憶のユーザー確認フロー
- 期限切れ記憶の自動無効化
- MemoryManagerの本格的な独立クラス化

まずは既存の会話・記憶機能を壊さず、後から拡張しやすい保存構造にする。
