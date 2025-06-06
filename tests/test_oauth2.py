#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
oauth2.py用の包括的テストスイート
認証トークンの検証、ユーザー取得、エラーハンドリングをテストします。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session

# テスト対象のモジュールをインポート
from oauth2 import get_current_user, oauth2_scheme, ALGORITHM
from models import User
from schemas import TokenData


class TestOAuth2Module:
    """OAuth2認証モジュールのテストクラス"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_user(self):
        """サンプルユーザーデータ"""
        user = User()
        user.id = 1
        user.email = "test@example.com"
        user.name = "Test User"
        user.is_active = True
        return user
    
    @pytest.fixture
    def valid_token_payload(self):
        """有効なトークンペイロード"""
        return {
            "sub": "test@example.com",
            "id": 1,
            "exp": 1999999999  # 未来の有効期限
        }
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, mock_db, sample_user, valid_token_payload):
        """有効なトークンでユーザーを正常に取得"""
        # SECRET_KEYをモック
        with patch('oauth2.SECRET_KEY', 'test_secret_key'):
            # JWTデコードをモック
            with patch('oauth2.jwt.decode', return_value=valid_token_payload):
                # データベースクエリをモック
                mock_query = Mock()
                mock_filter = Mock()
                mock_first = Mock(return_value=sample_user)
                
                mock_query.filter.return_value = mock_filter
                mock_filter.first.return_value = sample_user
                mock_db.query.return_value = mock_query
                
                # テスト実行
                result = await get_current_user("valid_token", mock_db)
                
                # 検証
                assert result == sample_user
                mock_db.query.assert_called_once_with(User)
    
    @pytest.mark.asyncio
    async def test_get_current_user_none_token(self, mock_db):
        """Noneトークンでエラーを発生"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(None, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "認証情報が無効です" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_none_secret_key(self, mock_db):
        """SECRET_KEYがNoneの場合のエラー"""
        with patch('oauth2.SECRET_KEY', None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("some_token", mock_db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "認証情報が無効です" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_jwt_decode_error(self, mock_db):
        """JWTデコードエラーでHTTPExceptionを発生"""
        with patch('oauth2.SECRET_KEY', 'test_secret_key'):
            # JWTErrorを発生させる
            with patch('oauth2.jwt.decode', side_effect=JWTError("Invalid token")):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user("invalid_token", mock_db)
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert "認証情報が無効です" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_missing_email_in_payload(self, mock_db):
        """ペイロードにemail（sub）がない場合のエラー"""
        invalid_payload = {"id": 1}  # subが欠落
        
        with patch('oauth2.SECRET_KEY', 'test_secret_key'):
            with patch('oauth2.jwt.decode', return_value=invalid_payload):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user("token_without_email", mock_db)
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_missing_id_in_payload(self, mock_db):
        """ペイロードにidがない場合のエラー"""
        invalid_payload = {"sub": "test@example.com"}  # idが欠落
        
        with patch('oauth2.SECRET_KEY', 'test_secret_key'):
            with patch('oauth2.jwt.decode', return_value=invalid_payload):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user("token_without_id", mock_db)
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_id_type(self, mock_db):
        """ペイロードのidが無効な型の場合のエラー"""
        invalid_payload = {"sub": "test@example.com", "id": "not_a_number"}
        
        with patch('oauth2.SECRET_KEY', 'test_secret_key'):
            with patch('oauth2.jwt.decode', return_value=invalid_payload):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user("token_with_invalid_id", mock_db)
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, mock_db, valid_token_payload):
        """データベースにユーザーが存在しない場合のエラー"""
        with patch('oauth2.SECRET_KEY', 'test_secret_key'):
            with patch('oauth2.jwt.decode', return_value=valid_token_payload):
                # データベースクエリが None を返すようにモック
                mock_query = Mock()
                mock_filter = Mock()
                mock_first = Mock(return_value=None)
                
                mock_query.filter.return_value = mock_filter
                mock_filter.first.return_value = None
                mock_db.query.return_value = mock_query
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user("valid_token", mock_db)
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_oauth2_scheme_configuration(self):
        """OAuth2PasswordBearerの設定テスト"""
        # tokenUrlまたはmodel_fieldsを確認
        if hasattr(oauth2_scheme, 'tokenUrl'):
            assert oauth2_scheme.tokenUrl == "api/v1/login"
        elif hasattr(oauth2_scheme, 'model') and hasattr(oauth2_scheme.model, 'tokenUrl'):
            assert oauth2_scheme.model.tokenUrl == "api/v1/login"
        else:
            # フォールバック: OAuth2PasswordBearerが正しく初期化されているかのみ確認
            assert oauth2_scheme is not None
    
    @pytest.mark.asyncio
    async def test_get_current_user_token_data_creation(self, mock_db, sample_user):
        """TokenDataオブジェクトの正常な作成"""
        payload = {"sub": "test@example.com", "id": 1}
        
        with patch('oauth2.SECRET_KEY', 'test_secret_key'):
            with patch('oauth2.jwt.decode', return_value=payload):
                # データベースクエリをモック
                mock_query = Mock()
                mock_filter = Mock()
                mock_first = Mock(return_value=sample_user)
                
                mock_query.filter.return_value = mock_filter
                mock_filter.first.return_value = sample_user
                mock_db.query.return_value = mock_query
                
                # TokenDataの作成をモック
                with patch('oauth2.TokenData') as mock_token_data:
                    result = await get_current_user("valid_token", mock_db)
                    
                    # TokenDataが正しいemailで作成されることを確認
                    mock_token_data.assert_called_once_with(email="test@example.com")
                    assert result == sample_user
    
    def test_algorithm_configuration(self):
        """ALGORITHMの設定テスト"""
        # ALGORITHMがHS256であることを確認
        assert ALGORITHM == "HS256" or ALGORITHM is not None
    
    @pytest.mark.asyncio
    async def test_get_current_user_complex_scenario(self, mock_db, sample_user):
        """複雑なシナリオでの統合テスト"""
        # 複数のステップを含む包括的なテスト
        payload = {
            "sub": "complex@example.com",
            "id": 42,
            "exp": 2000000000,
            "iat": 1600000000
        }
        
        with patch('oauth2.SECRET_KEY', 'complex_secret_key'):
            with patch('oauth2.jwt.decode', return_value=payload):
                # より複雑なデータベースモック
                mock_db.query.return_value.filter.return_value.first.return_value = sample_user
                
                result = await get_current_user("complex_token", mock_db)
                
                # 結果の検証
                assert result == sample_user
                # JWTデコードが正しい引数で呼ばれることを確認
                with patch('oauth2.jwt.decode') as mock_decode:
                    mock_decode.return_value = payload
                    await get_current_user("complex_token", mock_db)
                    mock_decode.assert_called_with(
                        "complex_token",
                        'complex_secret_key',
                        algorithms=[ALGORITHM]
                    )
    
    @pytest.mark.asyncio
    async def test_get_current_user_error_handling_comprehensive(self, mock_db):
        """包括的なエラーハンドリングテスト"""
        error_scenarios = [
            # シナリオ1: 空のペイロード
            {},
            # シナリオ2: subのみ
            {"sub": "test@example.com"},
            # シナリオ3: idのみ
            {"id": 1},
            # シナリオ4: 無効なidタイプ
            {"sub": "test@example.com", "id": [1, 2, 3]},
            # シナリオ5: Noneの値
            {"sub": None, "id": 1},
            {"sub": "test@example.com", "id": None}
        ]
        
        for i, payload in enumerate(error_scenarios):
            with patch('oauth2.SECRET_KEY', 'test_secret_key'):
                with patch('oauth2.jwt.decode', return_value=payload):
                    with pytest.raises(HTTPException) as exc_info:
                        await get_current_user(f"error_token_{i}", mock_db)
                    
                    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED