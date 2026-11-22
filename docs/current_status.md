# Current Status

最終更新: 2026-11-22（基準 commit `22d89b5`、ブランチ `feature/conversation-v0.1`）
このファイルは「今の状態」だけを書く。上書き更新し、履歴は `docs/changelog.md` に残す。100行以内。

## 現在の開発主題

会話版Ver0.1（`docs/conversation_v01.md`）と、その記憶・思考の基盤（`docs/memory_thinking_architecture.md`）。
既存のVer2.75（`app.py`）とは別の入口で開発しており、`app.py` の動作は変えていない。

| 入口 | 内容 |
|---|---|
| `conversation_app.py` | ローカルQwen（Ollama）版。推論切替、既存DBの履歴・記憶を使用 |
| `conversation_api_trial.py` | API会話の試用。DB・長期記憶は使わない |
| `conversation_api_app.py` | 保存済み会話・長期記憶を使うAPI版。`--mode auto` の推論切替、`--enable-short-memory` の短期記憶 |

## 確定事項（資料・コードで確認済み）

- API会話エンジンは Sol を暫定候補とする（自然さの評価は暫定）
- 保存API版で `/remember` → 終了・再起動後の参照を実機確認済み
- API版の推論切替は初期値 `fast`。`auto` はローカル分類を使い、失敗したら medium。標準設定にはまだしていない
- 短期記憶は `/extract-memory` → `/accept-memory` による明示的な採用のみ。別DB `data/conversation_memory.sqlite3` に保存し、再起動後に復元する
- オフライン検証は fake / 一時DB で計100件が通過（`docs/memory_thinking_architecture.md` の記録による）
- OpenAI利用は起動ごとの承認予算で運用中。月間上限の累計管理は未実装
- クラウドセッションから feature ブランチへ push できることを確認済み（`docs/cloud_development.md`）

## 未解決・未検証

- 実モデルでの会話品質・自然さ、自動推論切替の分類精度、短期記憶の要点を正しく使えているか（すべて実機評価待ち）
- 通常会話からの自動採用・自動繰り上げ・自動忘却は未接続（自動保存と明示保存の併存は目標として合意済み）
- 記憶設計の未決事項5件（`docs/memory_thinking_architecture.md` の「8. すり合わせが必要な判断」）
- 意味検索、月間予算管理、PC移行時のDB再紐付け、複数ユーザー分離は未実装
- クラウドではWindowsパス前提の5本の check がNGになる（ローカルでは通る想定だが、今回は未確認。`docs/cloud_development.md`）
- ローカルの `~/.claude/CLAUDE.md` や SessionStart hook が追加で資料を読み込んでいないかは未確認（PC側で確認予定）
- 起動時の資料読み込みの削減効果は推定値のみで、トークン数は実測していない（下記参照）

## 次の作業候補

1. PCで `22d89b5` 以降を取り込み、短期記憶付きAPI版の実機試用（予算と送信範囲を承認してから）
2. 記憶設計の未決事項についてユーザーと合意し、自動採用の基準を決める
3. 起動時の読み込み量を実測する（ローカルで `/context` などを使い、変更前後を比較）

## 関連 check（会話版の変更時に優先して実行）

```bash
python3 -B scripts/check_conversation_v01.py
python3 -B scripts/check_saved_api_conversation.py
python3 -B scripts/check_persistent_conversation_memory.py
```

ほかに、`scripts/check_conversation_*.py` と `scripts/check_memory_extraction_evaluation.py` もある。
いずれもクラウドで通過済み（2026-11-22）。Windowsでは `venv\Scripts\python.exe -B` で実行する。

## 起動時の読み込み量（2026-11-22 の整理）

| | 対象 | 文字数（実測） | トークン（推定） |
|---|---|---|---|
| 変更前 | 旧Read first 9ファイル | 183,427字 | 約10.2万 |
| 変更後 | `CLAUDE.md` + 本ファイル | 約8,500字（5,960 + 約2,500） | 約3千 |

文字数は Python の `len()` による実測（変更前は commit `22d89b5` の内容）。
トークン数は「日本語1文字≒1トークン、英字4文字≒1トークン」とした推定で、実測ではない（推定削減率 約97%）。
必要に応じて読む詳細資料の分は含まない。実測はローカルの `/context` 等で行う。

## 更新ルール

- Verや作業の区切りごとに、Claude Code がこのファイルを上書き更新し、同じcommitに含める
- 更新するのは、確定事項・未解決事項・次の作業・基準commitの4つ。完了した経緯は changelog に移す
- 推測の進捗を「確定」に書かない。実機で未確認のものは「未検証」と明記する
