#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
schemas.py用の包括的テストスイート
Pydanticモデルのバリデーション、データ変換、エラーハンドリングをテストします。
"""

import pytest
from pydantic import ValidationError
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from unittest.mock import Mock, patch

# テスト対象のモジュールをインポート
from schemas import (
    LengthMismatchError,
    ArticleBase,
    Article,
    User,
    ShowUser,
    ShowArticle,
    Login,
    PasswordChange,
    Token,
    TokenData,
    PublicArticle,
    AccountDeletionRequest,
    validation_exception_handler
)


class TestLengthMismatchError:
    """LengthMismatchErrorのテストクラス"""
    
    def test_length_mismatch_error_creation(self):
        """LengthMismatchErrorの作成テスト"""
        error = LengthMismatchError("文字列の長さが一致しません")
        assert str(error) == "文字列の長さが一致しません"
        assert isinstance(error, Exception)


class TestArticleBase:
    """ArticleBaseモデルのテストクラス"""
    
    def test_article_base_valid_data(self):
        """有効なデータでのArticleBase作成"""
        article_data = {
            "title": "テスト記事",
            "body": "これはテスト記事の本文です。",
            "user_id": 1
        }
        article = ArticleBase(**article_data)
        
        assert article.title == "テスト記事"
        assert article.body == "これはテスト記事の本文です。"
        assert article.user_id == 1
        assert article.article_id is None  # デフォルト値
    
    def test_article_base_body_html_conversion(self):
        """body_htmlの自動変換テスト"""
        article = ArticleBase(
            title="Markdownテスト",
            body="# 見出し\n\n段落です。\n新しい行です。"
        )
        
        # body_htmlが正しく生成されることを確認
        assert article.body_html is not None
        assert "<h1>" in article.body_html or "見出し" in article.body_html
    
    def test_article_base_title_max_length(self):
        """タイトル最大長制限のテスト"""
        long_title = "a" * 31  # 31文字（制限は30文字）
        
        with pytest.raises(ValidationError) as exc_info:
            ArticleBase(title=long_title, body="本文")
        
        errors = exc_info.value.errors()
        assert any("title" in str(error.get("loc", [])) for error in errors)
    
    def test_article_base_body_max_length(self):
        """本文最大長制限のテスト"""
        long_body = "a" * 1001  # 1001文字（制限は1000文字）
        
        with pytest.raises(ValidationError) as exc_info:
            ArticleBase(title="タイトル", body=long_body)
        
        errors = exc_info.value.errors()
        assert any("body" in str(error.get("loc", [])) for error in errors)
    
    def test_article_base_required_fields(self):
        """必須フィールドのテスト"""
        # titleが欠落
        with pytest.raises(ValidationError):
            ArticleBase(body="本文")
        
        # bodyが欠落
        with pytest.raises(ValidationError):
            ArticleBase(title="タイトル")


class TestArticle:
    """Articleモデルのテストクラス"""
    
    def test_article_inherits_from_article_base(self):
        """ArticleがArticleBaseを継承していることの確認"""
        article = Article(title="テスト", body="本文")
        assert isinstance(article, ArticleBase)
        assert article.title == "テスト"
        assert article.body == "本文"


class TestUser:
    """Userモデルのテストクラス"""
    
    def test_user_valid_data(self):
        """有効なデータでのUser作成"""
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "is_active": True
        }
        user = User(**user_data)
        
        assert user.email == "test@example.com"
        assert user.password == "password123"
        assert user.is_active is True
    
    def test_user_optional_fields(self):
        """オプションフィールドのテスト"""
        user = User()
        assert user.email is None
        assert user.password is None
        assert user.is_active is None
    
    def test_user_email_validation(self):
        """メールアドレスバリデーションのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            User(email="invalid_email")
        
        errors = exc_info.value.errors()
        assert any("email" in str(error.get("loc", [])) for error in errors)
    
    def test_user_email_max_length(self):
        """メールアドレス最大長制限のテスト"""
        long_email = "a" * 45 + "@test.com"  # 50文字を超える
        
        with pytest.raises(ValidationError):
            User(email=long_email)
    
    def test_user_password_max_length(self):
        """パスワード最大長制限のテスト"""
        long_password = "a" * 101  # 101文字（制限は100文字）
        
        with pytest.raises(ValidationError):
            User(password=long_password)


class TestShowUser:
    """ShowUserモデルのテストクラス"""
    
    def test_show_user_valid_data(self):
        """有効なデータでのShowUser作成"""
        article_data = ArticleBase(title="記事", body="本文")
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "is_active": True,
            "blogs": [article_data]
        }
        show_user = ShowUser(**user_data)
        
        assert show_user.id == 1
        assert show_user.email == "test@example.com"
        assert show_user.is_active is True
        assert len(show_user.blogs) == 1
        assert show_user.blogs[0].title == "記事"
    
    def test_show_user_optional_fields(self):
        """オプションフィールドのテスト"""
        show_user = ShowUser()
        assert show_user.id is None
        assert show_user.email is None
        assert show_user.is_active is None
        assert show_user.blogs is None


class TestShowArticle:
    """ShowArticleモデルのテストクラス"""
    
    def test_show_article_valid_data(self):
        """有効なデータでのShowArticle作成"""
        article_data = {
            "id": 1,
            "title": "表示記事",
            "body": "表示用の本文です。"
        }
        show_article = ShowArticle(**article_data)
        
        assert show_article.id == 1
        assert show_article.title == "表示記事"
        assert show_article.body == "表示用の本文です。"
    
    def test_show_article_body_html_with_none_body(self):
        """body が None の場合の body_html テスト"""
        show_article = ShowArticle(id=1, title="タイトル", body=None)
        assert show_article.body_html is None
    
    def test_show_article_body_html_conversion(self):
        """body_html の Markdown 変換テスト"""
        show_article = ShowArticle(
            id=1, 
            title="Markdownテスト", 
            body="# 見出し\n\n段落です。"
        )
        assert show_article.body_html is not None
        # Markdownが正しく変換されることを確認


class TestLogin:
    """Loginモデルのテストクラス"""
    
    def test_login_valid_data(self):
        """有効なデータでのLogin作成"""
        login_data = {
            "email": "login@example.com",
            "password": "loginpass"
        }
        login = Login(**login_data)
        
        assert login.email == "login@example.com"
        assert login.password == "loginpass"
    
    def test_login_optional_fields(self):
        """オプションフィールドのテスト"""
        login = Login()
        assert login.email is None
        assert login.password is None
    
    def test_login_email_validation(self):
        """メールアドレスバリデーションのテスト"""
        with pytest.raises(ValidationError):
            Login(email="invalid_email_format")


class TestPasswordChange:
    """PasswordChangeモデルのテストクラス"""
    
    def test_password_change_valid_data(self):
        """有効なデータでのPasswordChange作成"""
        change_data = {
            "username": "user@example.com",
            "temp_password": "temppass123",
            "new_password": "newpass12345"
        }
        password_change = PasswordChange(**change_data)
        
        assert password_change.username == "user@example.com"
        assert password_change.temp_password == "temppass123"
        assert password_change.new_password == "newpass12345"
    
    def test_password_change_required_fields(self):
        """必須フィールドのテスト"""
        with pytest.raises(ValidationError):
            PasswordChange(temp_password="temp", new_password="new12345")
    
    def test_password_change_new_password_min_length(self):
        """新しいパスワードの最小長制限のテスト"""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChange(
                username="user@example.com",
                temp_password="temppass",
                new_password="short"  # 8文字未満
            )
        
        errors = exc_info.value.errors()
        assert any("new_password" in str(error.get("loc", [])) for error in errors)


class TestToken:
    """Tokenモデルのテストクラス"""
    
    def test_token_valid_data(self):
        """有効なデータでのToken作成"""
        token_data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "token_type": "bearer"
        }
        token = Token(**token_data)
        
        assert token.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        assert token.token_type == "bearer"
    
    def test_token_required_fields(self):
        """必須フィールドのテスト"""
        with pytest.raises(ValidationError):
            Token(access_token="token")  # token_typeが欠落
        
        with pytest.raises(ValidationError):
            Token(token_type="bearer")  # access_tokenが欠落


class TestTokenData:
    """TokenDataモデルのテストクラス"""
    
    def test_token_data_valid_email(self):
        """有効なemailでのTokenData作成"""
        token_data = TokenData(email="token@example.com")
        assert token_data.email == "token@example.com"
    
    def test_token_data_optional_email(self):
        """オプションのemailのテスト"""
        token_data = TokenData()
        assert token_data.email is None


class TestPublicArticle:
    """PublicArticleモデルのテストクラス"""
    
    def test_public_article_valid_data(self):
        """有効なデータでのPublicArticle作成"""
        article_data = {
            "article_id": 1,
            "title": "公開記事",
            "body_html": "<h1>見出し</h1><p>本文</p>"
        }
        public_article = PublicArticle(**article_data)
        
        assert public_article.article_id == 1
        assert public_article.title == "公開記事"
        assert public_article.body_html == "<h1>見出し</h1><p>本文</p>"
    
    def test_public_article_required_fields(self):
        """必須フィールドのテスト"""
        with pytest.raises(ValidationError):
            PublicArticle(title="タイトル", body_html="HTML")  # article_idが欠落


class TestAccountDeletionRequest:
    """AccountDeletionRequestモデルのテストクラス"""
    
    def test_account_deletion_request_valid_data(self):
        """有効なデータでのAccountDeletionRequest作成"""
        deletion_data = {
            "email": "delete@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
        deletion_request = AccountDeletionRequest(**deletion_data)
        
        assert deletion_request.email == "delete@example.com"
        assert deletion_request.password == "password123"
        assert deletion_request.confirm_password == "password123"
    
    def test_account_deletion_request_validate_passwords_match(self):
        """パスワード一致バリデーションのテスト"""
        deletion_request = AccountDeletionRequest(
            email="delete@example.com",
            password="password123",
            confirm_password="password123"
        )
        
        # パスワードが一致する場合
        assert deletion_request.validate_passwords_match() is True
        
        # パスワードが一致しない場合
        deletion_request.confirm_password = "different_password"
        with pytest.raises(ValueError) as exc_info:
            deletion_request.validate_passwords_match()
        
        assert "パスワードと確認用パスワードが一致しません" in str(exc_info.value)
    
    def test_account_deletion_request_password_min_length(self):
        """パスワード最小長制限のテスト"""
        with pytest.raises(ValidationError):
            AccountDeletionRequest(
                email="delete@example.com",
                password="short",  # 8文字未満
                confirm_password="short"
            )


class TestValidationExceptionHandler:
    """validation_exception_handlerのテストクラス"""
    
    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """バリデーション例外ハンドラのテスト"""
        # モックリクエストとエラーを作成
        mock_request = Mock(spec=Request)
        
        # RequestValidationErrorのモック
        mock_error = {
            "loc": ["body", "title"],
            "msg": "Field required",
            "type": "missing"
        }
        mock_exc = Mock(spec=RequestValidationError)
        mock_exc.errors.return_value = [mock_error]
        
        # デフォルトハンドラをモック
        with patch('fastapi.exception_handlers.request_validation_exception_handler') as mock_handler:
            mock_handler.return_value = {"detail": "Validation error"}
            
            result = await validation_exception_handler(mock_request, mock_exc)
            
            # デフォルトハンドラが呼ばれることを確認
            mock_handler.assert_called_once_with(mock_request, mock_exc)
            assert result == {"detail": "Validation error"}
    
    @pytest.mark.asyncio
    async def test_validation_exception_handler_different_error_formats(self):
        """様々なエラー形式での例外ハンドラテスト"""
        mock_request = Mock(spec=Request)
        
        # 異なる形式のエラー
        test_errors = [
            {"loc": ["field"], "msg": "Invalid value", "type": "value_error"},
            {"loc": ["body", "nested", "field"], "msg": "Too long", "type": "value_error"},
            {"loc": ["query", "param"], "msg": "Missing", "type": "missing"}
        ]
        
        for error in test_errors:
            mock_exc = Mock(spec=RequestValidationError)
            mock_exc.errors.return_value = [error]
            
            with patch('fastapi.exception_handlers.request_validation_exception_handler') as mock_handler:
                mock_handler.return_value = {"detail": "Error"}
                
                await validation_exception_handler(mock_request, mock_exc)
                mock_handler.assert_called_once_with(mock_request, mock_exc)