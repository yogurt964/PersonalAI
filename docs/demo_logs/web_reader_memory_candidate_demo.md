# Web Reader Memory Candidate Demo

## 目的

このデモログは、Web Reader → Memory Candidate → 確認応答dry-run の流れを説明するための資料である。

Ver2.15時点では、Web Readerで読み取った結果からMemory Candidateを作り、保存確認の応答をdry-runで解釈できる。
ただし、まだMemory保存の本実装はしていない。
Memory CandidateのDB保存もしない。

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
保存要求は受け取りましたが、Ver2.13ではまだMemory保存しません。
```

## このデモで分かること

- URL入力だけではWeb Readerを実行しない
- 外部Webアクセス前にユーザー確認を挟む
- Web Reader成功時にタイトル、URL、本文プレビューを返す
- Reader結果からMemory Candidateを作る
- Memory Candidate dry-runとして保存候補を表示する
- `保存する` と言われても、まだMemory保存しません
- 完成済み機能と未実装機能を分けて扱っている

## Ver2.15時点で未実装のこと

- Memory保存の本実装
- Memory CandidateのDB保存
- Reader結果のDB保存
- Memory Candidate編集UI
- PDF / Image / YouTube / File Reader
- OpenAI / Claude / Gemini 接続
- GUI
- PC操作
