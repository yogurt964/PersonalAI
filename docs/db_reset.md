# DBリセット手順

## いつDBリセットが必要か

開発中に、テスト用の会話履歴や長期記憶を消して最初から確認したい場合にDBをリセットする。

たとえば、以下のようなときに使う。

- テスト用の名前や好きな食べ物を消したい
- 記憶抽出の動作を最初から確認したい
- 会話履歴が増えすぎて動作確認しづらい

## DBファイルについて

開発用DBは以下のファイルである。

```text
data/personal_ai.db
```

このファイルは `.gitignore` に入っており、Git管理外である。

## 注意

DBを削除すると、会話履歴と長期記憶が消える。

本番運用時や、残したい記憶がある場合は、削除前に必ずバックアップする。

## 1. PersonalAIを停止する

PowerShellでPersonalAIを起動している場合は、先に停止する。

`python app.py` を実行中なら、以下を入力して終了する。

```powershell
exit
```

念のため、Pythonプロセスが残っていないか確認する。

```powershell
Get-Process | Where-Object { $_.ProcessName -like "*python*" }
```

何も表示されなければ、Pythonプロセスは残っていない。

## 2. DBファイルを削除する

PowerShellでプロジェクトフォルダに移動する。

```powershell
cd C:\AIProject\PersonalAI
```

DBファイルを削除する。

```powershell
Remove-Item -LiteralPath .\data\personal_ai.db
```

削除できたか確認する。

```powershell
Test-Path .\data\personal_ai.db
```

`False` と表示されれば削除済みである。

## 3. DBを再作成する

DBのテーブルを作り直す。

```powershell
python create_db.py
```

この環境で `python` が起動エイリアスに当たる場合は、仮想環境のPythonを使う。

```powershell
.\venv\Scripts\python.exe create_db.py
```

## 4. 動作確認する

PersonalAIを起動する。

```powershell
python app.py
```

この環境で `python` が起動エイリアスに当たる場合は、仮想環境のPythonを使う。

```powershell
.\venv\Scripts\python.exe app.py
```

会話できること、名前や好きな食べ物をもう一度記憶できることを確認する。
