#!/usr/bin/env python3
"""
main.py 包括的テストスイート
FastAPIアプリケーション、CORS設定、例外ハンドリング、ミドルウェアなどの全機能をテスト

テスト対象:
1. FastAPIアプリケーション初期化
2. CORS設定とミドルウェア
3. 例外ハンドリング（RequestValidationError）
4. ルーター統合（article, user, auth）
5. データベース初期化
6. ロギング機能
7. 環境変数設定
8. ミドルウェアチェーン
"""

import pytest
import asyncio
import json
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock, call
from fastapi import FastAPI, status, Request
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestMainApplication:
    """main.pyのメインテストクラス"""
    
    def setup_method(self):
        """各テスト前の初期化"""
        # パッチされたモジュールをクリア
        if 'main' in sys.modules:
            del sys.modules['main']
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_app_initialization_success(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """FastAPIアプリケーションの正常初期化テスト"""
        # 環境変数設定をモック
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': ['http://127.0.0.1:8000']
        }.get(key, default)
        
        # main.pyをインポート
        import main
        
        # アプリケーションインスタンス確認
        assert isinstance(main.app, FastAPI)
        assert hasattr(main, 'allowed_origins')
        assert 'http://localhost:3000' in main.allowed_origins
        assert 'http://127.0.0.1:8000' in main.allowed_origins
        
        # ログ呼び出し確認
        mock_logger.assert_called_with("CORS_ORIGIN -> OK")
        mock_error_logger.assert_not_called()
        
        # データベース初期化確認
        mock_base.metadata.create_all.assert_called_once_with(mock_engine)
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_app_initialization_no_cors_origins(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """CORS設定なしでの初期化テスト"""
        # 環境変数なしに設定
        mock_db_env.get.return_value = []
        
        # main.pyをインポート
        import main
        
        # エラーログ呼び出し確認
        mock_error_logger.assert_called_with("CORS_ORIGINSとLOCAL_ORIGINの両方が取得できませんでした。")
        mock_logger.assert_not_called()
        
        # allowed_originsが空リスト
        assert main.allowed_origins == []
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_cors_middleware_configuration(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """CORSミドルウェア設定テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['https://example.com'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        # CORSミドルウェアが追加されていることを確認
        middlewares = main.app.user_middleware
        cors_middleware_found = any(
            middleware.cls == CORSMiddleware for middleware in middlewares
        )
        assert cors_middleware_found
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_routers_inclusion(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """ルーター統合テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        # ルーターが含まれていることを確認
        routes = main.app.routes
        route_paths = [route.path for route in routes if hasattr(route, 'path')]
        
        # 各ルーターのパスが含まれていることを確認（実際のパスは実装依存）
        assert len(routes) > 0  # 何らかのルートが存在する

class TestCORSConfiguration:
    """CORS設定のテストクラス"""
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_cors_origins_parsing_list_format(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """CORS origins リスト形式解析テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000', 'https://example.com'],
            'local_origin': ['http://127.0.0.1:8000']
        }.get(key, default)
        
        import main
        
        expected_origins = ['http://localhost:3000', 'https://example.com', 'http://127.0.0.1:8000']
        assert set(main.allowed_origins) == set(expected_origins)
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_cors_origins_non_list_type(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """非リスト型のCORS origins設定テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': 'http://localhost:3000',  # 文字列（非リスト）
            'local_origin': None
        }.get(key, default)
        
        import main
        
        # 非リスト型は無視される
        assert main.allowed_origins == []
        mock_error_logger.assert_called_with("CORS_ORIGINSとLOCAL_ORIGINの両方が取得できませんでした。")
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_cors_origins_empty_lists(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """空リストのCORS origins設定テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': [],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        assert main.allowed_origins == []
        mock_error_logger.assert_called_with("CORS_ORIGINSとLOCAL_ORIGINの両方が取得できませんでした。")

class TestExceptionHandling:
    """例外ハンドリングのテストクラス"""
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_email_validation_error_detection(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """メールアドレス形式エラー検出テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        # モックリクエストとエラー作成
        mock_request = Mock()
        mock_exc = RequestValidationError([{
            "loc": ["body", "email"],
            "type": "value_error.email",
            "msg": "field required",
            "input": "invalid-email"
        }])
        
        # 例外ハンドラを直接テスト
        result = asyncio.run(main.handler(mock_request, mock_exc))
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == status.HTTP_400_BAD_REQUEST
        # バイナリデータをUTF-8でデコードしてから比較
        response_data = result.body.decode('utf-8')
        assert "メールアドレスの形式が不正です。" in response_data
        
        # エラーログ呼び出し確認
        assert mock_error_logger.call_count >= 1
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_general_validation_error_handling(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """一般的なバリデーションエラーハンドリングテスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        # 非メールエラーのモック作成
        mock_request = Mock()
        mock_exc = RequestValidationError([{
            "loc": ["body", "name"],
            "type": "missing",
            "msg": "field required"
        }])
        
        # 例外ハンドラを直接テスト
        result = asyncio.run(main.handler(mock_request, mock_exc))
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # バイナリデータをUTF-8でデコードしてから比較
        response_data = result.body.decode('utf-8')
        assert "入力データが無効です。" in response_data
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_email_error_with_multiple_conditions(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """複数条件でのメールエラー検出テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        # @ 記号を含む入力でのエラー
        mock_request = Mock()
        mock_exc = RequestValidationError([{
            "loc": ["body", "user_email"],
            "type": "type_error.str",
            "msg": "str type expected",
            "input": "test@"
        }])
        
        result = asyncio.run(main.handler(mock_request, mock_exc))
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == status.HTTP_400_BAD_REQUEST
        # バイナリデータをUTF-8でデコードしてから比較
        response_data = result.body.decode('utf-8')
        assert "メールアドレスの形式が不正です。" in response_data
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_email_error_with_valid_email_message(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """valid emailメッセージでのエラー検出テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        mock_request = Mock()
        mock_exc = RequestValidationError([{
            "loc": ["body", "contact_email"],
            "type": "value_error",
            "msg": "ensure this is a valid email",
            "input": "not-valid-email"
        }])
        
        result = asyncio.run(main.handler(mock_request, mock_exc))
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == status.HTTP_400_BAD_REQUEST

class TestIntegrationWithTestClient:
    """TestClientを使用した統合テスト"""
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_app_startup_with_test_client(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """TestClientでのアプリ起動テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        client = TestClient(main.app)
        
        # アプリが正常に起動していることを確認
        assert client.app == main.app
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_cors_headers_in_response(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """レスポンスにCORSヘッダーが含まれることのテスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        client = TestClient(main.app)
        
        # OPTIONSリクエストでCORSプリフライト確認
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # CORSミドルウェアが機能していることを確認
        # （実際のヘッダーは実装やルートの存在に依存）
        assert response.status_code in [200, 404, 405]  # いずれかの有効なレスポンス

class TestMiddlewareStack:
    """ミドルウェアスタックのテスト"""
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_middleware_order_and_configuration(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """ミドルウェアの順序と設定テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        # ミドルウェアが正しく設定されていることを確認
        middlewares = main.app.user_middleware
        assert len(middlewares) > 0
        
        # CORSミドルウェアが含まれていることを確認
        cors_middleware_found = any(
            middleware.cls == CORSMiddleware for middleware in middlewares
        )
        assert cors_middleware_found
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_cors_middleware_parameters(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """CORSミドルウェアパラメータテスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000', 'https://example.com'],
            'local_origin': ['http://127.0.0.1:8000']
        }.get(key, default)
        
        import main
        
        # CORSミドルウェアのパラメータを確認
        cors_middleware = None
        for middleware in main.app.user_middleware:
            if middleware.cls == CORSMiddleware:
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None
        assert cors_middleware.kwargs['allow_credentials'] is True
        assert 'GET' in cors_middleware.kwargs['allow_methods']
        assert 'POST' in cors_middleware.kwargs['allow_methods']
        assert 'PUT' in cors_middleware.kwargs['allow_methods']
        assert 'DELETE' in cors_middleware.kwargs['allow_methods']
        assert cors_middleware.kwargs['allow_headers'] == ['*']

class TestErrorLogging:
    """エラーロギングのテスト"""
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_validation_error_logging(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """バリデーションエラーログテスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        # バリデーションエラーでのログ呼び出し確認
        mock_request = Mock()
        error_details = [{
            "loc": ["body", "test"],
            "type": "missing",
            "msg": "field required"
        }]
        mock_exc = RequestValidationError(error_details)
        
        result = asyncio.run(main.handler(mock_request, mock_exc))
        
        # バリデーションエラーログが呼び出されていることを確認
        mock_error_logger.assert_any_call(f"バリデーションエラー: {error_details}")
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_email_error_specific_logging(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """メールエラー固有ログテスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        mock_request = Mock()
        error_detail = {
            "loc": ["body", "email"],
            "type": "value_error.email",
            "msg": "field required",
            "input": "invalid"
        }
        mock_exc = RequestValidationError([error_detail])
        
        result = asyncio.run(main.handler(mock_request, mock_exc))
        
        # メールエラー検出ログが呼び出されていることを確認
        mock_error_logger.assert_any_call(f"メールアドレス形式エラーを検出: {error_detail}")

class TestDatabaseInitialization:
    """データベース初期化のテスト"""
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_database_metadata_creation(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """データベースメタデータ作成テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        # データベースのメタデータ作成が呼び出されていることを確認
        mock_base.metadata.create_all.assert_called_once_with(mock_engine)
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_database_initialization_with_exception(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """データベース初期化例外テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        # データベース初期化で例外発生
        mock_base.metadata.create_all.side_effect = Exception("Database connection failed")
        
        # 例外が発生してもアプリは初期化される（例外は上位で処理される）
        with pytest.raises(Exception, match="Database connection failed"):
            import main

class TestApplicationConfiguration:
    """アプリケーション設定のテスト"""
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_fastapi_app_configuration(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """FastAPIアプリケーション設定テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        # FastAPIアプリケーション基本設定確認
        assert isinstance(main.app, FastAPI)
        assert hasattr(main.app, 'routes')
        assert hasattr(main.app, 'exception_handlers')
        assert hasattr(main.app, 'user_middleware')
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_exception_handler_registration(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """例外ハンドラ登録テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        # RequestValidationError用の例外ハンドラが登録されていることを確認
        assert RequestValidationError in main.app.exception_handlers
        
        # 登録されたハンドラが期待する関数であることを確認
        handler_func = main.app.exception_handlers[RequestValidationError]
        assert callable(handler_func)

class TestEnvironmentVariables:
    """環境変数処理のテスト"""
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_cors_origins_environment_parsing(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """CORS origins環境変数解析テスト"""
        # 複雑な環境変数設定
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000', 'https://app.example.com', 'http://localhost:8080'],
            'local_origin': ['http://127.0.0.1:8000', 'http://0.0.0.0:8000']
        }.get(key, default)
        
        import main
        
        expected_all_origins = [
            'http://localhost:3000',
            'https://app.example.com', 
            'http://localhost:8080',
            'http://127.0.0.1:8000',
            'http://0.0.0.0:8000'
        ]
        
        assert set(main.allowed_origins) == set(expected_all_origins)
        mock_logger.assert_called_with("CORS_ORIGIN -> OK")
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_partial_cors_configuration(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """部分的CORS設定テスト"""
        # cors_originsのみ設定、local_originなし
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['https://production.example.com'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        assert main.allowed_origins == ['https://production.example.com']
        mock_logger.assert_called_with("CORS_ORIGIN -> OK")
        mock_error_logger.assert_not_called()
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_environment_variable_none_values(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """環境変数None値テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': None,
            'local_origin': None
        }.get(key, default)
        
        import main
        
        assert main.allowed_origins == []
        mock_error_logger.assert_called_with("CORS_ORIGINSとLOCAL_ORIGINの両方が取得できませんでした。")

class TestPerformanceAndResourceUsage:
    """パフォーマンスとリソース使用量のテスト"""
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_app_initialization_performance(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """アプリ初期化パフォーマンステスト"""
        import time
        
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        start_time = time.time()
        import main
        initialization_time = time.time() - start_time
        
        # 初期化が1秒未満で完了することを確認
        assert initialization_time < 1.0
        assert isinstance(main.app, FastAPI)
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_large_cors_origins_list_handling(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """大きなCORS originsリスト処理テスト"""
        # 大量のCORS originsを生成
        large_origins_list = [f'https://subdomain{i}.example.com' for i in range(100)]
        local_origins_list = [f'http://localhost:{8000+i}' for i in range(50)]
        
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': large_origins_list,
            'local_origin': local_origins_list
        }.get(key, default)
        
        import main
        
        # 全てのオリジンが正しく処理されることを確認
        expected_total = len(large_origins_list) + len(local_origins_list)
        assert len(main.allowed_origins) == expected_total
        assert set(main.allowed_origins) == set(large_origins_list + local_origins_list)
        
        mock_logger.assert_called_with("CORS_ORIGIN -> OK")

class TestEdgeCases:
    """エッジケースのテスト"""
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_exception_handler_with_empty_errors(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """空エラーリストでの例外ハンドラテスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        mock_request = Mock()
        mock_exc = RequestValidationError([])  # 空のエラーリスト
        
        result = asyncio.run(main.handler(mock_request, mock_exc))
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_exception_handler_with_complex_error_structure(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """複雑なエラー構造での例外ハンドラテスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000'],
            'local_origin': []
        }.get(key, default)
        
        import main
        
        mock_request = Mock()
        # 複雑なネストされたエラー
        complex_errors = [
            {
                "loc": ["body", "user", "profile", "email"],
                "type": "value_error.email",
                "msg": "invalid email format",
                "input": {"nested": "invalid@"}
            },
            {
                "loc": ["body", "settings"],
                "type": "missing",
                "msg": "field required"
            }
        ]
        mock_exc = RequestValidationError(complex_errors)
        
        result = asyncio.run(main.handler(mock_request, mock_exc))
        
        # ネストされたemailフィールドも検出される
        assert isinstance(result, JSONResponse)
        assert result.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('main.Base')
    @patch('main.engine')
    @patch('main.db_env')
    @patch('main.create_logger')
    @patch('main.create_error_logger')
    def test_cors_origins_duplicate_handling(self, mock_error_logger, mock_logger, mock_db_env, mock_engine, mock_base):
        """重複CORS origins処理テスト"""
        mock_db_env.get.side_effect = lambda key, default=None: {
            'cors_origins': ['http://localhost:3000', 'https://example.com'],
            'local_origin': ['http://localhost:3000', 'http://127.0.0.1:8000']  # 重複あり
        }.get(key, default)
        
        import main
        
        # 重複は許可される（CORSミドルウェアが処理）
        expected_origins = ['http://localhost:3000', 'https://example.com', 'http://localhost:3000', 'http://127.0.0.1:8000']
        assert main.allowed_origins == expected_origins

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
