# Render.com デプロイ設定ガイド

## 1. PostgreSQLデータベースの作成

1. Renderダッシュボードにログイン
2. "New +" → "PostgreSQL" を選択
3. 以下の設定を行う：
   - Name: `blog-api-db`
   - Database: `blog_db`
   - User: `blog_user`
   - Region: 任意（Oregon推奨）
   - PostgreSQL Version: 15
   - Plan: Free（開発用）またはStarter（本番用）

4. データベース作成後、"Internal Database URL"をコピー

## 2. Webサービスの作成

1. "New +" → "Web Service" を選択
2. GitHubリポジトリを接続
3. 以下の設定を行う：

### Basic Settings
- **Name**: `blog-api`
- **Region**: データベースと同じリージョン
- **Branch**: `main`
- **Root Directory**: （空欄）
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Environment Variables
以下の環境変数を設定：

```
ENVIRONMENT=production
DATABASE_URL=<PostgreSQLのInternal Database URLをペースト>
SECRET_KEY=<ランダムな64文字の文字列>
ALGORITHM=HS256
CORS_ORIGINS=<フロントエンドのURL>
AA03=[database.py]
AA05=[models.py]
AA06=[schemas.py]
AA07=[articles.py]
AA08=[users.py]
AA09=[auth.py]
AA10=[oauth2.py]
```

### Advanced Settings
- **Auto-Deploy**: Yes
- **Health Check Path**: `/` （オプション）

## 3. データベース初期化

Webサービスが正常にデプロイされた後、以下の手順でデータベースを初期化：

### 方法1: Render Shell経由
1. Renderダッシュボードでサービスを選択
2. "Shell" タブをクリック
3. 以下のコマンドを実行：
```bash
python database_setup.py --environment production --init-data
```

### 方法2: ローカルから本番DBに接続
1. ローカルの`.env`ファイルを一時的に本番設定に変更
2. 以下のコマンドを実行：
```bash
ENVIRONMENT=production DATABASE_URL="<本番PostgreSQL URL>" python database_setup.py --init-data
```

## 4. 動作確認

デプロイ完了後、以下のURLで動作確認：

- **APIドキュメント**: `https://your-service-name.onrender.com/docs`
- **記事一覧**: `https://your-service-name.onrender.com/api/v1/public/articles`
- **記事検索**: `https://your-service-name.onrender.com/api/v1/public/articles/search?q=FastAPI`

## 5. SSL/HTTPS

RenderではHTTPSが自動的に有効になります。カスタムドメインを使用する場合は、Renderの設定でドメインを追加してください。

## 6. ログとモニタリング

- **ログ**: Renderダッシュボードの"Logs"タブで確認
- **メトリクス**: "Metrics"タブでCPU・メモリ使用量を確認
- **ヘルスチェック**: 自動的に実行されます

## 7. 環境変数の管理

本番環境では以下に注意：
- `SECRET_KEY`は長いランダム文字列を使用
- `DATABASE_URL`はRenderが自動生成
- `CORS_ORIGINS`はフロントエンドのドメインのみ許可

## 8. トラブルシューティング

### よくある問題と解決法

1. **データベース接続エラー**
   - DATABASE_URLが正しく設定されているか確認
   - PostgreSQLサービスが起動しているか確認

2. **デプロイエラー**
   - requirements.txtにpsycopg2-binaryが含まれているか確認
   - Build Commandが正しく設定されているか確認

3. **CORS エラー**
   - CORS_ORIGINSにフロントエンドのURLが含まれているか確認

4. **テーブルが存在しない**
   - database_setup.pyを実行してテーブルを作成

## 9. セキュリティ設定

本番環境では以下を確認：
- 環境変数が適切に設定されている
- SECRET_KEYが安全な値になっている
- CORSが適切に制限されている
- HTTPSが有効になっている
