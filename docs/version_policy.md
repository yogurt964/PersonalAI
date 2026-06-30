# Version Policy

## 目的

このドキュメントは、PersonalAIの長期開発におけるバージョン管理方針をまとめたものである。

PersonalAIでは、整数バージョンを「その状態で実用的に使える区切り」として扱う。

Ver1.0、Ver2.0、Ver3.0... の整数部分は、単なる作業番号ではない。
その段階でPersonalAIが何に使える状態なのかを表す。

## 基本方針

- Ver0.x は Ver1.0 へ進むための準備段階
- Ver1.0 以降の整数バージョンは、実用的に使える大きな区切りを表す
- x.1, x.2, x.3... は、そのメジャーバージョンを強化するための段階的な追加・改善を表す
- 整数バージョンを上げる前には、check、手動テスト、GO / HOLD / NO-GO判定を行う
- できないことをできるふりしない状態を維持する
- ユーザーに影響する操作はPermissionManagerで確認する

## バージョン番号の意味

```text
Ver0.x:
Ver1.0に向けた準備・設計・安全確認の段階

Ver1.x:
Core Assistantの改善段階。
会話品質、Memory利用バランス、Preferenceの自然な扱い、Ver1.x用チェック運用を整える。
Ver1.xではCore Assistantの会話品質改善も継続して扱う。
Reader追加前のTool / Adapter受け口整理もVer1.xで扱う。
Ver1.xではTool実行前確認とPermission連携準備も扱う。
Ver1.xではReader実装前のInputAnalyzer / Capability / Tool連携確認も扱う。
Ver1.xではTool実行ログと結果記録の設計も扱う。
Ver1.xではReader実装前のテストケース整理も扱う。
Ver1.xはReader実装前の土台整理までを扱う。
quick check / standard check / full pre-release check を使い分け、通常のVer1.x確認には run_ver1_checks.py を使う。

Ver2.x:
Reader / Knowledge機能の追加・改善段階

Ver3.x:
Work / Document機能の追加・改善段階

Ver4.x:
Development / Coding機能の追加・改善段階

Ver5.x:
Creative / Game / 3D / VRC機能の追加・改善段階

Ver6.x:
Integrated Daily AI機能の追加・改善段階
```

## メジャーバージョンの目標

### Ver1.0: Core Assistant

最低限の会話・記憶・安全確認をテストできる実用テスト版。

主な条件:

- 通常会話ができる
- 記憶保存・記憶参照の基礎がある
- Preference記憶を扱える
- 曖昧なPreferenceでは確認質問できる
- 確認回答後に保存できる
- 未実装機能をできたふりしない
- Permission / Capability の基礎がある
- Memoryを物理削除せず安全に扱う
- 引き継ぎ・復旧docsがある

### Ver2.0: Reader / Knowledge Assistant

情報を読み取り、理解・要約・比較・記憶できる段階。
Ver2.0はReader方面の最初の実用テスト版であり、少なくとも1つのReaderが実際に動く状態を目安にする。
Ver2.0は、Ver1.xで整理した土台の上に最初のReader実処理を接続する段階である。

主な対象:

- Web Reader
- PDF Reader
- Image Reader
- YouTube Reader
- Local File Reader
- Screenshot / Screen Reader
- 読み取った内容の要約
- 読み取った内容の記憶化
- 複数資料の比較

### Ver3.0: Work / Document Assistant

文書や作業ファイルを作成・整理できる段階。

主な対象:

- Markdown作成
- Word作成
- Excel作成
- PowerPoint作成
- PDF作成
- レポート作成
- 表作成
- ファイル整理
- タスク整理

### Ver4.0: Development / Coding Assistant

コードを書き、実行し、修正し、開発プロジェクトを扱える段階。

主な対象:

- VS Code操作
- PowerShell操作
- Git / GitHub操作
- Python開発
- JavaScript / Node開発
- アプリ開発補助
- 簡単なゲームロジック開発
- エラー修正
- テスト実行
- プロジェクト構成整理

Ver4.0は、主に「コードを書く・動かす・直す・管理する」段階である。

### Ver5.0: Creative / Game / 3D / VRC Assistant

制作物、ゲーム素材、3Dモデル、VRC制作、動画・画像・音楽などを扱える段階。

主な対象:

- 画像生成
- イラスト制作補助
- 動画生成・動画編集補助
- 音楽制作補助
- Blender連携
- 3Dモデリング
- Unity / Godot連携
- VRCアバター制作補助
- VRCワールド制作補助
- VRCギミック制作
- VRChat SDK
- Udon / UdonSharp
- Animator / Collider / Prefab設定
- モデル軽量化
- Vtuberモデル制作
- OBS / 配信補助

Ver5.0は、主に「素材を作る・3Dを扱う・演出を作る・VRC/ゲーム制作を本格化する」段階である。

### Ver6.0: Integrated Daily AI

日常作業と複数アプリを横断して支援できる段階。

主な対象:

- 予定管理
- タスク管理
- メール確認
- ブラウザ操作
- ファイル整理
- メモ整理
- 買い物候補整理
- 学習管理
- 複数アプリ横断ワークフロー

## Ver4.0とVer5.0の違い

Ver4.0 = 開発できるAI
Ver5.0 = 制作できるAI

より具体的には:

Ver4.0:
コード、プロジェクト、実行、修正、Git管理を扱う。
ゲーム開発では、プレイヤー操作、敵AI、スコア処理、UI、セーブ機能などのロジックを担当する。

Ver5.0:
画像、3D、動画、音楽、ゲーム素材、VRCギミックなどの制作物を扱う。
ゲーム制作では、キャラモデル、ステージ、アニメーション、エフェクト、UI素材、BGM/SE、VRCギミックを担当する。

VRC制作では、コードだけでなくBlender、Unity、VRChat SDK、Animator、Collider、Prefab、Udon / UdonSharp、モデル軽量化、アップロード前確認が必要になる。

そのため、VRC制作を本格的に扱う段階ではVer5.0系の機能が重要になる。

## 整数バージョンを上げる条件

整数バージョンを上げる条件は、「機能が存在すること」ではなく「その分野で一応使えること」である。

例:

Web Readerを少し作っただけではVer2.0とはしない。
Web / PDF / 画像 / YouTube / ローカルファイルなどの主要Readerが最低限使え、できないことを正直に扱える段階でVer2.0を検討する。

Word作成の試作だけではVer3.0とはしない。
Markdown / Word / Excel / PDFなどの主要作業ファイルを最低限扱える段階でVer3.0を検討する。

コード生成だけではVer4.0とはしない。
コード作成、実行、エラー確認、修正、Git管理まで最低限つながる段階でVer4.0を検討する。

Blender操作の試作だけではVer5.0とはしない。
画像・3D・ゲーム素材・VRC制作などの制作フローが最低限つながる段階でVer5.0を検討する。

## GO / HOLD / NO-GOとの関係

整数バージョンへ進む前には、必ずGO / HOLD / NO-GO判定を行う。

GO:
そのメジャーバージョンの目的を最低限満たしており、実用テストできる。

HOLD:
一部未確認や軽微な問題があり、修正または追加確認が必要。

NO-GO:
安全性、Memory、DB、未実装機能の正直な扱い、許可制御などに重大な問題がある。

## 今後の運用方針

- 新機能は小さいVerで追加する
- 整数バージョン前にはdocsとcheckを整備する
- その時点で使える範囲と使えない範囲を明記する
- 未実装機能はできたふりしない
- 既存機能を壊さない
- DBやMemoryを破壊しない
- Git commit / push はユーザー確認後に行う
