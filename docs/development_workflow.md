# Development Workflow

## 目的

このドキュメントは、PersonalAI開発をAIエージェントが自走しやすくするための運用方針である。

Ver2.14では、開発速度を上げるため、後から修正できる通常作業はAIエージェント側で進める方針に切り替える。
ユーザー確認は、実用面、不可逆操作、危険操作、課金、外部送信、重要な仕様判断に集中する。

## 現在の課題

これまでは、ChatGPT / Codex / VS Code / PowerShell の間をユーザーが行き来し、コード差分やログを貼って確認しながら進めていた。

この進め方は安全だが、次の課題がある。

- 開発速度が落ちる
- ユーザーがコード差分の細部確認に時間を取られる
- 実際にPersonalAIを使った実用面の確認に集中しづらい
- AIエージェントが毎回どこまで自走してよいか迷いやすい

## 新しい開発方針

Ver2.14以降は、後から修正できる操作はユーザー確認なしで進める。

AIエージェントは、通常のコード修正、機能追加、テスト追加、docs更新、Git操作を自走してよい。
ただし、不可逆操作、危険操作、外部送信、課金、DB削除、Memory物理削除、安全機能の弱体化は必ずユーザー確認する。

## ユーザーの役割

ユーザーは、コード差分の細部確認よりも、実際の使い勝手に集中する。

重視する確認:

- AIの返答が自然か
- ユーザーの意図を理解できているか
- 欲しい結果が出ているか
- 使いやすいか
- 明らかな破綻がないか
- 以前より便利になっているか
- ポートフォリオとして見せられる品質か
- 不可逆操作・危険操作・課金・外部送信を承認してよいか

## AIエージェントの役割

AIエージェントは、実装、テスト、docs更新、Git操作、問題修正をできるだけ自走する。

期待する動き:

- 目的を理解する
- 必要なファイルを読む
- 後から直せる細部は仮決定する
- 実装する
- 自動チェックを実行する
- 問題があれば修正する
- commit / pushまで進める
- ユーザーには動作結果と確認ポイントを報告する

## 確認不要な操作

通常の後から修正できる操作は確認不要。

- コード修正
- 機能追加
- 軽いリファクタリング
- テスト追加
- docs更新
- ファイル編集
- `git add`
- `git commit`
- `git push`
- branch作成
- 通常merge
- 修正用commit

## 確認必須の操作

以下は必ずユーザー確認する。

- force push
- `reset --hard`
- rebase
- Git履歴の書き換え
- 作業内容の消失につながる操作
- DB削除
- DB初期化
- DBスキーマの破壊的変更
- Memory物理削除
- 大量ファイル削除
- APIキー、個人情報、機密情報の外部送信
- 課金、契約、購入
- PermissionManagerや安全チェックを弱める変更
- 後から戻すのが難しい仕様変更

## Git操作方針

通常の `git add`、`git commit`、`git push` はユーザー確認不要で進めてよい。

ただし、以下は確認必須である。

- force push
- rebase
- reset
- Git履歴の書き換え
- 作業内容が消える可能性がある操作

commit messageは、作業内容が分かる短い英語にする。
push後は、commit hash、git status、確認ポイントを報告する。

## dry-run方針

dry-runは原則不要。

ただし、以下はdry-runまたはユーザー確認を挟む。

- DB保存
- 外部送信
- 課金
- 個人情報
- 機密情報
- Git履歴書き換え
- 破壊的操作
- Permission緩和

Memory Candidate、Reader結果のMemory保存、PC操作、外部API接続などは、段階的にdry-runから進める。

## テスト方針

自動チェックは最低限行う。

通常は以下を実行する。

```powershell
venv\Scripts\python.exe -B scripts\check_verXXXX.py
venv\Scripts\python.exe -B scripts\run_ver2_checks.py
git diff --check
git status
```

Codex環境でSQLiteの `disk I/O error` が出た場合は、DBを削除・初期化せず、権限付き再実行で確認する。
CRLF warningは問題なしとして扱う。

## Intent解釈方針

最終的にはユーザー入力をLLMで文脈込みにIntent解釈する。
ただし、LLMがそのまま実行可否を決めるのではなく、PermissionManager・risk判定・状態管理で制御する。
Ver2.19時点では、LLM判定は入れず、確認待ち状態をルールベースで安全に処理する。
確認待ち中に不明な入力が来た場合は、通常会話へ流さず確認を聞き直す。

## 実用確認方針

ユーザーに確認してもらう内容は、コード差分ではなく実用面に寄せる。

確認ポイント:

- 実際にPersonalAIを動かして自然か
- 返答が目的に合っているか
- 読んだふり、保存したふり、実行したふりをしていないか
- 使いやすくなったか
- 不要な説明が増えていないか
- ポートフォリオとして説明しやすいか

## ポートフォリオ方針

PersonalAIは、単なる個人用スクリプトではなく、ポートフォリオとして見せられる品質を目指す。

重視すること:

- docsが整理されている
- checkスクリプトがある
- 安全方針が明確
- 未実装機能をできたふりしない
- 実装の段階が追える
- commit履歴で成長が分かる

## Claude Code / Cursor移行方針

今後、Claude Code / Cursor など別のAI開発環境へ移行しても、同じ方針で開発できるようにする。

そのために、AIエージェントが最初に読む `AGENTS.md` と、詳しい開発方針である `docs/development_workflow.md` をリポジトリに置く。

Ver2.14では、その前段階として、AIエージェントが自走しやすい開発方針をリポジトリに反映した。

Ver2.21では、Claude Code / Cursor など別環境へ移行するための包括的な引継書として `MIGRATION.md` を追加した。
Claude Code移行時は、AGENTS.md、MIGRATION.md、README.md、docs/development_workflow.md、docs/project_handoff.md、docs/check_workflow.md を最初に確認する。
