# Performance Benchmark

## 目的

Ver0.25では、PersonalAIの軽量性を確認するためのベンチマークを追加した。

目的は高速化ではなく、まず測定できる状態にすることである。
PersonalAIに機能を追加していくと、import、初期化、MemoryContext生成、各種判定が少しずつ重くなる可能性がある。
そのため、主要処理の時間を簡単に確認できるスクリプトを用意する。

## 追加したスクリプト

```powershell
venv\Scripts\python.exe -B scripts\benchmark_lightweight.py
```

このスクリプトは、標準出力に測定結果を表示する。
Qwen / Ollamaへの問い合わせ、外部通信、DB削除、Memory削除、`is_active` 変更は行わない。

## 測定項目

- PersonalAI import時間
- PersonalAI初期化時間
- Capability判定時間
- Preference抽出時間
- Preference確認判定時間
- MemoryContext生成時間
- 自動忘却dry-run時間
- 合計時間

## 方針

- Qwen / Ollamaには問い合わせない
- 外部通信しない
- DBを削除しない
- Memoryを物理削除しない
- `is_active` を変更しない
- 結果はPC環境やDBサイズによって変わる
- 失敗した項目があっても、他の測定を続ける

## 出力例

```text
PersonalAI Lightweight Benchmark
================================

[OK] import_time_personal_ai: 0.123 sec
[OK] personal_ai_init_time: 0.045 sec
[OK] capability_analyze_time: 0.002 sec
[OK] preference_extract_time: 0.001 sec
[OK] preference_confirmation_time: 0.001 sec
[OK] memory_context_build_time: 0.010 sec
[OK] forgetting_dry_run_time: 0.003 sec

[OK] total_benchmark_time: 0.185 sec
Total: 0.185 sec
```

## 将来的な使い方

- バージョンごとに重くなっていないか確認する
- Memory数が増えたときにMemoryContext生成が遅くならないか見る
- OpenAI / Web / PDF / Image Reader追加後に比較する
- Ver1.0前の安定性確認に使う

## まだ行わないこと

Ver0.25では、以下は行わない。

- 高速化のための大きな設計変更
- Qwen / Ollamaへの実問い合わせ
- OpenAI接続
- 外部通信
- DB削除
- Memory物理削除
- 自動 `is_active=False`
