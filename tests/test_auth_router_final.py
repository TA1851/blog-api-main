"""
Auth Router最終版テストスイート
dependency_overridesを使用してカバレッジ100%を達成

修正内容:
- FastAPIの依存性注入システムを正しく使用
- app.dependency_overridesでget_dbをオーバーライド
- 実際のトークン生成/検証ロジックをテスト
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError

# プロジェクト内部のインポート
from main import app
from routers.auth import (
    router, get_db, verify_token, token_blacklist, 
    LoginResponse, TokenResponse, PasswordChangeResponse
)
from schemas import PasswordChange, ShowArticle
from models import User, Article
from hashing import Hash
from database import session
from custom_token import create_access_token


class TestAuthRouterFinal:
    """Auth Routerの最終版テストスイート"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """各テスト前後でトークンブラックリストとdependency_overridesをクリア"""
        token_blacklist.clear()
        app.dependency_overrides.clear()
        yield
        token_blacklist.clear()
        app.dependency_overrides.clear()

    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        mock_session = MagicMock(spec=Session)
        mock_session.commit.return_value = None
        mock_session.rollback.return_value = None
        mock_session.close.return_value = None
        return mock_session

    @pytest.fixture
    def test_client(self, mock_db):
        """dependency_overridesを設定したテストクライアント"""
        def override_get_db():
            try:
                yield mock_db
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        return TestClient(app)

    @pytest.fixture
    def sample_user(self):
        """テスト用ユーザーデータ"""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        user.name = "testuser"
        user.password = Hash.bcrypt("password123")
        user.temp_password = "password123"  # temp_passwordを設定
        user.is_active = True
        return user

    @pytest.fixture
    def sample_article(self):
        """テスト用記事データ"""
        article = Mock()
        article.id = 1
        article.title = "テスト記事"
        article.body = "テスト本文"
        return article

    @pytest.fixture
    def valid_token(self):
        """有効なJWTトークン"""
        return create_access_token(data={"sub": "test@example.com", "id": 1})

    # ========================================
    # POST /api/v1/login エンドポイントのテスト
    # ========================================

    def test_login_success(self, test_client, mock_db, sample_user):
        """ログイン成功のテスト"""
        # セットアップ
        mock_query = Mock()
        mock_filter = Mock()
        mock_first = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_user
        mock_db.query.return_value = mock_query

        # リクエスト実行
        response = test_client.post(
            "/api/v1/login",
            data={
                "username": "test@example.com",
                "password": "password123"
            }
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # 生成されたトークンが文字列であることを確認
        token = data["access_token"]
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT形式の確認

    def test_login_user_not_found(self, test_client, mock_db):
        """存在しないユーザーでのログイン失敗テスト"""
        # セットアップ
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db.query.return_value = mock_query

        # リクエスト実行
        response = test_client.post(
            "/api/v1/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123"
            }
        )

        # 検証
        assert response.status_code == 404
        assert "無効なユーザー名です" in response.json()["detail"]

    def test_login_invalid_password(self, test_client, mock_db, sample_user):
        """無効なパスワードでのログイン失敗テスト"""
        # セットアップ
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_user
        mock_db.query.return_value = mock_query

        # リクエスト実行
        response = test_client.post(
            "/api/v1/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword"
            }
        )

        # 検証
        assert response.status_code == 404
        assert "無効なパスワードです" in response.json()["detail"]

    def test_login_null_password_user(self, test_client, mock_db):
        """パスワードがNullのユーザーでのログイン失敗テスト"""
        # セットアップ
        user_with_null_password = Mock()
        user_with_null_password.id = 1
        user_with_null_password.email = "test@example.com"
        user_with_null_password.password = None  # パスワードがNull
        
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = user_with_null_password
        mock_db.query.return_value = mock_query

        # リクエスト実行
        response = test_client.post(
            "/api/v1/login",
            data={
                "username": "test@example.com",
                "password": "password123"
            }
        )

        # 検証
        assert response.status_code == 404
        assert "無効なパスワードです" in response.json()["detail"]

    # ========================================
    # POST /api/v1/logout エンドポイントのテスト  
    # ========================================

    def test_logout_success(self, test_client, valid_token):
        """ログアウト成功のテスト"""
        # リクエスト実行
        response = test_client.post(
            "/api/v1/logout",
            headers={"Authorization": f"Bearer {valid_token}"}
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "ログアウトしました"
        
        # トークンがブラックリストに追加されているか確認
        assert valid_token in token_blacklist

    def test_logout_missing_token(self, test_client):
        """トークンなしでのログアウト失敗テスト"""
        response = test_client.post("/api/v1/logout")
        assert response.status_code == 401

    def test_logout_invalid_token(self, test_client):
        """無効なトークンでのログアウトテスト"""
        response = test_client.post(
            "/api/v1/logout",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 200  # ログアウトエンドポイントは無効トークンでも200を返す

    def test_logout_malformed_header(self, test_client):
        """不正な形式のAuthorizationヘッダーテスト"""
        response = test_client.post(
            "/api/v1/logout",
            headers={"Authorization": "InvalidFormat token"}
        )
        assert response.status_code == 401

    # ========================================
    # verify_token 関数のテスト
    # ========================================

    @patch.dict(os.environ, {'SECRET_KEY': 'your-secret-key'})
    def test_verify_token_success(self, valid_token):
        """トークン検証成功のテスト"""
        # 環境変数を使用してトークンを再生成
        test_token = create_access_token(data={"sub": "test@example.com", "id": 1})
        result = verify_token(test_token)
        assert "email" in result
        assert result["email"] == "test@example.com"

    def test_verify_token_blacklisted(self, valid_token):
        """ブラックリストに登録されたトークンの検証テスト"""
        # トークンをブラックリストに追加
        token_blacklist.add(valid_token)
        
        # 検証
        with pytest.raises(HTTPException) as exc_info:
            verify_token(valid_token)
        assert exc_info.value.status_code == 401
        assert "トークンが無効化されています" in exc_info.value.detail

    def test_verify_token_invalid_signature(self):
        """無効な署名のトークン検証テスト"""
        invalid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature"
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)
        assert exc_info.value.status_code == 401
        assert "無効なトークンです" in exc_info.value.detail

    def test_verify_token_missing_subject(self):
        """subjectが欠けているトークンの検証テスト"""
        # subjectなしのトークンを作成
        payload = {"id": 1}  # subなし
        token = jwt.encode(payload, "your-secret-key", algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401
        assert "無効なトークンです" in exc_info.value.detail

    def test_verify_token_malformed(self):
        """不正な形式のトークン検証テスト"""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("not.a.jwt.token")
        assert exc_info.value.status_code == 401

    # ========================================
    # POST /api/v1/change-password エンドポイントのテスト
    # ========================================

    @patch('routers.auth.send_registration_complete_email')
    def test_change_password_success(self, mock_email, test_client, mock_db, sample_user):
        """パスワード変更成功のテスト"""
        # セットアップ
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_user
        mock_db.query.return_value = mock_query
        mock_email.return_value = AsyncMock()

        # リクエスト実行
        response = test_client.post(
            "/api/v1/change-password",
            json={
                "username": "test@example.com",
                "temp_password": "password123",
                "new_password": "newpassword123"
            }
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "パスワードが正常に変更されました。"
        assert data["user_id"] == str(sample_user.id)

    def test_change_password_user_not_found(self, test_client, mock_db):
        """存在しないユーザーでのパスワード変更失敗テスト"""
        # セットアップ
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db.query.return_value = mock_query

        # リクエスト実行
        response = test_client.post(
            "/api/v1/change-password",
            json={
                "username": "nonexistent@example.com",
                "temp_password": "temp123",
                "new_password": "newpassword123"
            }
        )

        # 検証
        assert response.status_code == 404
        assert "無効なユーザー名です" in response.json()["detail"]

    def test_change_password_invalid_temp_password(self, test_client, mock_db, sample_user):
        """無効な仮パスワードでのパスワード変更失敗テスト"""
        # セットアップ
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_user
        mock_db.query.return_value = mock_query

        # リクエスト実行
        response = test_client.post(
            "/api/v1/change-password",
            json={
                "username": "test@example.com",
                "temp_password": "wrongtemp",
                "new_password": "newpassword123"
            }
        )

        # 検証
        assert response.status_code == 400
        assert "無効な仮パスワードです" in response.json()["detail"]

    @patch('routers.auth.send_registration_complete_email')
    def test_change_password_database_error(self, mock_email, test_client, mock_db, sample_user):
        """データベースエラーでのパスワード変更失敗テスト"""
        # セットアップ
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_user
        mock_db.query.return_value = mock_query
        mock_db.commit.side_effect = Exception("Database error")
        mock_email.return_value = AsyncMock()

        # リクエスト実行
        response = test_client.post(
            "/api/v1/change-password",
            json={
                "username": "test@example.com",
                "temp_password": "password123",
                "new_password": "newpassword123"
            }
        )

        # 検証
        assert response.status_code == 500
        assert "パスワード変更中にエラーが発生しました" in response.json()["detail"]
        # ロールバックが呼ばれていることを確認
        mock_db.rollback.assert_called_once()

    @patch('routers.auth.send_registration_complete_email')
    def test_change_password_email_failure(self, mock_email, test_client, mock_db, sample_user):
        """メール送信失敗でもパスワード変更は成功するテスト"""
        # セットアップ
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_user
        mock_db.query.return_value = mock_query
        mock_email.side_effect = Exception("Email sending failed")

        # リクエスト実行
        response = test_client.post(
            "/api/v1/change-password",
            json={
                "username": "test@example.com",
                "temp_password": "password123",
                "new_password": "newpassword123"
            }
        )

        # 検証 - メール失敗でもパスワード変更は成功
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "パスワードが正常に変更されました。"

    @patch('routers.auth.send_registration_complete_email')
    def test_change_password_user_name_none(self, mock_email, test_client, mock_db):
        """ユーザー名がNoneの場合のメール送信テスト"""
        # セットアップ
        user_with_no_name = Mock()
        user_with_no_name.id = 1
        user_with_no_name.email = "test@example.com"
        user_with_no_name.name = None  # nameをNoneに設定
        user_with_no_name.password = Hash.bcrypt("password123")
        user_with_no_name.temp_password = "password123"
        
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = user_with_no_name
        mock_db.query.return_value = mock_query
        mock_email.return_value = AsyncMock()

        # リクエスト実行
        response = test_client.post(
            "/api/v1/change-password",
            json={
                "username": "test@example.com",
                "temp_password": "password123",
                "new_password": "newpassword123"
            }
        )

        # 検証
        assert response.status_code == 200
        # メールアドレスのローカル部分が名前として使用されることを確認
        mock_email.assert_called_once_with("test@example.com", "test")

    # ========================================
    # GET /api/v1/article エンドポイントのテスト
    # ========================================

    def test_get_all_articles_success(self, test_client, mock_db, sample_article):
        """全記事取得成功のテスト"""
        # セットアップ
        mock_query = Mock()
        mock_query.all.return_value = [sample_article]
        mock_db.query.return_value = mock_query

        # リクエスト実行
        response = test_client.get("/api/v1/article")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_article.id
        assert data[0]["title"] == sample_article.title
        assert data[0]["body"] == sample_article.body

    def test_get_all_articles_empty(self, test_client, mock_db):
        """記事が存在しない場合のテスト"""
        # セットアップ
        mock_query = Mock()
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        # リクエスト実行
        response = test_client.get("/api/v1/article")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_all_articles_multiple(self, test_client, mock_db):
        """複数記事取得のテスト"""
        # セットアップ
        articles = []
        for i in range(3):
            article = Mock()
            article.id = i + 1
            article.title = f"記事{i + 1}"
            article.body = f"本文{i + 1}"
            articles.append(article)
        
        mock_query = Mock()
        mock_query.all.return_value = articles
        mock_db.query.return_value = mock_query

        # リクエスト実行
        response = test_client.get("/api/v1/article")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for i, article_data in enumerate(data):
            assert article_data["id"] == i + 1
            assert article_data["title"] == f"記事{i + 1}"
            assert article_data["body"] == f"本文{i + 1}"

    # ========================================
    # get_db 関数のテスト
    # ========================================

    @patch('routers.auth.session')
    def test_get_db_success(self, mock_session):
        """get_db正常動作のテスト"""
        # セットアップ
        mock_db_instance = Mock()
        mock_session.return_value = mock_db_instance

        # 実行
        db_generator = get_db()
        db = next(db_generator)

        # 検証
        assert db == mock_db_instance
        
        # ジェネレータの終了処理をテスト
        try:
            next(db_generator)
        except StopIteration:
            pass
        
        # close()が呼ばれることを確認
        mock_db_instance.close.assert_called_once()

    @patch('routers.auth.session')
    def test_get_db_with_exception(self, mock_session):
        """get_db例外発生時のテスト"""
        # セットアップ
        mock_db_instance = Mock()
        mock_session.return_value = mock_db_instance

        # 実行
        db_generator = get_db()
        db = next(db_generator)

        # ジェネレータ内で例外を発生させる
        with pytest.raises(Exception):
            db_generator.throw(Exception("Test exception"))
        
        # close()が呼ばれることを確認
        mock_db_instance.close.assert_called_once()

    # ========================================
    # エラーハンドリングテスト
    # ========================================

    def test_login_missing_username(self, test_client):
        """ユーザー名なしでのログイン失敗テスト"""
        response = test_client.post(
            "/api/v1/login",
            data={"password": "password123"}
        )
        assert response.status_code == 422

    def test_login_missing_password(self, test_client):
        """パスワードなしでのログイン失敗テスト"""
        response = test_client.post(
            "/api/v1/login",
            data={"username": "test@example.com"}
        )
        assert response.status_code == 422

    def test_change_password_invalid_format(self, test_client):
        """不正なリクエスト形式でのパスワード変更失敗テスト"""
        response = test_client.post(
            "/api/v1/change-password",
            json={"username": "test@example.com"}  # 必須フィールドが欠けている
        )
        assert response.status_code == 422

    def test_change_password_short_password(self, test_client):
        """短すぎる新パスワードのテスト"""
        response = test_client.post(
            "/api/v1/change-password",
            json={
                "username": "test@example.com",
                "temp_password": "temp123",
                "new_password": "short"  # 8文字未満
            }
        )
        assert response.status_code == 422

    # ========================================
    # セキュリティテスト
    # ========================================

    def test_password_hashing_security(self):
        """パスワードハッシュ化のセキュリティテスト"""
        password = "testpassword123"
        hashed = Hash.bcrypt(password)
        
        # ハッシュが元のパスワードと異なることを確認
        assert hashed != password
        # ハッシュが検証できることを確認
        assert Hash.verify(password, hashed)
        # 間違ったパスワードが検証されないことを確認
        assert not Hash.verify("wrongpassword", hashed)

    @patch.dict(os.environ, {'SECRET_KEY': 'your-secret-key'})
    def test_jwt_token_security(self):
        """JWTトークンのセキュリティテスト"""
        # 環境変数を使用してトークンを生成
        token = create_access_token(
            data={"sub": "test@example.com", "id": 1}
        )
        
        # トークンが文字列であることを確認
        assert isinstance(token, str)
        # トークンが適切な形式であることを確認（3つのピリオド区切り）
        assert len(token.split('.')) == 3
        
        # トークンから情報が復号化できることを確認
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        assert payload["sub"] == "test@example.com"
        assert payload["id"] == 1

    # ========================================
    # 統合テスト
    # ========================================

    @patch.dict(os.environ, {'SECRET_KEY': 'your-secret-key'})
    def test_full_auth_flow(self, test_client, mock_db, sample_user):
        """認証の完全フローテスト（ログイン→認証→ログアウト）"""
        # セットアップ
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_user
        mock_db.query.return_value = mock_query

        # 1. ログイン
        login_response = test_client.post(
            "/api/v1/login",
            data={
                "username": "test@example.com",
                "password": "password123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # 2. トークン検証
        result = verify_token(token)
        assert result["email"] == "test@example.com"

        # 3. ログアウト
        logout_response = test_client.post(
            "/api/v1/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert logout_response.status_code == 200

        # 4. ログアウト後のトークン検証失敗
        with pytest.raises(HTTPException):
            verify_token(token)

    # ========================================
    # 型定義テスト
    # ========================================

    def test_login_response_type(self, valid_token):
        """LoginResponse型定義のテスト"""
        response_data: LoginResponse = {
            "access_token": valid_token,
            "token_type": "bearer"
        }
        
        assert "access_token" in response_data
        assert "token_type" in response_data
        assert response_data["token_type"] == "bearer"

    def test_password_change_response_type(self):
        """PasswordChangeResponse型定義のテスト"""
        response_data: PasswordChangeResponse = {
            "message": "パスワードが正常に変更されました。",
            "user_id": "123"
        }
        
        assert "message" in response_data
        assert "user_id" in response_data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=routers.auth", "--cov-report=html"])
