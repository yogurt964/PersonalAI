# Reader Memory Policy

## 目的

このドキュメントは、Reader結果のMemory保存を将来実装するための設計方針である。

Ver2.9では、Web ReaderなどのReader結果をMemoryへ保存する前に、何を保存するか、何を保存しないか、いつユーザー確認が必要かを整理した。
Ver2.17では、ユーザーが明示的に確認した低リスクのMemory Candidateだけ、既存の長期記憶保存機構へ渡す。

## 1. 基本方針

Reader結果のMemory保存は便利だが、勝手に何でも保存しない。

基本方針:

- 重要な情報は忘れにくくする
- 低重要度情報は削除より先に圧縮・要約・Archive化を優先する
- 機密情報や個人情報は慎重に扱う
- 保存前にユーザー確認が必要な場合を明確にする
- Reader結果をそのまま長期Memoryに入れず、保存候補として段階的に扱う

Readerは外部情報や資料本文を扱うため、便利さだけで自動保存すると、不要情報、誤情報、機密情報、著作権上扱いづらい長文までMemoryに混ざる可能性がある。
そのため、長期Memoryへ入れる前に、重要度、リスク、出典、再利用性を確認する。

## 2. 保存候補

Reader結果から保存してよい候補:

- ユーザーが明示的に覚えてと言った情報
- プロジェクト進行に必要な情報
- 開発方針
- 仕様
- 調査結果の要点
- 今後の作業に必要なURLや資料名
- ユーザーの好みとして明確に役立つ情報
- 繰り返し参照する可能性が高い情報

保存候補は、本文そのものではなく、ユーザーの今後の作業に使える形へ整理した情報を優先する。

## 3. 原則保存しないもの

以下は原則として長期Memoryへ保存しない。

- ページ本文全文
- 著作権上そのまま保存すべきでない長文
- 一時的な検索結果
- 広告文
- 重要度の低い雑情報
- 機密情報
- 個人情報
- パスワード
- APIキー
- 認証情報
- 金銭・契約・法律に関わる敏感情報
- 医療など高リスク領域の断定的な判断材料

必要な場合でも、全文保存ではなく、要点、出典URL、確認日、ユーザーの目的に関係する短いメモとして扱う。

## 4. 保存形式

将来的には、Reader結果を以下のように分ける。

### Raw Reader Result

実行結果の短期保存。
長期Memoryとは別扱いにし、必要に応じて一定期間後に圧縮・Archive化・破棄候補へ回す。

### Reader Summary

本文の短い要約。
ユーザーが読み返しやすいように、出典URL、取得日時、要点を含める。

### Memory Candidate

Memory保存候補。
すぐ保存せず、ユーザー確認やリスク判定の対象にできる中間形式として扱う。

### Project Knowledge

プロジェクトに必要な知識。
仕様、設計方針、調査結果、再利用するURLなどを扱う。

### User Preference

ユーザーの好み。
明確に今後の提案や作業に役立つものだけを扱う。

### Archive

普段はMemoryContextへ出さないが、検索できる保管領域。
低重要度情報や古い資料、長めの履歴はArchiveに寄せる。

## 5. 保存前確認

以下は保存前にユーザー確認する。

- 個人情報を含む可能性がある
- 機密情報を含む可能性がある
- 金銭・契約・法律・医療など高リスク領域
- ページ本文が長い
- 出典が不明確
- ユーザーの好みとして保存してよいか迷う
- Memoryとして長期保存する必要性が不明
- プロジェクト外でも使える個人的な情報として扱う可能性がある

保存前にユーザー確認する場合は、「何を」「どの形式で」「どの範囲へ」保存するかを短く示す。

## 6. 自動保存してよい可能性があるもの

将来的に、以下は設定次第で自動保存候補にできる。

- ユーザーが明示的に「覚えて」と言った内容
- 現在の開発プロジェクトの状態
- ユーザーが確認済みの方針
- 短い要約
- 公開情報の出典URL

ただし、自動保存候補であっても、機密情報、個人情報、高リスク領域、長文本文は慎重に扱う。
重要記憶の削除・無効化はユーザー確認を基本とする。

## 7. Web Readerとの関係

Ver2.8時点では、Web Readerは読み取り結果を会話返答に出すだけで、Memory保存はまだしない。

今後の段階:

```text
Ver2.9:
Memory保存方針docs整理

Ver2.10:
Memory Candidate生成のdry-run

Ver2.11:
Memory CandidateをWeb Reader結果にdry-run接続

Ver2.12:
Memory Candidate確認UI方針

Ver2.13:
Memory Candidate確認応答のdry-run

Ver2.16:
Memory Candidate編集dry-run

Ver2.17:
Memory Candidateのユーザー確認つき保存

Ver2.18:
Memory保存後の確認・表示フロー

Ver2.20:
Memory検索の最小実用化

次以降:
Project Stateへの反映
重複・矛盾管理
```

Web Reader結果を保存する場合も、ページ本文全文をそのままMemoryへ入れない。
必要な場合は、短いReader Summary、Memory Candidate、Project Knowledge、User Preference、Archiveへ分ける。

Ver2.10では、Reader結果から保存候補を作る土台として `core/memory_candidate.py` を追加する。
これはdry-runであり、DBスキーマ変更はしない。
Memory保存はまだしない。
Web Reader本体にはまだ自動接続しない。
自動チェックでは実Webアクセス・LLM実行・ToolRunner実行・DB書き込みをしない。

Ver2.11では、Memory CandidateをWeb Reader結果にdry-run接続する。
Web Reader成功時に保存候補を作るが、Memory保存はまだしない。
Memory CandidateもDB保存しない。
DBスキーマ変更はしない。
失敗時・未実行時はMemory Candidateを作らない。
自動チェックではfake fetcherを使い、実Webアクセスしない。

Ver2.12では、Memory Candidate確認UI方針をdocs化する。
保存前にユーザーが確認できる形を整理する。
保存 / 保存しない / 編集 / 後で確認 の選択肢を整理する。
高リスク候補は自動保存しない。
まだMemory保存はしない。
DBスキーマ変更はしない。
Memory CandidateのDB保存もしない。

Ver2.13では、Memory Candidate確認応答のdry-runを追加する。
保存する / 保存しない / 編集して保存 / 後で確認 の応答を解釈する。
「保存する」と言われてもdry-runで止める。
まだMemory保存はしない。
DBスキーマ変更はしない。
Memory CandidateのDB保存もしない。
自動チェックでは実Webアクセス・LLM実行・DB書き込みをしない。

Ver2.16では、Memory Candidate編集dry-runを追加する。
`編集して保存` の後にユーザーから編集内容を受け取り、編集済み候補としてdry-run保持する。
編集内容を受け取っても、まだMemory保存はしない。
DBスキーマ変更はしない。
Memory CandidateのDB保存もしない。
Reader結果のDB保存もしない。

Ver2.17では、Memory Candidateのユーザー確認つき保存を追加する。
ユーザーが明示的に `保存する` と答えた低リスク候補だけ、既存の長期記憶保存機構へ渡す。
自動チェックでは実DB保存しない。
高リスク候補は自動保存しない。
DBスキーマ変更はしない。
Memory Candidate専用テーブルは作らない。
Reader結果全文のDB保存はしない。

Ver2.18では、Memory保存後の確認・表示フローを追加する。
保存成功後に保存内容プレビューを表示し、直近保存したMemoryを会話内で確認できるようにする。
`今保存した記憶を確認して` と聞かれた場合は、直近保存結果を表示する。
本格的なMemory検索UIにはまだ踏み込まない。
DBスキーマ変更はしない。
自動チェックではfake保存・fake記憶確認を使い、実DB保存しない。

Ver2.20では、保存済みMemoryをあとから探せるように、Memory検索の最小実用化を追加する。
`覚えてる？` などの入力から簡易queryを抽出し、保存済みMemoryをキーワード検索する。
DBスキーマ変更はしない。
ベクトル検索やLLMによる検索query生成はまだ実装しない。
自動チェックではfake検索を使い、実DB保存や実Webアクセスを行わない。

## 8. File Reader / PDF Reader とMemoryの関係（Ver2.35時点）

Ver2.35時点では、Memory Candidateへの接続はWeb Readerだけである。
File Reader（Ver2.29）・PDF Reader（Ver2.32）は、読み取り結果からMemory Candidateを作らない。

Ver2.31で追加した `last_read_document`（`core/personal_ai.py`）は、Memory（長期記憶）とは別物である。

- 直近1件のReader結果（Web Reader / File Reader / PDF Reader共通）だけを一時的に保持する
- ユーザー確認や重要度判定を経ず、会話が続く間だけQwenが参照できるようにする、あくまで暫定的なキャッシュ
- 新しいファイルを読むと前の内容は失われる（Ver2.34で、この制約についてLLMが誤った断定をしないよう修正済み）
- 長期Memory・Memory Candidate・Memory検索とは独立している

## 9. 将来の記憶アーキテクチャとの関係（ユーザー方針、Ver2.35時点で未着手）

ユーザーは、最終的に以下のような記憶方針を望んでいる。

- 会話から得た情報も、Web検索・File Reader・PDF Readerなど他のReaderから得た情報も、同じ枠組みで扱う
- 短期記憶・長期記憶・知識に分類する
- 重要度などを自動判定する
- 何を覚えるか・忘れるかを自動的に判断する

これは `docs/final_product_vision.md` の「5. 記憶方針」で整理した記憶階層（Raw Log / Turn Summary / Session Summary / Project State / Long-term Memory / Knowledge / Archive / Deletion Candidate）の本格実装、かつその対象をReader結果にも広げる話であり、File Reader / PDF Reader個別の機能ではなく、PersonalAIの記憶機能そのものの本実装として扱う。

方針:

- 記憶機能をしっかり作り直すタイミングで、あらためてユーザーと設計を確認する
- それまでの間、Reader結果の一時的な扱い（`last_read_document`、Memory Candidateの手動確認フローなど）は、AIエージェントの判断で安全側に倒しながら暫定対応してよい
- 暫定対応の間も、DBスキーマ変更、Memory物理削除、自動忘却の実行はユーザー確認なしに行わない

Ver2.51（Reader結果全文のDB保存）に関する補足（ユーザー確認済み、Ver2.51時点）:

- Reader結果全文のDB保存は、あくまで生ログ（Raw Log相当）の保存であり、長期記憶そのものではない
- 将来、長期記憶へ昇格させる際は全文をそのまま使わず、必要な情報に絞って要約・抽出する設計にする
- これは当たり前の前提であり、本格的な記憶アーキテクチャ設計（上記）に含まれる話として扱う

## Ver2.9で実装しないこと

Ver2.9では、以下は実装しない。

- Memory保存の本実装
- Memory Candidate生成のコード実装
- DBスキーマ変更
- Reader結果のDB保存
- OpenAI / Claude / Gemini接続
- PDF / Image / YouTube / File Reader実装
- PC操作
