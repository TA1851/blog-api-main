"""custom_tokenモジュールの包括的テストスイート

このテストスイートは以下をカバーします：
- TokenType Enumの検証
- TokenConfigクラスの設定テスト
- create_access_token関数の全機能テスト
- verify_token_with_type関数のテスト
- verify_token関数のテスト
- get_user_by_id関数のテスト
- エラーハンドリングのテスト
- 環境変数設定のテスト
- JWTセキュリティシナリオのテスト
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import os
import json
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# テスト対象のインポート
from custom_token import (
    TokenType,
    TokenConfig,
    create_access_token,
    verify_token_with_type,
    verify_token,
    get_user_by_id,
    JWTPayload,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from models import User, Base
from schemas import TokenData


class TestTokenType:
    """TokenType Enumのテストクラス"""
    
    def test_token_type_values(self):
        """TokenTypeの値が正しく定義されているかテスト"""
        assert TokenType.ACCESS.value == "access"
        assert TokenType.EMAIL_VERIFICATION.value == "email_verification"
        assert TokenType.PASSWORD_RESET.value == "password_reset"
    
    def test_token_type_enum_members(self):
        """TokenTypeのメンバーが期待通りかテスト"""
        expected_types = {"ACCESS", "EMAIL_VERIFICATION", "PASSWORD_RESET"}
        actual_types = {member.name for member in TokenType}
        assert actual_types == expected_types
    
    def test_token_type_comparison(self):
        """TokenTypeの比較テスト"""
        assert TokenType.ACCESS == TokenType.ACCESS
        assert TokenType.ACCESS != TokenType.EMAIL_VERIFICATION
        assert TokenType.EMAIL_VERIFICATION != TokenType.PASSWORD_RESET
    
    def test_token_type_string_representation(self):
        """TokenTypeの文字列表現テスト"""
        assert str(TokenType.ACCESS) == "TokenType.ACCESS"
        assert repr(TokenType.ACCESS) == "<TokenType.ACCESS: 'access'>"


class TestTokenConfig:
    """TokenConfigクラスのテストクラス"""
    
    def test_default_expires_structure(self):
        """DEFAULT_EXPIRESの構造が正しいかテスト"""
        assert isinstance(TokenConfig.DEFAULT_EXPIRES, dict)
        assert len(TokenConfig.DEFAULT_EXPIRES) == 3
    
    def test_access_token_default_expiry(self):
        """アクセストークンのデフォルト有効期限テスト"""
        access_expire = TokenConfig.DEFAULT_EXPIRES[TokenType.ACCESS]
        assert isinstance(access_expire, timedelta)
        assert access_expire == timedelta(hours=1)
        assert access_expire.total_seconds() == 3600
    
    def test_email_verification_token_default_expiry(self):
        """メール確認トークンのデフォルト有効期限テスト"""
        email_expire = TokenConfig.DEFAULT_EXPIRES[TokenType.EMAIL_VERIFICATION]
        assert isinstance(email_expire, timedelta)
        assert email_expire == timedelta(hours=1)
        assert email_expire.total_seconds() == 3600
    
    def test_password_reset_token_default_expiry(self):
        """パスワードリセットトークンのデフォルト有効期限テスト"""
        reset_expire = TokenConfig.DEFAULT_EXPIRES[TokenType.PASSWORD_RESET]
        assert isinstance(reset_expire, timedelta)
        assert reset_expire == timedelta(minutes=30)
        assert reset_expire.total_seconds() == 1800
    
    def test_all_token_types_have_defaults(self):
        """すべてのトークンタイプにデフォルト設定があるかテスト"""
        for token_type in TokenType:
            assert token_type in TokenConfig.DEFAULT_EXPIRES
            assert isinstance(TokenConfig.DEFAULT_EXPIRES[token_type], timedelta)


class TestCreateAccessToken:
    """create_access_token関数のテストクラス"""
    
    @pytest.fixture
    def valid_data(self):
        """有効なテストデータ"""
        return {"sub": "test@example.com", "id": 1, "user_id": 1}
    
    @pytest.fixture
    def mock_env_vars(self):
        """環境変数のモック"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test_secret_key_12345',
            'ALGORITHM': 'HS256',
            'ENVIRONMENT': 'test'
        }):
            yield
    
    def test_create_access_token_basic(self, valid_data, mock_env_vars):
        """基本的なアクセストークン作成テスト"""
        token = create_access_token(valid_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # トークンをデコードして検証
        decoded = jwt.decode(token, "test_secret_key_12345", algorithms=["HS256"])
        assert decoded["sub"] == "test@example.com"
        assert decoded["id"] == 1
        assert decoded["type"] == TokenType.ACCESS.value
        assert "exp" in decoded
        assert "iat" in decoded
    
    def test_create_access_token_with_custom_expiry(self, valid_data, mock_env_vars):
        """カスタム有効期限でのトークン作成テスト"""
        custom_expiry = timedelta(hours=2)
        token = create_access_token(valid_data, expires_delta=custom_expiry)
        
        decoded = jwt.decode(token, "test_secret_key_12345", algorithms=["HS256"])
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(decoded["iat"], tz=timezone.utc)
        
        # 有効期限が約2時間後かチェック（数秒の誤差を許容）
        expected_duration = timedelta(hours=2)
        actual_duration = exp_time - iat_time
        assert abs(actual_duration.total_seconds() - expected_duration.total_seconds()) < 5
    
    def test_create_access_token_with_different_token_types(self, valid_data, mock_env_vars):
        """異なるトークンタイプでの作成テスト"""
        # EMAIL_VERIFICATIONトークン
        email_token = create_access_token(valid_data, token_type=TokenType.EMAIL_VERIFICATION)
        decoded_email = jwt.decode(email_token, "test_secret_key_12345", algorithms=["HS256"])
        assert decoded_email["type"] == TokenType.EMAIL_VERIFICATION.value
        
        # PASSWORD_RESETトークン
        reset_token = create_access_token(valid_data, token_type=TokenType.PASSWORD_RESET)
        decoded_reset = jwt.decode(reset_token, "test_secret_key_12345", algorithms=["HS256"])
        assert decoded_reset["type"] == TokenType.PASSWORD_RESET.value
    
    def test_create_access_token_empty_data_error(self, mock_env_vars):
        """空データでのエラーテスト"""
        with pytest.raises(ValueError, match="データが空です"):
            create_access_token({})
        
        with pytest.raises(ValueError, match="データが空です"):
            create_access_token(None)
    
    def test_create_access_token_invalid_data_type_error(self, mock_env_vars):
        """無効なデータ型でのエラーテスト"""
        with pytest.raises(ValueError, match="データは辞書形式である必要があります"):
            create_access_token("invalid_data")
        
        with pytest.raises(ValueError, match="データは辞書形式である必要があります"):
            create_access_token(123)
        
        with pytest.raises(ValueError, match="データは辞書形式である必要があります"):
            create_access_token([1, 2, 3])
    
    def test_create_access_token_missing_secret_key_error(self, valid_data):
        """SECRET_KEY未設定でのエラーテスト"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="SECRET_KEYが設定されていません"):
                create_access_token(valid_data)
    
    @patch('custom_token.jwt.encode')
    def test_create_access_token_jwt_error(self, mock_encode, valid_data, mock_env_vars):
        """JWT生成エラーのテスト"""
        mock_encode.side_effect = JWTError("JWT encoding failed")
        
        with pytest.raises(RuntimeError, match="トークン生成に失敗しました"):
            create_access_token(valid_data)
    
    @patch('custom_token.jwt.encode')
    def test_create_access_token_unexpected_error(self, mock_encode, valid_data, mock_env_vars):
        """予期しないエラーのテスト"""
        mock_encode.side_effect = Exception("Unexpected error")
        
        with pytest.raises(RuntimeError, match="トークン生成中に予期しないエラーが発生しました"):
            create_access_token(valid_data)
    
    def test_create_access_token_token_structure(self, valid_data, mock_env_vars):
        """生成されたトークンの構造テスト"""
        token = create_access_token(valid_data)
        decoded = jwt.decode(token, "test_secret_key_12345", algorithms=["HS256"])
        
        # 必須フィールドの存在確認
        required_fields = ["sub", "id", "exp", "iat", "type"]
        for field in required_fields:
            assert field in decoded
        
        # データ型の確認
        assert isinstance(decoded["exp"], int)
        assert isinstance(decoded["iat"], int)
        assert isinstance(decoded["type"], str)
    
    def test_create_access_token_development_logging(self, valid_data):
        """開発環境でのログ出力テスト"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test_secret_key_12345',
            'ALGORITHM': 'HS256',
            'ENVIRONMENT': 'development'
        }):
            with patch('custom_token.create_logger') as mock_logger:
                create_access_token(valid_data)
                mock_logger.assert_called_once()
                call_args = mock_logger.call_args[0][0]
                assert "トークン生成成功" in call_args
                assert TokenType.ACCESS.value in call_args


class TestVerifyTokenWithType:
    """verify_token_with_type関数のテストクラス"""
    
    @pytest.fixture
    def valid_token_data(self):
        """有効なトークンデータ"""
        return {"sub": "test@example.com", "id": 1, "type": TokenType.ACCESS.value}
    
    @pytest.fixture
    def mock_env_vars(self):
        """環境変数のモック"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test_secret_key_12345',
            'ALGORITHM': 'HS256'
        }):
            yield
    
    @pytest.fixture
    def credentials_exception(self):
        """認証例外"""
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    def test_verify_token_with_type_success(self, valid_token_data, mock_env_vars, credentials_exception):
        """有効なトークンの検証成功テスト"""
        # トークンを作成
        token = jwt.encode(valid_token_data, "test_secret_key_12345", algorithm="HS256")
        
        # 検証
        payload = verify_token_with_type(token, TokenType.ACCESS, credentials_exception)
        
        assert payload["sub"] == "test@example.com"
        assert payload["id"] == 1
        assert payload["type"] == TokenType.ACCESS.value
    
    def test_verify_token_with_type_wrong_type(self, mock_env_vars, credentials_exception):
        """間違ったトークンタイプでの検証失敗テスト"""
        # EMAIL_VERIFICATIONトークンを作成
        token_data = {"sub": "test@example.com", "id": 1, "type": TokenType.EMAIL_VERIFICATION.value}
        token = jwt.encode(token_data, "test_secret_key_12345", algorithm="HS256")
        
        # ACCESSトークンとして検証（失敗するはず）
        with pytest.raises(HTTPException):
            verify_token_with_type(token, TokenType.ACCESS, credentials_exception)
    
    def test_verify_token_with_type_missing_secret_key(self, valid_token_data, credentials_exception):
        """SECRET_KEY未設定でのエラーテスト"""
        with patch.dict(os.environ, {}, clear=True):
            token = "dummy_token"
            
            with pytest.raises(ValueError, match="SECRET_KEYが設定されていません"):
                verify_token_with_type(token, TokenType.ACCESS, credentials_exception)
    
    def test_verify_token_with_type_invalid_token(self, mock_env_vars, credentials_exception):
        """無効なトークンでの検証失敗テスト"""
        invalid_token = "invalid.token.string"
        
        with pytest.raises(HTTPException):
            verify_token_with_type(invalid_token, TokenType.ACCESS, credentials_exception)
    
    def test_verify_token_with_type_expired_token(self, mock_env_vars, credentials_exception):
        """期限切れトークンでの検証失敗テスト"""
        # 期限切れトークンを作成
        expired_data = {
            "sub": "test@example.com",
            "id": 1,
            "type": TokenType.ACCESS.value,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)  # 1時間前に期限切れ
        }
        token = jwt.encode(expired_data, "test_secret_key_12345", algorithm="HS256")
        
        with pytest.raises(HTTPException):
            verify_token_with_type(token, TokenType.ACCESS, credentials_exception)
    
    def test_verify_token_with_type_missing_type_field(self, mock_env_vars, credentials_exception):
        """typeフィールドが欠けているトークンのテスト"""
        token_data = {"sub": "test@example.com", "id": 1}  # typeフィールドなし
        token = jwt.encode(token_data, "test_secret_key_12345", algorithm="HS256")
        
        with pytest.raises(HTTPException):
            verify_token_with_type(token, TokenType.ACCESS, credentials_exception)
    
    @patch('custom_token.create_error_logger')
    def test_verify_token_with_type_error_logging(self, mock_error_logger, mock_env_vars, credentials_exception):
        """エラーログ出力のテスト"""
        invalid_token = "invalid.token.string"
        
        with pytest.raises(HTTPException):
            verify_token_with_type(invalid_token, TokenType.ACCESS, credentials_exception)
        
        mock_error_logger.assert_called()
        call_args = mock_error_logger.call_args[0][0]
        assert "トークン検証エラー" in call_args


class TestVerifyToken:
    """verify_token関数のテストクラス"""
    
    @pytest.fixture
    def mock_db_session(self):
        """モックデータベースセッション"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """モックユーザー"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.name = "Test User"
        return user
    
    @pytest.fixture
    def credentials_exception(self):
        """認証例外"""
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    @pytest.fixture
    def mock_env_vars(self):
        """環境変数のモック"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test_secret_key_12345',
            'ALGORITHM': 'HS256'
        }):
            yield
    
    @patch('custom_token.SECRET_KEY', 'test_secret_key_12345')
    @patch('custom_token.ALGORITHM', 'HS256')
    @patch('custom_token.get_user_by_id')
    @patch('schemas.TokenData')
    def test_verify_token_success(self, mock_token_data_class, mock_get_user, mock_db_session, mock_user, credentials_exception):
        """有効なトークンの検証成功テスト"""
        # モックの設定
        mock_get_user.return_value = mock_user
        
        # トークンデータを作成
        token_data = {"sub": "test@example.com", "id": 1}
        token = jwt.encode(token_data, "test_secret_key_12345", algorithm="HS256")
        
        # 検証
        result = verify_token(token, credentials_exception, mock_db_session)
        
        assert result == mock_user
        mock_get_user.assert_called_once_with(1, mock_db_session)
        mock_token_data_class.assert_called_once_with(email="test@example.com")
    
    @patch('custom_token.SECRET_KEY', None)
    def test_verify_token_missing_secret_key(self, mock_db_session, credentials_exception):
        """SECRET_KEY未設定でのエラーテスト"""
        token = "dummy_token"
        
        with pytest.raises(HTTPException):
            verify_token(token, credentials_exception, mock_db_session)
    
    @patch('custom_token.SECRET_KEY', 'test_secret_key_12345')
    @patch('custom_token.ALGORITHM', 'HS256')
    def test_verify_token_missing_email(self, mock_db_session, credentials_exception):
        """emailフィールドが欠けているトークンのテスト"""
        token_data = {"id": 1}  # subフィールドなし
        token = jwt.encode(token_data, "test_secret_key_12345", algorithm="HS256")
        
        with pytest.raises(HTTPException):
            verify_token(token, credentials_exception, mock_db_session)
    
    @patch('custom_token.SECRET_KEY', 'test_secret_key_12345')
    @patch('custom_token.ALGORITHM', 'HS256')
    def test_verify_token_missing_id(self, mock_db_session, credentials_exception):
        """idフィールドが欠けているトークンのテスト"""
        token_data = {"sub": "test@example.com"}  # idフィールドなし
        token = jwt.encode(token_data, "test_secret_key_12345", algorithm="HS256")
        
        with pytest.raises(HTTPException):
            verify_token(token, credentials_exception, mock_db_session)
    
    @patch('custom_token.SECRET_KEY', 'test_secret_key_12345')
    @patch('custom_token.ALGORITHM', 'HS256')
    def test_verify_token_invalid_token(self, mock_db_session, credentials_exception):
        """無効なトークンでの検証失敗テスト"""
        invalid_token = "invalid.token.string"
        
        with pytest.raises(HTTPException):
            verify_token(invalid_token, credentials_exception, mock_db_session)
    
    @patch('custom_token.SECRET_KEY', 'test_secret_key_12345')
    @patch('custom_token.ALGORITHM', 'HS256')
    @patch('custom_token.get_user_by_id')
    @patch('custom_token.create_error_logger')
    def test_verify_token_error_logging(self, mock_error_logger, mock_get_user, mock_db_session, credentials_exception):
        """エラーログ出力のテスト"""
        invalid_token = "invalid.token.string"
        
        with pytest.raises(HTTPException):
            verify_token(invalid_token, credentials_exception, mock_db_session)
        
        mock_error_logger.assert_called()


class TestGetUserById:
    """get_user_by_id関数のテストクラス"""
    
    @pytest.fixture
    def mock_db_session(self):
        """モックデータベースセッション"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """モックユーザー"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.name = "Test User"
        return user
    
    def test_get_user_by_id_success(self, mock_db_session, mock_user):
        """ユーザー取得成功テスト"""
        # モックの設定
        mock_query = Mock()
        mock_filter = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_user
        
        # 実行
        result = get_user_by_id(1, mock_db_session)
        
        # 検証
        assert result == mock_user
        mock_db_session.query.assert_called_once_with(User)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()
    
    def test_get_user_by_id_not_found(self, mock_db_session):
        """ユーザーが見つからない場合のテスト"""
        # モックの設定
        mock_query = Mock()
        mock_filter = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None  # ユーザーが見つからない
        
        # 実行と検証
        with pytest.raises(HTTPException) as exc_info:
            get_user_by_id(999, mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User with id 999 not found" in str(exc_info.value.detail)
    
    def test_get_user_by_id_different_ids(self, mock_db_session, mock_user):
        """異なるIDでのユーザー取得テスト"""
        # モックの設定
        mock_query = Mock()
        mock_filter = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_user
        
        # 異なるIDでテスト
        for user_id in [1, 42, 123]:
            result = get_user_by_id(user_id, mock_db_session)
            assert result == mock_user
    
    def test_get_user_by_id_zero_id(self, mock_db_session):
        """ID=0でのテスト"""
        # モックの設定
        mock_query = Mock()
        mock_filter = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            get_user_by_id(0, mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User with id 0 not found" in str(exc_info.value.detail)
    
    def test_get_user_by_id_negative_id(self, mock_db_session):
        """負のIDでのテスト"""
        # モックの設定
        mock_query = Mock()
        mock_filter = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            get_user_by_id(-1, mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User with id -1 not found" in str(exc_info.value.detail)


class TestIntegrationScenarios:
    """統合テストシナリオ"""
    
    @pytest.fixture
    def mock_env_vars(self):
        """環境変数のモック"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test_secret_key_12345',
            'ALGORITHM': 'HS256',
            'ENVIRONMENT': 'test'
        }):
            yield
    
    @pytest.fixture
    def credentials_exception(self):
        """認証例外"""
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    def test_full_token_lifecycle(self, mock_env_vars, credentials_exception):
        """トークンの完全なライフサイクルテスト"""
        # 1. トークン作成
        user_data = {"sub": "test@example.com", "id": 1}
        token = create_access_token(user_data)
        
        # 2. トークン検証
        payload = verify_token_with_type(token, TokenType.ACCESS, credentials_exception)
        
        # 3. 検証結果の確認
        assert payload["sub"] == "test@example.com"
        assert payload["id"] == 1
        assert payload["type"] == TokenType.ACCESS.value
        assert "exp" in payload
        assert "iat" in payload
    
    def test_different_token_types_lifecycle(self, mock_env_vars, credentials_exception):
        """異なるトークンタイプのライフサイクルテスト"""
        user_data = {"sub": "test@example.com", "id": 1}
        
        # 各トークンタイプをテスト
        for token_type in TokenType:
            # トークン作成
            token = create_access_token(user_data, token_type=token_type)
            
            # 正しいタイプで検証（成功）
            payload = verify_token_with_type(token, token_type, credentials_exception)
            assert payload["type"] == token_type.value
            
            # 間違ったタイプで検証（失敗）
            other_types = [t for t in TokenType if t != token_type]
            if other_types:
                with pytest.raises(HTTPException):
                    verify_token_with_type(token, other_types[0], credentials_exception)
    
    def test_token_expiry_scenarios(self, mock_env_vars, credentials_exception):
        """トークン有効期限のシナリオテスト"""
        user_data = {"sub": "test@example.com", "id": 1}
        
        # 長い有効期限でトークン作成（テスト用）
        long_expiry = timedelta(hours=1)
        token = create_access_token(user_data, expires_delta=long_expiry)
        
        # 即座に検証（成功）
        payload = verify_token_with_type(token, TokenType.ACCESS, credentials_exception)
        assert payload["sub"] == "test@example.com"
        
        # 期限切れトークンのテスト（過去の時刻で作成）
        expired_data = {
            "sub": "test@example.com",
            "id": 1,
            "type": TokenType.ACCESS.value,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # 1時間前に期限切れ
            "iat": datetime.now(timezone.utc) - timedelta(hours=2)   # 2時間前に発行
        }
        expired_token = jwt.encode(expired_data, "test_secret_key_12345", algorithm="HS256")
        
        # 期限切れトークンの検証（失敗）
        with pytest.raises(HTTPException):
            verify_token_with_type(expired_token, TokenType.ACCESS, credentials_exception)
    
    def test_security_scenarios(self, mock_env_vars, credentials_exception):
        """セキュリティシナリオのテスト"""
        user_data = {"sub": "test@example.com", "id": 1}
        
        # 正しいキーでトークン作成
        token = create_access_token(user_data)
        
        # 正しいキーで検証（成功）
        payload = verify_token_with_type(token, TokenType.ACCESS, credentials_exception)
        assert payload["sub"] == "test@example.com"
        
        # 間違ったキーで検証を試行（失敗）
        with patch.dict(os.environ, {'SECRET_KEY': 'wrong_key'}):
            with pytest.raises(HTTPException):
                verify_token_with_type(token, TokenType.ACCESS, credentials_exception)


class TestErrorHandling:
    """エラーハンドリングのテストクラス"""
    
    def test_environment_variable_edge_cases(self):
        """環境変数のエッジケースのテスト"""
        # 空文字列の環境変数
        with patch.dict(os.environ, {'SECRET_KEY': ''}):
            with pytest.raises(RuntimeError, match="SECRET_KEYが設定されていません"):
                create_access_token({"test": "data"})
        
        # None値の環境変数
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="SECRET_KEYが設定されていません"):
                create_access_token({"test": "data"})
    
    def test_malformed_token_scenarios(self):
        """不正な形式のトークンのテスト"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
        
        malformed_tokens = [
            "invalid",
            "not.a.jwt",
            "",
            "too.many.parts.here.invalid",
            "header.payload",  # 3つのパートが必要
            "invalid_base64.invalid_base64.invalid_base64"
        ]
        
        with patch.dict(os.environ, {'SECRET_KEY': 'test_key'}):
            for token in malformed_tokens:
                with pytest.raises(HTTPException):
                    verify_token_with_type(token, TokenType.ACCESS, credentials_exception)
    
    @patch('custom_token.create_error_logger')
    def test_comprehensive_error_logging(self, mock_error_logger):
        """包括的なエラーログのテスト"""
        # エラーログが呼ばれることを確認
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Test exception"
        )
        
        with patch.dict(os.environ, {'SECRET_KEY': 'test_key'}):
            with pytest.raises(HTTPException):
                verify_token_with_type("invalid_token", TokenType.ACCESS, credentials_exception)
        
        mock_error_logger.assert_called()
        assert "トークン検証エラー" in str(mock_error_logger.call_args)


class TestConstants:
    """定数のテストクラス"""
    
    def test_algorithm_constant(self):
        """ALGORITHMの定数テスト"""
        assert ALGORITHM is not None
        assert isinstance(ALGORITHM, str)
    
    def test_access_token_expire_minutes_constant(self):
        """ACCESS_TOKEN_EXPIRE_MINUTESの定数テスト"""
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert isinstance(ACCESS_TOKEN_EXPIRE_MINUTES, int)
    
    def test_jwt_payload_type_hint(self):
        """JWTPayload型ヒントのテスト"""
        # 型ヒントが正しく定義されているかの簡単なテスト
        test_payload: JWTPayload = {"sub": "test", "id": 1, "exp": datetime.now()}
        assert isinstance(test_payload, dict)


if __name__ == "__main__":
    # テストの実行
    pytest.main([__file__, "-v", "--tb=short"])
