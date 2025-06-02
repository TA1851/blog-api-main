# HTMLレポート管理ディレクトリ

このディレクトリは、Blog APIプロジェクトで生成される各種HTMLレポートを整理・管理するためのものです。

## ディレクトリ構造

```
reports/
├── test_results/           # テスト結果HTMLレポート
├── bug_reports/           # バグトラッキングレポート
└── coverage_html/         # HTMLカバレッジレポート
    ├── current/          # 最新のカバレッジレポート
    └── archived/         # 過去のカバレッジレポート
```

## 各ディレクトリの説明

### 📊 test_results/
テスト実行結果のHTMLレポートが保存されます。
- `test_results_main.html` - メインテストスイートの結果
- `test_results_auth_router*.html` - 認証ルーターのテスト結果
- `test_results_with_article_router.html` - 記事ルーター込みのテスト結果

### 🐛 bug_reports/
バグトラッキングと品質管理レポートが保存されます。
- `bug_report_latest.html` - 最新のバグレポート
- `bug_report_v*.html` - バージョン別バグレポート
- `comprehensive_bug_tracking_report.html` - 包括的バグトラッキングレポート

### 📈 coverage_html/
HTMLフォーマットのコードカバレッジレポートが保存されます。

#### current/ (最新カバレッジ)
- `main_coverage/` - メインアプリケーションのカバレッジ
- `full_coverage/` - 完全なテストカバレッジ
- `auth_final_coverage/` - 認証機能の最終カバレッジ
- `routers_final_coverage/` - ルーター機能の最終カバレッジ

#### archived/ (過去のカバレッジ)
- `user_router_coverage/` - ユーザールーターのカバレッジ（履歴）
- `tests_coverage/` - テスト固有のカバレッジ（履歴）

## アクセス方法

### ローカルでの確認
```bash
# 最新のメインカバレッジを確認
open reports/coverage_html/current/main_coverage/index.html

# 最新のテスト結果を確認
open reports/test_results/test_results_main.html

# 最新のバグレポートを確認
open reports/bug_reports/comprehensive_bug_tracking_report.html
```

### VS Codeでの確認
1. VS Codeのサイドバーでファイルを右クリック
2. "Open with Live Server" または "Preview" を選択

## ファイル管理ルール

### 命名規則
- **テスト結果**: `test_results_<component>_<version>.html`
- **バグレポート**: `bug_report_<version>_<component>.html`
- **カバレッジ**: ディレクトリ名で管理 (`<component>_coverage/`)

### 保持期間
- **current/**: 常に最新版を保持
- **archived/**: 30日経過後に削除検討
- **test_results/**: 各バージョンのマイルストーンレポートを保持

### 更新頻度
- テスト結果: テスト実行時に自動生成
- バグレポート: 品質管理時に手動生成
- カバレッジ: CI/CDパイプラインで自動生成

## 自動化連携

### Coverage.py設定
```bash
# HTMLカバレッジレポート生成
coverage html --directory=reports/coverage_html/current/main_coverage/
```

### Pytest設定
```bash
# HTMLテストレポート生成
pytest --html=reports/test_results/test_results_latest.html
```

## トラブルシューティング

### ファイルが見つからない場合
1. 生成スクリプトが正しく実行されているか確認
2. ディレクトリの権限を確認
3. 古いファイルがアーカイブされていないか確認

### レポートが表示されない場合
1. ブラウザでローカルファイルのアクセス許可を確認
2. HTMLファイルの整合性を確認
3. 依存するCSSやJSファイルの存在を確認

---
**作成日**: 2025年6月2日  
**管理対象**: 135個のHTMLファイル  
**自動整理**: `scripts/organize_html_files.py` (作成予定)
