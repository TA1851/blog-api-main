# 🧪 Blog API テストガイド

**最終更新**: 2025年6月12日  
**目的**: テスト実行とカバレッジ確認の簡単ガイド

---

## 🚀 **最速スタート（これだけでOK！）**

```bash
# プロジェクトディレクトリに移動
cd /Users/tatu/Documents/GitHub/blog-api-main

# 全テスト実行 + レポート自動更新
python test_runner_with_history.py
```

**✅ 上記1行で以下が全て実行されます:**
- 全てのテスト実行
- カバレッジ測定
- レポート生成
- 履歴更新

---

## 📊 **機能別テスト**

```bash
# ユーザー機能のテスト
./quick_test_update.sh user

# 記事機能のテスト
./quick_test_update.sh article

# 認証機能のテスト
./quick_test_update.sh auth

# 統合テスト
./quick_test_update.sh integration

# コア機能のみ（高速）
./quick_test_update.sh core
```

---

## 📋 **レポート確認**

### **テスト履歴確認**
```bash
# 履歴サマリー表示
./quick_test_update.sh history

# カバレッジレポート表示
coverage report -m
```

### **HTMLレポートをブラウザで確認**
```bash
# カバレッジHTMLレポートを開く
open htmlcov_core_only/index.html

# 最新のHTMLテストレポートを開く
open test_reports/$(ls test_reports/*.html | tail -1)
```

### **最新レポートファイル確認**
```bash
# 最新のテストレポート一覧
ls -la test_reports/ | tail -5

# 最新のMarkdownレポート表示
cat $(ls test_reports/test_report_*.md | tail -1)
```

---

## 🔍 **個別テスト実行（デバッグ用）**

### **特定のテストファイル実行**
```bash
# ユーザー関連テスト
python -m pytest tests/test_user_router.py -v

# 記事関連テスト
python -m pytest tests/test_article_router.py -v

# 認証関連テスト
python -m pytest tests/test_auth.py -v
```

### **詳細ログ付き実行**
```bash
# ログ出力付きでテスト実行
python -m pytest tests/test_user_router.py -v -s --log-cli-level=INFO

# 特定のテストメソッドのみ実行
python -m pytest tests/test_user_router.py::TestCreateUserEndpoint::test_create_user_success -v -s
```

---

## ⚡ **よく使うワンライナー**

```bash
# 開発中の基本フロー
python test_runner_with_history.py && ./quick_test_update.sh history

# 高速チェック
./quick_test_update.sh core && coverage report -m

# 全体確認
python test_runner_with_history.py && open htmlcov_core_only/index.html
```

---

## 📁 **主要ファイル場所**

- **テスト履歴**: `bug_history.json`, `coverage_history.json`
- **HTMLレポート**: `test_reports/` フォルダ
- **カバレッジHTML**: `htmlcov_*` フォルダ
- **メインテストスクリプト**: `test_runner_with_history.py`
- **クイックスクリプト**: `quick_test_update.sh`

---

## 💡 **Tips**

- **日常開発**: `python test_runner_with_history.py` を実行するだけ
- **機能追加時**: 該当機能のテストを個別実行してから全体テスト
- **バグ修正時**: 修正後に全体テストで回帰確認
- **レポート確認**: HTMLレポートが最も見やすい

---

**🎯 迷ったら `python test_runner_with_history.py` を実行すれば間違いありません！**
