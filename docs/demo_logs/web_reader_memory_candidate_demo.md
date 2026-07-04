# Web Reader Memory Candidate Demo

## 目的

このデモログは、Web Reader → Memory Candidate → Memory Candidateのユーザー確認つき保存 の流れを説明するための資料である。

Ver2.17以降では、ユーザーが明示的に「保存する」と答えた場合、低リスクのMemory Candidateは既存の長期記憶保存機構を通して保存される。
ただし、高リスク候補や保存不可時は保存しない。
DBスキーマ変更はしない。
自動チェックでは実DB保存しない。

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

保存結果:
- 保存先: 既存の長期記憶
- DBスキーマ変更: なし
```

## このデモで分かること

- URL入力だけではWeb Readerを実行しない
- 外部Webアクセス前にユーザー確認を挟む
- Web Reader成功時にタイトル、URL、本文プレビューを返す
- Reader結果からMemory Candidateを作る
- Memory Candidate dry-runとして保存候補を表示する
- `保存する` と明示された場合だけ、低リスク候補を既存の長期記憶保存機構へ渡す
- 高リスク候補や保存不可時は保存しない
- 完成済み機能と未実装機能を分けて扱っている

## Ver2.17時点で未実装のこと

- Memory Candidate専用テーブル
- Reader結果のDB保存
- PDF / Image / YouTube / File Reader
- OpenAI / Claude / Gemini 接続
- GUI
- PC操作
