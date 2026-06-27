# Changelog

## Version 0.8

開始内容:

- ExecutorをPersonalAI内部に接続
- PersonalAIからの直接 ask_llm 呼び出しを廃止
- planとrouteをExecutorへ渡し、ExecutorがQwen実行を担当する形へ変更
- 既存の会話履歴保存・記憶抽出・記憶保存フローを維持

## Version 0.7

開始内容:

- Executorクラス追加
- Executor設計書追加
- target=qwen のとき Qwen を実行する土台を追加
- target=openai_candidate のとき未実装メッセージを返す方針を追加

## Version 0.6

開始内容:

- Plan / Route データモデル追加
- PlannerがdictではなくPlanを返すように変更
- RouterがdictではなくRouteを返すように変更
- Routerは既存のdict形式planにも最低限対応

## Version 0.5

開始内容:

- CapabilityManager、Planner、RouterをPersonalAI内部に接続
- planとrouteを生成しつつ、既存のQwen回答生成フローを維持
- まだExecutorやOpenAI呼び出しは行わない方針を維持

## Version 0.4

開始内容:

- Router設計書追加
- Routerクラス追加
- ModelRouterではなく、道具選択全体を扱うRouter方針を採用

## Version 0.3

開始内容:

- Planner設計書追加
- Plannerクラス追加

## Version 0.2

開始内容:

- docs追加
- CapabilityManager追加

## Version 0.1

完了内容:

- Qwen接続
- 会話履歴保存
- 長期記憶
- 自動記憶抽出
- 複数記憶抽出
- categoryによる記憶更新
- PersonalAIクラス化
- Git/GitHub連携
