# 🔧 テストレポート更新手順書

**プロジェクト**: Blog API Testing System  
**作成日**: 2025年6月6日  
**目的**: 機能改善・バグ修正時のテストレポート自動更新

---

## 📋 目次
1. [概要](#概要)
2. [事前準備](#事前準備)
3. [基本の更新手順](#基本の更新手順)
4. [詳細コマンド集](#詳細コマンド集)
5. [レポート確認方法](#レポート確認方法)
6. [トラブルシューティング](#トラブルシューティング)

---

## 🎯 概要

機能改善やバグ修正を行った際に、以下のレポートを自動更新するための手順書です：

- **バグ履歴レポート** (`bug_history.json`)
- **カバレッジ履歴レポート** (`coverage_history.json`)
- **Markdownレポート** (`test_reports/`)
- **HTMLレポート** (`test_reports/`)
- **カバレッジHTMLレポート** (`htmlcov_*/`)

---

## 🛠️ 事前準備

### 1. ワークスペースに移動
```bash
cd /Users/tatu/Documents/GitHub/blog-api-main
```

### 2. 仮想環境の有効化（必要に応じて）
```bash
source .venv/bin/activate
```

### 3. 依存関係の確認
```bash
pip list | grep -E "(pytest|coverage)"
```

---

## 🚀 基本の更新手順

### ✅ **手順1: 全テスト実行 + 履歴更新**
```bash
# 全テスト実行 + バグ・カバレッジ履歴の自動更新
python test_runner_with_history.py
```

**実行内容:**
- 全266テストの実行
- バグ履歴の自動記録
- カバレッジ履歴の自動記録
- Markdown/HTMLレポートの自動生成
- タイムスタンプ付きファイル生成

### ✅ **手順2: 特定モジュールのテスト実行**
```bash
# 特定のテストファイルのみ実行
python test_runner_with_history.py test_user_router

# 複数のテストファイルを実行
python test_runner_with_history.py test_user_router test_auth_router
```

### ✅ **手順3: 統合テストのみ実行**
```bash
# 統合テストのみ実行
python test_runner_with_history.py test_integration test_user_deletion_integration
```

---

## 📝 詳細コマンド集

### 🔍 **個別実行コマンド**

#### A. 単体テスト実行（履歴なし）
```bash
# 特定テストファイルの実行
python -m pytest tests/test_user_router.py -v

# カバレッジ付きで実行
python -m pytest tests/test_user_router.py --cov=. --cov-report=html -v

# コア機能のみカバレッジ（テスト関連ファイル除外）
python -m pytest tests/ --cov=. --cov-config=.coveragerc_core --cov-report=html:htmlcov_core_only -v
```

#### B. カバレッジのみ測定
```bash
# 全体カバレッジ
python -m pytest tests/ --cov=. --cov-report=term-missing --cov-report=html

# テスト関連ファイル除外カバレッジ
python -m pytest tests/ --cov=. --cov-config=.coveragerc_core --cov-report=term-missing --cov-report=html:htmlcov_core_only
```

#### C. 特定の問題のデバッグ
```bash
# 失敗したテストの詳細表示
python -m pytest tests/test_user_router.py -v --tb=long

# 特定のテストメソッドのみ実行
python -m pytest tests/test_user_router.py::TestCreateUserEndpoint::test_create_user_success -v

# ログ出力付きでテスト実行
python -m pytest tests/test_user_router.py -v -s --log-cli-level=INFO
```

### 📊 **履歴管理コマンド**

#### A. バグ履歴の確認
```bash
# 最新のバグ履歴表示
python -c "
import json
with open('bug_history.json', 'r', encoding='utf-8') as f:
    history = json.load(f)
    print(f'総実行回数: {len(history)}')
    for i, entry in enumerate(history[-5:], 1):
        status = '✅' if entry['success_rate'] == 100.0 else '❌'
        print(f'{status} {entry[\"timestamp\"]} | {entry[\"test_name\"]} | 成功率: {entry[\"success_rate\"]}%')
"
```

#### B. カバレッジ履歴の確認
```bash
# 最新のカバレッジ履歴表示
python -c "
import json
with open('coverage_history.json', 'r', encoding='utf-8') as f:
    history = json.load(f)
    print(f'総測定回数: {len(history)}')
    for entry in history[-5:]:
        print(f'📊 {entry[\"timestamp\"]} | {entry[\"test_name\"]} | カバレッジ: {entry[\"coverage_percent\"]}%')
"
```

#### C. 履歴のクリーンアップ（必要時）
```bash
# 古いテスト結果ファイルの削除（30日以上前）
find . -name "test_results_*.xml" -mtime +30 -delete
find . -name "coverage_*.json" -mtime +30 -delete

# 古いHTMLカバレッジフォルダの削除
find . -name "htmlcov_*" -type d -mtime +30 -exec rm -rf {} +
```

---

## 📋 レポート確認方法

### 🔍 **A. 最新レポートの確認**
```bash
# 最新のMarkdownレポート表示
ls -la test_reports/test_report_*.md | tail -1

# 最新のHTMLレポートをブラウザで開く
ls -la test_reports/test_report_*.html | tail -1
# ↑ 表示されたファイルパスをブラウザで開く
```

### 📊 **B. カバレッジレポートの確認**
```bash
# 最新のカバレッジHTMLレポートをブラウザで開く
ls -ld htmlcov_* | tail -1
# ↑ 表示されたフォルダ内のindex.htmlをブラウザで開く

# コア機能のみのカバレッジレポート
open htmlcov_core_only/index.html
```

### 📈 **C. 履歴サマリーの確認**
```bash
# 履歴サマリーの表示（test_runner_with_history.py実行後に自動表示）
python test_runner_with_history.py
# ↑ 最後に履歴サマリーが表示される
```

---

## 🎯 シナリオ別の実行例

### 📝 **シナリオ1: ユーザー機能を修正した場合**
```bash
# 1. ユーザー関連テストのみ実行
python test_runner_with_history.py test_user_router

# 2. 統合テストも実行（ユーザー削除機能含む）
python test_runner_with_history.py test_user_router test_user_deletion_integration

# 3. 全体への影響確認
python test_runner_with_history.py
```

### 📝 **シナリオ2: 記事機能を修正した場合**
```bash
# 1. 記事関連テストのみ実行
python test_runner_with_history.py test_article_router

# 2. 統合テストも実行
python test_runner_with_history.py test_article_router test_integration

# 3. カバレッジの改善確認
python -m pytest tests/ --cov=routers.article --cov-report=term-missing -v
```

### 📝 **シナリオ3: 認証機能を修正した場合**
```bash
# 1. 認証関連テストのみ実行
python test_runner_with_history.py test_auth_router test_oauth2 test_custom_token

# 2. 統合テストも実行
python test_runner_with_history.py test_auth_router test_integration

# 3. セキュリティ関連テスト確認
python -m pytest tests/test_oauth2.py tests/test_custom_token.py -v
```

### 📝 **シナリオ4: 新機能追加の場合**
```bash
# 1. 新機能のテストファイル作成後
python test_runner_with_history.py test_new_feature

# 2. 全体テスト実行
python test_runner_with_history.py

# 3. カバレッジ向上の確認
python -m pytest tests/ --cov=. --cov-config=.coveragerc_core --cov-report=term-missing
```

---

## 🔧 トラブルシューティング

### ❌ **問題1: テストが失敗する場合**
```bash
# 詳細なエラー情報を表示
python -m pytest tests/test_failing_module.py -v --tb=long

# ログ出力でデバッグ
python -m pytest tests/test_failing_module.py -v -s --log-cli-level=DEBUG

# 特定のテストのみ実行してデバッグ
python -m pytest tests/test_failing_module.py::TestClass::test_method -v -s
```

### ❌ **問題2: カバレッジが測定されない場合**
```bash
# pytest-covの確認
pip show pytest-cov

# 設定ファイルの確認
cat .coveragerc_core

# 手動でカバレッジ実行
coverage run -m pytest tests/
coverage report
coverage html
```

### ❌ **問題3: 履歴ファイルが破損した場合**
```bash
# バックアップから復元（存在する場合）
cp bug_history.json.bak bug_history.json
cp coverage_history.json.bak coverage_history.json

# 新規で履歴を開始
echo "[]" > bug_history.json
echo "[]" > coverage_history.json
```

### ❌ **問題4: メモリ不足エラーの場合**
```bash
# テストを分割して実行
python test_runner_with_history.py test_user_router
python test_runner_with_history.py test_article_router
python test_runner_with_history.py test_auth_router

# 並列実行を無効化
python -m pytest tests/ -v --disable-warnings
```

---

## 📚 参考情報

### 🔗 **関連ファイル**
- `test_runner_with_history.py` - メインの実行スクリプト
- `.coveragerc_core` - コア機能カバレッジ設定
- `bug_history.json` - バグ履歴データ
- `coverage_history.json` - カバレッジ履歴データ
- `test_reports/` - 生成されるレポートフォルダ

### 📊 **レポート生成のタイミング**
- **即座に更新**: `test_runner_with_history.py`実行時
- **自動生成**: テスト実行毎にタイムスタンプ付きファイル
- **履歴追記**: 既存履歴に新しい実行結果を追加

### 🎯 **ベストプラクティス**
1. **修正前**: 現在のテスト状況を記録
2. **修正後**: すぐにテスト実行でバグ修正を確認
3. **定期実行**: 週1回の全体テスト実行
4. **リリース前**: 全テスト + カバレッジ確認

---

## 🎉 まとめ

この手順書により、機能改善やバグ修正時に簡単にテストレポートを更新できます。

**基本コマンド:**
```bash
# 最も使用頻度の高いコマンド
python test_runner_with_history.py
```

**問題発生時:**
```bash
# デバッグ用コマンド
python -m pytest tests/test_specific.py -v --tb=long -s
```

これらのコマンドを活用して、継続的な品質管理を実現してください！

---

**📅 最終更新**: 2025年6月6日  
**🎯 対象**: Blog API Testing System  
**📊 現在のテスト数**: 266個 (100%成功)  
**📈 現在のカバレッジ**: 83% (コア機能)
