# InputAnalyzer

## 役割

InputAnalyzerは、ユーザー入力を構造化するためのモジュールである。

PersonalAIが受け取る入力は、通常の会話だけではない。URL、YouTube、PDF、画像、Word文書の作成依頼など、将来的にはさまざまな種類の入力を扱う必要がある。

InputAnalyzerは、まず入力の種類と依頼内容を簡単に判定し、後続のPlannerやRouterが使いやすいdict形式に変換する。

## 現在判定する内容

現在は、以下の項目を返す。

- `input_type`: 入力の種類
- `task_type`: 依頼の種類
- `has_url`: URLを含むかどうか
- `url`: 見つかったURL
- `requires_external_reading`: 外部情報の読み取りが必要そうか
- `requires_file_creation`: ファイル作成が必要そうか
- `notes`: 人が確認しやすい短いメモ

## input_type

現時点で扱う `input_type` は以下である。

- `text`: 通常のテキスト
- `url`: 一般的なURL
- `youtube`: YouTube URL
- `unknown`: 空文字など、判定しにくい入力

## task_type

現時点で扱う `task_type` は以下である。

- `chat`: 通常会話
- `summarize`: 要約依頼
- `create_document`: Wordや文書作成の依頼
- `recommend`: おすすめ依頼
- `remember`: 記憶してほしい依頼
- `question`: 質問
- `unknown`: 空文字など、判定しにくい入力

## 返すdictの例

```python
{
    "input_type": "youtube",
    "task_type": "summarize",
    "has_url": True,
    "url": "https://youtube.com/...",
    "requires_external_reading": True,
    "requires_file_creation": False,
    "notes": "YouTube URLの要約依頼",
}
```

## 現在の制限

現時点では、WebやYouTubeを実際に読みに行かない。

InputAnalyzerは「これは外部読み取りが必要そうだ」と判定するだけである。実際の読み取りは、将来的にRouterやExecutor、専用Toolを通して行う。

## PersonalAIとの接続

Version 0.9で、InputAnalyzerはPersonalAI本体に接続された。
Version 0.9.1では、ルールベースの判定語彙を少し追加した。

`handle_user_input()` では、ユーザー発言を保存したあとに `input_analyzer.analyze(user_input)` を呼び、結果を `self.last_input_analysis` に保存する。

また、Plannerの `context` に `input_analysis` を渡す。ただし、現時点ではPlannerの大きな分岐変更は行わない。

Version 0.10では、Plannerが `input_analysis` を使ってactionをより具体的に分類するようになった。

- YouTube URL + 要約: `summarize_youtube`
- URL + 要約: `summarize_url`
- 文書作成依頼: `create_document`
- おすすめ・提案依頼: `recommend`
- 質問: `answer_question`

ただし、InputAnalyzerは引き続き判定だけを行う。
WebやYouTubeの実読み取り、PDF読み取り、画像認識、実ファイル作成はまだ行わない。

## Version 0.9.1で追加した判定語彙

以下のような語彙を追加した。

- summarize: `要約`, `まとめて`, `まとめ`, `内容を教えて`, `簡単に説明`
- create_document: `Word`, `ワード`, `文書`, `レポート`, `資料`, `PDFにして`, `文章にして`
- recommend: `おすすめ`, `オススメ`, `候補`, `どれがいい`, `提案`
- remember: `覚えて`, `記憶して`, `忘れないで`
- question: `？`, `?`, `どうすれば`, `なぜ`, `なんで`, `方法`, `教えて`
