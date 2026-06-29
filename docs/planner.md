# Planner

## 役割

PlannerはPersonalAIの行動選択を担当する。

ユーザー入力、文脈、CapabilityManagerの情報をもとに、PersonalAIが次に何をするべきかを計画としてまとめる。

## Plannerが扱う情報

Plannerは将来的に、主に以下の情報を使う。

- ユーザー入力
- 会話履歴や長期記憶などの文脈
- CapabilityManagerが管理する利用可能な能力
- 安全性
- コスト
- 許可要否

## 返す計画

Plannerは最終的に、Executorへ渡せる計画を返す。
Version 0.6以降、この計画はdictではなく `Plan` クラスのインスタンスとして扱う。

計画の例:

```python
Plan(
    action="chat",
    reason="通常の会話として処理できるため",
    required_capabilities=["chat", "llm_qwen"],
    requires_permission=False,
    risk="low",
)
```

従来のdict形式が必要な場合は、`plan.to_dict()` で変換できる。

## 現在の実装

現時点では、ルールベースの簡易Plannerとして実装する。

ユーザー入力に含まれる言葉と、InputAnalyzerが作った `input_analysis` を見て、以下のように大まかな行動を選ぶ。

- 通常会話: `chat`
- 長期記憶の保存・更新: `memory_write`
- 長期記憶の参照: `memory_read`

Version 0.10では、InputAnalyzer結果を使って以下のactionも作る。

- YouTube URL + 要約: `summarize_youtube`
- URL + 要約: `summarize_url`
- 文書作成依頼: `create_document`
- おすすめ・提案依頼: `recommend`
- 質問: `answer_question`
- その他の外部読み取りが必要な入力: `unsupported_external_reading`
- その他のファイル作成が必要な入力: `unsupported_file_creation`

ただし、Web、YouTube、PDF、画像の実読み取りや、Word / PDFなどの実ファイル作成はまだ行わない。
未実装の機能は、Executorで読んだふり・作ったふりをしないように扱う。

Version 0.11では、明らかに情報が足りない場合に `ask_clarification` を返す。

例:

- YouTube / 動画の要約依頼だがURLがない
- Webページ / URLの要約依頼だがURLがない
- PDF / 画像 / 資料の読み取り依頼だが対象ファイルやURLがない

既存の `memory_read` / `memory_write` 判定は優先して維持する。
ClarificationManagerとしての本格分離はまだ行わず、Planner内の最小ルールとして扱う。

## 今後の予定

将来的には、QwenやOpenAIを使って、より高度な計画を作る。

また、安全性、コスト、許可要否もPlannerで考慮し、必要に応じてユーザー確認や別の行動選択につなげる。
