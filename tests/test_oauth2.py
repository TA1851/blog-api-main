"""OAuth2モジュールのテストスイート

このテストスイートは以下をカバーします：
- JWTトークンの検証機能
- get_current_user関数のテスト
- 認証エラーハンドリング
- データベース統合テスト
- トークンの各種エラーケース
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os

# テスト対象のインポート
from oauth2 import get_current_user, oauth2_scheme, ALGORITHM
from models import User, Base
from schemas import TokenData
from custom_token import SECRET_KEY, create_access_token, TokenType


class TestOAuth2Scheme:
    """OAuth2PasswordBearerスキームのテスト"""
    
    def test_oauth2_scheme_creation(self):
        """OAuth2スキームの作成テスト"""
        assert oauth2_scheme is not None
        assert isinstance(oauth2_scheme, OAuth2PasswordBearer)
        # OAuth2PasswordBearerの実際の属性名を確認
        assert oauth2_scheme.model.flows.password.tokenUrl == "api/v1/login"
    
    def test_oauth2_scheme_attributes(self):
        """OAuth2スキームの属性テスト"""
        assert hasattr(oauth2_scheme, 'model')
        assert hasattr(oauth2_scheme.model.flows.password, 'tokenUrl')
        assert hasattr(oauth2_scheme, 'scheme_name')
        assert oauth2_scheme.scheme_name == "OAuth2PasswordBearer"


class TestGetCurrentUser:
    """get_current_user関数のテストクラス"""
    
    @pytest.fixture
    def mock_db_session(self):
        """モックデータベースセッションを作成"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestingSessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def sample_user(self, mock_db_session):
        """テスト用のサンプルユーザーを作成"""
        user = User(
            id=1,
            name="test_user",
            email="test@example.com",
            password="hashed_password",
            is_active=True
        )
        mock_db_session.add(user)
        mock_db_session.commit()
        mock_db_session.refresh(user)
        return user
    
    @pytest.fixture
    def valid_token(self, sample_user):
        """有効なJWTトークンを作成"""
        token_data = {
            "sub": sample_user.email,
            "id": sample_user.id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    @pytest.fixture
    def expired_token(self, sample_user):
        """期限切れのJWTトークンを作成"""
        token_data = {
            "sub": sample_user.email,
            "id": sample_user.id,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    @pytest.fixture
    def invalid_signature_token(self, sample_user):
        """不正な署名のJWTトークンを作成"""
        token_data = {
            "sub": sample_user.email,
            "id": sample_user.id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        return jwt.encode(token_data, "wrong_secret", algorithm=ALGORITHM)
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_db_session, sample_user, valid_token):
        """有効なトークンで現在ユーザーを取得するテスト"""
        result = await get_current_user(token=valid_token, db=mock_db_session)
        
        assert result is not None
        assert isinstance(result, User)
        assert result.id == sample_user.id
        assert result.email == sample_user.email
        assert result.is_active == sample_user.is_active
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token_format(self, mock_db_session):
        """不正な形式のトークンでエラーが発生するテスト"""
        invalid_token = "invalid.token.format"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=invalid_token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "認証情報が無効です"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, mock_db_session, expired_token):
        """期限切れトークンでエラーが発生するテスト"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=expired_token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "認証情報が無効です"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_signature(self, mock_db_session, invalid_signature_token):
        """不正な署名のトークンでエラーが発生するテスト"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=invalid_signature_token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "認証情報が無効です"
    
    @pytest.mark.asyncio
    async def test_get_current_user_missing_sub_claim(self, mock_db_session):
        """subクレームが欠けているトークンのテスト"""
        token_data = {
            "id": 1,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "認証情報が無効です"
    
    @pytest.mark.asyncio
    async def test_get_current_user_missing_id_claim(self, mock_db_session):
        """idクレームが欠けているトークンのテスト"""
        token_data = {
            "sub": "test@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "認証情報が無効です"
    
    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, mock_db_session):
        """存在しないユーザーIDのトークンのテスト"""
        token_data = {
            "sub": "nonexistent@example.com",
            "id": 999,  # 存在しないユーザーID
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "認証情報が無効です"
    
    @patch('oauth2.SECRET_KEY', None)
    @pytest.mark.asyncio
    async def test_get_current_user_no_secret_key(self, mock_db_session):
        """SECRET_KEYが設定されていない場合のテスト"""
        token_data = {
            "sub": "test@example.com",
            "id": 1,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(token_data, "any_secret", algorithm=ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "認証情報が無効です"
    
    @pytest.mark.asyncio
    async def test_get_current_user_jwt_error_handling(self, mock_db_session):
        """JWTエラーの適切な処理テスト"""
        # 完全に不正なトークン
        malformed_token = "not.a.jwt"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=malformed_token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "認証情報が無効です"
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_inactive_user(self, mock_db_session):
        """非アクティブユーザーでも認証が通ることを確認（仕様による）"""
        # 非アクティブユーザーを作成
        inactive_user = User(
            id=2,
            name="inactive_user",
            email="inactive@example.com",
            password="hashed_password",
            is_active=False
        )
        mock_db_session.add(inactive_user)
        mock_db_session.commit()
        mock_db_session.refresh(inactive_user)
        
        token_data = {
            "sub": inactive_user.email,
            "id": inactive_user.id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        # 現在の実装では非アクティブユーザーもトークンが有効なら認証される
        result = await get_current_user(token=token, db=mock_db_session)
        assert result.id == inactive_user.id
        assert result.is_active == False


class TestTokenDataIntegration:
    """TokenDataスキーマとの統合テスト"""
    
    def test_token_data_creation_from_payload(self):
        """ペイロードからTokenDataの作成テスト"""
        email = "test@example.com"
        token_data = TokenData(email=email)
        
        assert token_data.email == email
        assert isinstance(token_data, TokenData)
    
    def test_token_data_optional_email(self):
        """TokenDataのオプショナルなemailフィールドのテスト"""
        token_data = TokenData()
        assert token_data.email is None
        
        token_data = TokenData(email=None)
        assert token_data.email is None


class TestAlgorithmConfiguration:
    """アルゴリズム設定のテスト"""
    
    def test_algorithm_default_value(self):
        """デフォルトアルゴリズムの確認"""
        assert ALGORITHM is not None
        assert isinstance(ALGORITHM, str)
        # 環境変数またはデフォルト値"HS256"が設定されていることを確認
        assert ALGORITHM in ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
    
    def test_algorithm_from_environment(self):
        """環境変数からのアルゴリズム設定テスト"""
        # 実際の環境では起動時に設定されるため、現在の値を確認
        from database import db_env
        algo = db_env.get("algo") or "HS256"
        # 設定可能なアルゴリズムのいずれかであることを確認
        assert algo in ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]


class TestDependencyInjection:
    """依存性注入のテスト"""
    
    def test_oauth2_scheme_dependency(self):
        """OAuth2スキームの依存性注入テスト"""
        # get_current_user関数のシグネチャを確認
        import inspect
        sig = inspect.signature(get_current_user)
        
        assert 'token' in sig.parameters
        assert 'db' in sig.parameters
        
        token_param = sig.parameters['token']
        db_param = sig.parameters['db']
        
        # 依存性注入が正しく設定されていることを確認
        assert token_param.default != inspect.Parameter.empty
        assert db_param.default != inspect.Parameter.empty


class TestSecurityHeaders:
    """セキュリティヘッダーのテスト"""
    
    @pytest.mark.asyncio
    async def test_credentials_exception_headers(self):
        """認証例外のヘッダー設定テスト"""
        # get_current_user内で使用される認証例外を検証
        invalid_token = "invalid_token"
        mock_db = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=invalid_token, db=mock_db)
        
        assert "WWW-Authenticate" in exc_info.value.headers
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"


class TestDatabaseIntegration:
    """データベース統合テスト"""
    
    @pytest.fixture
    def real_db_session(self):
        """実際のデータベースセッションテスト"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestingSessionLocal()
        yield session
        session.close()
    
    @pytest.mark.asyncio
    async def test_user_query_performance(self, real_db_session):
        """ユーザークエリのパフォーマンステスト"""
        # 複数のユーザーを作成
        users = []
        for i in range(10):
            user = User(
                id=i + 1,
                name=f"user_{i}",
                email=f"user{i}@example.com",
                password="hashed_password",
                is_active=True
            )
            users.append(user)
            real_db_session.add(user)
        
        real_db_session.commit()
        
        # 最後のユーザーのトークンでテスト
        last_user = users[-1]
        token_data = {
            "sub": last_user.email,
            "id": last_user.id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        # パフォーマンス測定
        import time
        start_time = time.time()
        result = await get_current_user(token=token, db=real_db_session)
        end_time = time.time()
        
        assert result.id == last_user.id
        assert (end_time - start_time) < 0.1  # 100ms以内で完了することを確認
    
    @pytest.mark.asyncio
    async def test_database_transaction_handling(self, real_db_session):
        """データベーストランザクション処理のテスト"""
        user = User(
            id=1,
            name="test_user",
            email="test@example.com",
            password="hashed_password",
            is_active=True
        )
        real_db_session.add(user)
        real_db_session.commit()
        
        token_data = {
            "sub": user.email,
            "id": user.id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        # 複数回の認証が正常に動作することを確認
        for _ in range(3):
            result = await get_current_user(token=token, db=real_db_session)
            assert result.id == user.id


class TestErrorLogging:
    """エラーログのテスト"""
    
    @patch('oauth2.print')
    @pytest.mark.asyncio
    async def test_jwt_error_logging(self, mock_print, mock_db_session=None):
        """JWTエラーのログ出力テスト"""
        if mock_db_session is None:
            mock_db_session = Mock()
        
        invalid_token = "invalid.jwt.token"
        
        with pytest.raises(HTTPException):
            await get_current_user(token=invalid_token, db=mock_db_session)
        
        # print関数が呼ばれることを確認（JWTErrorのログ出力）
        mock_print.assert_called()
        call_args = mock_print.call_args[0][0]
        assert "JWTErrorが発生しました" in call_args


class TestEdgeCases:
    """エッジケースのテスト"""
    
    @pytest.mark.asyncio
    async def test_empty_token(self, mock_db_session=None):
        """空文字トークンのテスト"""
        if mock_db_session is None:
            mock_db_session = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="", db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_none_token(self, mock_db_session=None):
        """Noneトークンのテスト"""
        if mock_db_session is None:
            mock_db_session = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=None, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_malformed_base64_token(self, mock_db_session=None):
        """不正なBase64エンコードトークンのテスト"""
        if mock_db_session is None:
            mock_db_session = Mock()
        
        malformed_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid_payload.signature"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=malformed_token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_large_token(self, mock_db_session=None):
        """異常に大きなトークンのテスト"""
        if mock_db_session is None:
            mock_db_session = Mock()
            mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # 非常に大きなペイロードを持つトークン
        large_data = "x" * 10000
        token_data = {
            "sub": "test@example.com",
            "id": 1,
            "large_field": large_data,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        large_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        # 大きなトークンでもエラーハンドリングが適切に動作することを確認
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=large_token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestTypeConversion:
    """型変換のテスト"""
    
    @pytest.mark.asyncio
    async def test_string_id_conversion(self, mock_db_session=None):
        """文字列IDの整数変換テスト"""
        if mock_db_session is None:
            mock_db_session = Mock()
            mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        token_data = {
            "sub": "test@example.com",
            "id": "123",  # 文字列として渡されたID
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=mock_db_session)
        
        # ユーザーが見つからないため認証エラーになることを確認
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_non_numeric_id(self, mock_db_session=None):
        """非数値IDのテスト"""
        if mock_db_session is None:
            mock_db_session = Mock()
        
        token_data = {
            "sub": "test@example.com",
            "id": "not_a_number",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
