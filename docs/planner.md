# Planner

## 役割

PlannerはPersonalAIの行動選択を担当する。

ユーザー入力、文脈、CapabilityManagerの情報をもとに、PersonalAIが次に何をするべきかを計画としてまとめる。

## Plannerが扱う情報

Plannerは将来的に、主に以下の情報を使う。

- ユーザー入力
- 会話履歴や長期記憶などの文脈
- CapabilityManagerが管理する利用可能な能力
- 安全性
- コスト
- 許可要否

## 返す計画

Plannerは最終的に、Executorへ渡せる計画を返す。

計画の例:

```python
{
    "action": "chat",
    "reason": "通常の会話として処理できるため",
    "required_capabilities": ["chat", "llm_qwen"],
    "requires_permission": False,
    "risk": "low",
}
```

## 現在の実装

現時点では、ルールベースの簡易Plannerとして実装する。

ユーザー入力に含まれる言葉を見て、以下のように大まかな行動を選ぶ。

- 通常会話: `chat`
- 長期記憶の保存・更新: `memory_write`
- 長期記憶の参照: `memory_read`

## 今後の予定

将来的には、QwenやOpenAIを使って、より高度な計画を作る。

また、安全性、コスト、許可要否もPlannerで考慮し、必要に応じてユーザー確認や別の行動選択につなげる。
