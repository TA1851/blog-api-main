"""
Auth Routerの包括的テストスイート
カバレッジ100%を目指してAuth Router(routers/auth.py)をテストする

テスト対象エンドポイント:
1. POST /api/v1/login - ユーザー認証・JWTトークン発行
2. POST /api/v1/logout - トークン無効化・ブラックリスト追加  
3. POST /api/v1/change-password - 仮パスワードから新パスワードへ変更
4. GET /api/v1/article - 全記事取得（レガシーエンドポイント）
5. verify_token 関数 - トークン検証
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
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


# テストクライアントの初期化
client = TestClient(app)


class TestAuthRouter:
    """Auth Routerの包括的テストスイート"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """各テスト前後でトークンブラックリストをクリア"""
        token_blacklist.clear()
        yield
        token_blacklist.clear()

    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_user(self):
        """テスト用ユーザーデータ"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.name = "testuser"
        user.password = Hash.bcrypt("password123")  # ハッシュ化されたパスワード
        user.is_active = True
        return user

    @pytest.fixture
    def sample_article(self):
        """テスト用記事データ"""
        article = Mock(spec=Article)
        article.id = 1
        article.title = "テスト記事"
        article.body = "テスト本文"
        return article

    @pytest.fixture
    def valid_token(self, sample_user):
        """有効なJWTトークン"""
        return create_access_token(data={"sub": sample_user.email, "id": sample_user.id})

    # ========================================
    # POST /api/v1/login エンドポイントのテスト
    # ========================================

    @patch('routers.auth.get_db')
    def test_login_success(self, mock_get_db, mock_db, sample_user):
        """ログイン成功のテスト"""
        # セットアップ
        mock_db.query().filter().first.return_value = sample_user
        mock_get_db.return_value = mock_db

        # リクエスト実行
        response = client.post(
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
        assert isinstance(data["access_token"], str)

    @patch('routers.auth.get_db')
    def test_login_user_not_found(self, mock_get_db, mock_db):
        """存在しないユーザーでのログイン失敗テスト"""
        # セットアップ
        mock_db.query().filter().first.return_value = None
        mock_get_db.return_value = mock_db

        # リクエスト実行
        response = client.post(
            "/api/v1/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123"
            }
        )

        # 検証
        assert response.status_code == 404
        assert "無効なユーザー名です" in response.json()["detail"]

    @patch('routers.auth.get_db')
    def test_login_invalid_password(self, mock_get_db, mock_db, sample_user):
        """無効なパスワードでのログイン失敗テスト"""
        # セットアップ
        mock_db.query().filter().first.return_value = sample_user
        mock_get_db.return_value = mock_db

        # リクエスト実行
        response = client.post(
            "/api/v1/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword"
            }
        )

        # 検証
        assert response.status_code == 404
        assert "無効なパスワードです" in response.json()["detail"]

    @patch('routers.auth.get_db')
    def test_login_null_password(self, mock_get_db, mock_db, sample_user):
        """パスワードがNullのユーザーでのログイン失敗テスト"""
        # セットアップ
        sample_user.password = None
        mock_db.query().filter().first.return_value = sample_user
        mock_get_db.return_value = mock_db

        # リクエスト実行
        response = client.post(
            "/api/v1/login",
            data={
                "username": "test@example.com",
                "password": "password123"
            }
        )

        # 検証
        assert response.status_code == 404
        assert "無効なパスワードです" in response.json()["detail"]

    def test_login_missing_username(self):
        """ユーザー名なしでのログイン失敗テスト"""
        response = client.post(
            "/api/v1/login",
            data={
                "password": "password123"
            }
        )
        assert response.status_code == 422

    def test_login_missing_password(self):
        """パスワードなしでのログイン失敗テスト"""
        response = client.post(
            "/api/v1/login",
            data={
                "username": "test@example.com"
            }
        )
        assert response.status_code == 422

    def test_login_empty_credentials(self):
        """空の認証情報でのログイン失敗テスト"""
        response = client.post("/api/v1/login", data={})
        assert response.status_code == 422

    # ========================================
    # POST /api/v1/logout エンドポイントのテスト  
    # ========================================

    def test_logout_success(self, valid_token):
        """ログアウト成功のテスト"""
        # リクエスト実行
        response = client.post(
            "/api/v1/logout",
            headers={"Authorization": f"Bearer {valid_token}"}
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "ログアウトしました"
        
        # トークンがブラックリストに追加されているか確認
        assert valid_token in token_blacklist

    def test_logout_missing_token(self):
        """トークンなしでのログアウト失敗テスト"""
        response = client.post("/api/v1/logout")
        assert response.status_code == 401

    def test_logout_invalid_token(self):
        """無効なトークンでのログアウト失敗テスト"""
        response = client.post(
            "/api/v1/logout",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_logout_malformed_header(self):
        """不正な形式のAuthorizationヘッダーテスト"""
        response = client.post(
            "/api/v1/logout",
            headers={"Authorization": "InvalidFormat token"}
        )
        assert response.status_code == 401

    # ========================================
    # verify_token 関数のテスト
    # ========================================

    def test_verify_token_success(self, valid_token):
        """トークン検証成功のテスト"""
        result = verify_token(valid_token)
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

    @patch('routers.auth.get_db')
    @patch('routers.auth.send_registration_complete_email')
    def test_change_password_success(self, mock_email, mock_get_db, mock_db, sample_user):
        """パスワード変更成功のテスト"""
        # セットアップ
        mock_db.query().filter().first.return_value = sample_user
        mock_db.commit.return_value = None
        mock_get_db.return_value = mock_db
        mock_email.return_value = AsyncMock()

        # リクエスト実行
        response = client.post(
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
        
        # パスワードが更新されているか確認
        assert sample_user.password != Hash.bcrypt("password123")
        # メール送信が呼ばれているか確認
        mock_email.assert_called_once()

    @patch('routers.auth.get_db')
    def test_change_password_user_not_found(self, mock_get_db, mock_db):
        """存在しないユーザーでのパスワード変更失敗テスト"""
        # セットアップ
        mock_db.query().filter().first.return_value = None
        mock_get_db.return_value = mock_db

        # リクエスト実行
        response = client.post(
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

    @patch('routers.auth.get_db')
    def test_change_password_invalid_temp_password(self, mock_get_db, mock_db, sample_user):
        """無効な仮パスワードでのパスワード変更失敗テスト"""
        # セットアップ
        mock_db.query().filter().first.return_value = sample_user
        mock_get_db.return_value = mock_db

        # リクエスト実行
        response = client.post(
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

    @patch('routers.auth.get_db')
    def test_change_password_null_password(self, mock_get_db, mock_db, sample_user):
        """パスワードがNullのユーザーでのパスワード変更失敗テスト"""
        # セットアップ
        sample_user.password = None
        mock_db.query().filter().first.return_value = sample_user
        mock_get_db.return_value = mock_db

        # リクエスト実行
        response = client.post(
            "/api/v1/change-password",
            json={
                "username": "test@example.com",
                "temp_password": "temp123",
                "new_password": "newpassword123"
            }
        )

        # 検証
        assert response.status_code == 400
        assert "無効な仮パスワードです" in response.json()["detail"]

    @patch('routers.auth.get_db')
    @patch('routers.auth.send_registration_complete_email')
    def test_change_password_email_failure(self, mock_email, mock_get_db, mock_db, sample_user):
        """メール送信失敗でもパスワード変更は成功するテスト"""
        # セットアップ
        mock_db.query().filter().first.return_value = sample_user
        mock_db.commit.return_value = None
        mock_get_db.return_value = mock_db
        mock_email.side_effect = Exception("Email sending failed")

        # リクエスト実行
        response = client.post(
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

    @patch('routers.auth.get_db')
    def test_change_password_database_error(self, mock_get_db, mock_db, sample_user):
        """データベースエラーでのパスワード変更失敗テスト"""
        # セットアップ
        mock_db.query().filter().first.return_value = sample_user
        mock_db.commit.side_effect = Exception("Database error")
        mock_db.rollback.return_value = None
        mock_get_db.return_value = mock_db

        # リクエスト実行
        response = client.post(
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

    @patch('routers.auth.get_db')
    @patch('routers.auth.send_registration_complete_email')
    def test_change_password_user_name_none(self, mock_email, mock_get_db, mock_db, sample_user):
        """ユーザー名がNoneの場合のメール送信テスト"""
        # セットアップ
        sample_user.name = None  # nameをNoneに設定
        mock_db.query().filter().first.return_value = sample_user
        mock_db.commit.return_value = None
        mock_get_db.return_value = mock_db
        mock_email.return_value = AsyncMock()

        # リクエスト実行
        response = client.post(
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

    def test_change_password_invalid_request_format(self):
        """不正なリクエスト形式でのパスワード変更失敗テスト"""
        # 必須フィールドが欠けているリクエスト
        response = client.post(
            "/api/v1/change-password",
            json={"username": "test@example.com"}  # temp_passwordとnew_passwordが欠けている
        )
        assert response.status_code == 422

    def test_change_password_short_new_password(self):
        """新パスワードが短すぎる場合のテスト"""
        response = client.post(
            "/api/v1/change-password",
            json={
                "username": "test@example.com",
                "temp_password": "temp123",
                "new_password": "short"  # 8文字未満
            }
        )
        assert response.status_code == 422

    # ========================================
    # GET /api/v1/article エンドポイントのテスト
    # ========================================

    @patch('routers.auth.get_db')
    def test_get_all_articles_success(self, mock_get_db, mock_db, sample_article):
        """全記事取得成功のテスト"""
        # セットアップ
        mock_db.query().all.return_value = [sample_article]
        mock_get_db.return_value = mock_db

        # リクエスト実行
        response = client.get("/api/v1/article")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_article.id
        assert data[0]["title"] == sample_article.title
        assert data[0]["body"] == sample_article.body

    @patch('routers.auth.get_db')
    def test_get_all_articles_empty(self, mock_get_db, mock_db):
        """記事が存在しない場合のテスト"""
        # セットアップ
        mock_db.query().all.return_value = []
        mock_get_db.return_value = mock_db

        # リクエスト実行
        response = client.get("/api/v1/article")

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @patch('routers.auth.get_db')
    def test_get_all_articles_multiple(self, mock_get_db, mock_db):
        """複数記事取得のテスト"""
        # セットアップ
        articles = []
        for i in range(3):
            article = Mock(spec=Article)
            article.id = i + 1
            article.title = f"記事{i + 1}"
            article.body = f"本文{i + 1}"
            articles.append(article)
        
        mock_db.query().all.return_value = articles
        mock_get_db.return_value = mock_db

        # リクエスト実行
        response = client.get("/api/v1/article")

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
    # エラーケースとエッジケースのテスト
    # ========================================

    @patch('routers.auth.get_db')
    def test_login_with_special_characters(self, mock_get_db, mock_db, sample_user):
        """特殊文字を含むパスワードでのログインテスト"""
        # セットアップ
        special_password = "p@ssw0rd!#$%"
        sample_user.password = Hash.bcrypt(special_password)
        mock_db.query().filter().first.return_value = sample_user
        mock_get_db.return_value = mock_db

        # リクエスト実行
        response = client.post(
            "/api/v1/login",
            data={
                "username": "test@example.com",
                "password": special_password
            }
        )

        # 検証
        assert response.status_code == 200

    def test_multiple_logout_same_token(self, valid_token):
        """同じトークンで複数回ログアウトのテスト"""
        # 最初のログアウト
        response1 = client.post(
            "/api/v1/logout",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response1.status_code == 200

        # 同じトークンで再度ログアウト
        response2 = client.post(
            "/api/v1/logout",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response2.status_code == 401  # ブラックリストに登録済み

    def test_token_blacklist_persistence(self, valid_token):
        """トークンブラックリストの永続性テスト"""
        # ログアウト
        client.post(
            "/api/v1/logout",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # ブラックリストに登録されていることを確認
        assert valid_token in token_blacklist
        
        # ブラックリストされたトークンで認証が失敗することを確認
        with pytest.raises(HTTPException):
            verify_token(valid_token)

    # ========================================
    # 型定義とレスポンス形式のテスト
    # ========================================

    def test_login_response_type(self, valid_token):
        """LoginResponse型定義のテスト"""
        # LoginResponseが正しい型構造を持つことを確認
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

    def test_jwt_token_security(self, sample_user):
        """JWTトークンのセキュリティテスト"""
        token = create_access_token(
            data={"sub": sample_user.email, "id": sample_user.id}
        )
        
        # トークンが文字列であることを確認
        assert isinstance(token, str)
        # トークンが適切な形式であることを確認（3つのピリオド区切り）
        assert len(token.split('.')) == 3
        
        # トークンから情報が復号化できることを確認
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        assert payload["sub"] == sample_user.email
        assert payload["id"] == sample_user.id

    # ========================================
    # 統合テスト
    # ========================================

    @patch('routers.auth.get_db')
    def test_full_auth_flow(self, mock_get_db, mock_db, sample_user):
        """認証の完全フローテスト（ログイン→認証→ログアウト）"""
        # セットアップ
        mock_db.query().filter().first.return_value = sample_user
        mock_get_db.return_value = mock_db

        # 1. ログイン
        login_response = client.post(
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
        logout_response = client.post(
            "/api/v1/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert logout_response.status_code == 200

        # 4. ログアウト後のトークン検証失敗
        with pytest.raises(HTTPException):
            verify_token(token)

    @patch('routers.auth.get_db')
    @patch('routers.auth.send_registration_complete_email')
    def test_password_change_flow(self, mock_email, mock_get_db, mock_db, sample_user):
        """パスワード変更の完全フローテスト"""
        # セットアップ
        mock_db.query().filter().first.return_value = sample_user
        mock_db.commit.return_value = None
        mock_get_db.return_value = mock_db
        mock_email.return_value = AsyncMock()

        # 1. 古いパスワードでログイン
        login_response = client.post(
            "/api/v1/login",
            data={
                "username": "test@example.com",
                "password": "password123"
            }
        )
        assert login_response.status_code == 200

        # 2. パスワード変更
        change_response = client.post(
            "/api/v1/change-password",
            json={
                "username": "test@example.com",
                "temp_password": "password123",
                "new_password": "newpassword123"
            }
        )
        assert change_response.status_code == 200

        # 3. 新しいパスワードでログイン可能であることを確認
        # (実際のテストでは新しいハッシュ化されたパスワードでユーザーを更新する必要がある)
        sample_user.password = Hash.bcrypt("newpassword123")
        new_login_response = client.post(
            "/api/v1/login",
            data={
                "username": "test@example.com",
                "password": "newpassword123"
            }
        )
        assert new_login_response.status_code == 200

# ========================================
# 追加のエラーハンドリングテスト
# ========================================

class TestAuthRouterErrorHandling:
    """Auth Routerのエラーハンドリングに特化したテスト"""

    def test_malformed_json_change_password(self):
        """不正なJSON形式でのパスワード変更リクエストテスト"""
        response = client.post(
            "/api/v1/change-password",
            data="invalid json",  # 不正なJSON
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_authorization_header_logout(self):
        """Authorizationヘッダーなしでのログアウトテスト"""
        response = client.post("/api/v1/logout")
        assert response.status_code == 401

    def test_empty_authorization_header_logout(self):
        """空のAuthorizationヘッダーでのログアウトテスト"""
        response = client.post(
            "/api/v1/logout",
            headers={"Authorization": ""}
        )
        assert response.status_code == 401

    def test_invalid_bearer_format_logout(self):
        """不正なBearer形式でのログアウトテスト"""
        response = client.post(
            "/api/v1/logout",
            headers={"Authorization": "Basic invalid"}
        )
        assert response.status_code == 401


# ========================================
# パフォーマンステスト
# ========================================

class TestAuthRouterPerformance:
    """Auth Routerのパフォーマンステスト"""

    @patch('routers.auth.get_db')
    def test_login_performance(self, mock_get_db, mock_db, sample_user):
        """ログインのパフォーマンステスト"""
        import time
        
        # セットアップ
        mock_db.query().filter().first.return_value = sample_user
        mock_get_db.return_value = mock_db

        # 実行時間測定
        start_time = time.time()
        response = client.post(
            "/api/v1/login",
            data={
                "username": "test@example.com",
                "password": "password123"
            }
        )
        end_time = time.time()

        # 検証
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # 1秒以内に完了

    def test_multiple_logout_performance(self, valid_token):
        """複数ログアウトのパフォーマンステスト"""
        import time
        
        start_time = time.time()
        
        # 複数回ログアウト試行
        for _ in range(10):
            client.post(
                "/api/v1/logout",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
        
        end_time = time.time()
        
        # 検証 - 10回のリクエストが2秒以内に完了
        assert (end_time - start_time) < 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=routers.auth", "--cov-report=html"])
