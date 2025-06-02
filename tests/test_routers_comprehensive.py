#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routers包括的統合テストスイート

Blog API の全ルーターモジュール（article.py, auth.py, user.py）の
包括的なテストを実行し、完全なカバレッジを目指します。

テスト対象:
- Article Router: 記事管理とパブリック記事機能
- Auth Router: 認証とJWTトークン管理
- User Router: ユーザー管理とメール認証
"""

import pytest
import asyncio
import os
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import func
from jose import jwt
from uuid import uuid4
import urllib.parse

# アプリケーションインポート
from main import app
from routers import article, auth, user
from schemas import ArticleBase, User as UserSchema, Login, PasswordChange, AccountDeletionRequest
from models import Article, User as UserModel, EmailVerification
from database import get_db
from hashing import Hash
from oauth2 import get_current_user, SECRET_KEY, ALGORITHM
from custom_token import create_access_token


# テストクライアント
client = TestClient(app)


class TestRoutersIntegration:
    """Routers統合テストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前処理"""
        self.mock_db = MagicMock(spec=Session)
        self.mock_user = MagicMock(spec=UserModel)
        self.mock_user.id = 1
        self.mock_user.email = "test@example.com"
        self.mock_user.password = Hash.bcrypt("testpassword")
        self.mock_user.name = "Test User"
        
        # テスト用記事データ
        self.mock_article = MagicMock(spec=Article)
        self.mock_article.id = 1
        self.mock_article.title = "Test Article"
        self.mock_article.content = "Test content"
        self.mock_article.user_id = 1
        self.mock_article.published = True
        self.mock_article.created_at = datetime.now()
        self.mock_article.updated_at = datetime.now()


class TestArticleRouterComprehensive:
    """Article Router包括的テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.mock_db = MagicMock(spec=Session)
        self.mock_user = MagicMock(spec=UserModel)
        self.mock_user.id = 1
        self.mock_user.email = "test@example.com"
        self.mock_article = MagicMock(spec=Article)
        self.mock_article.id = 1
        self.mock_article.title = "Test Article"
        self.mock_article.content = "Test content"
    
    @patch('routers.article.get_db')
    @patch('routers.article.get_current_user')
    def test_all_fetch_success(self, mock_get_user, mock_get_db):
        """記事一覧取得成功テスト"""
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_user
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [self.mock_article]
        
        response = client.get("/api/v1/articles")
        assert response.status_code == 200
    
    @patch('routers.article.get_db')
    @patch('routers.article.get_current_user')
    def test_all_fetch_with_pagination(self, mock_get_user, mock_get_db):
        """ページネーション付き記事取得テスト"""
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_user
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        response = client.get("/api/v1/articles?limit=10&skip=0")
        assert response.status_code == 200
    
    @patch('routers.article.get_db')
    @patch('routers.article.get_current_user')
    def test_get_article_success(self, mock_get_user, mock_get_db):
        """個別記事取得成功テスト"""
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_user
        self.mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = self.mock_article
        
        response = client.get("/api/v1/articles/1")
        assert response.status_code == 200
    
    @patch('routers.article.get_db')
    @patch('routers.article.get_current_user')
    def test_get_article_not_found(self, mock_get_user, mock_get_db):
        """記事が見つからない場合のテスト"""
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_user
        self.mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/api/v1/articles/999")
        assert response.status_code == 404
    
    @patch('routers.article.get_db')
    @patch('routers.article.get_current_user')
    def test_create_article_success(self, mock_get_user, mock_get_db):
        """記事作成成功テスト"""
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_user
        
        article_data = {
            "title": "New Article",
            "content": "New content",
            "published": True
        }
        
        response = client.post("/api/v1/articles", json=article_data)
        assert response.status_code == 201
    
    @patch('routers.article.get_db')
    @patch('routers.article.get_current_user')
    def test_update_article_success(self, mock_get_user, mock_get_db):
        """記事更新成功テスト"""
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_user
        self.mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = self.mock_article
        
        update_data = {
            "title": "Updated Article",
            "content": "Updated content",
            "published": True
        }
        
        response = client.put("/api/v1/articles/1", json=update_data)
        assert response.status_code == 202
    
    @patch('routers.article.get_db')
    @patch('routers.article.get_current_user')
    def test_delete_article_success(self, mock_get_user, mock_get_db):
        """記事削除成功テスト"""
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_user
        self.mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = self.mock_article
        
        response = client.delete("/api/v1/articles/1")
        assert response.status_code == 204
    
    @patch('routers.article.get_db')
    def test_get_public_articles_success(self, mock_get_db):
        """パブリック記事取得成功テスト"""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [self.mock_article]
        
        response = client.get("/api/v1/public/articles")
        assert response.status_code == 200
    
    @patch('routers.article.get_db')
    def test_search_public_articles_success(self, mock_get_db):
        """パブリック記事検索成功テスト"""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [self.mock_article]
        
        response = client.get("/api/v1/public/articles/search?q=test")
        assert response.status_code == 200
    
    @patch('routers.article.get_db')
    def test_get_public_article_by_id_success(self, mock_get_db):
        """パブリック記事個別取得成功テスト"""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = self.mock_article
        
        response = client.get("/api/v1/public/articles/1")
        assert response.status_code == 200


class TestAuthRouterComprehensive:
    """Auth Router包括的テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.mock_user = MagicMock(spec=UserModel)
        self.mock_user.id = 1
        self.mock_user.email = "test@example.com"
        self.mock_user.password = Hash.bcrypt("testpassword")
        self.mock_user.name = "Test User"
    
    @patch('routers.auth.session')
    def test_login_success(self, mock_session):
        """ログイン成功テスト"""
        mock_session.query.return_value.filter.return_value.first.return_value = self.mock_user
        
        login_data = {
            "username": "test@example.com",
            "password": "testpassword"
        }
        
        with patch('routers.auth.Hash.verify', return_value=True):
            response = client.post("/api/v1/login", data=login_data)
            assert response.status_code == 200
            assert "access_token" in response.json()
    
    @patch('routers.auth.session')
    def test_login_user_not_found(self, mock_session):
        """ユーザーが見つからない場合のログインテスト"""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        login_data = {
            "username": "nonexistent@example.com",
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/login", data=login_data)
        assert response.status_code == 401
    
    @patch('routers.auth.session')
    def test_login_invalid_password(self, mock_session):
        """無効なパスワードでのログインテスト"""
        mock_session.query.return_value.filter.return_value.first.return_value = self.mock_user
        
        login_data = {
            "username": "test@example.com",
            "password": "wrongpassword"
        }
        
        with patch('routers.auth.Hash.verify', return_value=False):
            response = client.post("/api/v1/login", data=login_data)
            assert response.status_code == 401
    
    @patch('routers.auth.session')
    @patch('routers.auth.blacklisted_tokens', new_set=set())
    def test_logout_success(self, mock_session):
        """ログアウト成功テスト"""
        # トークン生成
        token = create_access_token(data={"sub": "test@example.com"})
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/v1/logout", headers=headers)
        assert response.status_code == 200
    
    def test_logout_no_token(self):
        """トークンなしのログアウトテスト"""
        response = client.post("/api/v1/logout")
        assert response.status_code == 401
    
    @patch('routers.auth.session')
    def test_change_password_success(self, mock_session):
        """パスワード変更成功テスト"""
        mock_session.query.return_value.filter.return_value.first.return_value = self.mock_user
        
        password_data = {
            "email": "test@example.com",
            "current_password": "testpassword",
            "new_password": "newpassword123"
        }
        
        with patch('routers.auth.Hash.verify', return_value=True):
            with patch('routers.auth.send_registration_complete_email'):
                response = client.post("/api/v1/change-password", json=password_data)
                assert response.status_code == 200
    
    @patch('routers.auth.session')
    def test_get_articles_legacy_success(self, mock_session):
        """レガシー記事取得成功テスト"""
        mock_article = MagicMock()
        mock_article.id = 1
        mock_article.title = "Test Article"
        mock_session.query.return_value.all.return_value = [mock_article]
        
        response = client.get("/api/v1/articles-legacy")
        assert response.status_code == 200
    
    @patch('routers.auth.session')
    def test_get_articles_legacy_empty(self, mock_session):
        """レガシー記事取得（空）テスト"""
        mock_session.query.return_value.all.return_value = []
        
        response = client.get("/api/v1/articles-legacy")
        assert response.status_code == 200
        assert response.json() == []


class TestUserRouterComprehensive:
    """User Router包括的テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.mock_db = MagicMock(spec=Session)
        self.mock_user = MagicMock(spec=UserModel)
        self.mock_user.id = 1
        self.mock_user.email = "test@example.com"
        self.mock_user.name = "Test User"
    
    @patch('routers.user.get_db')
    @patch('routers.user.is_valid_email_domain')
    @patch('routers.user.send_verification_email')
    def test_create_user_success(self, mock_send_email, mock_email_valid, mock_get_db):
        """ユーザー作成成功テスト"""
        mock_get_db.return_value = self.mock_db
        mock_email_valid.return_value = True
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        user_data = {
            "name": "New User",
            "email": "new@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 201
    
    @patch('routers.user.get_db')
    @patch('routers.user.is_valid_email_domain')
    def test_create_user_email_exists(self, mock_email_valid, mock_get_db):
        """既存メールアドレスでのユーザー作成テスト"""
        mock_get_db.return_value = self.mock_db
        mock_email_valid.return_value = True
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_user
        
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 400
    
    @patch('routers.user.get_db')
    @patch('routers.user.is_valid_email_domain')
    def test_create_user_invalid_email_domain(self, mock_email_valid, mock_get_db):
        """無効なメールドメインでのユーザー作成テスト"""
        mock_get_db.return_value = self.mock_db
        mock_email_valid.return_value = False
        
        user_data = {
            "name": "Test User",
            "email": "test@invalid.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 400
    
    @patch('routers.user.get_db')
    def test_verify_email_success(self, mock_get_db):
        """メール認証成功テスト"""
        mock_get_db.return_value = self.mock_db
        mock_verification = MagicMock(spec=EmailVerification)
        mock_verification.user_id = 1
        mock_verification.expires_at = datetime.now() + timedelta(hours=1)
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_verification
        
        response = client.get("/api/v1/verify-email/test-token")
        assert response.status_code == 200
    
    @patch('routers.user.get_db')
    def test_verify_email_invalid_token(self, mock_get_db):
        """無効なトークンでのメール認証テスト"""
        mock_get_db.return_value = self.mock_db
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/api/v1/verify-email/invalid-token")
        assert response.status_code == 400
    
    @patch('routers.user.get_db')
    @patch('routers.user.get_current_user')
    def test_get_current_user_info(self, mock_get_user, mock_get_db):
        """現在のユーザー情報取得テスト"""
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_user
        
        token = create_access_token(data={"sub": "test@example.com"})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
    
    @patch('routers.user.get_db')
    @patch('routers.user.get_current_user')
    def test_update_user_success(self, mock_get_user, mock_get_db):
        """ユーザー情報更新成功テスト"""
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_user
        
        update_data = {
            "name": "Updated Name",
            "email": "updated@example.com"
        }
        
        token = create_access_token(data={"sub": "test@example.com"})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.put("/api/v1/users/me", json=update_data, headers=headers)
        assert response.status_code == 200
    
    @patch('routers.user.get_db')
    @patch('routers.user.get_current_user')
    @patch('routers.user.send_account_deletion_email')
    def test_delete_user_success(self, mock_send_email, mock_get_user, mock_get_db):
        """ユーザー削除成功テスト"""
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = self.mock_user
        
        delete_data = {
            "email": "test@example.com",
            "password": "testpassword"
        }
        
        token = create_access_token(data={"sub": "test@example.com"})
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch('routers.user.Hash.verify', return_value=True):
            response = client.delete("/api/v1/users/me", json=delete_data, headers=headers)
            assert response.status_code == 200


class TestRoutersErrorHandling:
    """Routers エラーハンドリングテスト"""
    
    @patch('routers.article.get_db')
    @patch('routers.article.get_current_user')
    def test_article_database_error(self, mock_get_user, mock_get_db):
        """記事取得時のデータベースエラーテスト"""
        mock_get_db.return_value = self.mock_db
        mock_get_user.return_value = MagicMock()
        mock_get_db.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/v1/articles")
        assert response.status_code == 500
    
    @patch('routers.auth.session')
    def test_auth_database_error(self, mock_session):
        """認証時のデータベースエラーテスト"""
        mock_session.query.side_effect = Exception("Database error")
        
        login_data = {
            "username": "test@example.com",
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/login", data=login_data)
        assert response.status_code == 500
    
    @patch('routers.user.get_db')
    def test_user_database_error(self, mock_get_db):
        """ユーザー作成時のデータベースエラーテスト"""
        mock_get_db.side_effect = Exception("Database error")
        
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 500


class TestRoutersPerformance:
    """Routersパフォーマンステスト"""
    
    @patch('routers.article.get_db')
    @patch('routers.article.get_current_user')
    def test_large_article_list_performance(self, mock_get_user, mock_get_db):
        """大量記事リストのパフォーマンステスト"""
        mock_get_db.return_value = MagicMock()
        mock_get_user.return_value = MagicMock()
        
        # 大量のモック記事を作成
        large_article_list = [MagicMock() for _ in range(1000)]
        mock_get_db.return_value.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = large_article_list
        
        import time
        start_time = time.time()
        response = client.get("/api/v1/articles?limit=1000")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5  # 5秒以内
    
    def test_concurrent_login_requests(self):
        """同時ログイン要求のパフォーマンステスト"""
        login_data = {
            "username": "test@example.com",
            "password": "testpassword"
        }
        
        import concurrent.futures
        import time
        
        def make_login_request():
            return client.post("/api/v1/login", data=login_data)
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_login_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.time()
        
        assert (end_time - start_time) < 10  # 10秒以内
        assert len(results) == 10


class TestRoutersSecurityFeatures:
    """Routersセキュリティ機能テスト"""
    
    def test_jwt_token_validation(self):
        """JWTトークン検証テスト"""
        # 無効なトークン
        invalid_token = "invalid.token.here"
        headers = {"Authorization": f"Bearer {invalid_token}"}
        
        response = client.get("/api/v1/articles", headers=headers)
        assert response.status_code == 401
    
    def test_expired_token_handling(self):
        """期限切れトークンの処理テスト"""
        # 期限切れトークンを生成
        expired_payload = {
            "sub": "test@example.com",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get("/api/v1/articles", headers=headers)
        assert response.status_code == 401
    
    @patch('routers.user.is_valid_email_domain')
    def test_email_domain_validation(self, mock_email_valid):
        """メールドメイン検証テスト"""
        mock_email_valid.return_value = False
        
        user_data = {
            "name": "Test User",
            "email": "test@blocked-domain.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 400
    
    def test_password_hashing_security(self):
        """パスワードハッシュ化セキュリティテスト"""
        password = "testpassword123"
        hashed = Hash.bcrypt(password)
        
        # ハッシュ化されたパスワードは元のパスワードと異なることを確認
        assert hashed != password
        assert Hash.verify(password, hashed)
        assert not Hash.verify("wrongpassword", hashed)


class TestRoutersValidation:
    """Routersバリデーションテスト"""
    
    def test_article_validation_empty_title(self):
        """記事作成時の空タイトルバリデーション"""
        article_data = {
            "title": "",
            "content": "Test content",
            "published": True
        }
        
        response = client.post("/api/v1/articles", json=article_data)
        assert response.status_code in [400, 422]  # バリデーションエラー
    
    def test_user_validation_invalid_email(self):
        """ユーザー作成時の無効メールバリデーション"""
        user_data = {
            "name": "Test User",
            "email": "invalid-email",
            "password": "password123"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code in [400, 422]  # バリデーションエラー
    
    def test_password_strength_validation(self):
        """パスワード強度バリデーション"""
        weak_passwords = ["123", "pass", ""]
        
        for weak_password in weak_passwords:
            user_data = {
                "name": "Test User",
                "email": "test@example.com",
                "password": weak_password
            }
            
            response = client.post("/api/v1/users", json=user_data)
            assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
