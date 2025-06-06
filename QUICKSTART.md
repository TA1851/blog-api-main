# 🚀 クイックスタート - 今すぐ始める！

**⏱️ 所要時間: 2分**  
**🎯 目的: テストレポート自動更新の最速導入**

---

## 🏃‍♂️ **Step 1: ワンライン実行**

```bash
cd /Users/tatu/Documents/GitHub/blog-api-main && python test_runner_with_history.py
```

**✅ これだけで完了！**  
- バグ履歴更新
- カバレッジ測定
- HTMLレポート生成
- 全て自動実行

---

## 📊 **Step 2: 結果確認**

```bash
# 履歴サマリー確認
./quick_test_update.sh history

coverage report -m
coverage html
```

---

## ⚡ **Step 3: 日常使いパターン**

### 🔧 **開発中（推奨）**
```bash
# 短時間でコア機能チェック
./quick_test_update.sh core
```

### 🐛 **バグ修正後**
```bash
# 該当機能のテスト
./quick_test_update.sh [user|article|auth|integration]

# 全体確認
python test_runner_with_history.py
```

### 🚀 **リリース前**
```bash
# 完全チェック
python test_runner_with_history.py
./quick_test_update.sh history
```

---

## 💡 **生産性UP設定**

### エイリアス設定（推奨）
```bash
# ~/.zshrc に追加
alias bt="cd /Users/tatu/Documents/GitHub/blog-api-main && python test_runner_with_history.py"
alias bc="cd /Users/tatu/Documents/GitHub/blog-api-main && ./quick_test_update.sh core"
alias bh="cd /Users/tatu/Documents/GitHub/blog-api-main && ./quick_test_update.sh history"
```

設定後は：
```bash
bt    # 全テスト実行
bc    # コア機能テスト
bh    # 履歴確認
```

---

## 🎯 **覚えるコマンド（2つだけ）**

```bash
# 1. メイン実行
python test_runner_with_history.py

# 2. 履歴確認
./quick_test_update.sh history
```

**これで完璧！** 🎉

---

## 📚 **さらに詳しく**

- 📖 **完全ガイド**: `TESTING_MASTER_GUIDE.md`
- 🔧 **詳細手順**: `TEST_REPORT_UPDATE_GUIDE.md`
- ⚡ **コマンド集**: `QUICK_TEST_COMMANDS.md`

---

*🎯 このクイックスタートで、2分でテスト自動化が始められます！*
