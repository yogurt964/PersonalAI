# PersonalAI 会話版 Ver0.1

2026-10-22。既存Ver2.75（c75e2da）上の会話優先プロトタイプ。
既存のバージョン番号は巻き戻さない。元の起動入口は `app.py`。

## 現状確認

- Python、Ollama Qwen3:8b、SQLite/SQLAlchemyを使用。
- `core/personal_ai.py` に会話、記憶、Reader、外部APIエスカレーションを接続済み。
- Planner / Router / Executor、Permission管理、記憶の編集・無効化を実装済み。
- Reader、OpenAI接続の存在はソース上で確認。今回の環境で実機動作は未確認。
- 旧Routerには実装状況に合わない説明が残る。新しい入口へそのまま移植しない。
- 旧回答生成はcasual/developmentで履歴取得数が1。会話版は直近20件・16000文字以内。

## 今回の仕様

1. テキストCLIで会話する。起動は `python conversation_app.py`。
2. 同一の既存DBから会話履歴・有効な長期記憶を利用する。
3. ローカルLLMが文脈込みで重要度・複雑度・記憶利用度を分類。
   重要度か複雑度がhighならQwenのthink=True、それ以外はFalse。
   分類JSONの不正時は深い推論へ。通信エラー時は停止し、成功を偽らない。
   `/mode auto|fast|deep` で回答生成の推論を上書きできる。
4. 人格・話し方は `config/conversation_policy.md`。毎ターン読み直す。
5. `/remember 内容` で明示保存、`/memories` で有効な記憶の上位20件を表示。
   編集・無効化・復元の既存UIは `app.py` に残す。
6. 回答が成功したターンのみ、入力と応答をまとめてトランザクション保存。
7. この入口は有料API、Reader、PC操作、自動保存を呼び出さない。
   会話方針にも利用可能な機能を明示する。

## 再利用と分離

再利用: `database/models.py`、`database/chat_history.py`、
`database/memory_manager.py`、`ai/memory_context.py`、Ollama/モデル。
追加: `core/conversation_session.py`、`conversation_app.py`、会話方針。
既存の `app.py` とPermission経路は変更しない。
新しい会話処理はCLIと分離してあり、将来のPC/スマホUIから呼べる。

## Windowsで試す

既存環境でOllamaを起動し、qwen3:8bが導入済みであることを確認する。
リポジトリのルートで以下を実行する。

```powershell
venv\Scripts\python.exe conversation_app.py
```

新規環境では会話版に必要な依存だけインストールできる。

```powershell
python -m pip install ollama==0.6.2 SQLAlchemy==2.0.51
ollama pull qwen3:8b
python conversation_app.py
```

起動時に既存のcreate_databaseを使い、不足テーブル・既存の追加列だけ整備する。
DBを削除・初期化しない。履歴・明示記憶は既存DBに保存される。
この会話版で保存した内容を後で既存app.pyが読み取る可能性がある。

## 自動検証と受入条件

`python -B scripts/check_conversation_v01.py`
一時SQLiteを使い、複数ターン・再起動・推論切替・記憶・失敗時非保存を検証。
実LLMの自然さや分類精度はこのテストでは評価できない。

実機で確認する内容:

- 「今日疲れた」への返事が自然で、余計な質問を続けない。
- 複数条件の相談後に「それなら？」と言って話題が継続する。
- `/remember 好きな色は青` 後、再起動しても参照できる。
- `/mode fast` と `/mode deep` の応答時間・品質を比較する。
- 不明な固有名詞や最新情報で、知っているふりをしない。

## 制限・次の段階

### 2026-10-22 実機テスト後の調整

ユーザー実機で応答5秒未満、直前の会話の参照を確認。
会話方針の変更だけでは、以前と同じ冗長な返答が再現した。
更新・再起動はユーザーの実行ログで確認済み。原因は未確定。
モデルに渡す連続した3個のsystemメッセージを1個にまとめ、
機能制約・記憶・最新版の会話方針をひとまとまりで渡すよう変更。
履歴は保持する。自動チェックでは指示の受け渡しを検証し、
返答の改善は実機で再評価する。これは原因の断定や改善保証ではない。

分類も含め毎ターン最大2回のローカルLLM呼び出し。速度・分類精度は実測が必要。
長期記憶は既存の重要度順取得であり、意味検索は未実装。
会話履歴は同一ユーザー共有。セッション分離・認証・スマホUIは次段階。
音声、画面認識、PC操作、自律行動は今回追加しない。
外部APIの選択は会話評価後に行い、予算・送信範囲を設定してから接続する。

推論切替の公式資料: https://github.com/ollama/ollama/blob/main/docs/capabilities/thinking.mdx

### 記憶確認の返答改善（実機評価待ち）

実機診断では履歴形式の変更（D）・文脈長8192への拡大（E）でもAと同じ冗長な返答になった。
原因は未確定。ユーザー自身の過去の事実を確認する質問では、分類時に関連するユーザー発言の原文を選び、実際の履歴と完全一致するものだけを回答の根拠にする。
この場合は過去のAI返答を回答モデルに再投入しない。通常の会話・AIの提案への言及では従来の双方の履歴を維持する。
長期記憶の扱いとDBは変更しない。原文照合は出典を検証するものであり、選択された発言の関連性や返答品質は実機で確認する必要がある。
