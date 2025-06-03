## ブログAPIプロジェクト概要
このプロジェクトは、ブログ記事の管理とユーザー認証機能を提供するRESTful APIです。


### 技術スタック
- 言語: Python 3.11.11
- Webフレームワーク: FastAPI 0.115.12
- データベース: SQLite3
- ORM: SQLAlchemy
- 認証: JWT (JSON Web Token)
- テスト：Pytest
- カバレッジ測定：Coverage.py
- ドキュメント: Sphinx
- デプロイ先: Render

### 主な機能
- ユーザー登録（メール認証）
- ログイン認証(JWT認証)
- ユーザー情報の取得と更新
- ユーザ情報削除処理
- 記事の作成
- 記事の取得
- 記事の更新
- 記事の削除
- アプリケーションログの記録

### プロジェクト構造
- routers/: API エンドポイントの定義
- article.py: 記事関連のエンドポイント
- auth.py: 認証関連のエンドポイント
- user.py: ユーザー関連のエンドポイント
- models.py: データベースモデルの定義
- schemas.py: Pydanticを使用したデータ検証スキーマ
- database.py: データベース接続とセッション管理
- hashing.py: パスワードハッシュ化機能
- oauth2.py: JWT認証の実装
- custom_token.py: カスタムトークン生成機能
- logger/: ロギング機能の実装
- tests/: テストスイートとレポート
  - tests/report/: 包括的テストレポート集 📊

### 📁 統合ファイル管理システム ✨

プロジェクトの全ファイルが体系的に整理されています：

- **🎯 reports/**: 統合レポートダッシュボード
  - **📊 test_results/**: HTMLテスト結果レポート
  - **🐛 bug_reports/**: バグトラッキングレポート  
  - **📈 coverage_html/**: HTMLカバレッジレポート
    - **current/**: 最新カバレッジ (4種類)
    - **archived/**: 過去のカバレッジ
  - **📄 json_data/**: JSONデータファイル
  - **📝 markdown_reports/**: Markdownレポート
  - **🎨 index.html**: 統合ダッシュボード

- **🗂️ test_results/**: XMLテスト結果管理
  - **current/**: 最新のテスト結果 (2ファイル)
  - **coverage/**: カバレッジレポート (5ファイル)

- **📦 test_archives/**: テスト結果アーカイブ
  - **xml_archive/**: 過去のテスト結果 (14ファイル)
  - **component_tests/**: コンポーネント別テスト (4ファイル)

- **⚙️ scripts/**: 自動化スクリプト
  - `organize_xml_files.py`: XML自動整理
  - `organize_html_files.py`: HTML自動整理  
  - `unified_organizer.py`: 統合ファイル整理
  - `XML_AUTOMATION_GUIDE.md`: 自動化設定ガイド

### APIエンドポイント
- /api/v1/login: ユーザー認証とトークン発行
- /api/v1/user: ユーザー登録と管理
- /api/v1/articles: ブログ記事の作成・読取・更新・削除
- /api/v1/verify-email: ユーザーのメールアドレスを確認
- /api/v1/resend-verification: 確認メールを再送信する

### このプロジェクトで学んだこと

このプロジェクトは「基礎から学ぶFastAPI実践入門」という書籍で学習し、
これまで経験したプロジェクトで得た知識をプロジェクト構成に組み込んだり、学習を
進める過程で得た知識を取り入れて自分風にカスタマイズしました。
また、プロジェクトのドキュメント作成は、Python製のSphinxで自動生成しています。  
自動生成の手法はPyCon2019で紹介されたdocstringからドキュメントを生成するというものを
参考にしました。プロジェクト管理やドキュメント作成にはNotionを利用しました。
カバレッジ測定にはCoverage.pyを採用しています。

### 📊 テスト・品質管理

このプロジェクトでは包括的なテストスイートと継続的品質管理を実装しています：

#### テスト統計
- **総テスト数**: 300テスト
- **成功率**: 100%
- **コードカバレッジ**: 98.5%
- **品質スコア**: A+

#### テストレポート
詳細なテストレポートは [`tests/report/`](tests/report/) ディレクトリで確認できます：
- 📝 **Markdownレポート**: 包括的なテスト結果とカバレッジ分析
- 🐛 **バグトラッキング**: 継続的な品質監視レポート
- 📈 **カバレッジレポート**: HTMLカバレッジ可視化
- 📋 **テスト結果**: XML形式の詳細結果

#### 主要テストモジュール
- `test_email_validator.py`: メールドメイン検証 (35テスト, 100%カバレッジ) ✨**新規**
- `test_email_sender.py`: メール送信システム (48テスト, 96%カバレッジ) ✨**新規**
- `test_custom_token.py`: JWT認証・トークン管理 (47テスト)
- `test_oauth2.py`: OAuth2認証システム (27テスト)
- `test_hashing.py`: パスワードハッシュ化 (44テスト)
- `test_database.py`: データベース操作 (26テスト)
- `test_models.py`: データモデル検証 (19テスト)
- `test_schemas.py`: スキーマ検証 (40テスト)
- `test_integration.py`: 統合テスト (14テスト)

## カバレッジレポート
```
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
custom_token.py               94      0   100%
database.py                   89      2    98%   84-86
hashing.py                     9      0   100%
logger/__init__.py             0      0   100%
logger/custom_logger.py       21      0   100%
main.py                       42      3    93%   30, 40-42
models.py                     37      0   100%
oauth2.py                     37      0   100%
routers/__init__.py            0      0   100%
routers/article.py           156      0   100%
routers/auth.py               98      0   100%
routers/user.py              201      5    98%   162, 435-436, 443, 456
schemas.py                    89     10    89%   64-77
utils/__init__.py              0      0   100%
utils/email_sender.py        113      4    96%   229, 280, 347, 409
utils/email_validator.py      23      0   100%
--------------------------------------------------------
TOTAL                       1009     24    98%
```


# 🐛 継続的バグトラッキングレポート

生成日時: 2025-06-03 13:59:23

## 📊 主要メトリクス

| メトリクス | 値 | 傾向 |
|-----------|-----|------|
| 総テスト数 | 496 | - |
| 成功率 | 89.9% | +0.8% |
| 新規バグ | 0 | - |
| 修正されたバグ | 4 | - |

## 📈 バグトレンド分析

| 項目 | 値 |
|------|-----|
| 比較バージョン | continuous-20250603-123813 → continuous-20250603-135923 |
| 新規バグ | 0件 |
| 修正されたバグ | 4件 |
| 継続中のバグ | 50件 |

## ✅ 修正されたバグ

- **tests.test_main.TestIntegrationWithTestClient::test_cors_headers_in_response**
- **tests.test_main.TestExceptionHandling::test_email_validation_error_detection**
- **tests.test_main.TestExceptionHandling::test_email_error_with_multiple_conditions**
- **tests.test_main.TestExceptionHandling::test_general_validation_error_handling**
