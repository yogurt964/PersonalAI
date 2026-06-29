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

## 現時点でまだ行わないこと

Version 0.13では、Memoryの土台を強化するだけである。

まだ以下は行わない。

- 短期記憶、長期記憶、知識の完全な分離
- ベクトルDBの導入
- embedding検索
- 記憶のユーザー確認フロー
- 期限切れ記憶の自動無効化
- MemoryManagerの本格的な独立クラス化

まずは既存の会話・記憶機能を壊さず、後から拡張しやすい保存構造にする。
