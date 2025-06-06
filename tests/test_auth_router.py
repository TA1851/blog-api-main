"""routers/auth.pyの包括的な単体テスト"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Generator


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
    def test_login_success(self, mock_verify, mock_create_token, 
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
    
    def test_login_user_not_found(self, login_request_form):
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
    
    @patch('routers.auth.Hash.verify')
    def test_login_invalid_password(self, mock_verify, 
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
            "valid_token", "SECRET_KEY", algorithms=["HS256"]
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
    
    @patch('routers.auth.jwt.decode')
    def test_verify_token_jwt_error(self, mock_jwt_decode):
        """JWT例外が発生した場合のテスト"""
        from routers.auth import verify_token
        from jose import JWTError
        
        # モック設定でJWTErrorを発生させる
        mock_jwt_decode.side_effect = JWTError("Invalid token")
        
        # テスト実行
        with pytest.raises(HTTPException) as exc_info:
            verify_token("malformed_token")
        
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
    
    def test_logout_success(self):
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


class TestChangePasswordEndpoint:
    """パスワード変更エンドポイントのテスト"""
    
    @pytest.fixture
    def password_change_request(self):
        """テスト用パスワード変更リクエスト"""
        request = Mock()
        request.username = "test@example.com"
        request.temp_password = "temp_password"
        request.new_password = "new_password"
        return request
    
    @pytest.fixture
    def mock_user(self):
        """テスト用ユーザーモック"""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        user.name = "Test User"
        user.password = "hashed_temp_password"
        return user
    
    @patch('routers.auth.send_registration_complete_email')
    @patch('routers.auth.create_access_token')
    @patch('routers.auth.Hash.bcrypt')
    @patch('routers.auth.Hash.verify')
    def test_change_password_success(self, mock_verify, mock_bcrypt, 
                                   mock_create_token, mock_send_email,
                                   password_change_request, mock_user):
        """パスワード変更成功テスト"""
        from routers.auth import change_password
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = mock_user
        mock_verify.return_value = True
        mock_bcrypt.return_value = "hashed_new_password"
        mock_create_token.return_value = "new_access_token"
        mock_send_email.return_value = None
        
        # 非同期関数のテスト
        async def test_change_password():
            result = await change_password(password_change_request, mock_db)
            return result
        
        result = asyncio.run(test_change_password())
        
        # 結果検証
        assert result["message"] == "パスワードが正常に変更されました。"
        assert result["user_id"] == "1"
        assert result["access_token"] == "new_access_token"
        assert result["token_type"] == "bearer"
        assert result["email_sent"] is True
        assert "email_error" not in result
        
        # モック呼び出し検証
        mock_db.query.assert_called()
        mock_verify.assert_called_with("temp_password", "hashed_temp_password")
        mock_bcrypt.assert_called_with("new_password")
        mock_db.commit.assert_called_once()
        mock_send_email.assert_called_once_with("test@example.com", "Test User")
    
    def test_change_password_user_not_found(self, password_change_request):
        """ユーザーが見つからない場合のテスト"""
        from routers.auth import change_password
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = None
        
        # 非同期関数のテスト
        async def test_change_password():
            with pytest.raises(HTTPException) as exc_info:
                await change_password(password_change_request, mock_db)
            return exc_info.value
        
        exception = asyncio.run(test_change_password())
        
        # 例外検証
        assert exception.status_code == status.HTTP_404_NOT_FOUND
        assert "無効なユーザー名です" in str(exception.detail)
    
    @patch('routers.auth.Hash.verify')
    def test_change_password_invalid_temp_password(self, mock_verify, 
                                                 password_change_request, mock_user):
        """無効な仮パスワードの場合のテスト"""
        from routers.auth import change_password
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = mock_user
        mock_verify.return_value = False
        
        # 非同期関数のテスト
        async def test_change_password():
            with pytest.raises(HTTPException) as exc_info:
                await change_password(password_change_request, mock_db)
            return exc_info.value
        
        exception = asyncio.run(test_change_password())
        
        # 例外検証
        assert exception.status_code == status.HTTP_400_BAD_REQUEST
        assert "無効な仮パスワードです" in str(exception.detail)

    @patch('routers.auth.send_registration_complete_email')
    @patch('routers.auth.create_access_token')
    @patch('routers.auth.Hash.bcrypt')
    @patch('routers.auth.Hash.verify')
    def test_change_password_email_connection_error(self, mock_verify, mock_bcrypt, 
                                                   mock_create_token, mock_send_email,
                                                   password_change_request, mock_user):
        """メール送信コネクションエラーのテスト"""
        from routers.auth import change_password
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = mock_user
        mock_verify.return_value = True
        mock_bcrypt.return_value = "hashed_new_password"
        mock_create_token.return_value = "new_access_token"
        mock_send_email.side_effect = ConnectionError("Connection failed")
        
        # 非同期関数のテスト
        async def test_change_password():
            result = await change_password(password_change_request, mock_db)
            return result
        
        result = asyncio.run(test_change_password())
        
        # 結果検証
        assert result["message"] == "パスワードが正常に変更されました。"
        assert result["user_id"] == "1"
        assert result["access_token"] == "new_access_token"
        assert result["token_type"] == "bearer"
        assert result["email_sent"] is False
        assert result["email_error"] == "メールサーバーに接続できませんでした"
        
        # データベースコミット確認
        mock_db.commit.assert_called_once()
    
    @patch('routers.auth.send_registration_complete_email')
    @patch('routers.auth.create_access_token')
    @patch('routers.auth.Hash.bcrypt')
    @patch('routers.auth.Hash.verify')
    def test_change_password_email_timeout_error(self, mock_verify, mock_bcrypt, 
                                                mock_create_token, mock_send_email,
                                                password_change_request, mock_user):
        """メール送信タイムアウトエラーのテスト"""
        from routers.auth import change_password
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = mock_user
        mock_verify.return_value = True
        mock_bcrypt.return_value = "hashed_new_password"
        mock_create_token.return_value = "new_access_token"
        mock_send_email.side_effect = TimeoutError("Timeout occurred")
        
        # 非同期関数のテスト
        async def test_change_password():
            result = await change_password(password_change_request, mock_db)
            return result
        
        result = asyncio.run(test_change_password())
        
        # 結果検証
        assert result["message"] == "パスワードが正常に変更されました。"
        assert result["email_sent"] is False
        assert result["email_error"] == "メール送信がタイムアウトしました"
    
    @patch('routers.auth.send_registration_complete_email')
    @patch('routers.auth.create_access_token')
    @patch('routers.auth.Hash.bcrypt')
    @patch('routers.auth.Hash.verify')
    def test_change_password_email_value_error(self, mock_verify, mock_bcrypt, 
                                             mock_create_token, mock_send_email,
                                             password_change_request, mock_user):
        """メール送信バリューエラーのテスト"""
        from routers.auth import change_password
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = mock_user
        mock_verify.return_value = True
        mock_bcrypt.return_value = "hashed_new_password"
        mock_create_token.return_value = "new_access_token"
        mock_send_email.side_effect = ValueError("Invalid email format")
        
        # 非同期関数のテスト
        async def test_change_password():
            result = await change_password(password_change_request, mock_db)
            return result
        
        result = asyncio.run(test_change_password())
        
        # 結果検証
        assert result["email_sent"] is False
        assert result["email_error"] == "無効なメールアドレスです"
    
    @patch('routers.auth.send_registration_complete_email')
    @patch('routers.auth.create_access_token')
    @patch('routers.auth.Hash.bcrypt')
    @patch('routers.auth.Hash.verify')
    def test_change_password_email_general_error(self, mock_verify, mock_bcrypt, 
                                                mock_create_token, mock_send_email,
                                                password_change_request, mock_user):
        """メール送信一般エラーのテスト"""
        from routers.auth import change_password
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = mock_user
        mock_verify.return_value = True
        mock_bcrypt.return_value = "hashed_new_password"
        mock_create_token.return_value = "new_access_token"
        mock_send_email.side_effect = Exception("Unexpected error")
        
        # 非同期関数のテスト
        async def test_change_password():
            result = await change_password(password_change_request, mock_db)
            return result
        
        result = asyncio.run(test_change_password())
        
        # 結果検証
        assert result["email_sent"] is False
        assert result["email_error"] == "メール送信中に予期しないエラーが発生しました"
    
    @pytest.fixture
    def mock_user_no_email(self):
        """メールアドレスなしのテスト用ユーザーモック"""
        user = Mock()
        user.id = 1
        user.email = None
        user.name = "Test User"
        user.password = "hashed_temp_password"
        return user
    
    @patch('routers.auth.create_access_token')
    @patch('routers.auth.Hash.bcrypt')
    @patch('routers.auth.Hash.verify')
    def test_change_password_no_email(self, mock_verify, mock_bcrypt, 
                                    mock_create_token, password_change_request, 
                                    mock_user_no_email):
        """ユーザーにメールアドレスがない場合のテスト"""
        from routers.auth import change_password
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = mock_user_no_email
        mock_verify.return_value = True
        mock_bcrypt.return_value = "hashed_new_password"
        mock_create_token.return_value = "new_access_token"
        
        # 非同期関数のテスト
        async def test_change_password():
            result = await change_password(password_change_request, mock_db)
            return result
        
        result = asyncio.run(test_change_password())
        
        # 結果検証
        assert result["message"] == "パスワードが正常に変更されました。"
        assert result["email_sent"] is False
        assert result["email_error"] == "ユーザーにメールアドレスが設定されていません"
    
    @patch('routers.auth.Hash.bcrypt')
    @patch('routers.auth.Hash.verify')
    def test_change_password_database_constraint_error(self, mock_verify, mock_bcrypt, 
                                                      password_change_request, mock_user):
        """データベース制約違反エラーのテスト"""
        from routers.auth import change_password
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = mock_user
        mock_verify.return_value = True
        mock_bcrypt.return_value = "hashed_new_password"
        mock_db.commit.side_effect = Exception("constraint violation")
        
        # 非同期関数のテスト
        async def test_change_password():
            with pytest.raises(HTTPException) as exc_info:
                await change_password(password_change_request, mock_db)
            return exc_info.value
        
        exception = asyncio.run(test_change_password())
        
        # 例外検証
        assert exception.status_code == status.HTTP_409_CONFLICT
        assert "データベース制約違反が発生しました" in str(exception.detail)
        mock_db.rollback.assert_called_once()
    
    @patch('routers.auth.Hash.bcrypt')
    @patch('routers.auth.Hash.verify')
    def test_change_password_database_connection_error(self, mock_verify, mock_bcrypt, 
                                                      password_change_request, mock_user):
        """データベース接続エラーのテスト"""
        from routers.auth import change_password
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = mock_user
        mock_verify.return_value = True
        mock_bcrypt.return_value = "hashed_new_password"
        mock_db.commit.side_effect = Exception("connection timeout")
        
        # 非同期関数のテスト
        async def test_change_password():
            with pytest.raises(HTTPException) as exc_info:
                await change_password(password_change_request, mock_db)
            return exc_info.value
        
        exception = asyncio.run(test_change_password())
        
        # 例外検証
        assert exception.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "データベース接続エラーが発生しました" in str(exception.detail)
        mock_db.rollback.assert_called_once()
    
    @patch('routers.auth.Hash.bcrypt')
    @patch('routers.auth.Hash.verify')
    def test_change_password_database_general_error(self, mock_verify, mock_bcrypt, 
                                                   password_change_request, mock_user):
        """データベース一般エラーのテスト"""
        from routers.auth import change_password
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = mock_user
        mock_verify.return_value = True
        mock_bcrypt.return_value = "hashed_new_password"
        mock_db.commit.side_effect = Exception("unexpected database error")
        
        # 非同期関数のテスト
        async def test_change_password():
            with pytest.raises(HTTPException) as exc_info:
                await change_password(password_change_request, mock_db)
            return exc_info.value
        
        exception = asyncio.run(test_change_password())
        
        # 例外検証
        assert exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "パスワード変更中にエラーが発生しました" in str(exception.detail)
        mock_db.rollback.assert_called_once()


if __name__ == "__main__":
    # このファイルを直接実行した場合のテスト実行
    pytest.main([__file__, "-v"])