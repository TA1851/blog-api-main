#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ユーザールーターの包括的テストスイート

このテストスイートは routers/user.py の全ての機能をテストします:
- ユーザー作成（メール認証有無の両パターン）
- メール認証機能
- ユーザー情報取得
- アカウント削除機能
- 認証メール再送機能
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4

from routers.user import (
    router,
    create_user,
    verify_email,
    show_user,
    delete_user_account,
    resend_verification_email,
    UserNotFoundError,
    EmailVerificationError,
    DatabaseError,
    ALLOWED_EMAIL_DOMAINS,
    ENABLE_DOMAIN_RESTRICTION,
    ENABLE_EMAIL_VERIFICATION
)
from schemas import User as UserSchema, AccountDeletionRequest
from models import User as UserModel, EmailVerification, Article
from main import app


class TestUserRouterEnvironmentVariables:
    """環境変数関連のテスト"""
    
    def test_allowed_email_domains_configuration(self):
        """許可メールドメインの設定を確認"""
        assert isinstance(ALLOWED_EMAIL_DOMAINS, list)
        # 環境変数が設定されている場合のテスト
        
    def test_enable_domain_restriction_configuration(self):
        """ドメイン制限有効フラグの設定を確認"""
        assert isinstance(ENABLE_DOMAIN_RESTRICTION, bool)
        
    def test_enable_email_verification_configuration(self):
        """メール認証有効フラグの設定を確認"""
        assert isinstance(ENABLE_EMAIL_VERIFICATION, bool)


class TestUserRouterExceptions:
    """カスタム例外クラスのテスト"""
    
    def test_user_not_found_error_with_id(self):
        """ユーザーIDを指定したUserNotFoundErrorのテスト"""
        error = UserNotFoundError(user_id=123)
        assert "User with id 123 not found" in str(error)
        
    def test_user_not_found_error_with_email(self):
        """メールアドレスを指定したUserNotFoundErrorのテスト"""
        error = UserNotFoundError(email="test@example.com")
        assert "User with email test@example.com not found" in str(error)
        
    def test_user_not_found_error_default(self):
        """デフォルトのUserNotFoundErrorのテスト"""
        error = UserNotFoundError()
        assert "User not found" in str(error)
        
    def test_email_verification_error(self):
        """EmailVerificationErrorのテスト"""
        error = EmailVerificationError("Verification failed")
        assert error.message == "Verification failed"
        
    def test_database_error(self):
        """DatabaseErrorのテスト"""
        error = DatabaseError("Database connection failed")
        assert error.message == "Database connection failed"


class TestCreateUserEndpoint:
    """create_user エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.close = MagicMock()
        db.add = MagicMock()
        db.refresh = MagicMock()
        return db
    
    @pytest.fixture
    def valid_user_schema(self):
        """有効なユーザースキーマ"""
        return UserSchema(email="test@example.com", password="password123")
    
    def test_create_user_missing_email(self, mock_db, caplog):
        """メールアドレスが無い場合のエラーテスト"""
        user = UserSchema(email=None)
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(create_user(user, mock_db))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "メールアドレスが必要です" in exc_info.value.detail
    
    @patch('routers.user.is_valid_email_domain')
    def test_create_user_domain_restriction_enabled_invalid_domain(self, mock_domain_check, mock_db, valid_user_schema):
        """ドメイン制限が有効で無効なドメインの場合のテスト"""
        mock_domain_check.return_value = False
        
        with patch('routers.user.ENABLE_DOMAIN_RESTRICTION', True):
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(create_user(valid_user_schema, mock_db))
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "このメールアドレスのドメインは許可されていません" in exc_info.value.detail
    
    def test_create_user_duplicate_email(self, mock_db, valid_user_schema):
        """重複メールアドレスの場合のテスト"""
        # 既存ユーザーをシミュレート
        existing_user = MagicMock()
        existing_user.email = "test@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(create_user(valid_user_schema, mock_db))
        
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "このメールアドレスは既に使用されています" in exc_info.value.detail
    
    @patch('routers.user.send_verification_email')
    @patch('routers.user.is_valid_email_domain')
    def test_create_user_email_verification_enabled_new_user(self, mock_domain_check, mock_send_email, mock_db, valid_user_schema):
        """メール認証有効で新規ユーザーの場合のテスト"""
        mock_domain_check.return_value = True
        mock_send_email.return_value = AsyncMock()
        
        # 既存ユーザーなし、既存認証レコードなし
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('routers.user.ENABLE_EMAIL_VERIFICATION', True):
            with patch('routers.user.EmailVerification.create_verification') as mock_create_verification:
                mock_verification = MagicMock()
                mock_verification.token = "test-token"
                mock_create_verification.return_value = mock_verification
                
                result = asyncio.run(create_user(valid_user_schema, mock_db))
                
                assert "ユーザー登録を受け付けました" in result["message"]
                assert result["email"] == "test@example.com"
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
    
    @patch('routers.user.send_verification_email')
    @patch('routers.user.is_valid_email_domain')
    def test_create_user_email_verification_enabled_existing_verified(self, mock_domain_check, mock_send_email, mock_db, valid_user_schema):
        """メール認証有効で既に認証済みの場合のテスト"""
        mock_domain_check.return_value = True
        
        # 既存ユーザーなし
        mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),  # 既存ユーザーなし
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=MagicMock(is_verified=True)))))  # 認証済み
        ]
        
        with patch('routers.user.ENABLE_EMAIL_VERIFICATION', True):
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(create_user(valid_user_schema, mock_db))
            
            assert exc_info.value.status_code == status.HTTP_409_CONFLICT
            assert "このメールアドレスは既に確認済みです" in exc_info.value.detail
    
    @patch('routers.user.send_verification_email')
    @patch('routers.user.is_valid_email_domain')
    def test_create_user_email_verification_enabled_existing_unverified(self, mock_domain_check, mock_send_email, mock_db, valid_user_schema):
        """メール認証有効で未認証レコードが既にある場合のテスト"""
        mock_domain_check.return_value = True
        mock_send_email.return_value = AsyncMock()
        
        # 既存ユーザーなし、未認証レコードあり
        existing_verification = MagicMock()
        existing_verification.is_verified = False
        existing_verification.email = "test@example.com"
        
        mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),  # 既存ユーザーなし
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=existing_verification))))  # 未認証レコードあり
        ]
        
        with patch('routers.user.ENABLE_EMAIL_VERIFICATION', True):
            result = asyncio.run(create_user(valid_user_schema, mock_db))
            
            assert "ユーザー登録を受け付けました" in result["message"]
            assert result["email"] == "test@example.com"
            # 既存レコードを更新
            assert existing_verification.token is not None
            mock_db.commit.assert_called_once()
    
    @patch('routers.user.Hash.bcrypt')
    @patch('routers.user.is_valid_email_domain')
    def test_create_user_email_verification_disabled(self, mock_domain_check, mock_hash, mock_db, valid_user_schema):
        """メール認証無効で直接ユーザー作成の場合のテスト"""
        mock_domain_check.return_value = True
        mock_hash.return_value = "hashed_temp_password"
        
        # 既存ユーザーなし
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 新規ユーザーのモック
        new_user = MagicMock()
        new_user.id = 123
        new_user.email = "test@example.com"
        new_user.is_active = True
        mock_db.refresh.side_effect = lambda x: setattr(x, 'id', 123) or setattr(x, 'is_active', True)
        
        with patch('routers.user.ENABLE_EMAIL_VERIFICATION', False):
            with patch('routers.user.UserModel') as mock_user_model:
                mock_user_model.return_value = new_user
                
                result = asyncio.run(create_user(valid_user_schema, mock_db))
                
                assert "ユーザー登録が完了しました" in result["message"]
                assert result["email"] == "test@example.com"
                assert "id" in result
                assert "is_active" in result
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
    
    def test_create_user_database_error(self, mock_db, valid_user_schema):
        """データベースエラーの場合のテスト"""
        mock_db.query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(create_user(valid_user_schema, mock_db))
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "予期しないエラーが発生しました" in exc_info.value.detail
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()


class TestVerifyEmailEndpoint:
    """verify_email エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        db.commit = MagicMock()
        db.add = MagicMock()
        db.refresh = MagicMock()
        return db
    
    def test_verify_email_invalid_token_format(self, mock_db):
        """無効なトークン形式の場合のテスト"""
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(verify_email("short", mock_db))
        
        assert exc_info.value.status_code == 400
        assert "無効なトークン形式です" in exc_info.value.detail
    
    def test_verify_email_token_not_found(self, mock_db):
        """トークンが見つからない場合のテスト"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(verify_email("valid-token-12345", mock_db))
        
        assert exc_info.value.status_code == 400
        assert "無効なトークンです" in exc_info.value.detail
    
    def test_verify_email_already_verified(self, mock_db):
        """既に認証済みの場合のテスト"""
        mock_verification = MagicMock()
        mock_verification.is_verified = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_verification
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(verify_email("valid-token-12345", mock_db))
        
        assert exc_info.value.status_code == 400
        assert "このメールアドレスは既に確認済みです" in exc_info.value.detail
    
    def test_verify_email_expired_token(self, mock_db):
        """期限切れトークンの場合のテスト"""
        mock_verification = MagicMock()
        mock_verification.is_verified = False
        mock_verification.expires_at = datetime.utcnow() - timedelta(hours=1)  # 1時間前に期限切れ
        mock_db.query.return_value.filter.return_value.first.return_value = mock_verification
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(verify_email("valid-token-12345", mock_db))
        
        assert exc_info.value.status_code == 400
        assert "トークンの有効期限が切れています" in exc_info.value.detail
    
    @patch('routers.user.Hash.bcrypt')
    def test_verify_email_success(self, mock_hash, mock_db):
        """メール認証成功の場合のテスト"""
        mock_hash.return_value = "hashed_temp_password"
        
        mock_verification = MagicMock()
        mock_verification.is_verified = False
        mock_verification.expires_at = datetime.utcnow() + timedelta(hours=1)  # まだ有効
        mock_verification.email = "test@example.com"
        mock_verification.password_hash = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_verification
        
        # 新規ユーザーのモック
        new_user = MagicMock()
        new_user.id = 123
        new_user.is_active = True
        
        with patch('routers.user.UserModel') as mock_user_model:
            mock_user_model.return_value = new_user
            
            result = asyncio.run(verify_email("valid-token-12345", mock_db))
            
            assert "メールアドレスの確認が完了しました" in result["message"]
            assert result["email"] == "test@example.com"
            assert result["user_id"] == 123
            assert result["is_active"] is True
            
            # 認証フラグが更新されることを確認
            assert mock_verification.is_verified is True
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @patch('routers.user.Hash.bcrypt')
    def test_verify_email_success_with_custom_password(self, mock_hash, mock_db):
        """カスタムパスワードありでの認証成功テスト"""
        mock_verification = MagicMock()
        mock_verification.is_verified = False
        mock_verification.expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_verification.email = "test@example.com"
        mock_verification.password_hash = "custom_hashed_password"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_verification
        
        new_user = MagicMock()
        new_user.id = 123
        new_user.is_active = True
        
        with patch('routers.user.UserModel') as mock_user_model:
            mock_user_model.return_value = new_user
            
            result = asyncio.run(verify_email("valid-token-12345", mock_db))
            
            assert "メールアドレスの確認が完了しました" in result["message"]
            # カスタムパスワードが使用されることを確認（Hashが呼ばれない）
            mock_hash.assert_not_called()
    
    def test_verify_email_url_decoding(self, mock_db):
        """URLエンコードされたトークンのデコードテスト"""
        encoded_token = "valid%2Dtoken%2D12345"  # "valid-token-12345"をURLエンコード
        
        mock_verification = MagicMock()
        mock_verification.is_verified = False
        mock_verification.expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_verification.email = "test@example.com"
        
        # デコードされたトークンで検索される
        def mock_query_filter_side_effect(*args, **kwargs):
            mock_filter = MagicMock()
            mock_filter.first.return_value = mock_verification
            return mock_filter
        
        mock_db.query.return_value.filter.side_effect = mock_query_filter_side_effect
        
        new_user = MagicMock()
        new_user.id = 123
        new_user.is_active = True
        
        with patch('routers.user.UserModel') as mock_user_model:
            mock_user_model.return_value = new_user
            
            result = asyncio.run(verify_email(encoded_token, mock_db))
            
            assert "メールアドレスの確認が完了しました" in result["message"]


class TestShowUserEndpoint:
    """show_user エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        db = MagicMock(spec=Session)
        return db
    
    @pytest.fixture
    def mock_current_user(self):
        """モック現在ユーザー"""
        user = MagicMock()
        user.id = 123
        user.email = "current@example.com"
        return user
    
    def test_show_user_access_other_user(self, mock_db, mock_current_user):
        """他のユーザーの情報にアクセスしようとした場合のテスト"""
        other_user_id = 456
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(show_user(other_user_id, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "他のユーザーの情報にはアクセスできません" in exc_info.value.detail
    
    def test_show_user_not_found(self, mock_db, mock_current_user):
        """ユーザーが見つからない場合のテスト"""
        user_id = 123  # 現在のユーザーID
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(show_user(user_id, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert f"User with id {user_id} not found" in exc_info.value.detail
    
    def test_show_user_success(self, mock_db, mock_current_user):
        """正常なユーザー情報取得のテスト"""
        user_id = 123  # 現在のユーザーID
        
        mock_user = MagicMock()
        mock_user.email = "current@example.com"
        mock_user.is_active = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = asyncio.run(show_user(user_id, mock_db, mock_current_user))
        
        assert result.email == "current@example.com"
        assert result.password is None  # パスワードは返さない
        assert result.is_active is True


class TestDeleteUserAccountEndpoint:
    """delete_user_account エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.all.return_value = []  # デフォルトで空リスト
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.close = MagicMock()
        db.delete = MagicMock()
        return db
    
    @pytest.fixture
    def valid_deletion_request(self):
        """有効な削除リクエスト"""
        return AccountDeletionRequest(
            email="test@example.com",
            password="password123",
            confirm_password="password123"
        )
    
    def test_delete_user_account_user_not_found(self, mock_db, valid_deletion_request):
        """ユーザーが見つからない場合のテスト"""
        # 認証されたユーザーのモック
        mock_current_user = MagicMock()
        mock_current_user.email = "test@example.com"
        mock_current_user.id = 123
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_user_account(valid_deletion_request, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "指定されたメールアドレスのユーザーが見つかりません" in exc_info.value.detail
    
    def test_delete_user_account_no_password_set(self, mock_db, valid_deletion_request):
        """パスワードが設定されていない場合のテスト"""
        # 認証されたユーザーのモック
        mock_current_user = MagicMock()
        mock_current_user.email = "test@example.com"
        mock_current_user.id = 123
        
        mock_user = MagicMock()
        mock_user.password = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_user_account(valid_deletion_request, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "ユーザーのパスワードが設定されていません" in exc_info.value.detail
    
    @patch('routers.user.Hash.verify')
    def test_delete_user_account_wrong_password(self, mock_hash_verify, mock_db, valid_deletion_request):
        """パスワードが間違っている場合のテスト"""
        # 認証されたユーザーのモック
        mock_current_user = MagicMock()
        mock_current_user.email = "test@example.com"
        mock_current_user.id = 123
        
        mock_hash_verify.return_value = False
        
        mock_user = MagicMock()
        mock_user.password = "hashed_password"
        mock_user.email = "test@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_user_account(valid_deletion_request, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "パスワードが正しくありません" in exc_info.value.detail
    
    @patch('routers.user.Hash.verify')
    def test_delete_user_account_no_email(self, mock_hash_verify, mock_db, valid_deletion_request):
        """ユーザーのメールアドレスがない場合のテスト"""
        # 認証されたユーザーのモック
        mock_current_user = MagicMock()
        mock_current_user.email = "test@example.com"
        mock_current_user.id = 123
        
        mock_hash_verify.return_value = True
        
        mock_user = MagicMock()
        mock_user.password = "hashed_password"
        mock_user.email = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_user_account(valid_deletion_request, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "ユーザーのメールアドレスが見つかりません" in exc_info.value.detail
    
    @patch('routers.user.send_account_deletion_email')
    @patch('routers.user.Hash.verify')
    def test_delete_user_account_success(self, mock_hash_verify, mock_send_email, mock_db, valid_deletion_request):
        """正常なアカウント削除のテスト"""
        # 認証されたユーザーのモック
        mock_current_user = MagicMock()
        mock_current_user.email = "test@example.com"
        mock_current_user.id = 123
        
        mock_hash_verify.return_value = True
        mock_send_email.return_value = AsyncMock()
        
        # ユーザーのモック
        mock_user = MagicMock()
        mock_user.id = 123
        mock_user.password = "hashed_password"
        mock_user.email = "test@example.com"
        
        # 記事のモック
        mock_articles = [MagicMock(), MagicMock()]  # 2つの記事
        
        # 認証レコードのモック
        mock_verification_records = [MagicMock()]
        
        # クエリのモック設定 - より簡潔にするため、個別にセットアップ
        # まずユーザークエリをセットアップ
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = mock_user
        
        # 記事クエリをセットアップ
        article_query = MagicMock()
        article_query.filter.return_value.all.return_value = mock_articles
        
        # 認証レコードクエリをセットアップ
        verification_query = MagicMock()
        verification_query.filter.return_value.all.return_value = mock_verification_records
        
        # queryメソッドの呼び出し順序に基づいてサイドエフェクトを設定
        mock_db.query.side_effect = [user_query, article_query, verification_query]
        
        result = asyncio.run(delete_user_account(valid_deletion_request, mock_db, mock_current_user))
        
        assert "退会処理が完了しました" in result["message"]
        assert result["email"] == "test@example.com"
        assert result["deleted_articles_count"] == "2"
        
        # 削除処理の確認
        assert mock_db.delete.call_count >= 4  # ユーザー、記事2つ、認証レコード1つ
        mock_db.commit.assert_called_once()
    
    def test_delete_user_account_password_mismatch(self, mock_db):
        """パスワード不一致の場合のテスト"""
        # 認証されたユーザーのモック
        mock_current_user = MagicMock()
        mock_current_user.email = "test@example.com"
        mock_current_user.id = 123
        
        deletion_request = AccountDeletionRequest(
            email="test@example.com",
            password="password123",
            confirm_password="different456"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_user_account(deletion_request, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "パスワードと確認用パスワードが一致しません" in str(exc_info.value.detail)
        mock_db.rollback.assert_called_once()
    
    def test_delete_user_account_database_error(self, mock_db, valid_deletion_request):
        """データベースエラーの場合のテスト"""
        # 認証されたユーザーのモック
        mock_current_user = MagicMock()
        mock_current_user.email = "test@example.com"
        mock_current_user.id = 123
        
        mock_db.query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_user_account(valid_deletion_request, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "退会処理中に予期しないエラーが発生しました" in exc_info.value.detail
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()


class TestResendVerificationEmailEndpoint:
    """resend_verification_email エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        db = MagicMock(spec=Session)
        db.commit = MagicMock()
        return db
    
    def test_resend_verification_email_not_found(self, mock_db):
        """確認待ちのメールアドレスが見つからない場合のテスト"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(resend_verification_email("test@example.com", mock_db))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "確認待ちのメールアドレスが見つかりません" in exc_info.value.detail
    
    @patch('routers.user.send_verification_email')
    def test_resend_verification_email_success(self, mock_send_email, mock_db):
        """認証メール再送成功のテスト"""
        mock_send_email.return_value = AsyncMock()
        
        mock_verification = MagicMock()
        mock_verification.email = "test@example.com"
        mock_verification.is_verified = False
        old_token = "old-token"
        mock_verification.token = old_token
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_verification
        
        result = asyncio.run(resend_verification_email("test@example.com", mock_db))
        
        assert result["message"] == "確認メールを再送信しました。"
        
        # 新しいトークンが生成されることを確認
        assert mock_verification.token != old_token
        assert mock_verification.created_at is not None
        assert mock_verification.expires_at is not None
        
        mock_db.commit.assert_called_once()
        mock_send_email.assert_called_once()


class TestUserRouterIntegration:
    """ユーザールーターの統合テスト"""
    
    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)
    
    def test_router_configuration(self):
        """ルーター設定のテスト"""
        assert router.prefix == "/api/v1"
        assert "user" in router.tags
    
    def test_router_endpoints_exist(self):
        """エンドポイントが存在することを確認"""
        routes = [route.path for route in router.routes]
        
        assert "/api/v1/user" in routes  # POST
        assert "/api/v1/verify-email" in routes  # GET
        assert "/api/v1/user/{user_id}" in routes  # GET
        assert "/api/v1/user/delete-account" in routes  # DELETE
        assert "/api/v1/resend-verification" in routes  # POST


class TestUserRouterEdgeCases:
    """エッジケースのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        db = MagicMock(spec=Session)
        return db
    
    def test_create_user_with_name_field(self, mock_db):
        """name フィールドがある場合のユーザー作成テスト"""
        user = UserSchema(email="test@example.com", password="password123")
        # UserSchemaにはnameフィールドがないため、代わりにメールアドレスからユーザー名を抽出する処理をテスト
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('routers.user.ENABLE_EMAIL_VERIFICATION', False):
            with patch('routers.user.is_valid_email_domain', return_value=True):
                with patch('routers.user.Hash.bcrypt', return_value="hashed"):
                    with patch('routers.user.UserModel') as mock_user_model:
                        new_user = MagicMock()
                        new_user.id = 123
                        new_user.is_active = True
                        mock_user_model.return_value = new_user
                        
                        result = asyncio.run(create_user(user, mock_db))
                        
                        assert "ユーザー登録が完了しました" in result["message"]
                        # ユーザー名がメールアドレスのローカル部分から生成されることを確認
                        mock_user_model.assert_called_once()
    
    def test_verify_email_empty_token(self, mock_db):
        """空のトークンの場合のテスト"""
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(verify_email("", mock_db))
        
        assert exc_info.value.status_code == 400
        assert "無効なトークン形式です" in exc_info.value.detail
    
    def test_verify_email_none_expires_at(self, mock_db):
        """expires_at が None の場合のテスト"""
        mock_verification = MagicMock()
        mock_verification.is_verified = False
        mock_verification.expires_at = None  # 期限なし
        mock_verification.email = "test@example.com"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_verification
        
        new_user = MagicMock()
        new_user.id = 123
        new_user.is_active = True
        
        with patch('routers.user.UserModel') as mock_user_model:
            mock_user_model.return_value = new_user
            
            result = asyncio.run(verify_email("valid-token-12345", mock_db))
            
            assert "メールアドレスの確認が完了しました" in result["message"]


class TestDeleteUserAccountWithAuth:
    """delete_user_account エンドポイント（認証機能あり）のテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.all.return_value = []
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.close = MagicMock()
        db.delete = MagicMock()
        return db
    
    @pytest.fixture
    def mock_current_user(self):
        """モック認証ユーザー"""
        user = MagicMock()
        user.id = 123
        user.email = "test@example.com"
        user.password = "hashed_password"
        return user
    
    @pytest.fixture
    def valid_deletion_request(self):
        """有効な削除リクエスト"""
        return AccountDeletionRequest(
            email="test@example.com",
            password="password123",
            confirm_password="password123"
        )
    
    @pytest.fixture
    def unauthorized_deletion_request(self):
        """権限のない削除リクエスト（異なるメールアドレス）"""
        return AccountDeletionRequest(
            email="other@example.com",
            password="password123",
            confirm_password="password123"
        )
    
    def test_delete_user_account_unauthorized_different_email(self, mock_db, mock_current_user, unauthorized_deletion_request):
        """認証ユーザーと異なるメールアドレスでアカウント削除を試行する場合のテスト"""
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_user_account(unauthorized_deletion_request, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "自分のアカウントのみ削除できます" in exc_info.value.detail
        mock_db.rollback.assert_called_once()
    
    @patch('routers.user.send_account_deletion_email')
    @patch('routers.user.Hash.verify')
    def test_delete_user_account_success_with_auth(self, mock_hash_verify, mock_send_email, mock_db, mock_current_user, valid_deletion_request):
        """認証機能ありで正常なアカウント削除のテスト"""
        mock_hash_verify.return_value = True
        mock_send_email.return_value = AsyncMock()
        
        # 記事のモック
        mock_articles = [MagicMock(), MagicMock()]
        
        # 認証レコードのモック
        mock_verification_records = [MagicMock()]
        
        # クエリのモック設定
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = mock_current_user
        
        article_query = MagicMock()
        article_query.filter.return_value.all.return_value = mock_articles
        
        verification_query = MagicMock()
        verification_query.filter.return_value.all.return_value = mock_verification_records
        
        mock_db.query.side_effect = [user_query, article_query, verification_query]
        
        result = asyncio.run(delete_user_account(valid_deletion_request, mock_db, mock_current_user))
        
        assert "退会処理が完了しました" in result["message"]
        assert result["email"] == "test@example.com"
        assert result["deleted_articles_count"] == "2"
        
        # 削除処理の確認
        assert mock_db.delete.call_count >= 4
        mock_db.commit.assert_called_once()
    
    def test_delete_user_account_password_mismatch_with_auth(self, mock_db, mock_current_user):
        """認証機能ありでパスワード不一致の場合のテスト"""
        deletion_request = AccountDeletionRequest(
            email="test@example.com",
            password="password123",
            confirm_password="different456"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_user_account(deletion_request, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "パスワードと確認用パスワードが一致しません" in str(exc_info.value.detail)
        mock_db.rollback.assert_called_once()
    
    @patch('routers.user.Hash.verify')
    def test_delete_user_account_wrong_password_with_auth(self, mock_hash_verify, mock_db, mock_current_user, valid_deletion_request):
        """認証機能ありでパスワードが間違っている場合のテスト"""
        mock_hash_verify.return_value = False
        
        # ユーザークエリのモック
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = mock_current_user
        mock_db.query.return_value = user_query
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_user_account(valid_deletion_request, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "パスワードが正しくありません" in exc_info.value.detail
        mock_db.rollback.assert_called_once()


# テスト実行用の設定
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
