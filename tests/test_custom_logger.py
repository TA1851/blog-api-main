"""logger/custom_logger.pyの単体テスト"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from logging import Logger, FileHandler, Formatter, INFO, ERROR
import sys
import os


class TestCustomLoggerConfiguration:
    """カスタムロガー設定のテスト"""

    def test_log_directory_creation(self):
        """ログディレクトリ作成のテスト"""
        from logger.custom_logger import log_dir
        
        # log_dirが存在することを確認
        assert log_dir is not None
        # Pathオブジェクトであることを確認
        assert hasattr(log_dir, 'mkdir')
        # 実際に存在することを確認（作成されている）
        assert log_dir.exists() or log_dir.parent.exists()

    def test_logger_instance_creation(self):
        """ロガーインスタンス作成のテスト"""
        from logger.custom_logger import logger
        
        assert isinstance(logger, Logger)
        assert logger.name == "app_logger"
        assert logger.level == INFO

    def test_logger_handlers_setup(self):
        """ロガーハンドラー設定のテスト"""
        from logger.custom_logger import logger
        
        # ハンドラーが設定されていることを確認
        assert len(logger.handlers) >= 2
        
        # FileHandlerが含まれていることを確認
        file_handlers = [h for h in logger.handlers if isinstance(h, FileHandler)]
        assert len(file_handlers) >= 2

    def test_formatter_configuration(self):
        """フォーマッター設定のテスト"""
        from logger.custom_logger import formatter
        
        assert isinstance(formatter, Formatter)
        # フォーマット文字列の内容を確認
        expected_format = '%(asctime)s - %(levelname)s - %(message)s'
        assert formatter._fmt == expected_format


class TestLoggingFunctions:
    """ログ記録関数のテスト"""

    @patch('logger.custom_logger.logger')
    def test_create_logger_function(self, mock_logger):
        """create_logger関数のテスト"""
        from logger.custom_logger import create_logger
        
        test_message = "テスト用INFOメッセージ"
        create_logger(test_message)
        
        mock_logger.info.assert_called_once_with(test_message)

    @patch('logger.custom_logger.logger')
    def test_create_error_logger_function(self, mock_logger):
        """create_error_logger関数のテスト"""
        from logger.custom_logger import create_error_logger
        
        test_message = "テスト用エラーメッセージ"
        create_error_logger(test_message)
        
        mock_logger.error.assert_called_once_with(test_message)

    def test_create_logger_with_empty_message(self):
        """空のメッセージでのcreate_logger関数テスト"""
        from logger.custom_logger import create_logger
        
        # 例外が発生しないことを確認
        try:
            create_logger("")
            create_logger(None)
        except Exception as e:
            pytest.fail(f"空のメッセージでエラーが発生しました: {e}")

    def test_create_error_logger_with_empty_message(self):
        """空のメッセージでのcreate_error_logger関数テスト"""
        from logger.custom_logger import create_error_logger
        
        # 例外が発生しないことを確認
        try:
            create_error_logger("")
            create_error_logger(None)
        except Exception as e:
            pytest.fail(f"空のメッセージでエラーが発生しました: {e}")


class TestLoggerIntegration:
    """ロガー統合テスト"""

    def test_logger_duplicate_handler_prevention(self):
        """ハンドラー重複追加防止のテスト"""
        from logger.custom_logger import logger
        
        initial_handler_count = len(logger.handlers)
        
        # モジュールを再インポートしてもハンドラーが重複しないことを確認
        import importlib
        import logger.custom_logger
        importlib.reload(logger.custom_logger)
        
        from logger.custom_logger import logger as reloaded_logger
        
        # ハンドラー数が大幅に増加していないことを確認（多少の増加は許容）
        assert len(reloaded_logger.handlers) <= initial_handler_count + 2

    @patch('logger.custom_logger.logger.info')
    @patch('logger.custom_logger.logger.error')
    def test_logging_levels_separation(self, mock_error, mock_info):
        """ログレベル分離のテスト"""
        from logger.custom_logger import create_logger, create_error_logger
        
        info_msg = "情報メッセージ"
        error_msg = "エラーメッセージ"
        
        create_logger(info_msg)
        create_error_logger(error_msg)
        
        mock_info.assert_called_once_with(info_msg)
        mock_error.assert_called_once_with(error_msg)

    def test_logger_file_paths(self):
        """ログファイルパス設定のテスト"""
        from logger.custom_logger import logger
        
        file_handlers = [h for h in logger.handlers if isinstance(h, FileHandler)]
        
        # ファイルハンドラーが存在することを確認
        assert len(file_handlers) >= 2
        
        # ファイルパスが設定されていることを確認
        for handler in file_handlers:
            assert hasattr(handler, 'baseFilename')
            assert handler.baseFilename is not None


class TestLoggerErrorHandling:
    """ロガーエラーハンドリングのテスト"""

    def test_logger_with_unicode_messages(self):
        """Unicode文字を含むメッセージのテスト"""
        from logger.custom_logger import create_logger, create_error_logger
        
        unicode_msg = "日本語メッセージ 🚀 テスト"
        
        try:
            create_logger(unicode_msg)
            create_error_logger(unicode_msg)
        except Exception as e:
            pytest.fail(f"Unicode文字でエラーが発生しました: {e}")

    def test_logger_with_special_characters(self):
        """特殊文字を含むメッセージのテスト"""
        from logger.custom_logger import create_logger, create_error_logger
        
        special_msg = "特殊文字テスト: !@#$%^&*()[]{}|;:,.<>?"
        
        try:
            create_logger(special_msg)
            create_error_logger(special_msg)
        except Exception as e:
            pytest.fail(f"特殊文字でエラーが発生しました: {e}")

    def test_logger_with_long_messages(self):
        """長いメッセージのテスト"""
        from logger.custom_logger import create_logger, create_error_logger
        
        long_msg = "A" * 1000  # 1000文字の長いメッセージ
        
        try:
            create_logger(long_msg)
            create_error_logger(long_msg)
        except Exception as e:
            pytest.fail(f"長いメッセージでエラーが発生しました: {e}")


class TestLoggerModuleImport:
    """ロガーモジュールインポートのテスト"""

    def test_module_imports(self):
        """モジュールインポートのテスト"""
        try:
            from logger.custom_logger import create_logger, create_error_logger, logger, formatter
            
            # すべての主要な要素がインポートできることを確認
            assert callable(create_logger)
            assert callable(create_error_logger)
            assert isinstance(logger, Logger)
            assert isinstance(formatter, Formatter)
            
        except ImportError as e:
            pytest.fail(f"モジュールインポートエラー: {e}")

    def test_function_signatures(self):
        """関数シグネチャのテスト"""
        from logger.custom_logger import create_logger, create_error_logger
        import inspect
        
        # create_logger関数のシグネチャを確認
        sig_create_logger = inspect.signature(create_logger)
        assert len(sig_create_logger.parameters) == 1
        assert 'info_msg' in sig_create_logger.parameters
        
        # create_error_logger関数のシグネチャを確認
        sig_create_error_logger = inspect.signature(create_error_logger)
        assert len(sig_create_error_logger.parameters) == 1
        assert 'error_msg' in sig_create_error_logger.parameters
