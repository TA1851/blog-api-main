# 📚 ブログAPI プロジェクト構成 

## 🎯 プロジェクト概要

FastAPIを使用したブログAPIシステム。ユーザー認証、記事管理、メール認証などの機能を提供します。

### 🛠️ 技術スタック

| 技術 | バージョン | 役割 |
|------|-----------|------|
| **Python** | 3.11.11 | メイン言語 |
| **FastAPI** | 0.115.12 | Webフレームワーク |
| **SQLAlchemy** | - | ORM |
| **SQLite** | - | データベース（開発環境） |
| **PostgreSQL** | - | データベース（本番環境） |
| **JWT** | - | 認証トークン |
| **Pytest** | - | テストフレームワーク |
| **Sphinx** | - | ドキュメント生成 |
| **Alembic** | - | データベースマイグレーション |

## 📁 プロジェクト構造

```
blog-api-main/
├── 📄 設定ファイル
│   ├── .env                    # 環境変数設定
│   ├── .env.production         # 本番環境設定
│   ├── pyproject.toml          # プロジェクト設定・依存関係
│   ├── requirements.txt        # Python パッケージ依存関係
│   ├── runtime.txt             # Python バージョン指定
│   ├── alembic.ini            # データベースマイグレーション設定
│   └── mypy.ini               # 型チェック設定
│
├── 🚀 アプリケーションコア
│   ├── main.py                # FastAPI エントリーポイント
│   ├── database.py            # データベース接続・設定
│   ├── models.py              # SQLAlchemy データモデル
│   ├── schemas.py             # Pydantic バリデーションスキーマ
│   ├── hashing.py             # パスワードハッシュ化
│   ├── oauth2.py              # JWT認証実装
│   └── custom_token.py        # カスタムトークン生成
│
├── 🛣️ routers/               # API エンドポイント
│   ├── __init__.py
│   ├── article.py             # 記事関連 API
│   ├── auth.py                # 認証関連 API
│   └── user.py                # ユーザー関連 API
│
├── 📝 logger/                 # ロギングシステム
│   ├── __init__.py
│   └── custom_logger.py       # カスタムロガー実装
│
├── 🧪 tests/                  # テストスイート
│   ├── test_*.py              # 各種テストファイル
│   ├── htmlcov/              # カバレッジレポート（HTML）
│   ├── report/               # 統合テストレポート
│   └── Coverage_Report_*.html # カバレッジレポート
│
├── 🗃️ データベース
│   ├── blog.db               # SQLite データベース（開発環境）
│   ├── blog_api.db           # 予備データベース
│   ├── alembic/              # マイグレーションファイル
│   └── db_bak/               # データベースバックアップ
│
├── 📖 doc/                   # Sphinx ドキュメント
│   ├── _build/               # 生成されたドキュメント
│   ├── *.rst                 # ドキュメントソース
│   └── conf.py               # Sphinx設定
│
├── 📊 reports/               # レポート・分析
├── 📜 scripts/               # 運用スクリプト
├── 🔧 utils/                 # ユーティリティ
├── 🖼️ img/                   # 画像ファイル
├── 📦 site-packages/         # ローカルパッケージ
└── 🗂️ log/                   # ログファイル
```

## 🎭 主要コンポーネント詳細

### 🚀 アプリケーションコア

#### `main.py` - エントリーポイント
- FastAPIアプリケーションの初期化
- CORS設定
- ルーター登録
- エラーハンドリング設定

#### `database.py` - データベース管理
- 環境変数からDB設定を読み込み
- SQLAlchemy エンジン・セッション管理
- 開発環境（SQLite）・本番環境（PostgreSQL）の切り替え

#### `models.py` - データモデル
```python
- Article: 記事モデル
- User: ユーザーモデル  
- EmailVerification: メール認証モデル
```

#### `schemas.py` - バリデーションスキーマ
```python
- ArticleBase: 記事基本スキーマ
- PublicArticle: パブリック記事スキーマ
- User: ユーザースキーマ
- Login: ログインスキーマ
- Token: JWT トークンスキーマ
```

### 🛣️ APIエンドポイント

#### `routers/article.py` - 記事API
- `GET /api/v1/articles` - 記事一覧取得（認証必要）
- `GET /api/v1/articles/{id}` - 記事詳細取得（認証必要）
- `POST /api/v1/articles` - 記事作成（認証必要）
- `PUT /api/v1/articles` - 記事更新（認証必要）
- `DELETE /api/v1/articles` - 記事削除（認証必要）
- `GET /api/v1/public/articles` - パブリック記事一覧
- `GET /api/v1/public/articles/{id}` - パブリック記事詳細
- `GET /api/v1/public/articles/search` - パブリック記事検索

#### `routers/auth.py` - 認証API
- `POST /api/v1/login` - ログイン
- `POST /api/v1/register` - ユーザー登録
- `POST /api/v1/verify-email` - メール認証

#### `routers/user.py` - ユーザーAPI
- `GET /api/v1/user/{id}` - ユーザー詳細取得
- `PUT /api/v1/user/{id}` - ユーザー情報更新
- `DELETE /api/v1/user/{id}` - ユーザー削除

### 🔐 セキュリティ

#### `oauth2.py` - JWT認証
- JWT トークン生成・検証
- 認証が必要なエンドポイントの保護
- ユーザー情報の取得

#### `hashing.py` - パスワード管理
- bcrypt を使用したパスワードハッシュ化
- パスワード検証

### 📝 ログ機能

#### `logger/custom_logger.py`
- 構造化ログ出力
- エラーログとアクセスログの分離
- ファイル・コンソール出力対応

### 🧪 テスト環境

#### テストカバレッジ
- 単体テスト（Unit Tests）
- 統合テスト（Integration Tests）
- API エンドポイントテスト
- データベーステスト

#### テストファイル構成
```
tests/
├── test_main.py              # メインアプリケーション
├── test_models.py            # データモデル
├── test_schemas.py           # バリデーションスキーマ
├── test_database.py          # データベース接続
├── test_article_router.py    # 記事API
├── test_auth_router.py       # 認証API
├── test_user_router.py       # ユーザーAPI
├── test_oauth2.py            # JWT認証
├── test_hashing.py           # パスワードハッシュ
└── test_integration.py       # 統合テスト
```

## 🗄️ データベース設計

### テーブル構成

#### `articles` テーブル
| カラム | 型 | 説明 |
|--------|----|----- |
| id | INTEGER | 主キー（自動生成） |
| article_id | INTEGER | 記事ID |
| title | VARCHAR | 記事タイトル |
| body | VARCHAR | 記事本文 |
| user_id | INTEGER | 作成者ID（外部キー） |

#### `users` テーブル
| カラム | 型 | 説明 |
|--------|----|----- |
| id | INTEGER | 主キー（自動生成） |
| name | VARCHAR | ユーザー名 |
| email | VARCHAR | メールアドレス |
| password | VARCHAR | ハッシュ化パスワード |
| is_active | BOOLEAN | アクティブ状態 |

#### `email_verifications` テーブル
| カラム | 型 | 説明 |
|--------|----|----- |
| id | INTEGER | 主キー |
| email | VARCHAR | メールアドレス |
| token | VARCHAR | 認証トークン |
| password_hash | VARCHAR | ハッシュ化パスワード |
| is_verified | BOOLEAN | 認証状態 |
| created_at | DATETIME | 作成日時 |
| expires_at | DATETIME | 有効期限 |

## 🚀 デプロイメント

### 環境設定

#### 開発環境
- **データベース**: SQLite (`./blog.db`)
- **サーバー**: `uvicorn main:app --reload`

#### 本番環境
- **データベース**: PostgreSQL
- **デプロイ先**: Render
- **環境変数**: `.env.production`

### 環境変数

```bash
# 必須環境変数
ENVIRONMENT=development|production
SECRET_KEY=<JWT署名用秘密鍵>
ALGORITHM=HS256

# データベース（本番環境のみ）
DATABASE_URL=<PostgreSQL接続URL>
POSGRE_URL=<PostgreSQL接続URL>

# CORS設定
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## 🔧 開発・運用コマンド

### アプリケーション起動
```bash
# 開発サーバー起動
fastapi dev main.py

# 本番サーバー起動  
uvicorn main:app --host 0.0.0.0 --port 8000
```

### テスト実行
```bash
# 全テスト実行
pytest

# カバレッジ付きテスト
pytest --cov=. --cov-report=html

# 継続的テスト
python run_continuous_tests.py
```

### データベース操作
```bash
# マイグレーション生成
alembic revision --autogenerate -m "マイグレーション名"

# マイグレーション実行
alembic upgrade head
```

### ドキュメント生成
```bash
# Sphinx ドキュメント生成
cd doc && make html
```

## 📈 モニタリング・品質管理

### コードカバレッジ
- 目標: 90%以上
- レポート: `htmlcov/index.html`

### コード品質
- **型チェック**: mypy
- **フォーマット**: black, isort
- **リンティング**: flake8

### ログ監視
- アプリケーションログ: `log/`
- エラー追跡: カスタムロガー
- パフォーマンス監視: FastAPI自動生成メトリクス

## 🔍 トラブルシューティング

### よくある問題

1. **データベース接続エラー**
   - `.env`ファイルの環境変数を確認
   - データベースファイルの存在確認

2. **JWT認証エラー**
   - `SECRET_KEY`の設定確認
   - トークンの有効期限確認

3. **CORS エラー**
   - `CORS_ORIGINS`の設定確認
   - フロントエンドのオリジン確認

### デバッグモード
```bash
# 詳細ログ出力
export LOG_LEVEL=DEBUG
fastapi dev main.py
```

---

📝 **最終更新**: 2025年6月4日  
🏗️ **プロジェクトバージョン**: 1.0.0  
👥 **開発チーム**: Blog API Team
