# LLM Intent Resolver Design

## 目的

このドキュメントは、Ver2.26で整理するLLM Intent Resolverの設計方針である。

現在、確認待ち状態の解釈は `core/confirmation_intent.py`（Web Reader確認）と `core/memory_candidate_confirmation.py`（Memory Candidate確認・編集）の2つのルールベースresolverが個別に担っている。
どちらも固定語彙リストとの完全一致・正規化一致でしか意図を判定できず、言い回しの揺れ（例:「読んでもらえますか」「それは保存しなくていい」など）には対応できない。

LLM Intent Resolverは、この限界を段階的に解消するための設計であり、Ver2.26では設計のみを行い、実装は行わない。

## 現状の課題

- `core/confirmation_intent.py` はWeb Reader確認専用で、`WEB_READER_CONFIRMED_WORDS` / `WEB_READER_REJECTED_WORDS` に完全一致しない入力はすべて `unclear` になる
- `core/memory_candidate_confirmation.py` も同様に、`SAVE_WORDS` / `REJECT_WORDS` / `POSTPONE_WORDS` / `EDIT_WORDS` の固定語彙に依存する
- 2つのresolverは似た構造（正規化 → 語彙一致 → status/action/message構築）を持つが、統合されていない
- `docs/development_workflow.md` の「Intent解釈方針」では、最終的にLLMで文脈込みにIntent解釈する方針が既に示されているが、詳細設計はまだない

## 設計方針

### 1. LLMは「解釈」だけを担当し、「実行」は担当しない

LLM Intent Resolverは、ユーザー入力を既存のstatus値（`confirmed` / `rejected` / `unclear` / `postponed` / `edit_requested` など）にマッピングする役割に限定する。

実行可否の最終判断は、これまで通り以下が担う。

- `PermissionManager`（許可・risk判定）
- `ToolRunner`（実行前確認済みのToolRequestのみ実行）
- PersonalAI本体の状態管理（`pending_web_reader_confirmation` 等）

LLMの応答をそのままツール実行のトリガーにはしない。

### 2. 既存のルールベースresolverをフォールバックとして残す

LLM呼び出しが失敗した場合、応答が期待した形式でない場合、信頼度が低い場合は、既存のルールベースresolver（`core/confirmation_intent.py` / `core/memory_candidate_confirmation.py`）による判定にフォールバックする。

これにより、LLM側に問題が起きても「確認待ち中に何も答えられない」状態にはならない。

### 3. ハイブリッド判定によるコスト抑制

既存の固定語彙（「はい」「いいよ」「保存する」など）に完全一致する入力は、これまで通りルールベースで即座に判定し、LLMを呼ばない。

LLM呼び出しは、ルールベースで `unclear` になったケースに限定して行う。これにより、無駄なLLM呼び出し・API消費を避ける（`MIGRATION.md` のコスト方針・無駄なAPI消費を避ける方針に沿う）。

### 4. 入出力インターフェース

呼び出し側（`core/personal_ai.py`）への影響を最小化するため、LLM Intent Resolverの出力形式は既存resolverと同じ辞書構造を維持する。

想定する入力:

- `user_input`: ユーザーの生入力
- `context_type`: `web_reader` / `memory_candidate` / `memory_candidate_edit` など
- `pending_context`: 確認待ち中の対象（URL、Memory Candidate内容など）

想定する出力（既存と同じ形式）:

- `status`
- `action`
- `confidence`
- `message`
- （Memory Candidate系では）`candidate` / `should_save` / `should_execute` / `requires_followup`

### 5. モデル選定方針

`MIGRATION.md` の「Qwen / OpenAIの利用方針」に従う。

- まずはローカルのQwen（`ai/llm.py` の `ask_llm`）で判定を試みる
- Qwenでの判定精度が実用上不足する場合に、OpenAI利用を検討する
- OpenAI利用、APIキー設定、外部送信、課金が発生する変更は、実装段階で必ずユーザー確認を取る

### 6. 安全設計・プロンプト設計時の注意

- LLMの応答は、既知のstatus値以外にマッピングできない場合、安全側に倒して `unclear` として扱う
- 未知のaction文字列をそのまま実行経路に渡さない
- Web Reader結果やMemory Candidateの内容をプロンプトに含める場合、それらが指示文のように解釈されるプロンプトインジェクションのリスクに注意する（外部由来のテキストは「参考情報」として明示し、指示として扱わない）
- LLMの判定結果は会話ログ・実行ログに残し、後から「なぜその判定になったか」を追えるようにする

## 段階的な実装ステップ案（将来Ver向け、今回は未着手）

1. プロンプト設計とテストケース作成（想定入力・期待status一覧の整理）
2. fake LLM応答を使ったdry-run実装（実LLM呼び出しなし）
3. Qwenへの実接続（ローカル、ハイブリッド判定つき）
4. 実会話での精度確認、フォールバック動作の確認
5. 必要に応じてOpenAI利用オプションを検討（ユーザー確認必須）

## Ver2.26でやらないこと

- `core/confirmation_intent.py` / `core/memory_candidate_confirmation.py` の実装変更
- LLM呼び出しの追加接続
- プロンプトの実装
- DBスキーマ変更
- Memory保存・検索ロジック変更
- OpenAI / Claude / Gemini接続

Ver2.26は設計のみであり、既存の確認フローの動作は変更しない。
