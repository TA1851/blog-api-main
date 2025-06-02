"""
認証機能付きユーザー削除エンドポイントの統合テスト
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta
import os

from main import app
from schemas import AccountDeletionRequest
from models import User as UserModel
from oauth2 import SECRET_KEY, ALGORITHM


class TestDeleteUserAccountIntegration:
    """ユーザー削除エンドポイントの統合テスト（認証機能含む）"""
    
    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """モックユーザー"""
        user = MagicMock(spec=UserModel)
        user.id = 123
        user.email = "test@example.com"
        user.password = "hashed_password"
        user.name = "test"
        user.is_active = True
        return user
    
    @pytest.fixture
    def valid_token(self, mock_user):
        """有効なJWTトークン"""
        data = {
            "sub": mock_user.email,
            "id": mock_user.id
        }
        expire = datetime.utcnow() + timedelta(minutes=30)
        data.update({"exp": expire})
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        return token
    
    @pytest.fixture
    def auth_headers(self, valid_token):
        """認証ヘッダー"""
        return {"Authorization": f"Bearer {valid_token}"}
    
    @pytest.fixture
    def valid_deletion_data(self):
        """有効な削除リクエストデータ"""
        return {
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
    
    @patch('routers.user.get_db')
    @patch('routers.user.get_current_user')
    def test_delete_account_without_auth_header(self, mock_get_current_user, mock_get_db, client, valid_deletion_data):
        """認証ヘッダーなしでアカウント削除を試行するテスト"""
        response = client.request("DELETE", "/api/v1/user/delete-account", json=valid_deletion_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Not authenticated" in response.json()["detail"]
    
    @patch('routers.user.send_account_deletion_email')
    @patch('routers.user.Hash.verify')
    @patch('routers.user.get_db')
    @patch('oauth2.get_db')  # oauth2でのget_dbもモック
    def test_delete_account_success_with_auth(self, mock_oauth2_get_db, mock_get_db, mock_hash_verify, mock_send_email, client, mock_user, auth_headers, valid_deletion_data):
        """認証ありで正常なアカウント削除のテスト"""
        # モックの設定
        mock_hash_verify.return_value = True
        mock_send_email.return_value = AsyncMock()
        
        # データベースモックの設定（両方のget_dbに同じモックを返す）
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_oauth2_get_db.return_value = mock_db
        
        # OAuth2用のユーザークエリモック（認証時に使用）
        oauth2_user_query = MagicMock()
        oauth2_user_query.filter.return_value.first.return_value = mock_user
        
        # ユーザークエリのモック（削除時に使用）
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = mock_user
        
        # 記事クエリのモック
        article_query = MagicMock()
        article_query.filter.return_value.all.return_value = []
        
        # 認証レコードクエリのモック
        verification_query = MagicMock()
        verification_query.filter.return_value.all.return_value = []
        
        # queryの呼び出し順序に基づいてサイドエフェクトを設定
        # 1回目: OAuth2でのユーザー取得、2-4回目: 削除処理での各クエリ
        mock_db.query.side_effect = [oauth2_user_query, user_query, article_query, verification_query]
        
        response = client.request("DELETE", "/api/v1/user/delete-account", json=valid_deletion_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "退会処理が完了しました" in response_data["message"]
        assert response_data["email"] == "test@example.com"
        
        # データベース操作の確認
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()
    
    @patch('routers.user.get_db')
    @patch('routers.user.get_current_user')
    def test_delete_account_unauthorized_different_email(self, mock_get_current_user, mock_get_db, client, mock_user, auth_headers):
        """認証ユーザーと異なるメールアドレスでアカウント削除を試行するテスト"""
        mock_get_current_user.return_value = mock_user
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # 異なるメールアドレスでのリクエストデータ
        deletion_data = {
            "email": "other@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
        
        response = client.request("DELETE", "/api/v1/user/delete-account", json=deletion_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "自分のアカウントのみ削除できます" in response.json()["detail"]
        mock_db.rollback.assert_called_once()
    
    @patch('routers.user.get_db')
    @patch('routers.user.get_current_user')
    def test_delete_account_password_mismatch(self, mock_get_current_user, mock_get_db, client, mock_user, auth_headers):
        """パスワードと確認用パスワードが一致しない場合のテスト"""
        mock_get_current_user.return_value = mock_user
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db
        
        deletion_data = {
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "different456"
        }
        
        response = client.request("DELETE", "/api/v1/user/delete-account", json=deletion_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "パスワードと確認用パスワードが一致しません" in response.json()["detail"]
        mock_db.rollback.assert_called_once()
    
    @patch('routers.user.Hash.verify')
    @patch('routers.user.get_db')
    @patch('routers.user.get_current_user')
    def test_delete_account_wrong_password(self, mock_get_current_user, mock_get_db, mock_hash_verify, client, mock_user, auth_headers, valid_deletion_data):
        """間違ったパスワードでアカウント削除を試行するテスト"""
        mock_get_current_user.return_value = mock_user
        mock_hash_verify.return_value = False
        
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # ユーザークエリのモック
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = user_query
        
        response = client.request("DELETE", "/api/v1/user/delete-account", json=valid_deletion_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "パスワードが正しくありません" in response.json()["detail"]
        mock_db.rollback.assert_called_once()
    
    def test_delete_account_invalid_token(self, client, valid_deletion_data):
        """無効なトークンでアクセスするテスト"""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.request("DELETE", "/api/v1/user/delete-account", json=valid_deletion_data, headers=invalid_headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_delete_account_expired_token(self, client, valid_deletion_data, mock_user):
        """期限切れトークンでアクセスするテスト"""
        # 期限切れトークンを作成
        data = {
            "sub": mock_user.email,
            "id": mock_user.id
        }
        expire = datetime.utcnow() - timedelta(minutes=30)  # 過去の時刻
        data.update({"exp": expire})
        expired_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        
        expired_headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.request("DELETE", "/api/v1/user/delete-account", json=valid_deletion_data, headers=expired_headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]
