# Web Reader Memory Candidate Demo

## 目的

このデモログは、Web Reader → Memory Candidate → Memory Candidateのユーザー確認つき保存 の流れを説明するための資料である。

Ver2.17以降では、ユーザーが明示的に「保存する」と答えた場合、低リスクのMemory Candidateは既存の長期記憶保存機構を通して保存される。
ただし、高リスク候補や保存不可時は保存しない。
DBスキーマ変更はしない。
自動チェックでは実DB保存しない。

Ver2.18では、Memory保存後の確認として、直近保存したMemoryを会話内で表示できるようにする。

Ver2.19以降:
「はい」だけでなく、「いいよ」「お願いします」などもWeb Reader実行許可として扱う。
確認待ち中に不明な入力が来た場合は、通常会話へ流さず確認を聞き直す。

Ver2.20では、Memory検索の最小実用化として、保存済みMemoryをあとから簡易キーワード検索できるようにする。
DBスキーマ変更はしない。

## デモログ

```text
ユーザー:
このURLを読んで https://example.com

PersonalAI:
Web Readerで読み取ってもよいですか？

ユーザー:
はい

PersonalAI:
Web Readerで読み取りました。

タイトル:
Example Domain

URL:
https://example.com/

本文プレビュー:
Example Domain
This domain is for use in documentation examples...

Memory Candidate dry-run:
保存候補タイプ: reader_summary
重要度: medium
リスク: low
保存実行: しない
確認必要: はい
理由:
- 保存すべきか迷うため、dry-runでは候補提示に留めます。

ユーザー:
保存する

PersonalAI:
Memory Candidateを長期記憶に保存しました。

保存内容:
タイトル:
Example Domain

URL:
https://example.com/

要約:
Example Domain This domain is for use in documentation examples...

保存元:
web_reader

保存結果:
- 保存先: 既存の長期記憶
- DBスキーマ変更: なし

ユーザー:
今保存した記憶を確認して

PersonalAI:
直近保存したMemoryは以下です。

保存内容:
タイトル:
Example Domain

URL:
https://example.com/

要約:
Example Domain This domain is for use in documentation examples...

保存元:
web_reader

ユーザー:
Example Domainについて覚えてる？

PersonalAI:
保存済みMemoryから関連しそうな内容を見つけました。

1. [Reader Summary] Title: Example Domain URL: https://example.com Summary: Example Domain This domain is for use in documentation examples...
   URL: https://example.com
   保存元: web_reader
```

## このデモで分かること

- URL入力だけではWeb Readerを実行しない
- 外部Webアクセス前にユーザー確認を挟む
- Web Reader成功時にタイトル、URL、本文プレビューを返す
- Reader結果からMemory Candidateを作る
- Memory Candidate dry-runとして保存候補を表示する
- `保存する` と明示された場合だけ、低リスク候補を既存の長期記憶保存機構へ渡す
- 保存後に、直近保存したMemoryを会話内で確認できる
- `覚えてる？` と聞いたとき、保存済みMemoryを検索できる
- 高リスク候補や保存不可時は保存しない
- 完成済み機能と未実装機能を分けて扱っている

## Ver2.17時点で未実装のこと

- Memory Candidate専用テーブル
- Reader結果のDB保存
- ベクトル検索
- LLMによる高度な文脈検索
- PDF / Image / YouTube / File Reader
- OpenAI / Claude / Gemini 接続
- GUI
- PC操作
