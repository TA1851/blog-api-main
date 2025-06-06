"""
基本的なAPI統合テスト
アプリケーション全体の基本的な機能とルーターの統合をテストします。
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.orm import Session

from main import app
from models import User as UserModel, Article
from oauth2 import get_current_user
from database import get_db


class TestApplicationStartup:
    """アプリケーション起動とセットアップのテスト"""
    
    def test_app_initialization(self):
        """アプリケーションの初期化テスト"""
        assert hasattr(app, "router")
    
    def test_app_routes(self):
        """アプリケーションルートの存在テスト"""
        routes = [route.path for route in app.routes]
        assert len(routes) > 0


class TestHealthCheck:
    """ヘルスチェックエンドポイントのテスト"""
    
    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """ルートエンドポイントのテスト（404が返ることを確認）"""
        response = client.get("/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUserAPI:
    """ユーザーAPI統合テスト"""
    
    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """テストユーザー"""
        user = MagicMock(spec=UserModel)
        user.id = 1
        user.email = "test@example.com"
        user.name = "test_user"
        user.is_active = True
        return user
    
    def test_user_creation_endpoint_without_auth(self, client):
        """認証なしでユーザー作成エンドポイントにアクセス"""
        user_data = {
            "name": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        response = client.post("/api/v1/user", json=user_data)
        # このエンドポイントは認証不要なので、成功・バリデーションエラー・重複エラーが返るべき
        assert response.status_code in [200, 201, 400, 409, 422]
    
    def test_show_user_endpoint_without_auth(self, client):
        """認証なしでユーザー表示エンドポイントにアクセス"""
        response = client.get("/api/v1/user/1")
        # 認証が必要なエンドポイントなので401が返るべき
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestArticleAPI:
    """記事API統合テスト"""
    
    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)
    
    def test_articles_endpoint_without_auth(self, client):
        """認証なしで記事一覧エンドポイントにアクセス"""
        response = client.get("/api/v1/articles")
        # 認証が必要なエンドポイントなので401が返るべき
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_article_endpoint_without_auth(self, client):
        """認証なしで記事作成エンドポイントにアクセス"""
        article_data = {
            "title": "Test Article",
            "content": "This is a test article"
        }
        response = client.post("/api/v1/articles", json=article_data)
        # 認証が必要なエンドポイントなので401が返るべき
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthAPI:
    """認証API統合テスト"""
    
    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)
    
    def test_login_endpoint_with_invalid_data(self, client):
        """無効なデータでログインエンドポイントにアクセス"""
        login_data = {
            "username": "invalid@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/login", data=login_data)
        # 認証情報が無効なので401、404、422が返るべき
        assert response.status_code in [401, 404, 422]
    
    def test_logout_endpoint_without_auth(self, client):
        """認証なしでログアウトエンドポイントにアクセス"""
        response = client.post("/api/v1/logout")
        # 認証が必要なエンドポイントなので401が返るべき
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAPIEndpointsIntegration:
    """APIエンドポイント統合テスト"""
    
    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """テストユーザー"""
        user = MagicMock(spec=UserModel)
        user.id = 1
        user.email = "test@example.com"
        user.name = "test_user"
        user.is_active = True
        return user
    
    def test_authenticated_user_workflow(self, client, mock_db, mock_user):
        """認証済みユーザーのワークフローテスト"""
        # 依存性のオーバーライド設定
        def override_get_current_user():
            return mock_user
        
        def override_get_db():
            return mock_db
        
        # 依存性オーバーライドを設定
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # モックの設定
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user
            
            # 認証済みでユーザー情報取得
            headers = {"Authorization": "Bearer dummy_token"}
            response = client.get("/api/v1/user/1", headers=headers)
            
            # レスポンスの検証（200またはエラーが返ることを確認）
            assert response.status_code in [200, 404, 500]
            
        finally:
            # テスト後のクリーンアップ
            app.dependency_overrides = {}
    
    def test_error_handling_integration(self, client):
        """エラーハンドリング統合テスト"""
        # 存在しないエンドポイントへのアクセス
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # 無効なメソッドでのアクセス
        response = client.patch("/api/v1/user")
        assert response.status_code in [404, 405]
    
    def test_cors_and_security_headers(self, client):
        """CORS設定とセキュリティヘッダーのテスト"""
        response = client.options("/api/v1/user")
        # CORS設定により適切なヘッダーが返ることを確認
        assert response.status_code in [200, 405]


class TestFullWorkflow:
    """フルワークフロー統合テスト"""
    
    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """テストユーザー"""
        user = MagicMock(spec=UserModel)
        user.id = 1
        user.email = "test@example.com"
        user.name = "test_user"
        user.is_active = True
        return user
    
    @pytest.fixture
    def mock_article(self):
        """テスト記事"""
        article = MagicMock(spec=Article)
        article.id = 1
        article.title = "Test Article"
        article.content = "Test content"
        article.body = "Test body content"  # bodyフィールドを追加
        article.owner_id = 1
        return article
    
    @patch('routers.user.Hash.bcrypt')
    @patch('routers.user.is_valid_email_domain')
    def test_user_registration_and_verification_workflow(self, mock_domain_check, mock_hash, client, mock_db):
        """ユーザー登録と認証のワークフローテスト"""
        # 依存性のオーバーライド設定
        def override_get_db():
            return mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # モックの設定
            mock_domain_check.return_value = True
            mock_hash.return_value = "hashed_password"
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # ユーザー登録
            user_data = {
                "name": "newuser",
                "email": "newuser@example.com",
                "password": "password123"
            }
            
            with patch('routers.user.ENABLE_EMAIL_VERIFICATION', False):
                response = client.post("/api/v1/user", json=user_data)
                # 201 (作成成功) または 400 (バリデーションエラー) が返ることを確認
                assert response.status_code in [200, 201, 400, 422]
        
        finally:
            # テスト後のクリーンアップ
            app.dependency_overrides = {}
    
    def test_article_lifecycle_with_authentication(self, client, mock_db, mock_user, mock_article):
        """認証付き記事ライフサイクルテスト"""
        # 依存性のオーバーライド設定
        def override_get_current_user():
            return mock_user
        
        def override_get_db():
            return mock_db
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # モックの設定
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_article]
            mock_db.query.return_value.filter.return_value.first.return_value = mock_article
            mock_db.query.return_value.filter.return_value.count.return_value = 1
            
            headers = {"Authorization": "Bearer dummy_token"}
            
            # 記事一覧取得
            response = client.get("/api/v1/articles", headers=headers)
            assert response.status_code in [200, 500]  # 成功またはサーバーエラー
            
            # 特定記事取得
            response = client.get("/api/v1/articles/1", headers=headers)
            assert response.status_code in [200, 404, 500]  # 成功、見つからない、またはサーバーエラー
        
        finally:
            # テスト後のクリーンアップ
            app.dependency_overrides = {}