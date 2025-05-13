import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError
from unittest.mock import patch, MagicMock
from schemas import ArticleBase, validation_exception_handler, LengthMismatchError
import json
from schemas import create_logger, create_error_logger, ArticleBase

# Test ArticleBase model validation
class TestArticleBase:
    def test_valid_data(self):
        # Test with valid data
        article = ArticleBase(title="Valid Title", body="Valid Body")
        assert article.title == "Valid Title"
        assert article.body == "Valid Body"

    def test_none_values(self):
        # Test with None values (should be valid as per the model definition)
        article = ArticleBase(title=None, body=None)
        assert article.title is None
        assert article.body is None

    def test_empty_values(self):
        # Test with empty strings (should be valid)
        article = ArticleBase(title="", body="")
        assert article.title == ""
        assert article.body == ""

    @pytest.mark.parametrize("test_input,expected", [
        ({"title": "x" * 30, "body": "Valid Body"}, True),  # Max length title
        ({"title": "Valid Title", "body": "x" * 100}, True),  # Max length body
        ({"title": "x" * 31, "body": "Valid Body"}, False),  # Title too long
        ({"title": "Valid Title", "body": "x" * 101}, False),  # Body too long
    ])
    def test_length_validation(self, test_input, expected):
        if expected:
            # Should not raise an exception
            article = ArticleBase(**test_input)
            if "title" in test_input:
                assert article.title == test_input["title"]
            if "body" in test_input:
                assert article.body == test_input["body"]
        else:
            # Should raise ValidationError
            with pytest.raises(ValidationError):
                ArticleBase(**test_input)

app = FastAPI()

class ItemModel(ArticleBase):
    title: str | None = Field(None, title="タイトル", max_length=30, description="30文字以内で入力してください")
    body: str | None = Field(None, title="本文", max_length=100, description="100文字以内で入力してください")


@pytest.fixture
def validation_error():
    """Pydanticのバリデーションエラーを発生させるフィクスチャ"""
    try:
        ItemModel(title="a" * 31, body="b" * 101)
    except Exception as e:
        return e


@pytest.fixture
def mock_request():
    """モックリクエストを作成するフィクスチャ"""
    title_str = "あ" * 31
    body_str = "あ" * 101
    json_data = json.dumps({
        "title": title_str,
        "body": body_str
    })
    request = MagicMock(spec=Request)
    request.body.return_value = json_data.encode()
    return request

@pytest.mark.asyncio
async def test_validation_exception_handler_body_error(mock_request, validation_error):
    """bodyフィールドのバリデーションエラーが正しく処理されるかテスト"""
    # create_error_loggerをモック化
    with patch('schemas.create_error_logger') as mock_logger:
        # request_validation_exception_handlerをモック化
        with patch('fastapi.exception_handlers.request_validation_exception_handler') as mock_handler:
            mock_handler.return_value = {"status_code": 422}
            
            # テスト対象の関数を実行
            result = await validation_exception_handler(mock_request, validation_error)
            
            # ロガーが呼び出されたことを確認
            assert mock_logger.call_count == 2  # title と body の2つのエラー
            
            # エラーメッセージが正しく生成されたか確認
            calls = mock_logger.call_args_list
            error_messages = [call[0][0] for call in calls]
            
            # Padanticのデフォルトのエラーメッセージで確認する。
            assert "String should have at most 30 characters" in error_messages[0]
            assert "String should have at most 100 characters" in error_messages[1]

            # デフォルトのハンドラが呼び出されたことを確認
            mock_handler.assert_called_once_with(mock_request, validation_error)
            
            # 結果が正しいことを確認
            assert result == {"status_code": 422}

@pytest.mark.asyncio
async def test_validation_exception_handler_query_error():
    """queryパラメータのバリデーションエラーが正しく処理されるかテスト"""
    # クエリパラメータのエラーを模擬
    error_location = ("query", "page")
    error_msg = "値は整数である必要があります"
    
    errors = [{"loc": error_location, "msg": error_msg, "type": "type_error.integer"}]
    validation_error = RequestValidationError(errors=errors)
    mock_request = MagicMock(spec=Request)
    
    # create_error_loggerをモック化
    with patch('schemas.create_error_logger') as mock_logger:
        # request_validation_exception_handlerをモック化
        with patch('fastapi.exception_handlers.request_validation_exception_handler') as mock_handler:
            mock_handler.return_value = {"status_code": 422}
            
            # テスト対象の関数を実行
            result = await validation_exception_handler(mock_request, validation_error)
            
            # ロガーが呼び出されたことを確認
            mock_logger.assert_called_once()
            
            # エラーメッセージが正しく生成されたか確認
            error_message = mock_logger.call_args[0][0]
            assert "query.page" in error_message
            assert error_msg in error_message
            
            # デフォルトのハンドラが呼び出されたことを確認
            mock_handler.assert_called_once_with(mock_request, validation_error)
            
            # 結果が正しいことを確認
            assert result == {"status_code": 422}
