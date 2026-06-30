# Future App Integrations

## 目的

PersonalAIは、将来的に読み取り、作業、制作、PC操作、日常管理まで扱える統括システムを目指す。

ただし、Qwen、OpenAI、読み取りツール、作業ツール、PC操作ツール、制作アプリなどをPersonalAI本体に直接詰め込まない。
後から追加・交換しやすいように、Tool / Adapter形式で接続する方針とする。

PersonalAI本体は司令塔として、入力を解釈し、必要な能力を判定し、適切なToolやAdapterへ処理を渡す。

## 基本方針

- PersonalAI本体は、判断、記憶、計画、安全確認を担当する
- 外部アプリや専門処理はTool / Adapterとして分離する
- Tool / Adapterは、あとから追加・差し替えできるようにする
- 未実装のアプリ操作や読み取りをできたふりしない
- ユーザーに影響する操作はPermissionを通す

## 将来的に対応したい制作系

| 分野 | 候補ツール例 | 目的 |
|---|---|---|
| ゲーム開発 | Unity / Godot / Unreal Engine / VS Code / Git / Blender | ゲーム企画、コード作成、素材管理、ビルド補助 |
| アプリ開発 | VS Code / Python / Node.js / GitHub / Docker / ブラウザ | 設計、実装、テスト、デプロイ補助 |
| 動画制作 | DaVinci Resolve / Premiere Pro / CapCut / FFmpeg | カット編集、字幕、書き出し、素材整理 |
| イラスト制作 | CLIP STUDIO / Photoshop / Krita / Stable Diffusion系 | ラフ案、構図、差分、画像生成補助 |
| 資料作成 | Word / Excel / PowerPoint / PDF / Markdown | レポート、表、スライド、PDF作成 |
| 音楽制作 | FL Studio / Ableton Live / Cakewalk / Audacity / MIDIツール | 作曲補助、音声編集、MIDI管理 |
| 3Dモデリング | Blender / VRoid Studio / Unity | モデル作成、素材管理、Unity連携 |
| Vtuberモデル | VRoid Studio / Live2D Cubism / Blender / VTube Studio | モデル作成、表情差分、配信用設定 |
| 動画配信 | OBS Studio / YouTube Studio / Twitch / 配信素材管理 | 配信準備、シーン管理、チェックリスト |

## 日常使い

| 分野 | 将来の対応例 |
|---|---|
| 予定管理 | カレンダー確認、予定追加、リマインド |
| ファイル整理 | フォルダ分類、重複確認、命名補助 |
| メモ管理 | メモ検索、要約、タスク化 |
| タスク管理 | TODO整理、優先順位付け、進捗確認 |
| メール確認 | メール要約、返信案作成、重要メール抽出 |
| ブラウザ操作 | ページ閲覧、フォーム入力補助、調査 |
| 買い物候補の整理 | 候補比較、価格メモ、条件整理 |

## 情報読み取り・基本機能

- Webページ読み取り
- YouTube読み取り
- PDF読み取り
- 画像読み取り
- 音声読み取り
- 動画内容の読み取り
- ローカルファイル読み取り
- スクリーンショット読み取り
- PC画面読み取り

これらは、まずReader系Adapterとして追加する。
読み取っていない情報を読んだふりしない。

## 将来の構造イメージ

```text
PersonalAI
├─ Reader系
│  ├─ WebReader
│  ├─ PDFReader
│  ├─ ImageReader
│  ├─ VideoReader
│  └─ ScreenReader
│
├─ Creator系
│  ├─ DocumentCreator
│  ├─ ImageCreator
│  ├─ VideoCreator
│  ├─ MusicCreator
│  ├─ GameProjectCreator
│  └─ AppProjectCreator
│
├─ Operator系
│  ├─ VSCodeOperator
│  ├─ PowerShellOperator
│  ├─ BrowserOperator
│  ├─ BlenderOperator
│  ├─ ClipStudioOperator
│  ├─ OBSOperator
│  └─ FileOperator
│
├─ Manager系
│  ├─ CalendarManager
│  ├─ TaskManager
│  ├─ ProjectManager
│  ├─ GitManager
│  └─ PermissionManager
```

## 安全方針

| 操作 | 方針 |
|---|---|
| アプリ起動 | 原則確認あり |
| インストール | 必ず確認 |
| 有料ソフト購入 | 必ず確認 |
| 商品購入 | 必ず確認 |
| 外部投稿・配信開始 | 必ず確認 |
| ファイル削除 | 必ず確認 |
| Git push | 基本確認 |
| 個人情報入力 | 必ず確認 |

将来的には、以下のような柔軟な許可を目指す。

```text
このプロジェクト内のpip installは許可
このフォルダ内のファイル作成は許可
削除は毎回確認
購入・契約・投稿・配信は毎回確認
```

## 実装優先順位

1. 読み取り系
   Web / PDF / 画像 / ファイル / 画面

2. 開発系
   VS Code / PowerShell / Git / GitHub

3. 文書作成系
   Word / Excel / PowerPoint / PDF / Markdown

4. 制作補助系
   画像生成 / イラスト / Blender / 動画編集

5. 大型制作系
   ゲーム開発 / アプリ開発 / Vtuberモデル / 配信環境

6. 日常統合
   予定管理 / ファイル整理 / タスク管理 / メール

## Ver0.26時点の扱い

Ver0.26では、これらの連携はまだ実装しない。
方針を整理し、今後Tool / Adapterとして追加しやすくするための設計メモとして扱う。
