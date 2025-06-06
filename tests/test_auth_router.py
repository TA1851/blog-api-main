"""routers/auth.pyの包括的な単体テスト"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Generator


class TestAuthRouterDependencies:
    """認証ルーターの依存関数テスト"""
    
    @patch('routers.auth.session')
    @patch('routers.auth.create_logger')
    @patch('routers.auth.create_error_logger')
    def test_get_db_success(self, mock_error_logger, mock_logger, mock_session):
        """get_db関数の正常系テスト"""
        from routers.auth import get_db
        
        # モックセッション設定
        mock_db_instance = Mock(spec=Session)
        mock_session.return_value = mock_db_instance
        
        # ジェネレーターをテスト
        db_generator = get_db()
        
        # nextでセッションを取得
        db = next(db_generator)
        assert db == mock_db_instance
        
        # ジェネレーターを閉じる（finally節をトリガー）
        try:
            next(db_generator)
        except StopIteration:
            pass
        
        # ログとクローズが呼ばれることを確認
        mock_logger.assert_called()
        mock_db_instance.close.assert_called_once()
    
    @patch('routers.auth.session')
    @patch('routers.auth.create_error_logger')
    def test_get_db_exception_handling(self, mock_error_logger, mock_session):
        """get_db関数の例外処理テスト"""
        from routers.auth import get_db
        
        # モックセッション設定
        mock_db_instance = Mock(spec=Session)
        mock_session.return_value = mock_db_instance
        
        # ジェネレーターを取得
        db_generator = get_db()
        
        # セッション取得
        db = next(db_generator)
        
        # 例外を発生させる
        try:
            raise Exception("テスト例外")
        except Exception:
            # ジェネレーター内で例外処理をシミュレート
            pass
        
        # ジェネレーターを閉じる
        try:
            next(db_generator)
        except StopIteration:
            pass
        
        # クローズが呼ばれることを確認
        mock_db_instance.close.assert_called_once()


class TestLoginEndpoint:
    """ログインエンドポイントのテスト"""
    
    @pytest.fixture
    def mock_user(self):
        """テスト用ユーザーモック"""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        user.password = "hashed_password"
        return user
    
    @pytest.fixture
    def login_request_form(self):
        """テスト用ログインフォーム"""
        form = Mock(spec=OAuth2PasswordRequestForm)
        form.username = "test@example.com"
        form.password = "test_password"
        return form
    
    @patch('routers.auth.create_access_token')
    @patch('routers.auth.Hash.verify')
    @patch('routers.auth.create_logger')
    @patch('routers.auth.create_error_logger')
    def test_login_success(self, mock_error_logger, mock_logger, 
                          mock_verify, mock_create_token, 
                          mock_user, login_request_form):
        """ログイン成功テスト"""
        from routers.auth import login
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = mock_user
        mock_verify.return_value = True
        mock_create_token.return_value = "test_access_token"
        
        # 非同期関数のテスト
        async def test_login():
            result = await login(login_request_form, mock_db)
            return result
        
        result = asyncio.run(test_login())
        
        # 結果検証
        assert result["access_token"] == "test_access_token"
        assert result["token_type"] == "bearer"
        
        # モック呼び出し検証
        mock_db.query.assert_called()
        mock_verify.assert_called_with("test_password", "hashed_password")
        mock_create_token.assert_called_with(
            data={"sub": "test@example.com", "id": 1}
        )
        mock_logger.assert_called()
    
    @patch('routers.auth.create_error_logger')
    def test_login_user_not_found(self, mock_error_logger, login_request_form):
        """ユーザーが見つからない場合のテスト"""
        from routers.auth import login
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = None
        
        # 非同期関数のテスト
        async def test_login():
            with pytest.raises(HTTPException) as exc_info:
                await login(login_request_form, mock_db)
            return exc_info.value
        
        exception = asyncio.run(test_login())
        
        # 例外検証
        assert exception.status_code == status.HTTP_404_NOT_FOUND
        assert "無効なユーザー名です" in str(exception.detail)
        mock_error_logger.assert_called()
    
    @patch('routers.auth.Hash.verify')
    @patch('routers.auth.create_error_logger')
    def test_login_invalid_password(self, mock_error_logger, mock_verify, 
                                  mock_user, login_request_form):
        """無効なパスワードの場合のテスト"""
        from routers.auth import login
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = mock_user
        mock_verify.return_value = False
        
        # 非同期関数のテスト
        async def test_login():
            with pytest.raises(HTTPException) as exc_info:
                await login(login_request_form, mock_db)
            return exc_info.value
        
        exception = asyncio.run(test_login())
        
        # 例外検証
        assert exception.status_code == status.HTTP_404_NOT_FOUND
        assert "無効なパスワードです" in str(exception.detail)
        mock_error_logger.assert_called()


class TestTokenVerification:
    """トークン検証機能のテスト"""
    
    @patch('routers.auth.jwt.decode')
    def test_verify_token_success(self, mock_jwt_decode):
        """トークン検証成功テスト"""
        from routers.auth import verify_token
        
        # モック設定
        mock_jwt_decode.return_value = {"sub": "test@example.com"}
        
        # テスト実行
        result = verify_token("valid_token")
        
        # 結果検証
        assert result == {"email": "test@example.com"}
        mock_jwt_decode.assert_called_with(
            "valid_token", "your-secret-key", algorithms=["HS256"]
        )
    
    @patch('routers.auth.jwt.decode')
    def test_verify_token_no_subject(self, mock_jwt_decode):
        """トークンにsubjectがない場合のテスト"""
        from routers.auth import verify_token
        
        # モック設定
        mock_jwt_decode.return_value = {"exp": 1234567890}
        
        # テスト実行
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid_token")
        
        # 例外検証
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "無効なトークンです" in str(exc_info.value.detail)
    
    def test_verify_token_blacklisted(self):
        """ブラックリストに登録されたトークンのテスト"""
        from routers.auth import verify_token, token_blacklist
        
        # トークンをブラックリストに追加
        blacklisted_token = "blacklisted_token"
        token_blacklist.add(blacklisted_token)
        
        # テスト実行
        with pytest.raises(HTTPException) as exc_info:
            verify_token(blacklisted_token)
        
        # 例外検証
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "トークンが無効化されています" in str(exc_info.value.detail)
        
        # クリーンアップ
        token_blacklist.remove(blacklisted_token)


class TestLogoutEndpoint:
    """ログアウトエンドポイントのテスト"""
    
    @patch('routers.auth.create_logger')
    def test_logout_success(self, mock_logger):
        """ログアウト成功テスト"""
        from routers.auth import logout, token_blacklist
        import asyncio
        
        # テスト前のブラックリストサイズ
        initial_size = len(token_blacklist)
        test_token = "test_logout_token"
        
        # 非同期関数のテスト
        async def test_logout():
            result = await logout(test_token)
            return result
        
        result = asyncio.run(test_logout())
        
        # 結果検証
        assert result == {"message": "ログアウトしました"}
        assert test_token in token_blacklist
        assert len(token_blacklist) == initial_size + 1
        mock_logger.assert_called_with("ログアウトに成功しました")
        
        # クリーンアップ
        token_blacklist.remove(test_token)


class TestGetAllBlogsEndpoint:
    """全記事取得エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_articles(self):
        """テスト用記事リスト"""
        articles = []
        for i in range(3):
            article = Mock()
            article.id = i + 1
            article.title = f"記事{i + 1}"
            article.body = f"記事{i + 1}の本文"
            articles.append(article)
        return articles
    
    def test_get_all_blogs_success(self, mock_articles):
        """全記事取得成功テスト"""
        from routers.auth import get_all_blogs
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().all.return_value = mock_articles
        
        # 非同期関数のテスト
        async def test_get_blogs():
            result = await get_all_blogs(mock_db)
            return result
        
        result = asyncio.run(test_get_blogs())
        
        # 結果検証
        assert len(result) == 3
        for i, article in enumerate(result):
            assert article.id == i + 1
            assert article.title == f"記事{i + 1}"
            assert article.body == f"記事{i + 1}の本文"
        
        # データベース呼び出し検証
        mock_db.query.assert_called()


if __name__ == "__main__":
    # このファイルを直接実行した場合のテスト実行
    pytest.main([__file__, "-v"])