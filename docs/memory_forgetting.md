# Memory Forgetting Dry-run

## 目的

Version 0.24では、自動忘却のdry-runを追加した。

これは記憶を自動で消す機能ではない。
現在は、忘却候補を提案するだけである。

## 基本方針

- 実際の削除は行わない
- 自動で `is_active=False` にしない
- ユーザー確認なしに記憶を忘れない
- 物理削除はしない
- dry-run結果だけを返す

将来的には、以下の順番で進める。

```text
候補表示 → ユーザー確認 → is_active=False
```

物理削除は原則として行わない。

## 追加したモジュール

`ai/memory_forgetting.py` を追加した。

主な関数:

- `analyze_forgetting_candidates(memories, max_candidates=20, min_score=50)`
- `get_forgetting_candidates(limit=100, max_candidates=20, min_score=50)`

`analyze_forgetting_candidates()` は、渡されたMemory一覧を分析し、忘却候補を返す。
DBは変更しない。

`get_forgetting_candidates()` は、DBからMemoryを読み取り、dry-run候補を返す。
この関数もDBを変更しない。

## 忘却候補になりやすい記憶

- 低重要度
- 低信頼度
- 一時的な記憶
- test / debug系の記憶
- 期限切れ
- 短すぎて意味が薄い記憶

## 忘却候補になりにくい記憶

- ユーザーの基本情報
- 好み
- project情報
- core方針
- 高重要度・高信頼度の記憶
- `memory_type=user_profile` の記憶
- `memory_key` に `core`、`preference`、`user`、`project` を含む記憶

## dry-run結果

候補は以下のようなdictで返す。

```python
{
    "memory_id": 12,
    "memory_key": "temporary:old_note",
    "content": "一時的な古いメモ",
    "score": 75,
    "reasons": ["low_importance", "low_confidence", "temporary_scope"],
    "recommended_action": "review_for_deactivation",
    "dry_run": True,
}
```

`dry_run=True` は、この結果が提案だけであり、実際の削除や無効化をしていないことを示す。

## まだ実装しないこと

Version 0.24では、以下はまだ実装しない。

- 自動削除
- 自動無効化
- 物理削除
- ユーザー確認UI
- 一括無効化
- LLMによる高度な忘却判断
- Vector DBやEmbedding検索を使った重複・類似判定

まずは安全な候補提案だけを行う。
