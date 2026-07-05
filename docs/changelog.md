# Changelog

## Version 2.46

開始内容:

- SYSTEM_PROMPTの日本語指示に、明示指定があれば他言語に従う例外を追加
- Ver2.45で追加した「日本語で話しかけられたら日本語で回答する」指示が、ユーザーが「英語で答えて」のように明示的に別言語を指定した場合にも対応できるよう例外規定を追加
- `ai/llm.py` のSYSTEM_PROMPTに「ただし、ユーザーが別の言語を明示的に指定した場合は、その指定に従う」を追加
- `scripts/check_ver2460.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2460.py` を追加
- これも軽減策であり、根本的な言語切り替え問題（解釈精度）の完全解決はVer2.40で記録した本格設計で扱う
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持

## Version 2.45

開始内容:

- SYSTEM_PROMPTに日本語回答の指示を追加
- 実機テストのスクリーンショットで、日本語の「ありがとう」に対しQwenが英語で応答する場面が見つかった
- `ai/llm.py` のSYSTEM_PROMPTに「ユーザーが日本語で話しかけている場合は、日本語で回答する（英語などへ勝手に切り替えない）」を1行追加
- `scripts/check_ver2450.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2450.py` を追加
- これは軽減策であり、根本的な言語切り替え問題の完全解決を保証するものではない。完全な解決はVer2.40で記録した「Qwen性能改善・OpenAIエスカレーション」の本格設計で扱う
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持

## Version 2.44

開始内容:

- 確認判定にハイブリッド方式（固定語彙優先＋不明時のみLLM）を導入
- Web/File/PDF/Word/Excel/PowerPoint/YouTube Reader共通の実行確認（はい/いいえ）を、固定語彙リストで判定できない場合のみLLMに解釈させるよう更新
- 固定語彙に一致する入力は今まで通り決定的に処理し、LLMは一切呼び出さない
- LLMに渡すのはユーザー自身の返信テキストのみで、Readerが読み込んだ外部本文は一切含めない（prompt injectionリスクの抑制）
- LLMの応答が不明瞭・呼び出し失敗の場合は必ずunclearにfail-safeし、silentな実行許可は絶対にしない
- `core/confirmation_intent.py` にask_llm_func引数を追加し、7つのreader confirmationモジュールとpersonal_ai.pyの7つのhandle_pending_X_reader_confirmation()を橋渡しした
- ask_llm_funcを渡さない呼び出し元は暗黙にQwenを呼び出さずunclearのままにする設計にし、既存の全checkスクリプトが無変更で通るようにした
- `scripts/check_ver2260.py` の古いpinを、ハイブリッド方式実装済みであることを確認するpinに更新
- `scripts/check_ver2440.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2440.py` を追加
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持

## Version 2.43

開始内容:

- YouTube Reader最小実装を追加
- `requirements.txt` に `youtube-transcript-api` / `requests` / `urllib3` / `charset-normalizer` / `defusedxml` を追加
- `core/youtube_reader_adapter.py` を追加し、ユーザーが指定した単一のYouTube動画から、既存の字幕・自動生成トランスクリプトのみをyoutube-transcript-apiで取得できるようにした（動画・音声のダウンロードや文字起こしの実行はしない）
- 対応URL形式: youtube.com/watch?v=、youtu.be/、youtube.com/embed/、youtube.com/shorts/
- 字幕が存在しない・無効化されている・動画が非公開/削除済みの場合は読めたふりをせず正直に失敗を返す
- `core/youtube_reader_confirmation.py` を追加し、他Reader同様に実行前確認を必須にした
- `core/confirmation_intent.py` に `context_type="youtube_reader"` を追加
- `core/personal_ai.py` にYouTube Readerを接続し、capability_managerのyoutube_read_required（未実装扱い）より先に判定されるようにした
- 自動checkでは実際のYouTubeへアクセスせず、fakeのtranscript_fetcherで動作を確認する。実際のYouTube動画での動作確認はユーザー自身に行ってもらう方針（Web Readerの実Web手動テストと同じ運用）
- `scripts/check_ver2430.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2430.py` を追加
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持

## Version 2.42

開始内容:

- Excel Readerにグループ集計を追加
- これまで対応していなかった「一番売上が高い店舗はどこ？」のような、カテゴリ列（店舗名など）をまたぐ比較質問に対応した
- `core/excel_reader_adapter.py` に `_build_group_by_summary()` を追加し、繰り返し値を持つ文字列列（カテゴリ列）でグループ化して、数値列ごとの合計が最大・最小になるグループをPythonで正確に計算する
- 出力を抑えるため、グループの全内訳ではなく最大・最小のグループだけを報告する
- 全行が一意な値を持つ列（注文IDなど）は、合計しても意味がないため数値集計対象から除外する
- 値がすべて一意なカテゴリ列（グループ化する意味がない列）も対象外にする
- 集計結果は既存の数値列集計と同じく行データより先に配置し、文字数上限で切り詰められても残るようにした
- `scripts/check_ver2420.py` を追加し、実際の売上データに近いテストケースで店舗ごとの合計比較が正しく計算されること、ID列が誤って集計されないこと、同一ターンでの要約・別ターンでの追加質問の両方で参照できることを確認する
- `scripts/run_ver2_checks.py` に `check_ver2420.py` を追加
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持

## Version 2.41

開始内容:

- PowerPoint Reader最小実装を追加
- `requirements.txt` に `python-pptx` / `XlsxWriter` / `Pillow` を追加
- `core/pptx_reader_adapter.py` を追加し、ユーザーが指定した単一の.pptxファイルから、スライドのタイトル・本文・表・ノートのテキストをpython-pptxで抽出できるようにした
- 古い.ppt形式（バイナリ）や破損ファイル、画像だけのスライドは読めたふりをせず正直に失敗を返す
- `core/pptx_reader_confirmation.py` を追加し、他Reader同様に実行前確認を必須にした
- `core/confirmation_intent.py` に `context_type="pptx_reader"` を追加
- `core/personal_ai.py` にPowerPoint Readerを接続し、既存Reader群と同じ「確認 → ToolRunner経由実行 → 本文プレビュー、または要約・質問への直接回答」の流れを追加
- ファイル名に「powerpoint」を含むケースでも問題ないことを確認した（該当キーワード自体が既存の判定ロジックに存在しないため）
- `scripts/check_ver2410.py` を追加
- `scripts/check_ver2290.py` の「対応外拡張子」テストを、.pptxが実装済みになったため.pngに変更
- `scripts/run_ver2_checks.py` に `check_ver2410.py` を追加
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持
- これでOffice系Reader（Word/Excel/PowerPoint）が一通り揃った

## Version 2.40

開始内容:

- 応答の正直さ・Qwen性能・OpenAIエスカレーション方針をdocs化
- 実機テストで、Excel Reader経由の質問に対し、事前計算済みの正しい集計値があるのに受け流すだけで使わない、未実装のグループ集計をQwenが自己流に計算し検証されていない値を断定的に答えてしまう、という2つの問題が見つかった
- これはQwen（qwen3:8b）の推論能力・応答の一貫性に起因する部分が大きいと判断し、今回は修正しない（ユーザーの了承済み）
- ユーザーから、分からない場合は正直に「分からない」と言えるようにすること、Qwen自体の性能向上、精度不足時にOpenAIを頼れるようにすることを将来的に実現してほしいという方針を確認した
- `docs/conversation_quality.md`に「データ分析・集計の正直さ」節を追加
- `MIGRATION.md`の「Qwen / OpenAIの利用方針」に「OpenAIエスカレーションの将来トリガー」節を追加
- これらは会話品質・ModelRouter・OpenAI接続に関わる本格的な設計判断であり、着手する際はあらためてユーザーと設計を確認する方針とした
- `scripts/check_ver2400.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2400.py` を追加
- コード実装は行っていない

## Version 2.39

開始内容:

- CLIに考え中表示を追加
- 実機テストで、Excelの集計質問への応答にQwenが5分以上かかり、何も表示されないため停止したように見える状況が発生した
- トレースバックで確認した結果、`ask_llm`がOllamaからのHTTP応答を待っている最中であり、コードの不具合ではなく、qwen3:8bが実際に処理に時間をかけていたことが分かった
- `core/personal_ai.py`の`run()`に、ユーザー入力受付直後・`handle_user_input`呼び出し前に「Qwenが考え中です。内容によっては数分かかることがあります…」という表示を追加し、処理中であることが分かるようにした
- `scripts/check_ver2390.py` を追加し、表示が入力受付後・応答生成前の正しい位置にあることを確認する
- `scripts/run_ver2_checks.py` に `check_ver2390.py` を追加
- ユーザーから、Qwenで答えられる工夫（今回のExcel自動集計のような設計）を優先しつつ、将来的に必要な場面ではOpenAIを頼れるようにしてほしいという方針を確認した。MIGRATION.mdの既存のQwen / OpenAI利用方針に沿うため、追加のdocs変更は行っていない
- 応答生成ロジックやタイムアウト処理は変更していない

## Version 2.38

開始内容:

- Excel Readerに数値列の自動集計を追加
- 実機テストで、「総売上はいくら」「平均満足度は」のような集計質問に対し、AIが実際に計算せず一般的な説明を繰り返すだけの問題が見つかった
- 原因は、行データをそのままテキストで渡すだけで合計・平均などの値がどこにも計算されておらず、LLMにテキストから再計算させるのは精度が低いこと、かつ大きな表では文字数上限で本文が途中で切れ、全行を見られない場合があること
- `core/excel_reader_adapter.py` に `_build_numeric_column_summary()` を追加し、1行目をヘッダーとみなして数値だけの列について合計・平均・最小・最大・件数をPythonで正確に計算するようにした
- 計算結果は行データより先に配置し、文字数上限で本文が切り詰められても正確な集計値が残るようにした
- 文字列だけの列（店舗名など）は誤って集計しないことを確認した
- `scripts/check_ver2380.py` を追加し、実際の売上データに近いテストケースで合計・平均が正しく計算されること、同一ターンでの要約・別ターンでの追加質問の両方で集計値を参照できることを確認する
- 「一番売上が高い店舗はどこか」のようなグループ集計（店舗ごとの合計比較）は今回のスコープ外とし、今後の課題として残す
- `scripts/run_ver2_checks.py` に `check_ver2380.py` を追加
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持

## Version 2.37

開始内容:

- Excel Reader最小実装を追加
- `requirements.txt` に `openpyxl` / `et-xmlfile` を追加
- `core/excel_reader_adapter.py` を追加し、ユーザーが指定した単一の.xlsxファイルからopenpyxlでシート・セルのテキストを抽出できるようにした
- 数式は評価値ではなく保存済みの計算済み値（data_only=True）を読み取り、マクロは実行しない
- 古い.xls形式（バイナリ）や破損ファイルは読めたふりをせず正直に失敗を返す
- Windowsで`load_workbook(read_only=True)`のファイルハンドルが残る問題を、明示的な`close()`で解消
- `core/excel_reader_confirmation.py` を追加し、他Reader同様に実行前確認を必須にした
- `core/confirmation_intent.py` に `context_type="excel_reader"` を追加
- `core/personal_ai.py` にExcel Readerを接続し、既存Reader群と同じ「確認 → ToolRunner経由実行 → 本文プレビュー、または要約・質問への直接回答」の流れを追加
- ファイル名に「excel」を含むケース（例: excel_report (1).xlsx）でも、Ver2.36で修正済みのキーワード衝突対策により誤判定なく動作することを確認した
- `scripts/check_ver2370.py` を追加
- `scripts/check_ver2290.py` の「対応外拡張子」テストを、.xlsxが実装済みになったため.pptxに変更
- `scripts/run_ver2_checks.py` に `check_ver2370.py` を追加
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持
- 次はPowerPoint Reader（.pptx）を同じ設計パターンで追加予定

## Version 2.36

開始内容:

- Word Reader最小実装を追加
- `requirements.txt` に `python-docx` / `lxml` を追加
- `core/word_reader_adapter.py` を追加し、ユーザーが指定した単一の.docxファイルからpython-docxで段落・表のテキストを抽出できるようにした
- 古い.doc形式（バイナリ）や破損ファイルは読めたふりをせず正直に失敗を返す
- `core/word_reader_confirmation.py` を追加し、Web/File/PDF Reader同様に実行前確認を必須にした
- `core/confirmation_intent.py` に `context_type="word_reader"` を追加
- `core/personal_ai.py` にWord Readerを接続し、既存Reader群と同じ「確認 → ToolRunner経由実行 → 本文プレビュー、または要約・質問への直接回答」の流れを追加
- 開発中に、文書作成判定にある素の「Word」「word」「Excel」「excel」キーワードが、ファイル名自体に含まれる「word」と衝突し、読み取り+要約の同時実行が誤って文書作成モードに入ってしまう不具合を発見（Ver2.30の「ワード」/「キーワード」衝突と同種）
- `core/input_analyzer.py` / `core/capability_manager.py` / `core/tool_request_builder.py` の該当キーワードを、より具体的な語（"Word file"、"Word document"、"in Word"、"Wordで"、"Excel file"、"Excel document"、"in Excel"）に置き換えて修正（Excelも予防的に修正）
- `scripts/check_ver2360.py` を追加し、ファイル名にword/excelを含むケースでの結合テストも含めて確認する
- `scripts/check_ver2290.py` の「対応外拡張子」テストを、.docxが実装済みになったため.xlsxに変更
- `scripts/run_ver2_checks.py` に `check_ver2360.py` を追加
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持
- 次はExcel Reader（.xlsx）、PowerPoint Reader（.pptx）を同じ設計パターンで順次追加予定

## Version 2.35

開始内容:

- 将来の記憶アーキテクチャ方針をdocs化
- ユーザーから、会話・Web検索・File/PDF Readerなどで得た情報を、短期記憶・長期記憶・知識に自動分類し、重要度判定・自動的な忘却判断を行う記憶アーキテクチャを最終的に望んでいるという方針を確認した
- これは `docs/final_product_vision.md` の記憶階層（Raw Log〜Deletion Candidate）の本格実装であり、Reader個別の機能ではなくPersonalAIの記憶機能そのものの本実装として扱う方針を `docs/reader_memory_policy.md` に整理した
- 現在のFile Reader / PDF ReaderはMemory Candidateへ未接続であること、`last_read_document`（Ver2.31）は長期Memoryとは別の暫定キャッシュであることを明記した
- 記憶機能を本格的に作り直すタイミングで、あらためてユーザーと設計を確認する方針とし、それまでの暫定対応はAIエージェントの判断に委ねられた
- コード実装は行っていない

## Version 2.34

開始内容:

- last_read_documentの誤解答を防止
- 実機テストで、2件目のファイル（PDF）を読んだ後に1件目のファイル（テキスト）の内容を聞くと、「他のファイルには記載されていません」と誤って断定する挙動が見つかった
- `last_read_document` は直近1件のみを保持する設計（Ver2.31時点の既知の制約）のため、以前のファイルの本文はもうLLMに渡っていないが、そのことをLLM側に明示していなかったため、不正確な断定応答になっていた
- `build_last_read_document_context()` のsystem message文言を修正し、「これより前に読み取った別のファイルの内容は、この会話ではもう保持していません」「別のファイルにも書かれていないと断定しないでください」を明記
- 実際のバグ再現ケース（2件連続で読み取り、1件目について質問）で、context messageが正しく警告することを確認した
- `scripts/check_ver2340.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2340.py` を追加
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持

## Version 2.33

開始内容:

- ファイルパス抽出のスペース対応バグを修正
- PDF Reader実機テストで、スペースを含むファイル名（Windowsの重複ダウンロードによる「curry_shop_reading_test (1).txt」形式）を指定すると、パスの一部（「(1).txt」）しか読み取られない不具合が見つかった
- 原因は `core/file_reader_adapter.py` と `core/pdf_reader_adapter.py` が、スペースなしの1トークンだけを拾う正規表現（`\S+\.拡張子`）でパスを抽出していたこと
- `core/file_path_extraction.py` を新規作成し、引用符つきパス・ドライブレター始まりのWindows絶対パス（スペースや括弧を含んでもよい）・スペースなしの単純パス、の優先順位で抽出する共通関数 `extract_single_file_path_from_text` を追加
- `file_reader_adapter.py` / `pdf_reader_adapter.py` を、この共通関数を使うようリファクタリング（公開関数名・シグネチャは変更なし）し、同じバグを将来のWord/Excel/PowerPoint Readerで再発させない設計にした
- `core/confirmation_intent.py` の `WEB_READER_CONFIRMED_WORDS` に「イエス」を追加（実機テストで確認できた語彙の抜け）
- 実際のバグ再現ケース（スペースを含む絶対パス）でPersonalAI経由の読み取りが正しく動作することを確認した
- `scripts/check_ver2330.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2330.py` を追加
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持

## Version 2.32

開始内容:

- PDF Reader最小実装を追加
- `requirements.txt` を新規作成し、実際に使用しているパッケージ（ollama、SQLAlchemy、pypdf）を記録
- `core/pdf_reader_adapter.py` を追加し、ユーザーが指定した単一のPDFファイルからpypdfでテキストを抽出できるようにした
- ページ数上限（デフォルト50ページ）・ファイルサイズ上限（デフォルト20MB）を設け、暗号化・破損PDFや画像だけのスキャンPDF（テキストなし）は読めたふりをせず正直に失敗を返す
- `core/pdf_reader_confirmation.py` を追加し、Web/File Reader同様に実行前確認を必須にした
- `core/confirmation_intent.py` に `context_type="pdf_reader"` を追加し、既存の「はい/いいえ」語彙を再利用
- `core/personal_ai.py` にPDF Readerを接続し、Web/File Readerと同じ「確認 → ToolRunner経由実行 → 本文プレビュー、または要約・質問への直接回答」の流れを追加
- 自動チェックでは、手書きで生成した実PDFバイナリを使いpypdfでの実テキスト抽出を確認し、PersonalAI経由の会話フローもfakeのPDF Readerで確認する
- `scripts/check_ver2320.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2320.py` を追加
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持
- 次はWord Reader（.docx）、Excel Reader（.xlsx）、PowerPoint Reader（.pptx）を同じ設計パターンで順次追加予定

## Version 2.31

開始内容:

- Reader結果をQwenでの応答に接続
- File Reader実機テストで、読み取った内容について追加質問できない、「読んで要約して」を同時に実行できないという課題が見つかった
- `core/personal_ai.py` に `last_read_document`（直近に読み取ったWeb Reader / File Readerの本文）を保持する仕組みを追加
- `build_messages()` に `last_read_document` の内容をsystem messageとして注入し、読み取り後の別ターンでの追加質問にも、本文（上限4000文字）をもとに答えられるようにした
- 読み取り依頼に要約・質問などの目的（InputAnalyzerのtask_type）が含まれていた場合、読み取った本文全文をもとにQwenへ直接問い合わせて回答するようにし、「読んで要約して」を同一ターンで実行できるようにした
- 単なる「読んで」だけの依頼は、従来通りの本文プレビュー表示を維持する
- 自動チェックで実LLMを呼ばないよう、`PersonalAI.ask_llm_func`（デフォルトは実際の`ask_llm`）を注入可能にした
- `scripts/check_ver2310.py` を追加し、fakeのLLM関数を使って各シナリオを確認
- `scripts/run_ver2_checks.py` に `check_ver2310.py` を追加
- DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持

## Version 2.30

開始内容:

- File Reader実機テストで見つかった「ワード」/「キーワード」誤判定バグを修正
- ユーザーが実際にFile Readerを試した際、「テストキーワードを教えて」という質問が文書作成依頼として誤って扱われる不具合を発見
- 原因は `core/input_analyzer.py` / `core/capability_manager.py` / `core/tool_request_builder.py` の文書作成判定が、単純な部分一致で「ワード」を検出しており、「キーワード」という単語自体に「ワード」が含まれるため誤爆していたこと
- 3ファイルの該当キーワードを「ワード文書」「ワードで」「ワードファイル」というより具体的な語に修正し、「キーワード」との衝突を解消
- 「Wordで文書を作って」のような実際のWord文書作成依頼は引き続き正しく検出されることを確認
- File Reader自体のロジックは変更していない
- `scripts/check_ver2300.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2300.py` を追加

## Version 2.29

開始内容:

- File Reader最小実装を追加
- `core/file_reader_adapter.py` を追加し、ユーザーが指定した単一のtxt/mdファイルだけを読み取れるようにした
- 対応拡張子はtxt/mdに限定し、ディレクトリ探索・ワイルドカード・書き込み・実行は行わない
- ファイルサイズ上限（デフォルト1MB）を超える場合は読み取らない方針を追加
- `core/file_reader_confirmation.py` を追加し、Web Reader同様に実行前確認を必須にした
- `core/confirmation_intent.py` を汎用化し、`context_type="file_reader"` でもWeb Readerと同じ「はい/いいえ」語彙を再利用できるようにした（Web Reader側の挙動・語彙は変更なし）
- `core/personal_ai.py` にFile Readerを接続し、確認 → ToolRunner経由実行 → 本文プレビュー表示、の流れをWeb Readerと同じ設計で追加
- Ver2.29ではMemory Candidateへの接続はまだ行わない（Web ReaderがVer2.0で辿った最小スコープと同じ段階）
- 対応外拡張子（PDFなど）は、既存のCapabilityManagerによる「未実装」応答にそのまま委ねる
- `scripts/check_ver2290.py` を追加し、一時ディレクトリ内のfakeファイルのみを使ってパス検出・確認・ToolRunner実行・キャンセル・存在しないファイル・対応外拡張子・PersonalAI結合の各シナリオを確認
- 自動チェックでは実際のユーザーファイルへアクセスせず、一時テスト用ファイルのみを使う
- `scripts/run_ver2_checks.py` に `check_ver2290.py` を追加
- DBスキーマ変更、Memory保存・検索ロジック変更、PDF/Image/YouTube Readerの実装は行わない方針を維持

## Version 2.28

開始内容:

- OpenAI利用方針を見直し
- OpenAI機能が今後複数増えると都度確認が煩雑になるとのユーザー指摘を受け、OpenAI利用を「月間上限額を決めた運用」に変更
- OpenAIを初めて実接続する前に月間上限額を決める（初回設定・引き上げは都度ユーザー確認）方針に変更
- 月間上限額の範囲内であれば、通常のOpenAI API呼び出しは都度確認しない方針にした
- APIキーの新規設定・変更、個人情報・機密情報を含む外部送信は、月間上限額の話とは別に引き続き都度ユーザー確認する方針を維持
- 作業や回答の精度を最優先とし、コスト削減のために精度を犠牲にしない方針を明記
- `MIGRATION.md` / `CLAUDE.md` / `AGENTS.md` / `README.md` / `docs/claude_code_start.md` / `docs/llm_intent_resolver_design.md` のOpenAI関連記述を更新
- 実際の月間上限額（具体的な金額）は、OpenAIを実接続する段階で改めてユーザーと決める方針を明記
- `scripts/check_ver2280.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2280.py` を追加
- OpenAI実接続、APIキー設定、DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持

## Version 2.27

開始内容:

- project_handoff.mdの現在バージョン固定依存を解消
- `scripts/check_ver2180.py`〜`scripts/check_ver2260.py`（9本）が`docs/project_handoff.md`の「現在バージョン: VerX.X」を厳密な文字列一致で要求しており、バージョンを上げるたびに過去checkを機械的に追随修正する必要があった問題を解消
- 該当する9本のcheckを、「現在バージョン:」という項目の存在確認に緩和し、具体的なバージョン番号には依存しないよう修正
- 過去の実績を記録する行（例:「Ver2.24: Claude Code引継ぎ確認結果の反映」）は、履歴として引き続き要求する方針を維持
- `scripts/check_ver2270.py` を追加し、対象9本のcheckに固定バージョン番号への依存が残っていないことを継続的に確認
- `scripts/run_ver2_checks.py` に `check_ver2270.py` を追加
- 新機能実装、DBスキーマ変更、Memory保存・検索ロジック変更は行わない方針を維持

## Version 2.26

開始内容:

- LLM Intent Resolver設計を追加
- `docs/llm_intent_resolver_design.md` を新規作成
- LLMは解釈のみを担当し、実行可否はPermissionManager / ToolRunner / 状態管理が最終判断する方針を明記
- 既存のルールベースresolver（`core/confirmation_intent.py`、`core/memory_candidate_confirmation.py`）をLLM呼び出し失敗時のフォールバックとして残す方針を明記
- 固定語彙で判定できる入力はLLMを呼ばないハイブリッド判定で、無駄なAPI消費を避ける方針を明記
- モデル選定はQwenを優先し、精度不足時にOpenAI利用を検討する方針（ユーザー確認必須）を明記
- プロンプト設計 → dry-run → Qwen接続 → 精度確認 → OpenAI検討、という段階的な実装ステップ案を整理
- Ver2.26では設計のみを行い、`core/confirmation_intent.py` / `core/memory_candidate_confirmation.py` の実装変更、LLM呼び出し追加、DBスキーマ変更、Memory保存・検索ロジック変更、OpenAI/Claude/Gemini接続は行わない方針を維持
- `scripts/check_ver2260.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2260.py` を追加

## Version 2.25

開始内容:

- Claude Code自走運用モードを整備
- `CLAUDE.md` を新規作成し、Claude Code向けの短い運用ルール（Project / Read first / Current development mode / User preferences / Autonomous development rules / Confirmation rules / Cost rules / Failure handling / Checks / Git rules / Report format / Next version policy）を整理
- `AGENTS.md` に「Claude Code entrypoint」を追加し、`CLAUDE.md` を最初に読む入口として明記
- `docs/claude_code_start.md` を更新し、初回移行時は本ファイル、継続開発では `CLAUDE.md` / `docs/project_handoff.md` を中心に見る方針を明記
- `MIGRATION.md` に `CLAUDE.md` / `AGENTS.md` / `MIGRATION.md` / `README.md` の役割分担を追記
- README固定Ver表記問題を解消:READMEの「現在はVer2.23です。」という固定文言を、`docs/project_handoff.md` / `docs/changelog.md` を参照する表現に変更
- README内の固定Ver番号を厳密チェックしていた過去check（`check_ver2190.py` / `check_ver2200.py` / `check_ver2210.py` / `check_ver2230.py`）を、README内固定文言ではなく `docs/project_handoff.md` 参照へ緩和し、今後のバージョン更新で過去checkが壊れにくいようにした
- `docs/project_handoff.md` の現在バージョンをVer2.25に更新し、次候補をVer2.26以降にそろえる
- `scripts/check_ver2250.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2250.py` を追加
- LLM Intent Resolver、File Reader、PDF Reader、Image Reader、YouTube Reader、Office/メール/カレンダー連携、DBスキーマ変更、Memory保存・検索ロジック変更、OpenAI/Claude/Gemini接続、GUI、PC操作は今回実装しない方針を維持

## Version 2.24

開始内容:

- Claude Code引継ぎ確認結果をdocsへ反映
- Claude Codeが AGENTS.md、MIGRATION.md、README.md、docs/development_workflow.md、docs/project_handoff.md、docs/check_workflow.md、docs/changelog.md、docs/portfolio_readme_policy.md、docs/demo_logs/web_reader_memory_candidate_demo.md を読み、目的・実装済み機能・未実装スコープ・開発スタイル・コスト方針・失敗時対応・致命的リスク・次Ver候補を正しく把握したことを確認
- `docs/claude_code_start.md` の「Ver2.22まで完了」という古い表記をVer2.24に修正
- 最初の引継ぎ確認ではユーザー指示により `run_ver2_checks.py` を実行せず、git status / git log / docs読み取りだけを行ったことを補足
- `MIGRATION.md` のロードマップに残っていた古いVer2.22候補の重複を整理し、Ver2.25 / Ver2.26 / Ver2.x候補にそろえる
- `MIGRATION.md` のコスト方針に、金額ラインが未確定であり有料API利用前にユーザーとすり合わせる方針を追記
- `MIGRATION.md` / `README.md` / `docs/project_handoff.md` / `docs/claude_code_start.md` にQwen / OpenAIの利用方針を追加し、OpenAI API利用・APIキー設定・外部送信・課金は必ずユーザー確認する方針を明記
- `docs/project_handoff.md` の現在バージョンをVer2.24に更新し、次候補をVer2.25以降にそろえる
- `scripts/check_ver2240.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2240.py` を追加
- LLM Intent Resolver、File Reader、PDF Reader、Image Reader、YouTube Reader、Office/メール/カレンダー連携、DBスキーマ変更、Memory保存・検索ロジック変更、OpenAI/Claude/Gemini接続、GUI、PC操作は今回実装しない方針を維持

## Version 2.23

開始内容:

- Claude Code移行準備を整理
- `docs/claude_code_start.md` を追加
- Claude Codeが最初に実行するコマンドと読むファイル順を明記
- ユーザー対応方針、コスト方針、失敗時対応、致命的リスクを短い開始手順として整理
- 移行後の最初の作業を「引継ぎ確認」にする方針を明記
- `scripts/check_ver2230.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2230.py` を追加

## Version 2.22

開始内容:

- READMEをポートフォリオ向けに整理
- Mermaidによるアーキテクチャ図と処理フローを追加
- Web Reader → Memory Candidate → 保存 → 検索 のデモ導線を強化
- 技術的に工夫した点を面接で説明しやすい形に整理
- `docs/portfolio_readme_policy.md` を追加
- `scripts/check_ver2220.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2220.py` を追加

## Version 2.21

開始内容:

- `MIGRATION.md` を追加
- Claude Code / Cursor への開発環境移行用の引継書を作成
- 実装済み機能、未実装機能、安全ルール、開発コマンドを整理
- README / project_handoff / development_workflow / check_workflow を移行方針に合わせて更新
- `scripts/check_ver2210.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2210.py` を追加
- `MIGRATION.md` にPersonalAIの最終利用スコープを追加
- 画像、音声、動画、Office、創作支援、予定管理、メールなどは将来スコープとして整理
- 具体的な外部ツール名は固定ではなく、用途や開発段階に応じて選ぶ方針を明記
- ユーザー適応仕様、開発コスト方針、失敗時の対応方針を `MIGRATION.md` に追記
- 致命的リスク中心の安全管理、無駄なAPI消費を避ける方針、必要な課金は理由を説明して検討する方針を整理
- `AGENTS.md` と `docs/development_workflow.md` に、移行先AIエージェント向けのユーザー対応方針を追記

## Version 2.20

開始内容:

- Memory検索の最小実用化を追加
- `core/memory_search.py` を追加し、保存済みMemoryをキーワード検索できる土台を作成
- `覚えてる？` / `記憶ある？` / `Memoryを探して` などの簡易Intent抽出を追加
- 直近保存Memory確認と、保存済みMemory全体の検索を分離
- DBスキーマ変更はしない方針を維持
- 自動チェックではfake検索を使い、実DB保存や実Webアクセスを行わない
- `scripts/check_ver2200.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2200.py` を追加

## Version 2.19

開始内容:

- 確認待ち状態の文脈解釈を改善
- `core/confirmation_intent.py` を追加し、confirmation intentをルールベースで分離
- Web Reader確認待ち中の `いいよ` / `お願いします` / `OKです` などを実行許可として扱う
- Web Reader確認待ち中の `キャンセル` / `やめて` / `今回はいい` などを拒否として扱う
- 確認待ち中に不明な入力が来た場合、通常会話へ流さず確認を聞き直す
- Memory Candidate確認応答に、保存・拒否・保留・編集の自然表現を追加
- Web Reader未対応という誤解を避ける返答へ調整
- LLM解釈はまだ実装しない方針を維持
- `scripts/check_ver2190.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2190.py` を追加

## Version 2.18

開始内容:

- Memory保存後の確認・表示フローを追加
- Memory Candidate保存成功後の返答に保存内容プレビューを表示
- 直近保存したMemoryを会話内で確認できる基礎を追加
- `今保存した記憶を確認して` などの入力で直近保存内容を表示
- `last_saved_memory_candidate_result` で保存成功結果を保持
- 編集済みMemory Candidate保存後も編集後summaryを確認表示に反映
- DBスキーマ変更はしない方針を維持
- 自動チェックではfake保存・fake記憶確認を使い、実DB保存しない
- `scripts/check_ver2180.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2180.py` を追加

## Version 2.17

開始内容:

- Memory Candidateのユーザー確認つき保存を追加
- ユーザーが明示的に `保存する` と答えた場合だけ、低リスク候補を保存対象にする
- `core/memory_candidate_saver.py` を追加
- Memory Candidateを既存の長期記憶保存機構へ渡せる保存用テキストに変換
- 編集済みMemory Candidateも保存対象にできるようにした
- 高リスク候補はVer2.17では自動保存しない
- DBスキーマ変更はしない方針を維持
- 自動チェックでは実DB保存しない方針を維持
- `scripts/check_ver2170.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2170.py` を追加

## Version 2.16

開始内容:

- Memory Candidate編集dry-runを追加
- `編集して保存` の後に、次のユーザー入力を編集内容として受け取る流れを追加
- 編集内容を反映した編集済みMemory Candidateをdry-run保持
- `pending_memory_candidate_edit` で編集待ち状態を管理
- `core/memory_candidate_confirmation.py` に編集応答解釈を追加
- まだMemory保存はしない方針を維持
- Memory CandidateのDB保存もしない方針を維持
- DBスキーマ変更はしない方針を維持
- `scripts/check_ver2160.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2160.py` を追加

## Version 2.15

開始内容:

- ポートフォリオREADMEを整備
- `README.md` を就活ポートフォリオ向けに追加
- `docs/portfolio_notes.md` を追加
- `docs/demo_logs/web_reader_memory_candidate_demo.md` を追加
- Web Reader から Memory Candidate dry-run までのデモログを整理
- 実装済み機能と未実装機能を分けて記載
- MIGRATION.mdはまだ作らない方針を維持
- `scripts/check_ver2150.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2150.py` を追加

## Version 2.14

開始内容:

- 開発自走方針をリポジトリに反映
- `AGENTS.md` を追加
- `docs/development_workflow.md` を追加
- 後から修正できる通常作業はユーザー確認なしで進める方針を明記
- 通常の `git add` / `git commit` / `git push` は確認不要とする方針を明記
- 不可逆操作、DB削除、Memory物理削除、課金、外部送信は確認必須とする方針を明記
- `MIGRATION.md` はVer2.14ではまだ作らない方針を明記
- `scripts/check_ver2140.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2140.py` を追加

## Version 2.13

開始内容:

- Memory Candidate確認応答のdry-runを追加
- `core/memory_candidate_confirmation.py` を追加
- 保存する / 保存しない / 編集して保存 / 後で確認 の応答を解釈
- Web Reader成功後のMemory Candidate pendingに確認応答dry-runを軽く接続
- 「保存する」と言われてもdry-runで止める
- まだMemory保存はしない方針を維持
- DBスキーマ変更はしない方針を維持
- Memory CandidateのDB保存もしない方針を維持
- 自動チェックでは実Webアクセス・LLM実行・DB書き込みをしない
- `scripts/check_ver2130.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2130.py` を追加

## Version 2.12

開始内容:

- Memory Candidate確認UI方針をdocs化
- `docs/memory_candidate_ui_policy.md` を追加
- 保存前にユーザーが確認できる形を整理
- 保存 / 保存しない / 編集 / 後で確認 の選択肢を整理
- 高リスク候補は自動保存しない方針を明記
- まだMemory保存はしない方針を維持
- DBスキーマ変更はしない方針を維持
- Memory CandidateのDB保存もしない方針を維持
- `scripts/check_ver2120.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2120.py` を追加

## Version 2.11

開始内容:

- Memory CandidateをWeb Reader結果にdry-run接続
- Web Reader成功時に保存候補を作る
- Web Reader成功時の返答にMemory Candidate dry-run情報を短く表示
- 失敗時・未実行時はMemory Candidateを作らない
- まだMemory保存はしない方針を維持
- DBスキーマ変更はしない方針を維持
- Memory CandidateもDB保存しない方針を維持
- 自動チェックではfake fetcherを使い、実Webアクセスしない
- `scripts/check_ver2110.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2110.py` を追加

## Version 2.10

開始内容:

- Memory Candidate生成のdry-runを追加
- `core/memory_candidate.py` を追加
- Reader結果から保存候補を作る土台を追加
- `scripts/check_ver2100.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver2100.py` を追加
- まだMemory保存はしない方針を維持
- DBスキーマ変更はしない方針を維持
- Web Reader本体にはまだ自動接続しない方針を維持
- 自動チェックでは実Webアクセス・LLM実行・ToolRunner実行・DB書き込みをしない

## Version 2.9

開始内容:

- Reader結果のMemory保存方針をdocs化
- `docs/reader_memory_policy.md` を追加
- Reader結果から保存する候補、保存しないもの、保存前確認が必要な条件を整理
- Memory Candidate / Project Knowledge / User Preference / Archive の扱いを整理
- Memory保存の本実装はまだしない方針を維持
- Web Reader結果のMemory保存はまだしない方針を維持
- `scripts/check_ver290.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver290.py` を追加

## Version 2.8

開始内容:

- Web Reader結果の会話品質を改善
- 成功時の返答を見やすくした
- 本文プレビューの余分な空白を整理し、長すぎる場合は短く表示するようにした
- 失敗時に読めたふりをしない方針を維持
- 自動チェックではfake fetcherを使い、実Webアクセスしない方針を維持
- Reader結果のMemory保存はまだしない方針を維持
- `scripts/check_ver280.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver280.py` を追加

## Version 2.7

開始内容:

- 完成形ビジョンをdocs化
- `docs/final_product_vision.md` を追加
- `docs/conversation_policy.md` を追加
- 高自律・記憶・ModelRouter / ToolRouter・自己アップデート・自律調査方針を整理
- 会話品質・返答方針を整理
- 実装はまだ行わない方針を維持
- `scripts/check_ver270.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver270.py` を追加

## Version 2.6

開始内容:

- Web Reader実Web手動テスト結果をdocsへ整理
- `https://example.com` を会話UIから読み取り、`Example Domain` と `text_preview` が返ったことを記録
- 自動チェックではfake fetcherを使い、実Webアクセスしない方針を維持
- Reader結果のMemory保存はまだしない方針を維持
- PDF / Image / YouTube / File Reader は今後の段階追加として維持
- `scripts/check_ver260.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver260.py` を追加

## Version 2.5

開始内容:

- `user_confirmed=True` 後にToolRunner経由でWeb Readerを実行する接続を追加
- URL検出だけでは実行せず、保留中の確認に対する肯定応答がある場合だけ実行
- 成功時にtitle / final_url / text_previewを会話返答へ含める
- 失敗時に読めたふりをせず、失敗理由を返す
- 自動チェックではfake fetcherを使い、実Webアクセスしない方針を維持
- `scripts/check_ver250.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver250.py` を追加

## Version 2.4

開始内容:

- Web Reader確認応答の前段処理を整理
- 肯定・否定・別話題・pendingなしをdry-run結果として扱えるようにした
- 肯定時にToolRequest候補を作れるようにした
- ただしWeb Reader実行、ToolRunner呼び出し、run_tool_request呼び出し、fetch実行はまだ行わない
- `scripts/check_ver240.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver240.py` を追加

## Version 2.3

開始内容:

- URL確認メッセージを会話返答として表示するdry-run接続を追加
- `core/personal_ai.py` でWeb Reader確認メッセージを返せるようにした
- ユーザーが「はい」と答えてもWeb Reader実行には進まない方針を維持
- ToolRunnerを会話UIから呼ばず、WebReaderAdapterのfetchも実行しない方針を維持
- `scripts/check_ver230.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver230.py` を追加

## Version 2.2

開始内容:

- URL入力検出から確認メッセージ生成までのdry-runを追加
- `core/web_reader_confirmation.py` を追加
- Web Reader実行前確認メッセージを作れるようにした
- ToolRunnerを呼ばず、WebReaderAdapterのfetchも実行しない方針を維持
- 会話UIへの実接続はまだ行わない方針を維持
- `scripts/check_ver220.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver220.py` を追加

## Version 2.1

開始内容:

- Web Reader手動実行テスト手順を整理
- Web Readerの会話UI接続方針を整理
- `user_confirmed` と自動Webアクセス禁止方針を再確認
- `docs/web_reader_manual_test.md` を追加
- `docs/web_reader_ui_connection_plan.md` を追加
- `scripts/check_ver210.py` を追加
- `scripts/run_ver2_checks.py` に `check_ver210.py` を追加

## Version 2.0

開始内容:

- Web Reader最小実用版を追加
- WebReaderAdapter を追加
- URL抽出とHTMLテキスト化の基礎を追加
- Permission確認なしではWebアクセスしないToolRunnerを追加
- Web Reader結果を ToolResult と ToolExecutionLog に接続
- 自動checkではfake fetcherを使い、実Webアクセスしない方針を追加
- `scripts/check_ver200.py` を追加
- `scripts/run_ver2_checks.py` を追加
- `docs/web_reader_design.md` を追加

## Version 1.10

開始内容:

- Ver1.x総仕上げ確認を追加
- Ver1.1からVer1.9までの実装内容を整理
- Ver2.0 Reader実装前の準備状態を確認
- Ver2.0でやること / やらないことを再確認
- Web Readerを最初の実装候補として再確認
- `docs/ver1_x_final_review.md` を追加
- `scripts/check_ver1100.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver1100.py` を追加

## Version 1.9

開始内容:

- Ver2.0 Reader実装計画を整理
- Ver2.0を付ける条件をdocs化
- Readerの実装順序を整理
- Web Readerを最初の実装候補として整理
- PDF / Image / YouTube / File Reader の段階的追加方針を整理
- Reader共通の ToolRequest / ToolResult / Permission / ToolExecutionLog 方針を整理
- `docs/reader_implementation_plan_v2.md` を追加
- `scripts/check_ver190.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver190.py` を追加

## Version 1.8

開始内容:

- Reader実装前の手動テストケースを整理
- 通常会話 / URL / YouTube / PDF / Image / File / Document / PC操作の期待挙動をdocs化
- ToolRequest dry-run / ToolPermission / ToolExecutionLog の確認観点を整理
- 未実装Toolを実行したふりしないためのテスト観点を追加
- `docs/reader_pre_implementation_test_cases.md` を追加
- `scripts/check_ver180.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver180.py` を追加

## Version 1.7

開始内容:

- Tool実行ログと結果記録の設計を追加
- ToolExecutionRecord を追加
- ToolExecutionLogger を追加
- build_tool_execution_record を追加
- ToolRequest / ToolPermissionDecision / ToolResult をまとめて記録できる土台を追加
- executed=False を明確に記録する方針を追加
- DB保存はまだ行わない方針をdocs化
- `docs/tool_execution_log_design.md` を追加
- `scripts/check_ver170.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver170.py` を追加

## Version 1.6

開始内容:

- Reader実装前のInputAnalyzer / Capability / Tool連携確認を追加
- ToolRequestDecision を追加
- build_tool_request_decision を追加
- 通常会話ではToolRequestを作らない方針を追加
- Reader系入力ではToolRequestを作るが実行しないdry-run方針を追加
- `docs/tool_input_integration.md` を追加
- `scripts/check_ver160.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver160.py` を追加

## Version 1.5

開始内容:

- PermissionManagerとTool実行前確認の接続準備を追加
- ToolPermissionDecision を追加
- evaluate_tool_permission を追加
- build_permission_message を追加
- ToolRequest の requires_permission / risk_level を使った判定方針を追加
- 未許可ならToolを実行しない方針をdocs化
- `docs/tool_permission_design.md` を追加
- `scripts/check_ver150.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver150.py` を追加

## Version 1.4

開始内容:

- Reader追加前のTool / Adapter受け口を整理
- ToolRequest / ToolResult / ToolAdapter を追加
- ToolRegistry を追加
- 未実装Toolを実行したふりせず扱う方針を追加
- `docs/tool_adapter_design.md` を追加
- `scripts/check_ver140.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver140.py` を追加

## Version 1.3

開始内容:

- 会話品質方針を追加
- 通常会話では短めで自然に返す方針を追加
- 相談では結論、理由、選択肢を整理する方針を追加
- 開発補助では手順、変更対象、確認コマンド、注意点を明確にする方針を追加
- 不明点を断定しない方針を追加
- `ai/conversation_quality_policy.py` を追加
- `scripts/check_ver130.py` を追加
- `scripts/run_ver1_checks.py` に `check_ver130.py` を追加

## Version 1.2

開始内容:

- Ver1.x用チェック運用を整理
- quick check / standard check / full pre-release check の考え方を追加
- `scripts/run_ver1_checks.py` を追加
- `scripts/check_ver120.py` を追加
- Ver1.xのcheck番号方針をdocsに整理

## Version 1.1

開始内容:

- 通常会話でMemory情報を使いすぎないように調整
- Memory利用方針 minimal / normal / detailed を追加
- 明示的な記憶参照ではMemoryを詳しく使い、通常会話では控えめに使う方針を追加
- Preference情報を雑談に毎回混ぜない方針を追加
- `ai/memory_usage_policy.py` を追加
- `scripts/check_ver110.py` を追加

## Version 1.0 Final Preparation

開始内容:

- `docs/version_1_0_release_decision.md` の総合判定を GO に更新
- Git状態をOKに更新
- Ver1.0直前の最終自動check、benchmark、app起動確認を実施
- Ver1.0は完成版ではなく、最低限の会話・記憶・安全確認・未実装機能の正直な扱いをテストできる実用テスト版として位置づけ
- `scripts/check_v1_final_preparation.py` を追加
- 今回はまだVer1.0タグやGitHub Releaseは作成しない

## Version 0.31

開始内容:

- Ver0.30で保留だった通常会話2件と記憶参照1件をOKに更新
- `docs/version_1_0_release_decision.md` の総合判定を GO候補 に更新
- 通常会話でMemory情報を使いすぎる傾向をVer1.1以降の改善候補として記録
- `scripts/check_ver031.py` を追加
- 今回はまだVer1.0タグやGitHub Releaseは作成しない
- コード機能本体、DB削除、Memory物理削除、Git commit / push は行わない

## Version 0.30

開始内容:

- Ver1.0直前の手動テスト表を実測に基づいて更新
- `docs/version_1_0_release_decision.md` の判定欄を更新
- `scripts/check_ver030.py` を追加
- Ver1.0前の自動check、benchmark、manual test、未実装機能の扱い、Memory安全性、docs最新性を確認
- 今回はまだVer1.0タグやGitHub Releaseは作成しない
- コード機能本体、DB削除、Memory物理削除、Git commit / push は行わない

## Version 0.29

開始内容:

- `docs/version_policy.md` を追加
- 整数バージョンを「実用的に使える区切り」として扱う方針を整理
- Ver1.0〜Ver6.0の大まかな役割を整理
- Ver4.0とVer5.0の違いを整理
- GO / HOLD / NO-GO とメジャーバージョン更新の関係を整理
- `scripts/check_ver029.py` を追加
- 今回はコード機能本体を変更せず、長期開発に向けたバージョン管理方針をdocsとして明文化

## Version 0.28

開始内容:

- `docs/version_1_0_release_decision.md` を追加
- `scripts/check_ver028.py` を追加
- Ver1.0へ進めるGO / HOLD / NO-GO条件を整理
- Ver1.0後に回す作業を整理
- Ver1.0直前の推奨確認手順を整理
- 今回はコード機能本体を変更せず、Ver1.0へ進む前の判定基準をdocsとして明文化

## Version 0.27

開始内容:

- `docs/version_1_0_final_check.md` を追加
- `scripts/run_pre_v1_checks.py` を追加
- `scripts/check_ver027.py` を追加
- Ver1.0前の自動チェック、ベンチマーク、手動テスト、Git確認の順番を整理
- Ver1.0へ進める判定基準を整理
- `run_pre_v1_checks.py` はVer0.11〜Ver0.26のcheckと軽量性ベンチマークを順番に実行し、最後に結果を集計する
- 今回はコード機能本体を変更せず、docs整備と確認スクリプト追加として実施

## Version 0.26

開始内容:

- `docs/future_app_integrations.md` を追加
- `docs/version_1_0_manual_test.md` を追加
- 将来的に対応したい制作系・日常系・読み取り系・操作系アプリを整理
- Tool / Adapter形式で後から追加しやすくする方針を整理
- インストール、購入、外部投稿、配信開始、ファイル削除などは必ず許可を取る方針を整理
- Ver1.0前の手動テスト表を追加
- `scripts/check_ver026.py` を追加し、docsの存在、重要語、importを確認できるようにした
- 今回はコード機能本体を変更せず、docs整備と確認スクリプト追加として実施

## Version 0.25

開始内容:

- 軽量性ベンチマークを追加
- `scripts/benchmark_lightweight.py` を追加し、主要処理時間を測定できるように変更
- PersonalAI import時間、初期化時間、Capability判定時間、Preference抽出時間、Preference確認判定時間を測定
- MemoryContext生成時間と自動忘却dry-run時間を測定
- `scripts/check_ver025.py` を追加し、benchmarkスクリプトの存在と実行を確認
- `docs/performance_benchmark.md` を追加
- 今回は高速化ではなく、測定できる状態にすることを目的として実施
- Qwen / Ollama問い合わせ、外部通信、DB削除、Memory物理削除、`is_active` 変更は行わない方針を維持

## Version 0.24

開始内容:

- 自動忘却dry-runを追加
- `ai/memory_forgetting.py` を追加し、忘却候補をスコア方式で判定できるように変更
- `analyze_forgetting_candidates()` を追加
- `get_forgetting_candidates()` を追加
- 低重要度、低信頼度、一時記憶、test/debug系、期限切れ記憶を候補にしやすくする方針を追加
- ユーザー基本情報、Preference、project、core方針、高重要度・高信頼度の記憶を候補にしにくくする方針を追加
- dry-run結果に `dry_run=True`、`recommended_action`、`score`、`reasons` を含めるように変更
- `scripts/check_ver024.py` を追加し、synthetic memoryとDB読み取りdry-runを確認
- 物理削除、自動 `is_active=False`、ユーザー確認なしの忘却は行わない方針を明文化

## Version 0.23

開始内容:

- Capability判定を強化
- `CapabilityManager.analyze()` を追加し、入力に必要な能力と不足機能を判定できるように変更
- 通常会話、記憶参照、記憶保存、Preference記憶を現在対応可能な能力として分類
- Web / YouTube / PDF / 画像 / ファイル読み取り / 文書作成 / PC操作 / 外部API / OpenAI候補を必要能力として分類
- 未実装機能が必要な場合は、読んだふり・実行したふりをせず、`user_message` で正直に返す方針を追加
- PersonalAI本体にCapability判定を接続し、Planner / Router / Executorへ進む前に未実装機能を止めるように変更
- `scripts/check_ver023.py` を追加し、Capability判定とPersonalAI統合を確認
- CapabilityManagerは「できるかどうか」、PermissionManagerは「実行してよいか」を判断する役割として整理

## Version 0.22

開始内容:

- 確認質問後にPreference保存を続行する仕組みを追加
- PersonalAIが1件だけ `pending_preference_confirmation` を保持できるように変更
- pendingはPersonalAIインスタンス内のみで保持し、DBには保存しない方針を採用
- `resolve_preference_confirmation_answer()` を追加し、確認回答を `save_primary`、`save_addition`、`save_change`、`cancel`、`ask_again` に分類
- `save_resolved_preference_confirmation()` を追加し、確認回答後にPreferenceを保存できるように変更
- 一番好きな食べ物を `preference:food:primary` で保存する方針を追加
- `scripts/check_ver022.py` を追加し、回答解決、保存、PersonalAI pending flowを確認
- 完全な自然言語理解、長期的なpending DB保存、複数同時保留、OpenAI接続、Vector DB、Embedding検索は今後の課題として維持

## Version 0.21

開始内容:

- `docs/project_handoff.md` を追加
- `docs/recovery_guide.md` を追加
- `docs/core_principles.md` を追加
- ChatGPT / Codex / VS Code の履歴が消えても再開しやすいようにした
- PersonalAIの最終目標、安全方針、開発方針、回答精度重視の方針を明文化した
- `scripts/check_ver021.py` を追加し、引き継ぎ・復旧・原則docsの存在と重要語を確認できるようにした
- 今回は機能追加ではなく、プロジェクト継続性を高めるためのドキュメント整備として実施

## Version 0.20

開始内容:

- Preference矛盾時の確認質問設計を追加
- `ai/preference_confirmation.py` を追加し、Preference保存前に確認質問が必要か判定できるように変更
- `analyze_preference_confirmation()` を追加
- 好きなものの単純追加では確認しない方針を追加
- 明確な「好きじゃない」「嫌い」は確認せず更新してよい方針を追加
- 「一番好き」「今は / 前は」「変更」は確認候補にする方針を追加
- `core/personal_ai.py` にPreference保存前の確認判定を接続
- `scripts/check_ver020.py` を追加し、確認不要/確認必要の判定とVer0.19抽出維持を確認
- `docs/preference_confirmation.md` を追加し、確認しすぎない方針を整理
- 完全な自然言語理解、LLMによる高度な矛盾判定、自動忘却、OpenAI接続、ベクトルDB、Embedding検索は今後の課題として維持

## Version 0.19

開始内容:

- Preference記憶・矛盾記憶の最小実装を追加
- `ai/preference_memory.py` を追加し、明確な「好き」「好きじゃない」「嫌い」を抽出できるように変更
- `extract_preference_memories()` と `save_preference_memories()` を追加
- `memory_key=preference:food:<target>` により、同じ対象の現在Preferenceを更新できるように変更
- 好きな対象が複数ある場合は、別memory_keyとして複数保持できる方針を追加
- `core/personal_ai.py` にPreference記憶の最小接続を追加
- `scripts/check_ver019.py` を追加し、like / not_like / dislike の抽出・保存・更新を確認
- `docs/preference_memory.md` を追加し、記憶確認をしすぎない方針を整理
- 完全な自然言語理解、複雑なPreference抽出、自動忘却、OpenAI接続、ベクトルDB、Embedding検索は今後の課題として維持

## Version 0.18

開始内容:

- 無効化MemoryのMemoryContext反映確認を追加
- `scripts/check_ver018.py` を追加し、activeなMemoryがContextに出ること、無効化後に出ないこと、復元後に戻ることを確認
- inactiveなMemoryを直接 `build_memory_context()` に渡しても出力されないことを確認
- `docs/version_1_0_test_plan.md` を追加し、Ver1.0の位置づけとテスト計画を整理
- Ver1.0は完成版ではなく、最低限の会話・記憶・安全確認をテストできる実用テスト版と定義
- Preference記憶、矛盾記憶、記憶確認頻度、自動忘却、Capability判定、ユーザー応答調整、軽量性評価を今後の重要項目として整理
- Memory内容の編集、物理削除、自動忘却、OpenAI接続、Web/PDF/YouTube読み取り、Ver1.0本体への昇格は今後の課題として維持

## Version 0.17

開始内容:

- Memoryの手動無効化・復元機能を追加
- `database.memory_manager` に `get_memory_by_id()` と `set_memory_active()` を追加
- `scripts/manage_memory_status.py` を追加し、ID指定でMemoryを無効化・復元できるように変更
- `manage_memory_status.py` はデフォルトdry-runとし、実際に変更する場合は `--apply` を必須にした
- 無効化は `is_active=False`、復元は `is_active=True` とし、Memoryの物理削除は行わない
- 実行前に対象Memoryの内容を表示する安全確認を追加
- `scripts/check_ver017.py` を追加し、dry-run、無効化apply、復元applyを確認できるように変更
- Memory内容の編集、物理削除、自動無効化、短期記憶、Knowledge DB、ベクトルDB、Embedding検索の本格実装は今後の課題として維持

## Version 0.16

開始内容:

- Memory一覧・手動確認用スクリプトを追加
- `scripts/list_memories.py` を追加し、現在DBの長期記憶をブロック形式で一覧表示できるように変更
- `--limit`、`--memory-type`、`--category`、`--scope`、`--active-only`、`--include-inactive`、`--search` の簡易オプションを追加
- `scripts/check_ver016.py` を追加し、Memory一覧表示スクリプトの基本動作とフィルタ動作を確認できるように変更
- 一覧表示スクリプトは読み取り専用で、記憶の削除・更新・無効化は行わない方針を維持
- 記憶編集、無効化、削除、短期記憶、Knowledge DB、ベクトルDB、Embedding検索の本格実装は今後の課題として維持

## Version 0.15

開始内容:

- MemoryContextの実用確認・デバッグ機能を追加
- `scripts/show_memory_context.py` を追加し、現在DBの長期記憶からMemoryContextを表示できるように変更
- `show_memory_context.py` に `--limit`、`--category`、`--scope` の簡易オプションを追加
- `scripts/check_ver015.py` を追加し、MemoryContext生成とプレビュー用スクリプトの基本動作を確認できるように変更
- 既存記憶を削除・更新しない読み取り専用の確認スクリプトとして実装
- 短期記憶、Knowledge DB、ベクトルDB、Embedding検索の本格実装は今後の課題として維持

## Version 0.14

開始内容:

- MemoryContextを強化
- 長期記憶をカテゴリ別に整理してLLMへ渡すように変更
- `category` と `scope` を使い、ユーザー情報、好み・方針、プロジェクト、現在の作業、知識、その他へ分類
- `importance`、`confidence`、`scope`、`memory_key` をsystem message上で確認できるように変更
- `is_active=False` の記憶をLLMへ渡さないように変更
- `confidence < 50` の記憶に `低確信` 表示を追加
- MemoryContextの長さが伸びすぎないよう、全体件数と分類ごとの件数に上限を追加
- Ver0.14確認用スクリプト `scripts/check_ver014.py` を追加
- 短期記憶、知識DB、ベクトルDB、Embedding検索の本格実装は今後の課題として維持

## Version 0.13

開始内容:

- Memory設計を強化
- `memories` テーブルに `memory_key`、`subcategory`、`scope`、`confidence`、`updated_at`、`expires_at`、`is_active` を追加
- 既存DBを削除せず、足りない列だけを追加する安全なマイグレーションを追加
- `save_memory()` が `memory_key` による更新に対応
- `project`、`preference`、`goal`、`personality`、`other`、`knowledge` は、memory_keyがない場合にcategoryだけで上書きしない方針へ変更
- `get_memories()` に `memory_type`、`category`、`scope`、`active_only` の絞り込みを追加
- 記憶抽出プロンプトに任意項目として `memory_key`、`subcategory`、`scope`、`confidence` を追加
- Memory設計書 `docs/memory.md` を追加
- Ver0.13確認用スクリプト `scripts/check_ver013.py` を追加
- 短期記憶、知識、ベクトルDB、embedding検索の本格分離は今後の課題として維持

## Version 0.12

開始内容:

- Permission / Risk基礎を追加
- `core/permission_manager.py` を追加
- PersonalAI本体にPermissionManagerを接続
- Executor実行前にPermissionManagerの判断を通すように変更
- `self.last_permission_decision` を保存
- 許可が必要な操作は現時点では実行せず `blocked=True` とする方針を追加
- Ver0.12確認用スクリプト `scripts/check_ver012.py` を追加
- 実際の許可取得・許可後の再実行は今後の課題として維持

## Version 0.11

開始内容:

- Clarification基礎を追加
- 情報不足時に `ask_clarification` action を返すようにPlannerを更新
- YouTube / Web / PDF / 画像などの対象が不足している場合に追加質問するように変更
- Routerが `ask_clarification` を安全にQwenへルーティングするように更新
- Executorが必要最小限の固定質問文を返すように更新
- Ver0.11確認用スクリプト `scripts/check_ver011.py` を追加
- ClarificationManagerとしての本格分離は今後の課題として維持

## Version 0.10

開始内容:

- InputAnalyzer結果をPlannerのaction判定に反映
- YouTube URL + 要約を `summarize_youtube` に分類
- URL + 要約を `summarize_url` に分類
- 文書作成依頼を `create_document` に分類
- おすすめ依頼を `recommend`、質問を `answer_question` に分類
- Routerが新しいactionを安全にQwenへルーティングするように更新
- Executorが未実装の外部読み取り・実ファイル作成で読んだふり、作ったふりをしない固定メッセージを返すように更新

## Version 0.9.2

整理内容:

- docs/vision.mdを追加
- PersonalAIの完成形を「ユーザーが使う唯一のAI・作業入口」として明文化
- 短期記憶・長期記憶・知識の3層構造を整理
- 自律性と許可制の方針を整理
- 将来的にPersonalAI自身がコード実装・動作確認・Git管理まで行う方針を整理
- 開発中はChatGPT/Codex/Gitなどを使い、完成まではPersonalAIを普段使いしない方針を明記

## Version 0.9.1

整理内容:

- docsを現在のVer0.9状態に合わせて更新
- app_buckup.pyを旧テスト用コードとしてlegacy/app_buckup.pyへ移動
- .agentsフォルダは現時点ではPersonalAI本体で未使用であり、削除しない方針を明記
- system promptを整理し、記憶にないことを断定しない方針と未実装の外部読み取りを読んだふりしない方針を追加
- DBリセット手順をdocs/db_reset.mdに追加
- InputAnalyzerの判定語彙を少し追加
- 既存の会話、記憶、Qwen実行機能を壊さない安定化回として整理

## Version 0.9

開始内容:

- InputAnalyzerクラス追加
- ユーザー入力をinput_type、task_type、URL有無などに構造化
- InputAnalyzerをPersonalAI内部に接続
- 解析結果をself.last_input_analysisに保存
- まだWebやYouTubeの実読み取りは行わない方針を維持

## Version 0.8

開始内容:

- ExecutorをPersonalAI内部に接続
- PersonalAIからの直接 ask_llm 呼び出しを廃止
- planとrouteをExecutorへ渡し、ExecutorがQwen実行を担当する形へ変更
- 既存の会話履歴保存・記憶抽出・記憶保存フローを維持

## Version 0.7

開始内容:

- Executorクラス追加
- Executor設計書追加
- target=qwen のとき Qwen を実行する土台を追加
- target=openai_candidate のとき未実装メッセージを返す方針を追加

## Version 0.6

開始内容:

- Plan / Route データモデル追加
- PlannerがdictではなくPlanを返すように変更
- RouterがdictではなくRouteを返すように変更
- Routerは既存のdict形式planにも最低限対応

## Version 0.5

開始内容:

- CapabilityManager、Planner、RouterをPersonalAI内部に接続
- planとrouteを生成しつつ、既存のQwen回答生成フローを維持
- まだExecutorやOpenAI呼び出しは行わない方針を維持

## Version 0.4

開始内容:

- Router設計書追加
- Routerクラス追加
- ModelRouterではなく、道具選択全体を扱うRouter方針を採用

## Version 0.3

開始内容:

- Planner設計書追加
- Plannerクラス追加

## Version 0.2

開始内容:

- docs追加
- CapabilityManager追加

## Version 0.1

完了内容:

- Qwen接続
- 会話履歴保存
- 長期記憶
- 自動記憶抽出
- 複数記憶抽出
- categoryによる記憶更新
- PersonalAIクラス化
- Git/GitHub連携
