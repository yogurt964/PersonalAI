# Claude Code Start Guide for PersonalAI

## 1. このドキュメントの目的

このドキュメントは、Claude CodeがPersonalAI開発を引き継ぐための開始手順書である。

詳細な移行情報は `MIGRATION.md` を読む。
開発方針は `AGENTS.md` と `docs/development_workflow.md` を読む。
GitHub閲覧者向けの説明は `README.md` を読む。

このファイルは最初の入口であり、唯一の仕様書ではない。

## 2. 最初に実行するコマンド

まず現在状態を確認する。

```powershell
git status
git log --oneline -5
venv\Scripts\python.exe -B scripts\run_ver2_checks.py
```

`scripts/run_ver2_checks.py` は、環境によって SQLite disk I/O error や timeout が出ることがある。
その場合はDB削除や初期化をせず、個別checkや権限付き再実行で確認する。
DBを削除しない。

## 3. 最初に読むファイル

以下の順番で読む。

```text
AGENTS.md
MIGRATION.md
README.md
docs/development_workflow.md
docs/project_handoff.md
docs/check_workflow.md
docs/changelog.md
docs/portfolio_readme_policy.md
docs/demo_logs/web_reader_memory_candidate_demo.md
```

## 4. 現在の開発状態

Ver2.22まで完了している。

現在の主な状態:

- READMEのポートフォリオ見せ方強化済み
- MIGRATION.mdにユーザー適応・コスト・失敗対応・安全管理を反映済み
- Web Reader、Web Reader確認、確認待ち状態の文脈解釈が実装済み
- Memory Candidate生成、確認、編集dry-run、ユーザー確認つき保存が実装済み
- 直近保存Memory確認とMemory簡易検索が実装済み
- File / PDF / Image / YouTube / Office / メール / カレンダー連携は未実装
- LLM Intent Resolverは未実装
- OpenAI / Claude / Gemini接続は未実装

## 5. ユーザー対応方針

ユーザーは、実装の細かい差分より、実際にできるようになったことを重視する。

重視するもの:

- AIの返答の自然さ
- 使いやすさ
- 実用性
- ポートフォリオ価値
- 次に何を確認すべきか

目的が明確なら、必要以上に確認せず進める。
ただし致命的リスクがある操作は必ず確認する。

ユーザーが提案する前に、不足しそうな観点をAI側から先回りして提案・質問する。
ただし質問しすぎて作業を止めない。

## 6. コスト方針

基本は低コストで進める。

- ローカル環境、Qwen、既存ツールを優先する
- 無駄なAPI消費やblind retry loopは避ける
- ログを読まずに同じ失敗を繰り返さない
- 開発効率、AI性能、完成度、安定性、就活ポートフォリオ価値が明確に上がるなら必要な課金は許容する
- 課金、契約、購入、APIキー利用、外部送信は必ずユーザー確認する

## 7. 失敗時対応

失敗した場合は、破壊的な復旧を選ばず、小さく切り分ける。

基本手順:

1. まずログを読む
2. 原因を仮説立てする
3. 小さく修正する
4. 必要なチェックだけ再実行する
5. 同じ失敗を無限に繰り返さない
6. DB削除や初期化で解決しようとしない
7. 安全チェックを削ってテストを通さない
8. 失敗を隠さない

## 8. 致命的リスクと確認が必要な操作

確認が必要:

```text
PCが使い物にならなくなる可能性がある操作
OS / レジストリ / ドライバ / PATHなどへの大きな変更
大量課金
契約
購入
APIキーや個人情報の外部送信
重要データ削除
data/personal_ai.db の削除
DB初期化
DBスキーマの破壊的変更
Memory物理削除
大量ファイル削除
reset --hard
force push
rebase
Git履歴書き換え
PermissionManagerや安全チェックを大きく弱める変更
```

確認不要で進めてよい:

```text
通常の実装
docs更新
テスト追加
軽微なリファクタリング
git add
git commit
git push
修正用commit
後から戻せる変更
```

## 9. 次に進めるVer候補

推奨順:

```text
Ver2.24: Claude Code引継ぎ確認
Ver2.25: LLM Intent Resolver設計
Ver2.26: File Reader最小実装
Ver2.x: PDF Reader
Ver2.x: Image Reader
Ver2.x: YouTube Reader
Ver2.x: README用スクリーンショット/GIF追加
```

Claude Codeへ移行後の最初の作業は、いきなり実装ではなく、引継ぎ確認にする。

## 10. 最初の引継ぎ確認タスク

Claude Codeに最初にやらせるタスク:

```text
【Claude Code引継ぎ確認まとめ】

実装はまだ行わず、AGENTS.md、MIGRATION.md、README.md、docs/development_workflow.md、docs/project_handoff.md、docs/check_workflow.md、docs/changelog.md を読んで、以下をまとめてください。

1. PersonalAIの現在の目的
2. 現在実装済みの主な機能
3. 未実装の将来スコープ
4. ユーザーが好む開発・会話スタイル
5. コスト方針
6. 失敗時対応方針
7. 安全確認が必要な致命的リスク
8. 次に進めるべきVer候補
9. 引継ぎ資料で不足・矛盾・改善した方がよい点

この段階では、新機能実装、docs更新、DB変更、commit、pushは行わないでください。
```
