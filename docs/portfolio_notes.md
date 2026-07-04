# Portfolio Notes

## 目的

このドキュメントは、PersonalAIを就活・面接で説明しやすくするためのメモである。

README.mdは外部公開向けの概要、このファイルは面接で話す内容や想定質問を整理するための補助資料として使う。

## ポートフォリオとしての見せ方

PersonalAIは、単なるチャットAIではなく、長期記憶、Web Reader、安全確認、Memory Candidate、Tool実行設計を段階的に組み合わせている点を見せる。

見せ方の軸:

- ローカルLLMを使ったAIアシスタント開発
- 会話履歴と長期記憶の基礎
- InputAnalyzer / Planner / Router / Executorによる責務分離
- PermissionManager / ToolRunnerによる安全設計
- Web Readerで外部情報を読み取る流れ
- Reader結果をMemory Candidateとして保存候補化する流れ
- 保存前確認とdry-runによる安全な段階実装
- Verごとのチェックとdocs更新による継続開発

## 面接で説明する一言

```text
ローカルLLMとPythonを使って、長期記憶・Web読み取り・安全な確認フローを持つ個人AIアシスタントを開発しています。
単なるチャットではなく、外部情報を読み取り、記憶候補を作り、保存前にユーザー確認を挟むAIエージェント設計を実装しています。
```

## 技術的にアピールできる点

- Pythonで会話処理、Reader、Memory Candidate、Tool実行を段階的に分離している
- SQLite / SQLAlchemyで会話履歴とMemory基礎を扱っている
- Ollama / Qwenを使い、ローカルLLMで会話できる
- Web Readerは実行前確認を挟み、URL検出だけでは自動実行しない
- fake fetcherを使った自動チェックで、実Webアクセスなしに動作確認できる
- バージョンごとのcheckスクリプトで回帰を確認している
- 未実装機能をできたふりしない応答を重視している

## 設計面でアピールできる点

- InputAnalyzer / CapabilityManager / Planner / Router / Executorで責務を分けている
- PermissionManagerで危険操作を止める土台を作っている
- ToolRunnerでTool実行を共通化している
- Memory保存をいきなり実装せず、Memory Candidate dry-runから段階的に進めている
- Reader結果の保存方針、安全方針、会話品質方針をdocsに残している
- 開発自走方針をAGENTS.mdとdocs/development_workflow.mdに整理している

## まだ未完成だが伸びしろとして説明できる点

未実装:

- Memory保存の本実装
- Memory CandidateのDB保存
- PDF Reader
- Image Reader
- YouTube Reader
- File Reader
- OpenAI / Claude / Gemini 接続
- GUI
- PC操作
- MIGRATION.md

説明の仕方:

```text
現時点では、安全な土台を優先しているため、Memory保存や外部API接続はまだ本実装していません。
まずdry-runで確認フローを作り、保存してよい内容と危険な内容を分ける設計を進めています。
```

## 想定質問と回答例

### Q. これは普通のチャットボットと何が違いますか？

A. 会話だけでなく、入力分析、Web読み取り、Memory Candidate生成、保存前確認、Tool実行前Permissionなど、AIエージェント化に必要な周辺設計を進めている点です。

### Q. なぜローカルLLMを使っていますか？

A. 個人情報や作業文脈を扱うため、まずローカルで安全に動かせる構成を重視しています。将来的にはOpenAI / Claude / GeminiなどもRouterで選べる設計を考えています。

### Q. Memory保存をまだしていない理由は？

A. Reader結果には不要情報、著作権上扱いづらい長文、機密情報、個人情報が混ざる可能性があります。そのため、いきなり保存せず、Memory Candidateとして候補化し、ユーザー確認を挟む設計にしています。

### Q. 工夫した点は？

A. 機能を一気に作らず、設計docs、dry-run、自動チェック、実装接続の順に小さく進めた点です。未実装機能をできたように見せないことも重視しました。

### Q. 今後どう発展させますか？

A. Memory Candidate編集dry-run、ユーザー確認つき保存、PDF / YouTube / Image Reader、GUI、外部モデル連携へ段階的に広げる予定です。

## 1分説明

```text
PersonalAIは、PythonとローカルLLMを使った個人AIアシスタントです。
会話履歴や長期記憶の基礎に加えて、URLを読み取るWeb Reader、安全確認、Reader結果から保存候補を作るMemory Candidate機能を実装しています。
特に、外部WebアクセスやMemory保存を勝手に行わず、ユーザー確認やdry-runを挟む安全設計を重視しています。
現在は就活ポートフォリオとして、機能だけでなく、設計docs、チェックスクリプト、段階的な開発履歴も見せられるように整備しています。
```

## 3分説明

```text
PersonalAIは、ローカルLLMとPythonで開発している個人AIアシスタントです。
単なるチャットではなく、ユーザー入力をInputAnalyzerで分類し、CapabilityManager、Planner、Router、Executorで処理の流れを分けています。

現在はQwen / Ollamaでローカル会話ができ、会話履歴と長期記憶の基礎があります。
さらにWeb Readerを追加し、URLを受け取ったときにすぐWebアクセスせず、まずユーザーに確認します。
確認後にページを読み取り、タイトル、URL、本文プレビューを整形して返します。

読み取り結果はすぐMemory保存せず、Memory Candidateとして保存候補を作ります。
保存する、保存しない、編集して保存、後で確認といった応答もdry-runで解釈できます。
ただしVer2.15時点では、まだDBへ保存しません。
不要な情報や機密情報を勝手に保存しないため、安全な確認フローを先に作っています。

開発面では、バージョンごとにdocsとcheckスクリプトを追加し、既存機能を壊さないように進めています。
今後はMemory Candidateの編集、ユーザー確認つき保存、PDFやYouTube Reader、GUIなどへ拡張する予定です。
```

## 今後の改善予定

- Memory Candidate編集dry-run
- Memory Candidateのユーザー確認つき保存設計
- READMEへの画像・GIF・図の追加
- MIGRATION.md作成
- PDF Reader
- YouTube Reader
- Image Reader
- GUI
- 外部モデル連携
