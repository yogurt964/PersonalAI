# Check Workflow

## 目的

このドキュメントは、PersonalAIのVer1.x / Ver2.x開発で、どのcheckをいつ実行するかを整理するための運用メモである。

Ver1.xでは、毎回すべてのcheckを思い出して手動実行するのではなく、変更の大きさに応じて quick check / standard check / full pre-release check を使い分ける。
Ver2.xでは、Reader実装を追加するため `scripts/run_ver2_checks.py` も使う。

## quick check

quick check は、小さな変更後に短時間で最低限の確認をしたいときに使う。

例:

```powershell
venv\Scripts\python.exe -B scripts\check_ver1100.py
venv\Scripts\python.exe -B scripts\check_ver190.py
venv\Scripts\python.exe -B scripts\check_ver180.py
venv\Scripts\python.exe -B scripts\check_ver170.py
venv\Scripts\python.exe -B scripts\check_ver160.py
venv\Scripts\python.exe -B scripts\check_ver150.py
venv\Scripts\python.exe -B scripts\check_ver140.py
venv\Scripts\python.exe -B scripts\check_ver130.py
venv\Scripts\python.exe -B scripts\check_ver120.py
venv\Scripts\python.exe -B scripts\check_ver110.py
venv\Scripts\python.exe -B -c "from core.personal_ai import PersonalAI; print('PersonalAI import OK')"
```

確認すること:

- 最新version固有のcheckが通る
- Ver1.xで追加した重要機能が壊れていない
- PersonalAIのimportができる

## standard check

standard check は、Ver1.xの通常commit前に使う基本確認である。

Ver1.xの基本確認には `scripts/run_ver1_checks.py` を使う。

```powershell
venv\Scripts\python.exe -B scripts\run_ver1_checks.py
```

`run_ver1_checks.py` は、Ver1.xでよく使うcheckをまとめて実行する。

主な対象:

- `scripts/check_ver1100.py`
- `scripts/check_ver190.py`
- `scripts/check_ver180.py`
- `scripts/check_ver170.py`
- `scripts/check_ver160.py`
- `scripts/check_ver150.py`
- `scripts/check_ver140.py`
- `scripts/check_ver130.py`
- `scripts/check_ver120.py`
- `scripts/check_ver110.py`
- `scripts/check_v1_final_preparation.py`
- `scripts/check_ver031.py`
- `scripts/run_pre_v1_checks.py`

## Ver2.x standard check

Ver2.xの基本確認には `scripts/run_ver2_checks.py` を使う。

```powershell
venv\Scripts\python.exe -B scripts\run_ver2_checks.py
```

`run_ver2_checks.py` は以下を実行する。

- `scripts/check_ver2460.py`
- `scripts/check_ver2450.py`
- `scripts/check_ver2440.py`
- `scripts/check_ver2430.py`
- `scripts/check_ver2420.py`
- `scripts/check_ver2410.py`
- `scripts/check_ver2400.py`
- `scripts/check_ver2390.py`
- `scripts/check_ver2380.py`
- `scripts/check_ver2370.py`
- `scripts/check_ver2360.py`
- `scripts/check_ver2350.py`
- `scripts/check_ver2340.py`
- `scripts/check_ver2330.py`
- `scripts/check_ver2320.py`
- `scripts/check_ver2310.py`
- `scripts/check_ver2300.py`
- `scripts/check_ver2290.py`
- `scripts/check_ver2280.py`
- `scripts/check_ver2270.py`
- `scripts/check_ver2260.py`
- `scripts/check_ver2250.py`
- `scripts/check_ver2240.py`
- `scripts/check_ver2230.py`
- `scripts/check_ver2220.py`
- `scripts/check_ver2210.py`
- `scripts/check_ver2200.py`
- `scripts/check_ver2190.py`
- `scripts/check_ver2180.py`
- `scripts/check_ver2170.py`
- `scripts/check_ver2160.py`
- `scripts/check_ver2150.py`
- `scripts/check_ver2140.py`
- `scripts/check_ver2130.py`
- `scripts/check_ver2120.py`
- `scripts/check_ver2110.py`
- `scripts/check_ver2100.py`
- `scripts/check_ver290.py`
- `scripts/check_ver280.py`
- `scripts/check_ver270.py`
- `scripts/check_ver260.py`
- `scripts/check_ver250.py`
- `scripts/check_ver240.py`
- `scripts/check_ver230.py`
- `scripts/check_ver220.py`
- `scripts/check_ver210.py`
- `scripts/check_ver200.py`
- `scripts/run_ver1_checks.py`

Ver2.46では、`check_ver2460.py` でSYSTEM_PROMPTの日本語指示に、明示指定があれば他言語に従う例外が追加されていることを確認する。
実際のQwen呼び出し、DB書き込みはしない。
Ver2.45では、`check_ver2450.py` でSYSTEM_PROMPTへの日本語回答指示の追加を確認する。
実際のQwen呼び出し、DB書き込みはしない。
Ver2.44では、`check_ver2440.py` で確認判定のハイブリッド方式（固定語彙優先＋不明時のみLLM）を確認する。
このcheckはfakeのLLM関数で、固定語彙が一致する場合はLLMを一切呼ばないこと、一致しない場合のみLLMを呼ぶこと、LLMの応答が不明瞭・例外時は必ずunclearにfail-safeすること、LLMに渡すプロンプトにユーザーの返信テキスト以外（外部Reader本文など）が混ざらないこと、7つのreader confirmationモジュールとpersonal_ai.pyの7つのhandle_pending_X_reader_confirmation()がask_llm_funcを正しく橋渡ししていること、ask_llm_funcを持たない過去のtest doubleでも例外を起こさずunclearのままになることを確認する。
実際のQwen呼び出し、DB書き込みはしない。
Ver2.43では、`check_ver2430.py` でYouTube Reader最小実装を確認する。
このcheckはfakeのtranscript_fetcherで、YouTube URLの各形式（watch?v=/youtu.be/embed/shorts）からの動画ID抽出、字幕取得成功・失敗（存在しない・無効化）、確認フロー、PersonalAI結合フロー（同一ターンでの要約・別ターンでの追加質問）を確認する。
実際のYouTubeへのアクセスは行わず、requirements.txtの内容を確認する。実際のYouTube動画での動作確認はユーザー自身に行ってもらう。
Ver2.42では、`check_ver2420.py` でExcel Readerのグループ集計を確認する。
このcheckは実際の売上データに近いテストケースで店舗ごとの合計比較が正しく計算されること、ID列が誤って集計されないこと、値がすべて一意なカテゴリ列でグループ集計が出ないこと、同一ターンでの要約・別ターンでの追加質問の両方で参照できることを確認する。
実Webアクセス、DB書き込み、実LLM実行はしない。
Ver2.41では、`check_ver2410.py` でPowerPoint Reader最小実装を確認する。
このcheckはpython-pptxで実際に生成した.pptxファイルでの実テキスト抽出（タイトル・本文・表・ノート）、fakeのLLM関数を使ったPersonalAI結合フロー、ファイル名に「powerpoint」を含むケースでの動作、requirements.txtの内容を確認する。
実Webアクセス、DB書き込み、実LLM実行はしない。
Ver2.40では、`check_ver2400.py` で応答の正直さ・Qwen性能・OpenAIエスカレーション方針のdocs化を確認する。
このcheckはdocs確認のみを行い、実Webアクセス、DB書き込み、LLM実行、機能コード変更をしない。
Ver2.39では、`check_ver2390.py` でCLIの考え中表示を確認する。
このcheckは`PersonalAI.run()`のソースを確認し、表示が入力受付後・`handle_user_input`呼び出し前の正しい位置にあることを確認する。
実Webアクセス、DB書き込み、実LLM実行はしない。
Ver2.38では、`check_ver2380.py` でExcel Readerの数値列自動集計を確認する。
このcheckは実際の売上データに近いテストケースで合計・平均が正しく計算されること、集計値が行データより先に配置され切り詰めに強いこと、文字列だけの列を誤って集計しないこと、同一ターンでの要約・別ターンでの追加質問の両方で正しい集計値を参照できることを確認する。
実Webアクセス、DB書き込み、実LLM実行はしない。
Ver2.37では、`check_ver2370.py` でExcel Reader最小実装を確認する。
このcheckはopenpyxlで実際に生成した.xlsxファイルでの実テキスト抽出、fakeのLLM関数を使ったPersonalAI結合フロー、ファイル名に「excel」を含むケースで文書作成判定と衝突しないこと、requirements.txtの内容を確認する。
実Webアクセス、DB書き込み、実LLM実行はしない。
Ver2.36では、`check_ver2360.py` でWord Reader最小実装を確認する。
このcheckはpython-docxで実際に生成した.docxファイルでの実テキスト抽出、fakeのLLM関数を使ったPersonalAI結合フロー、ファイル名に「word」を含むケースで文書作成判定と衝突しないこと、requirements.txtの内容を確認する。
実Webアクセス、DB書き込み、実LLM実行はしない。
Ver2.35では、`check_ver2350.py` で将来の記憶アーキテクチャ方針のdocs化を確認する。
このcheckはdocs確認のみを行い、実Webアクセス、DB書き込み、LLM実行、機能コード変更をしない。
Ver2.34では、`check_ver2340.py` でlast_read_documentの誤解答防止を確認する。
このcheckは、2件連続で読み取った後に1件目について聞かれた場合のcontext messageに、「もう保持していません」「断定しないでください」という警告文言が含まれることを確認する。
実Webアクセス、DB書き込み、実LLM実行はしない。
Ver2.33では、`check_ver2330.py` でファイルパス抽出のスペース対応バグ修正を確認する。
このcheckはスペースを含むWindows絶対パス（引用符なし）が正しく抽出されること、既存の引用符つきパス・単純パスの挙動が維持されていること、PersonalAI経由の読み取りが実際のバグ再現ケースで成功することを確認する。
実Webアクセス、DB書き込み、実LLM実行はしない。
Ver2.32では、`check_ver2320.py` でPDF Reader最小実装を確認する。
このcheckは手書きで生成した実PDFバイナリでのpypdf抽出、fakeのPDF ReaderでのPersonalAI結合フロー（確認・実行・キャンセル・存在しないファイル・要約同時実行）、requirements.txtの内容を確認する。
実Webアクセス、DB書き込み、実LLM実行はしない。
Ver2.31では、`check_ver2310.py` でReader結果をQwenでの応答に接続したことを確認する。
このcheckはfakeのLLM関数を使い、読み取り+要約の同時実行、プレーンな読み取りの現状維持、別ターンでの文脈利用、未読み取り時に文脈が注入されないことを確認する。
実Webアクセス、実ファイルアクセス（一時テストファイルのみ使用）、DB書き込み、実LLM実行はしない。
Ver2.30では、`check_ver2300.py` で「ワード」/「キーワード」誤判定バグの修正を確認する。
このcheckは「キーワード」を含む入力が文書作成として誤判定されないこと、実際のWord文書作成依頼は引き続き検出されることを確認する。
実Webアクセス、DB書き込み、LLM実行はしない。
Ver2.29では、`check_ver2290.py` でFile Reader最小実装を確認する。
このcheckは一時ディレクトリ内のfakeファイルのみを使い、パス検出、確認メッセージ、ToolRunner経由の実行・未実行、キャンセル、存在しないファイル、対応外拡張子、PersonalAI結合フローを確認する。
実際のユーザーファイルへのアクセス、DB書き込み、LLM実行はしない。
Ver2.28では、`check_ver2280.py` でOpenAI利用方針の見直し（月間上限額制）を確認する。
このcheckは`MIGRATION.md` / `CLAUDE.md` / `AGENTS.md` / `README.md` / `docs/claude_code_start.md` / `docs/llm_intent_resolver_design.md`に月間上限額の運用方針が反映されていること、project_handoff.md / changelog.mdの内容、run_ver2_checks.pyへの登録を確認する。
実Webアクセス、DB書き込み、LLM実行、機能コード変更をしない。
Ver2.27では、`check_ver2270.py` でproject_handoff.mdの現在バージョン固定依存の解消を確認する。
このcheckは`check_ver2180.py`〜`check_ver2260.py`の9本に、project_handoff.mdの具体的なバージョン番号（現在バージョン: VerX.X）への固定依存が残っていないこと、run_ver2_checks.pyへの登録を確認する。
実Webアクセス、DB書き込み、LLM実行、機能コード変更をしない。
Ver2.26では、`check_ver2260.py` でLLM Intent Resolver設計docsの整備を確認する。
このcheckは `docs/llm_intent_resolver_design.md` の存在と必須語句、`core/confirmation_intent.py` / `core/memory_candidate_confirmation.py` に実装変更がないこと、project_handoff.md / changelog.mdの内容、run_ver2_checks.pyへの登録を確認する。
実Webアクセス、DB書き込み、LLM実行、機能コード変更をしない。
Ver2.25では、`check_ver2250.py` でClaude Code自走運用モードの整備を確認する。
このcheckは `CLAUDE.md` の存在と必須語句、AGENTS.md / MIGRATION.md / docs/claude_code_start.mdからの `CLAUDE.md` 参照、README.mdに固定Ver表記が残っていないこと、project_handoff.md / changelog.mdの内容、run_ver2_checks.pyへの登録を確認する。
実Webアクセス、DB書き込み、LLM実行、機能コード変更をしない。
Ver2.24では、`check_ver2240.py` でClaude Code引継ぎ確認結果のdocs反映を確認する。
このcheckはdocs/claude_code_start.md、MIGRATION.md、AGENTS.md、README.md、project_handoff.md、check_workflow.md、changelog.md、portfolio_readme_policy.md、run_ver2_checks.pyを確認し、MIGRATION.mdの古いロードマップ表記が残っていないこと、Qwen / OpenAIの利用方針が反映されていることも確認する。
実Webアクセス、DB書き込み、LLM実行、機能コード変更をしない。
Ver2.23では、`check_ver2230.py` でClaude Code移行準備パッケージを確認する。
このcheckはdocs/claude_code_start.md、MIGRATION.md、AGENTS.md、README.md、project_handoff、changelog、run_ver2_checks.pyを確認し、実Webアクセス、DB書き込み、LLM実行、機能コード変更をしない。
Ver2.22では、`check_ver2220.py` でREADMEのポートフォリオ見せ方を確認する。
このcheckはREADME、Mermaid、デモ導線、アーキテクチャ図、docs/portfolio_readme_policy.md、project_handoff、changelog、run_ver2_checks.pyを確認し、実Webアクセス、DB書き込み、LLM実行、機能コード変更をしない。
Ver2.21では、`check_ver2210.py` でClaude Code移行用MIGRATION.mdと関連docsを確認する。
このcheckはdocs確認のみを行い、実Webアクセス、LLM実行、Memory保存、DBスキーマ変更をしない。
Ver2.20では、`check_ver2200.py` でMemory検索の最小実用化を確認する。
このcheckはfake検索を使い、`覚えてる？` などの入力からqueryを取り出すこと、保存済みMemoryの検索結果表示、結果なし表示、既存Web Reader保存フロー維持を確認する。
DBスキーマ変更はしない。
自動チェックでは実DB保存や実Webアクセスを行わない。
Ver2.19では、`check_ver2190.py` で確認待ち状態の文脈解釈を確認する。
このcheckはfake fetcherとfake保存を使い、`いいよ` / `お願いします` がWeb Reader実行許可として扱われること、`キャンセル` で実行しないこと、不明入力では通常会話へ流さず確認を聞き直すことを確認する。
LLM解釈はまだ実装しない。
自動チェックでは実Webアクセス、実DB保存、LLM実行をしない。
Ver2.18では、`check_ver2180.py` でMemory保存後の確認・表示フローを確認する。
このcheckはfake保存とfake記憶確認を使い、保存内容プレビュー、直近保存したMemory、`今保存した記憶を確認して` の応答を確認する。
DBスキーマ変更はしない。
自動チェックでは実DB保存しない。
Ver2.17では、`check_ver2170.py` でMemory Candidateのユーザー確認つき保存を確認する。
このcheckはfake保存関数を使い、`保存する` と明示された低リスク候補だけが既存の長期記憶保存機構へ渡されることを確認する。
自動チェックでは実DB保存しない。
高リスク候補は保存せず、DBスキーマ変更もしない。
Ver2.16では、`check_ver2160.py` でMemory Candidate編集dry-runを確認する。
このcheckは「編集して保存」の後に編集内容を受け取り、編集済み候補をdry-run保持する流れを確認し、実Webアクセス、DB書き込み、LLM実行、Memory保存をしない。
Ver2.15では、`check_ver2150.py` でポートフォリオREADMEとデモログを確認する。
このcheckはREADME.md、docs/portfolio_notes.md、docs/demo_logs/web_reader_memory_candidate_demo.md、project_handoff、changelog、check_workflow、run_ver2_checks.pyを確認し、DB書き込み、実Webアクセス、LLM実行、Memory保存をしない。
Ver2.14では、`check_ver2140.py` で開発自走方針docsを確認する。
このcheckはAGENTS.md、docs/development_workflow.md、project_handoff、changelog、check_workflow、run_ver2_checks.pyを確認し、DB書き込み、実Webアクセス、LLM実行、Memory保存をしない。
Ver2.13では、`check_ver2130.py` でMemory Candidate確認応答のdry-runを確認する。
このcheckは保存する / 保存しない / 編集して保存 / 後で確認の解釈を確認し、実Webアクセス、DB書き込み、LLM実行、Memory保存をしない。
Ver2.12では、`check_ver2120.py` でMemory Candidate確認UI方針を確認する。
このcheckはdocs確認のみを行い、実Webアクセス、DB書き込み、LLM実行、ToolRunner実行、Memory保存をしない。
Ver2.11では、`check_ver2110.py` でMemory CandidateをWeb Reader結果にdry-run接続したことを確認する。
このcheckはfake fetcherのみを使い、実Webアクセス、DB書き込み、LLM実行、Memory保存、Memory CandidateのDB保存をしない。
Ver2.10では、`check_ver2100.py` でMemory Candidate生成のdry-runを確認する。
このcheckは実Webアクセス、DB書き込み、LLM実行、ToolRunner実行、Memory保存をしない。
Ver2.9では、`check_ver290.py` でReader結果のMemory保存方針docsを確認する。
このcheckはdocs確認のみを行い、実Webアクセス、DB書き込み、LLM実行、ToolRunner実行をしない。
Ver2.8では、`check_ver280.py` でWeb Reader結果の会話返答品質を確認する。
成功時の表示、失敗時の読めたふり防止、user_confirmed=False時の未実行、fake fetcherのみ使用、DB非変更を確認する。
Ver2.7では、`check_ver270.py` で完成形ビジョン、会話品質・返答方針、Ver2.7のdocs更新を確認する。
このcheckはdocs確認のみを行い、実Webアクセス、DB書き込み、LLM実行、ToolRunner実行をしない。
Ver2.6では、`check_ver260.py` で実Web手動テスト結果がdocsに記録されていることを確認する。
このcheckはdocs確認のみを行い、実Webアクセスしない。
Ver2.5では、`check_ver250.py` でuser_confirmed=True後のToolRunner経由Web Reader実行をfake fetcherで確認する。
Ver2.4では、`check_ver240.py` で確認応答のdry-runとToolRequest候補作成を確認する。
Ver2.3では、`check_ver230.py` でURL確認メッセージを会話返答として表示するdry-run接続を確認する。
Ver2.2では、`check_ver220.py` でURL入力検出から確認メッセージ生成までのdry-runを確認する。
Ver2.0では、`check_ver200.py` でWeb Reader最小実用版を確認する。
Ver2.1では、`check_ver210.py` でWeb Reader手動実行テストdocsと会話UI接続方針を確認する。
自動checkではfake fetcherを使い、実Webアクセスしない。

## full pre-release check

full pre-release check は、大きな区切りやRelease前に使う。

Release前や大きな変更では、`run_ver1_checks.py` に加えて、必要に応じて以下も確認する。

```powershell
venv\Scripts\python.exe -B scripts\run_pre_v1_checks.py
venv\Scripts\python.exe -B scripts\benchmark_lightweight.py
"exit" | venv\Scripts\python.exe -B app.py
git diff --check
git status
```

`run_pre_v1_checks.py` はVer1.0前に整備した一括checkであり、DBテスト書き込みを含む既存機能確認にも使う。
環境によってSQLiteの `disk I/O error` が出る場合は、Codexサンドボックス由来かどうかを確認し、必要なら権限付きで再実行する。

## Ver1.xのcheck番号方針

Ver1.1以降のcheck番号は、Ver0.xと混同しないように以下の形式にする。

```text
Ver1.1 -> scripts/check_ver110.py
Ver1.2 -> scripts/check_ver120.py
Ver1.3 -> scripts/check_ver130.py
Ver1.4 -> scripts/check_ver140.py
Ver1.5 -> scripts/check_ver150.py
Ver1.6 -> scripts/check_ver160.py
Ver1.7 -> scripts/check_ver170.py
Ver1.8 -> scripts/check_ver180.py
Ver1.9 -> scripts/check_ver190.py
Ver1.10 -> scripts/check_ver1100.py
```

各version固有のcheckは、作業内容に合わせて追加する。
Ver1.10のcheck名は `check_ver1100.py` であり、`check_ver110.py` はVer1.1用として残す。
たとえば、Ver1.1では `check_ver110.py` でMemory利用方針を確認し、Ver1.2では `check_ver120.py` でVer1.xチェック運用を確認する。
Ver1.3では `check_ver130.py` で会話品質方針を確認する。
Ver1.4では `check_ver140.py` でTool / Adapter受け口を確認する。
Ver1.5では `check_ver150.py` でTool実行前Permission判定を確認する。
Ver1.6では `check_ver160.py` でInputAnalyzer / Capability / Tool連携のdry-runを確認する。
Ver1.7では `check_ver170.py` でTool実行ログと結果記録の設計を確認する。
Ver1.8では `check_ver180.py` でReader実装前の手動テストケースとdry-run代表ケースを確認する。
Ver1.9では `check_ver190.py` でVer2.0 Reader実装計画を確認する。
Ver1.10では `check_ver1100.py` でVer1.x総仕上げ確認とVer2.0準備状態を確認する。

## 運用方針

- 小さな変更後は quick check を使う
- 通常のcommit前は standard check を使う
- 大きな区切りやRelease前は full pre-release check を使う
- checkはDB削除、Memory物理削除、既存Memory削除を行わない方針にする
- Ver2.14以降、通常のGit commit / push はユーザー確認なしで進めてよい
- force push、rebase、reset、履歴書き換え、作業消失につながる操作はユーザー確認する
