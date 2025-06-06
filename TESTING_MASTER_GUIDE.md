# 🧪 Blog API テスト自動化マスターガイド

**プロジェクト**: Blog API Testing System  
**最終更新**: 2025年6月6日  
**目的**: 機能改善・バグ修正時の完全自動化ワークフロー

---

## 🚀 **今すぐ開始！超簡単3ステップ**

### 1️⃣ **ワークスペースに移動**
```bash
cd /Users/tatu/Documents/GitHub/blog-api-main
```

### 2️⃣ **全テスト実行（最重要！）**
```bash
# この1行だけでバグレポート + カバレッジレポートが自動更新される！
python test_runner_with_history.py
```

### 3️⃣ **結果確認**
```bash
# 履歴サマリー表示
./quick_test_update.sh history

# カバレッジレポートをブラウザで確認
open htmlcov_core_only/index.html
```

---

## 📋 **よく使うコマンド一覧**

### 🏃‍♂️ **日常開発用（最頻用）**
```bash
# 全テスト + 履歴更新（メイン）
python test_runner_with_history.py

# コア機能カバレッジのみ（高速）
./quick_test_update.sh core

# 履歴サマリー確認
./quick_test_update.sh history
```

### 🎯 **機能別テスト**
```bash
./quick_test_update.sh user        # ユーザー機能
./quick_test_update.sh article     # 記事機能  
./quick_test_update.sh auth        # 認証機能
./quick_test_update.sh integration # 統合テスト
```

### 📊 **レポート生成**
```bash
./quick_test_update.sh coverage    # カバレッジレポートのみ
./quick_test_update.sh all         # 全テスト + レポート
```

---

## 🛠️ **シチュエーション別コマンド**

### 🐛 **バグ修正後**
```bash
# 1. 修正した機能のテスト実行
./quick_test_update.sh [user|article|auth|integration]

# 2. 全テスト実行で最終確認
python test_runner_with_history.py

# 3. 結果確認
./quick_test_update.sh history
```

### ⚡ **機能追加後**
```bash
# 1. 新機能のテストを追加後、コア機能確認
./quick_test_update.sh core

# 2. 全テスト実行
python test_runner_with_history.py

# 3. カバレッジ確認
open htmlcov_core_only/index.html
```

### 🔍 **リリース前**
```bash
# 1. 全テスト実行
python test_runner_with_history.py

# 2. 統合テスト確認
./quick_test_update.sh integration

# 3. 最終履歴確認
./quick_test_update.sh history
```

---

## 📁 **生成されるレポート**

| ファイル/フォルダ | 内容 | 用途 |
|---|---|---|
| `bug_history.json` | バグ履歴データ | テスト成功率追跡 |
| `coverage_history.json` | カバレッジ履歴 | コード品質追跡 |
| `test_reports/` | Markdownレポート | 人間可読形式 |
| `htmlcov_core_only/` | コア機能カバレッジHTML | 詳細分析用 |
| `htmlcov/` | 全機能カバレッジHTML | 全体把握用 |

---

## ⚡ **生産性向上のTips**

### 🔧 **エイリアス設定（推奨）**
```bash
# ~/.zshrc に追加
alias blogtest="cd /Users/tatu/Documents/GitHub/blog-api-main && python test_runner_with_history.py"
alias blogcore="cd /Users/tatu/Documents/GitHub/blog-api-main && ./quick_test_update.sh core"
alias bloghist="cd /Users/tatu/Documents/GitHub/blog-api-main && ./quick_test_update.sh history"
```

### 📈 **継続的監視**
```bash
# 作業中に定期実行（推奨）
watch -n 300 './quick_test_update.sh core'  # 5分毎
```

### 🎨 **カスタマイズ**
- `quick_test_update.sh` を編集して独自オプション追加
- `test_runner_with_history.py` で出力形式カスタマイズ
- `.coveragerc_core` でカバレッジ対象調整

---

## 🚨 **トラブルシューティング**

### ❌ **スクリプトが実行できない**
```bash
# 実行権限を付与
chmod +x quick_test_update.sh
```

### ❌ **テストが失敗する**
```bash
# 依存関係確認
pip list | grep -E "(pytest|coverage)"

# 仮想環境確認
which python
```

### ❌ **カバレッジが0%**
```bash
# テストファイル確認
find tests/ -name "*.py" | wc -l

# 設定ファイル確認
cat .coveragerc_core
```

---

## 📚 **詳細ドキュメント**

- 📖 **完全手順書**: `TEST_REPORT_UPDATE_GUIDE.md` - 詳細な操作手順
- 🚀 **クイックリファレンス**: `QUICK_TEST_COMMANDS.md` - ワンライナー集
- 📋 **基本ガイド**: `README_TEST_GUIDE.md` - シンプルな使い方

---

## 🎯 **まとめ**

**日常開発で覚えるべきコマンドはたった2つ！**

```bash
# 1. 全テスト実行（最重要）
python test_runner_with_history.py

# 2. 履歴確認
./quick_test_update.sh history
```

**これだけで、バグレポートとカバレッジレポートが自動更新され、品質管理が完璧になります！** 🎉

---

*🔄 このガイドは機能追加・改善に合わせて随時更新されます*
