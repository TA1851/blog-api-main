"""custom_token.pyの単体テスト"""
import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from jose import jwt, JWTError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# テスト対象のインポート
from custom_token import (
    create_access_token,
    verify_token_with_type,
    verify_token,
    get_user_by_id,
    TokenType,
    TokenConfig,
    JWTPayload
)
from models import User


class TestTokenType:
    """TokenType enumのテスト"""

    def test_token_type_values(self):
        """TokenTypeの値が正しいことを確認"""
        assert TokenType.ACCESS.value == "access"
        assert TokenType.EMAIL_VERIFICATION.value == "email_verification"
        assert TokenType.PASSWORD_RESET.value == "password_reset"


class TestTokenConfig:
    """TokenConfigクラスのテスト"""

    def test_default_expires_configuration(self):
        """デフォルトの有効期限設定が正しいことを確認"""
        assert TokenConfig.DEFAULT_EXPIRES[TokenType.ACCESS] == timedelta(hours=1)
        assert TokenConfig.DEFAULT_EXPIRES[TokenType.EMAIL_VERIFICATION] == timedelta(hours=1)
        assert TokenConfig.DEFAULT_EXPIRES[TokenType.PASSWORD_RESET] == timedelta(minutes=30)


class TestCreateAccessToken:
    """create_access_token関数のテスト"""

    @patch.dict(os.environ, {'SECRET_KEY': 'test_secret', 'ALGORITHM': 'HS256'})
    def test_create_access_token_success(self):
        """正常なトークン生成のテスト"""
        data = {"sub": "test@example.com", "id": 1}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # トークンをデコードして内容を確認
        decoded = jwt.decode(token, "test_secret", algorithms=["HS256"])
        assert decoded["sub"] == "test@example.com"
        assert decoded["id"] == 1
        assert decoded["type"] == "access"
        assert "exp" in decoded
        assert "iat" in decoded

    @patch.dict(os.environ, {'SECRET_KEY': 'test_secret', 'ALGORITHM': 'HS256'})
    def test_create_access_token_with_custom_expires(self):
        """カスタム有効期限でのトークン生成テスト"""
        data = {"sub": "test@example.com"}
        custom_expires = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=custom_expires)
        
        decoded = jwt.decode(token, "test_secret", algorithms=["HS256"])
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # 有効期限が約15分後であることを確認（±1分の誤差を許容）
        time_diff = exp_time - now
        assert 14 * 60 <= time_diff.total_seconds() <= 16 * 60

    @patch.dict(os.environ, {'SECRET_KEY': 'test_secret', 'ALGORITHM': 'HS256'})
    def test_create_access_token_different_types(self):
        """異なるトークンタイプでの生成テスト"""
        data = {"sub": "test@example.com"}
        
        # EMAIL_VERIFICATIONトークン
        email_token = create_access_token(data, token_type=TokenType.EMAIL_VERIFICATION)
        decoded_email = jwt.decode(email_token, "test_secret", algorithms=["HS256"])
        assert decoded_email["type"] == "email_verification"
        
        # PASSWORD_RESETトークン
        reset_token = create_access_token(data, token_type=TokenType.PASSWORD_RESET)
        decoded_reset = jwt.decode(reset_token, "test_secret", algorithms=["HS256"])
        assert decoded_reset["type"] == "password_reset"

    def test_create_access_token_empty_data(self):
        """空のデータでの例外テスト"""
        with pytest.raises(ValueError, match="データが空です"):
            create_access_token({})

    def test_create_access_token_invalid_data_type(self):
        """無効なデータ型での例外テスト"""
        with pytest.raises(ValueError, match="データは辞書形式である必要があります"):
            create_access_token("invalid_data")

    @patch.dict(os.environ, {}, clear=True)
    def test_create_access_token_missing_secret_key(self):
        """SECRET_KEYが未設定の場合の例外テスト"""
        data = {"sub": "test@example.com"}
        with pytest.raises(RuntimeError, match="SECRET_KEYが設定されていません"):
            create_access_token(data)

    @patch.dict(os.environ, {'SECRET_KEY': 'test_secret'})
    @patch('custom_token.jwt.encode')
    def test_create_access_token_jwt_error(self, mock_encode):
        """JWT生成エラーのテスト"""
        mock_encode.side_effect = JWTError("JWT encoding failed")
        data = {"sub": "test@example.com"}
        
        with pytest.raises(RuntimeError, match="トークン生成に失敗しました"):
            create_access_token(data)


class TestVerifyTokenWithType:
    """verify_token_with_type関数のテスト"""

    @patch.dict(os.environ, {'SECRET_KEY': 'test_secret', 'ALGORITHM': 'HS256'})
    def test_verify_token_with_type_success(self):
        """正常なトークン検証のテスト"""
        # テスト用トークンを生成
        data = {"sub": "test@example.com", "type": "access"}
        token = jwt.encode(data, "test_secret", algorithm="HS256")
        
        # 検証実行
        exception = HTTPException(status_code=401, detail="Invalid token")
        payload = verify_token_with_type(token, TokenType.ACCESS, exception)
        
        assert payload["sub"] == "test@example.com"
        assert payload["type"] == "access"

    @patch.dict(os.environ, {'SECRET_KEY': 'test_secret', 'ALGORITHM': 'HS256'})
    def test_verify_token_with_type_wrong_type(self):
        """異なるトークンタイプでの例外テスト"""
        # EMAIL_VERIFICATIONトークンを生成
        data = {"sub": "test@example.com", "type": "email_verification"}
        token = jwt.encode(data, "test_secret", algorithm="HS256")
        
        # ACCESSトークンとして検証（失敗するはず）
        exception = HTTPException(status_code=401, detail="Invalid token")
        with pytest.raises(HTTPException):
            verify_token_with_type(token, TokenType.ACCESS, exception)

    @patch.dict(os.environ, {}, clear=True)
    def test_verify_token_with_type_missing_secret_key(self):
        """SECRET_KEYが未設定の場合の例外テスト"""
        token = "dummy_token"
        exception = HTTPException(status_code=401, detail="Invalid token")
        
        with pytest.raises(ValueError, match="SECRET_KEYが設定されていません"):
            verify_token_with_type(token, TokenType.ACCESS, exception)

    @patch.dict(os.environ, {'SECRET_KEY': 'test_secret'})
    def test_verify_token_with_type_invalid_token(self):
        """無効なトークンでの例外テスト"""
        invalid_token = "invalid.jwt.token"
        exception = HTTPException(status_code=401, detail="Invalid token")
        
        with pytest.raises(HTTPException):
            verify_token_with_type(invalid_token, TokenType.ACCESS, exception)


class TestVerifyToken:
    """verify_token関数のテスト"""

    @patch('custom_token.get_user_by_id')
    @patch('custom_token.SECRET_KEY', 'test_secret')
    @patch('custom_token.ALGORITHM', 'HS256')
    def test_verify_token_success(self, mock_get_user):
        """正常なトークン検証のテスト"""
        # モックユーザー設定
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        # テスト用トークンを生成
        data = {"sub": "test@example.com", "id": 1}
        token = jwt.encode(data, "test_secret", algorithm="HS256")
        
        # モックデータベースセッション
        mock_db = Mock(spec=Session)
        
        # 検証実行
        exception = HTTPException(status_code=401, detail="Invalid credentials")
        result = verify_token(token, exception, mock_db)
        
        assert result == mock_user
        mock_get_user.assert_called_once_with(1, mock_db)

    @patch('custom_token.SECRET_KEY', None)
    def test_verify_token_missing_secret_key(self):
        """SECRET_KEYが未設定の場合の例外テスト"""
        token = "dummy_token"
        exception = HTTPException(status_code=401, detail="Invalid credentials")
        mock_db = Mock(spec=Session)
        
        with pytest.raises(HTTPException):
            verify_token(token, exception, mock_db)

    @patch('custom_token.SECRET_KEY', 'test_secret')
    @patch('custom_token.ALGORITHM', 'HS256')
    def test_verify_token_missing_email(self):
        """emailが含まれていないトークンでの例外テスト"""
        # emailが含まれていないトークン
        data = {"id": 1}
        token = jwt.encode(data, "test_secret", algorithm="HS256")
        
        exception = HTTPException(status_code=401, detail="Invalid credentials")
        mock_db = Mock(spec=Session)
        
        with pytest.raises(HTTPException):
            verify_token(token, exception, mock_db)

    @patch('custom_token.SECRET_KEY', 'test_secret')
    @patch('custom_token.ALGORITHM', 'HS256')
    def test_verify_token_missing_id(self):
        """idが含まれていないトークンでの例外テスト"""
        # idが含まれていないトークン
        data = {"sub": "test@example.com"}
        token = jwt.encode(data, "test_secret", algorithm="HS256")
        
        exception = HTTPException(status_code=401, detail="Invalid credentials")
        mock_db = Mock(spec=Session)
        
        with pytest.raises(HTTPException):
            verify_token(token, exception, mock_db)

    @patch('custom_token.SECRET_KEY', 'test_secret')
    def test_verify_token_invalid_jwt(self):
        """無効なJWTでの例外テスト"""
        invalid_token = "invalid.jwt.token"
        exception = HTTPException(status_code=401, detail="Invalid credentials")
        mock_db = Mock(spec=Session)
        
        with pytest.raises(HTTPException):
            verify_token(invalid_token, exception, mock_db)


class TestGetUserById:
    """get_user_by_id関数のテスト"""

    def test_get_user_by_id_success(self):
        """正常なユーザー取得のテスト"""
        # モックユーザー設定
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        # モックデータベースセッション設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_user
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        # 実行
        result = get_user_by_id(1, mock_db)
        
        # 検証
        assert result == mock_user
        mock_db.query.assert_called_once_with(User)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

    def test_get_user_by_id_not_found(self):
        """ユーザーが見つからない場合の例外テスト"""
        # モックデータベースセッション設定（ユーザーなし）
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        # 実行・検証
        with pytest.raises(HTTPException) as exc_info:
            get_user_by_id(999, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User with id 999 not found" in str(exc_info.value.detail)


class TestIntegration:
    """統合テスト"""

    @patch.dict(os.environ, {'SECRET_KEY': 'test_secret', 'ALGORITHM': 'HS256'})
    @patch('custom_token.get_user_by_id')
    def test_token_creation_and_verification_flow(self, mock_get_user):
        """トークン生成から検証までの一連の流れのテスト"""
        # モックユーザー設定
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        # 1. トークン生成
        data = {"sub": "test@example.com", "id": 1}
        token = create_access_token(data)
        
        # 2. トークン検証（verify_token_with_type）
        exception = HTTPException(status_code=401, detail="Invalid token")
        payload = verify_token_with_type(token, TokenType.ACCESS, exception)
        
        assert payload["sub"] == "test@example.com"
        assert payload["id"] == 1
        assert payload["type"] == "access"
        
        # 3. ユーザー検証（verify_token）
        mock_db = Mock(spec=Session)
        with patch('custom_token.SECRET_KEY', 'test_secret'), \
             patch('custom_token.ALGORITHM', 'HS256'):
            user = verify_token(token, exception, mock_db)
            assert user == mock_user