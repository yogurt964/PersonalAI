# PersonalAI Vision

## 1. 目指す完成形

PersonalAIの最終的な完成形は、ユーザーが使う唯一のAI・作業入口である。

ユーザーは基本的にPersonalAIだけを開けばよい。ChatGPT、Codex、Qwen、OpenAI、Claude、Gemini、Web検索、YouTube Reader、PDF Reader、Vision、VS Code、PowerShell、Git、GitHub、Word、Excel、PowerPointなどは、ユーザーが直接使い分けるものではなく、PersonalAIが必要に応じて裏側で選択・利用する道具として扱う。

PersonalAIは、会話、記憶、知識、外部情報読み取り、PC操作、文書作成、コード実装、Git管理を統合し、ユーザーの作業全体を支援するAI操作ハブを目指す。

## 2. 基本思想

PersonalAIはQwenそのものではない。

PersonalAIはPythonで実装されたAI統括システムであり、Qwen、OpenAI、Memory、Tool、Web Reader、PDF Reader、Visionなどは、PersonalAIが目的に応じて利用する道具である。

現在の責務分離は以下である。

- PersonalAI: 全体を統括する本体
- InputAnalyzer: ユーザー入力を構造化する
- CapabilityManager: 利用可能な能力を管理する
- Planner: 何をするかを決める
- Router: どこに渡すかを決める
- Executor: 実際に実行する
- Qwen: LLMとして応答生成に使う道具
- SQLite: 会話履歴と長期記憶の保存に使う

この責務分離を保ちながら、少しずつ扱える道具を増やしていく。

## 3. 自律性と許可制

PersonalAIは、状況を見て提案し、必要な作業を判断する。

ただし、すべてを勝手に実行するAIではない。安全な作業は自動化できるようにし、危険な作業は必ずユーザーの許可を取る。

基本方針:

- 安全な作業は自動で実行できるようにする
- 危険な作業は必ずユーザーの許可を取る
- 最初はほとんど許可制にする
- 会話の中で、どこまで自動化するかを調整する
- ユーザーから質問や作業依頼をすることもできる
- PersonalAI側から必要な提案をすることもできる

許可が必要な操作の例:

- ファイル読み取り
- ファイル作成
- ファイル編集
- ファイル削除
- ファイル上書き
- コマンド実行
- Git commit
- Git push
- 外部送信
- 個人情報を含む処理
- Webアクセス
- 外部API利用
- PC画面読み取り
- PC操作
- 課金が発生する処理

## 4. 記憶の3層構造

PersonalAIは、既存AIよりも強い記憶機能を重視する。

記憶は以下の3層に分ける。

### 1. 短期記憶

短期記憶は、直近の会話、現在の作業、今だけ必要な文脈を扱う。

例:

- 今開いている作業
- 直近の会話
- 現在のタスク
- 一時的な判断材料

### 2. 長期記憶

長期記憶は、ユーザーの好み、目標、進行中プロジェクト、過去の決定、作業スタイルなどを扱う。

例:

- ユーザーの好み
- PersonalAI開発の進捗
- 開発方針
- よく使う作業手順
- ユーザーの性格や希望
- 回答スタイルの好み

### 3. 知識

知識は、読み取った資料、Web、PDF、YouTube、プロジェクトdocs、技術情報など、再利用できる情報を扱う。

例:

- 読み取ったPDFの内容
- Web記事の内容
- YouTube動画の要点
- 技術ドキュメント
- PersonalAIプロジェクトのdocs
- Git履歴やchangelog

## 5. 記憶に持たせたい指標

将来的に記憶には以下のような指標を持たせる。

- importance
- category
- memory_type
- source
- tags
- confidence
- updated_at
- expires_at
- memory_key
- subcategory

現在はまだ簡易実装でよい。将来的には、複数のプロジェクト、好み、知識を扱えるようにする。

## 6. 性格と作業スタイル

PersonalAIの性格は、会話の中で調整していく。

初期状態では、人間のように自然に話すAIを目指す。ただし、性格だけでなく、作業スタイルも会話の中で調整する。

調整する内容の例:

- 詳しく説明するか、短く説明するか
- 先に結論を出すか、順番に説明するか
- Codex用の指示文を作るか
- 自分で実装するか
- どこまで確認を取るか
- どの作業を自動で行ってよいか

## 7. PC操作・アプリ操作の完成形

理想的には、ユーザーはPersonalAI以外のアプリを自分から開いたり操作したりする必要がない状態を目指す。

PersonalAIが必要に応じて裏側で以下を扱う。

- ブラウザ
- YouTube
- PDF
- 画像
- Word
- Excel
- PowerPoint
- VS Code
- PowerShell
- Git / GitHub
- ファイル管理
- Web検索
- 外部AIモデル
- 画像生成ツール

ただし、PC操作は危険を伴うため、段階的に実装する。

## 8. 自分自身を開発する方針

完成形では、PersonalAI自身がPersonalAIプロジェクトを読み取り、設計し、実装し、動作確認し、Git管理まで行えるようにする。

現在はChatGPTとCodexを使って開発しているが、これは開発途中の補助である。最終的にはCodexを挟まず、PersonalAI自身が以下を行う。

1. 過去の開発状況を思い出す
2. docsやGit履歴を確認する
3. 必要な資料や動画を読み取る
4. 実装すべきか判断する
5. 実装方針を作る
6. 危険度を判定する
7. 必要ならユーザーに許可を取る
8. コードを編集する
9. 動作確認する
10. git status / diff を確認する
11. changelogを更新する
12. 許可後にcommit / pushする
13. 結果を説明し、記憶する

## 9. 理想的な会話例

### 例1: AI開発の機能追加相談

ユーザー:

```text
この間話したAI開発を進めたいんだけど、この動画の内容のような機能追加したいんだけどどうかな？
```

期待するPersonalAIの動作:

- 過去の記憶からPersonalAI開発の進捗を思い出す
- 現在のVersion、実装済み機能、未実装機能を確認する
- 動画URLや画面情報を読み取る
- 動画内容を要約する
- 今のPersonalAIにその機能が必要か判断する
- 実装するなら手順を示す
- 不要または早すぎる場合は、その理由を説明する
- 最終的には、許可を取ってPersonalAI自身が実装まで進める

### 例2: 開発内容のスライド作成

ユーザー:

```text
AI開発した内容についてスライドでまとめて
```

期待するPersonalAIの動作:

- 過去の記憶からPersonalAI開発の内容を確認する
- docs、changelog、Git履歴を必要に応じて読む
- 目的が就活用、発表用、記録用のどれか推定する
- 情報不足なら必要な質問をする
- スライド構成を作る
- 必要ならPowerPointファイルを作成する
- ユーザーに確認して修正する

## 10. 開発中の方針

開発が完了するまで、PersonalAIは普段使いしない。

開発中は以下の流れで進める。

1. ChatGPTで設計相談する
2. ChatGPTがCodexに送る指示文を作る
3. Codexが実装する
4. ユーザーがPowerShellやVS Codeで最低限の動作確認をする
5. ChatGPTが結果を確認する
6. 問題なければGit commit / pushする
7. 徐々にPersonalAI自身ができる範囲を増やす

ユーザーはPython初心者であるため、できるだけユーザーの作業量を減らす。

ユーザーに求めることは主に以下である。

- Codexに指示文を貼る
- 実行結果をChatGPTに貼る
- 画面やログを共有する
- 理想と違う点を伝える
- 許可が必要な場面で判断する
- 必要な情報を提示する

## 11. 就活・ポートフォリオ方針

就活での使い方はまだ厳密には決めない。

ただし、将来的には以下を強みにできるようにする。

- AIエージェント設計
- 長期記憶
- 短期記憶・長期記憶・知識の分離
- Planner / Router / Executor
- Permission設計
- 自律型AI
- 自分自身を改善できるAI
- Git / GitHubを使った開発管理
- Python / SQLite / LLM / Tool連携

## 12. 今後の実装順の目安

現時点では、以下の順番を目安にする。

1. Ver0.9.2: vision整理
2. Ver0.10: InputAnalyzer結果をPlanner/Routerに反映
3. Ver0.11: Clarification機能
4. Ver0.12: Permission / Risk基礎
5. Ver0.13: Memory設計強化
6. Ver0.14: ProjectReader基礎
7. Ver0.15: FileReader / CodeReader
8. Ver0.16: PatchPlanner
9. Ver0.17: PatchExecutor
10. Ver0.18: TestRunner / GitManager
11. Ver0.19以降: 小規模な機能追加をPersonalAI自身が実装
