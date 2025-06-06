# 🚀 テストレポート更新 - クイックリファレンス

## 📋 よく使うコマンド（ワンライナー）

### 🏃‍♂️ **超高速実行**
```bash
# 1. 全テスト + 履歴更新（最頻用）
python test_runner_with_history.py

# 2. コア機能カバレッジのみ
./quick_test_update.sh core

# 3. 履歴サマリー確認
./quick_test_update.sh history
```

### 🎯 **機能別テスト**
```bash
# ユーザー機能
./quick_test_update.sh user

# 記事機能  
./quick_test_update.sh article

# 認証機能
./quick_test_update.sh auth

# 統合テスト
./quick_test_update.sh integration
```

### 📊 **レポート確認**
```bash
# 最新レポート一覧
ls -la test_reports/ | tail -5

# カバレッジHTMLを開く
open htmlcov_core_only/index.html

# 最新Markdownレポート表示
cat $(ls test_reports/test_report_*.md | tail -1)
```

### 🔍 **デバッグ用**
```bash
# 特定テスト詳細実行
python -m pytest tests/test_user_router.py::TestCreateUserEndpoint::test_create_user_success -v -s

# ログ付きデバッグ
python -m pytest tests/test_user_router.py -v -s --log-cli-level=INFO

# 失敗テストの詳細
python -m pytest tests/test_failing.py -v --tb=long
```

### 📈 **履歴確認**
```bash
# バグ履歴（最新5件）
python -c "import json; h=json.load(open('bug_history.json')); [print(f\"{'✅' if e['success_rate']==100 else '❌'} {e['timestamp']} | {e['test_name']} | {e['success_rate']}%\") for e in h[-5:]]"

# カバレッジ履歴（最新5件）  
python -c "import json; h=json.load(open('coverage_history.json')); [print(f\"📊 {e['timestamp']} | {e['test_name']} | {e.get('overall_coverage', e.get('coverage_percent', 0)):.1f}%\") for e in h[-5:]]"
```

### 🧹 **メンテナンス**
```bash
# 古いファイル削除（30日以上）
find . -name "test_results_*.xml" -mtime +30 -delete
find . -name "coverage_*.json" -mtime +30 -delete
find . -name "htmlcov_*" -type d -mtime +30 -exec rm -rf {} +

# ディスク使用量確認
du -sh test_reports/ htmlcov* coverage_*.json test_results_*.xml
```

---

## 🎯 シチュエーション別コマンド

### 🔧 **バグ修正後**
```bash
# Step1: 修正対象のテスト実行
python test_runner_with_history.py test_user_router

# Step2: 全体への影響確認  
python test_runner_with_history.py

# Step3: カバレッジ改善確認
./quick_test_update.sh core
```

### ✨ **新機能追加後**
```bash
# Step1: 新機能テスト実行
python test_runner_with_history.py test_new_feature

# Step2: 統合テスト確認
./quick_test_update.sh integration  

# Step3: 全体テスト
python test_runner_with_history.py
```

### 🚀 **リリース前確認**
```bash
# Step1: 全テスト実行
python test_runner_with_history.py

# Step2: カバレッジ確認
./quick_test_update.sh core

# Step3: 履歴確認
./quick_test_update.sh history
```

---

## 📊 **現在のステータス確認**

### ワンライナーステータス
```bash
# 現在のテスト成功率
python -c "import json; h=json.load(open('bug_history.json')); print(f'最新成功率: {h[-1][\"success_rate\"]}%')" 2>/dev/null || echo "履歴なし"

# 現在のカバレッジ
python -c "import json; h=json.load(open('coverage_history.json')); print(f'最新カバレッジ: {h[-1].get(\"overall_coverage\", h[-1].get(\"coverage_percent\", 0)):.1f}%')" 2>/dev/null || echo "履歴なし"

# 総テスト数確認
python -c "import subprocess; result=subprocess.run(['python', '-m', 'pytest', 'tests/', '--collect-only', '-q'], capture_output=True, text=True); print(f'総テスト数: {result.stdout.count(\"<Function\")}個')"
```

---

## 🆘 **緊急時コマンド**

### 🔥 **全部リセット**
```bash
# 履歴ファイルリセット
echo "[]" > bug_history.json
echo "[]" > coverage_history.json

# 古いレポート削除
rm -rf test_reports/* htmlcov*

# 新規テスト実行
python test_runner_with_history.py
```

### 🚨 **メモリ不足時**
```bash
# 分割実行
for test in test_user_router test_article_router test_auth_router; do
    python test_runner_with_history.py $test
    sleep 2
done
```

---

**💡 Tip:** これらのコマンドをエイリアスとして設定することで、さらに高速化可能です！

```bash
# ~/.zshrcに追加推奨
alias test-all="python test_runner_with_history.py"
alias test-core="./quick_test_update.sh core"  
alias test-history="./quick_test_update.sh history"
alias test-user="./quick_test_update.sh user"
```
