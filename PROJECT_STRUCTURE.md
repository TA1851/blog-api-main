# プロジェクト構造ドキュメント
Generated on: 2025年6月2日

## ディレクトリ構造概要

```
blog-api-main/
├── 📁 Core Application Files
│   ├── main.py                 # FastAPIアプリケーションエントリポイント
│   ├── database.py             # データベース接続設定
│   ├── models.py               # SQLAlchemyデータモデル
│   ├── schemas.py              # Pydanticスキーマ定義
│   ├── custom_token.py         # カスタムトークン生成
│   ├── oauth2.py              # OAuth2認証実装
│   └── hashing.py             # パスワードハッシュ化
│
├── 📁 routers/                 # APIルーター
│   ├── auth.py                # 認証エンドポイント
│   ├── user.py                # ユーザー管理エンドポイント
│   └── article.py             # 記事管理エンドポイント
│
├── 📁 tests/                   # テストスイート
│   ├── test_*.py              # 各種テストファイル
│   └── report/                # テストレポート集
│
├── 📁 test_results/ ✨ 新規整理
│   ├── current/               # 最新テスト結果
│   │   ├── test_results_main.xml
│   │   └── test_results_routers_comprehensive.xml
│   ├── coverage/              # カバレッジレポート
│   │   ├── coverage.xml
│   │   ├── coverage_full.xml
│   │   ├── coverage_routers.xml
│   │   ├── coverage_user_router.xml
│   │   └── email_validator_coverage.xml
│   └── README.md              # ディレクトリ使用説明
│
├── 📁 test_archives/ ✨ 新規整理
│   └── xml_archive/           # 過去のテスト結果
│       ├── component_tests/   # コンポーネント別テスト
│       │   ├── email_validator_test_results.xml
│       │   ├── email_sender_test_results.xml
│       │   ├── custom_token_test_results.xml
│       │   └── all_tests_with_email_sender.xml
│       ├── test_results_*.xml # 履歴データ (14ファイル)
│       └── README.md          # アーカイブ管理説明
│
├── 📁 scripts/ ✨ 新規作成
│   ├── organize_xml_files.py  # XML自動整理スクリプト
│   └── XML_AUTOMATION_GUIDE.md # 自動化設定ガイド
│
├── 📁 htmlcov*/               # HTMLカバレッジレポート
├── 📁 logger/                 # ログ機能
├── 📁 doc/                    # Sphinxドキュメント
├── 📁 alembic/                # データベースマイグレーション
├── 📁 db_bak/                 # データベースバックアップ
└── 📁 utils/                  # ユーティリティ関数
```

## ファイル整理の成果

### Before (整理前)
- ✅ ルートディレクトリに18個のXMLファイルが散乱
- ✅ テスト結果の検索が困難
- ✅ 古いファイルと新しいファイルの区別が不明確

### After (整理後)
- ✅ ルートディレクトリ: 0個のXMLファイル
- ✅ 分類別整理: 25個のXMLファイルが適切に分類
- ✅ 自動化スクリプト: 今後の管理を効率化
- ✅ ドキュメント: 維持管理方法を明文化

## ディレクトリ別ファイル数

| ディレクトリ | ファイル数 | 目的 |
|------------|-----------|------|
| test_results/current/ | 2 | 最新の重要なテスト結果 |
| test_results/coverage/ | 5 | カバレッジレポート |
| test_archives/xml_archive/ | 14 | 過去のテスト結果 |
| test_archives/xml_archive/component_tests/ | 4 | コンポーネント別テスト |

## 自動化機能

### 1. XML自動整理スクリプト
- **場所**: `scripts/organize_xml_files.py`
- **機能**: 新しいXMLファイルの自動分類・移動
- **実行**: `python scripts/organize_xml_files.py`

### 2. CI/CD統合
- **GitHub Actions**: XML整理の自動実行
- **Pre-commit Hook**: コミット前の自動整理
- **設定ガイド**: `scripts/XML_AUTOMATION_GUIDE.md`

### 3. .gitignore設定
- ルートディレクトリのXMLファイルを無視
- 整理済みディレクトリのファイルは保持
- 一時ファイルの自動除外

## メンテナンス計画

### 日次作業
- [ ] 新しいXMLファイルの自動整理実行

### 週次作業
- [ ] アーカイブディレクトリのサイズチェック
- [ ] テスト結果の品質確認

### 月次作業
- [ ] 30日以上古いアーカイブファイルの削除検討
- [ ] ディレクトリ構造の最適化確認

## アクセスパターン

### 開発者向け
```bash
# 最新のテスト結果確認
ls test_results/current/

# カバレッジレポート確認
ls test_results/coverage/

# 自動整理実行
python scripts/organize_xml_files.py
```

### CI/CD向け
```bash
# テスト実行後の自動整理
pytest --junit-xml=test_results/current/latest_results.xml
python scripts/organize_xml_files.py
```

---
**整理完了日**: 2025年6月2日  
**整理対象ファイル数**: 25個のXMLファイル  
**作成ディレクトリ数**: 4個  
**作成スクリプト数**: 2個
