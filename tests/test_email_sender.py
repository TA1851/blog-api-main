"""utils/email_sender.pyの単体テスト"""
import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from fastapi_mail import ConnectionConfig, MessageType
import os


class TestEmailSenderConfiguration:
    """メール送信設定テスト"""

    @patch('utils.email_sender.os.getenv')
    def test_get_mail_config(self, mock_getenv):
        """メール設定取得のテスト"""
        # 環境変数のモック設定
        mock_getenv.side_effect = lambda key, default="": {
            "MAIL_USERNAME": "test@example.com",
            "MAIL_PASSWORD": "test_password",
            "MAIL_FROM": "noreply@example.com",
            "MAIL_PORT": "587",
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_STARTTLS": "True",
            "MAIL_SSL_TLS": "False"
        }.get(key, default)
        
        from utils.email_sender import get_mail_config
        
        config = get_mail_config()
        assert isinstance(config, ConnectionConfig)
        assert config.MAIL_USERNAME == "test@example.com"
        assert config.MAIL_PASSWORD == "test_password"
        assert config.MAIL_FROM == "noreply@example.com"
        assert config.MAIL_PORT == 587
        assert config.MAIL_SERVER == "smtp.example.com"
        assert config.MAIL_STARTTLS == True
        assert config.MAIL_SSL_TLS == False

    @patch('utils.email_sender.os.getenv')
    def test_get_mail_config_defaults(self, mock_getenv):
        """メール設定デフォルト値のテスト"""
        # 必須フィールドを設定し、オプションフィールドはデフォルト値を使用
        def mock_getenv_func(key, default=""):
            values = {
                "MAIL_USERNAME": "test@example.com",
                "MAIL_PASSWORD": "password", 
                "MAIL_FROM": "test@example.com"
            }
            return values.get(key, default)
        
        mock_getenv.side_effect = mock_getenv_func
        
        from utils.email_sender import get_mail_config
        
        config = get_mail_config()
        assert config.MAIL_PORT == 587  # デフォルト値
        assert config.MAIL_SERVER == "smtp.gmail.com"  # デフォルト値

    @patch('utils.email_sender.os.getenv')
    def test_is_email_enabled_true(self, mock_getenv):
        """メール送信有効化テスト"""
        mock_getenv.side_effect = lambda key, default="false": {
            "ENABLE_EMAIL_SENDING": "true"
        }.get(key, default)
        
        from utils.email_sender import _is_email_enabled
        
        assert _is_email_enabled() == True

    @patch('utils.email_sender.os.getenv')
    def test_is_email_enabled_false(self, mock_getenv):
        """メール送信無効化テスト"""
        mock_getenv.side_effect = lambda key, default="false": {
            "ENABLE_EMAIL_SENDING": "false"
        }.get(key, default)
        
        from utils.email_sender import _is_email_enabled
        
        assert _is_email_enabled() == False

    @patch('utils.email_sender.os.getenv')
    def test_validate_mail_config_valid(self, mock_getenv):
        """有効なメール設定の検証テスト"""
        mock_getenv.side_effect = lambda key: {
            "MAIL_USERNAME": "test@example.com",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com"
        }.get(key)
        
        from utils.email_sender import _validate_mail_config
        
        assert _validate_mail_config() == True

    @patch('utils.email_sender.os.getenv')
    def test_validate_mail_config_invalid(self, mock_getenv):
        """無効なメール設定の検証テスト"""
        mock_getenv.side_effect = lambda key: {
            "MAIL_USERNAME": "",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com"
        }.get(key)
        
        from utils.email_sender import _validate_mail_config
        
        assert _validate_mail_config() == False


class TestEmailSenderDevMode:
    """開発モードでのメール送信テスト"""

    def test_print_dev_mode_email(self):
        """開発モード用コンソール出力のテスト"""
        from utils.email_sender import _print_dev_mode_email
        import io
        import sys
        
        # 標準出力をキャプチャ
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            _print_dev_mode_email(
                "テストタイトル",
                "test@example.com",
                "テスト件名",
                "テスト内容",
                "http://example.com/verify"
            )
            
            output = captured_output.getvalue()
            assert "📧 テストタイトル" in output
            assert "test@example.com" in output
            assert "テスト件名" in output
            assert "テスト内容" in output
            assert "http://example.com/verify" in output
            
        finally:
            sys.stdout = sys.__stdout__

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._print_dev_mode_email')
    @patch('utils.email_sender.create_logger')
    async def test_send_verification_email_dev_mode(self, mock_logger, mock_print, mock_enabled):
        """開発モードでの確認メール送信テスト"""
        mock_enabled.return_value = False
        
        from utils.email_sender import send_verification_email
        
        await send_verification_email("test@example.com", "test_token")
        
        mock_print.assert_called_once()
        mock_logger.assert_called()

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._print_dev_mode_email')
    @patch('utils.email_sender.create_logger')
    async def test_send_registration_complete_email_dev_mode(self, mock_logger, mock_print, mock_enabled):
        """登録完了メール開発モードテスト"""
        # メール送信無効（開発モード）
        mock_enabled.return_value = False
        
        from utils.email_sender import send_registration_complete_email
        
        await send_registration_complete_email("test@example.com", "testuser")
        
        # 開発モード出力が呼ばれることを確認
        mock_print.assert_called_once()
        mock_logger.assert_called()

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._print_dev_mode_email')
    @patch('utils.email_sender.create_logger')
    async def test_send_account_deletion_email_dev_mode(self, mock_logger, mock_print, mock_enabled):
        """退会完了メール開発モードテスト"""
        # メール送信無効（開発モード）
        mock_enabled.return_value = False
        
        from utils.email_sender import send_account_deletion_email
        
        await send_account_deletion_email("test@example.com", "testuser")
        
        # 開発モード出力が呼ばれることを確認
        mock_print.assert_called_once()
        mock_logger.assert_called()


class TestEmailSenderVerificationEmail:
    """確認メール送信テスト"""

    @patch('utils.email_sender.LOCAL_CORS_ORIGINS', 'http://localhost:3000')
    @patch('utils.email_sender.SERVER_PORT', '8080')
    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._print_dev_mode_email')
    @patch('utils.email_sender.create_logger')
    async def test_send_verification_email_local_url(self, mock_logger, mock_print, mock_enabled):
        """ローカル環境での確認URL生成テスト"""
        mock_enabled.return_value = False
        
        from utils.email_sender import send_verification_email
        
        await send_verification_email("test@example.com", "test_token")
        
        # ログ呼び出しを確認
        log_calls = [call[0][0] for call in mock_logger.call_args_list]
        assert any("127.0.0.1" in call for call in log_calls)

    @patch('utils.email_sender.LOCAL_CORS_ORIGINS', None)
    @patch('utils.email_sender.CORS_ORIGINS', 'https://example.com')
    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._print_dev_mode_email')
    @patch('utils.email_sender.create_logger')
    async def test_send_verification_email_production_url(self, mock_logger, mock_print, mock_enabled):
        """本番環境での確認URL生成テスト"""
        mock_enabled.return_value = False
        
        from utils.email_sender import send_verification_email
        
        await send_verification_email("test@example.com", "test_token")
        
        # ログ呼び出しを確認
        log_calls = [call[0][0] for call in mock_logger.call_args_list]
        assert any("example.com" in call for call in log_calls)

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender.get_mail_config')
    @patch('utils.email_sender.FastMail')
    @patch('utils.email_sender.MessageSchema')
    @patch('utils.email_sender.create_logger')
    async def test_send_verification_email_real_sending(self, mock_logger, mock_msg, mock_fastmail, mock_config, mock_validate, mock_enabled):
        """実際のメール送信テスト"""
        # メール送信有効、設定有効
        mock_enabled.return_value = True
        mock_validate.return_value = True
        
        # FastMailのモック設定
        mock_fastmail_instance = AsyncMock()
        mock_fastmail.return_value = mock_fastmail_instance
        mock_fastmail_instance.send_message = AsyncMock()
        
        from utils.email_sender import send_verification_email
        
        await send_verification_email("test@example.com", "test_token")
        
        # FastMailが呼び出されることを確認
        mock_fastmail.assert_called_once()
        mock_fastmail_instance.send_message.assert_called_once()

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender._print_dev_mode_email')
    @patch('utils.email_sender.create_error_logger')
    async def test_send_verification_email_invalid_config(self, mock_error_logger, mock_print, mock_validate, mock_enabled):
        """無効なメール設定でのテスト"""
        # メール送信有効、設定無効
        mock_enabled.return_value = True
        mock_validate.return_value = False
        
        from utils.email_sender import send_verification_email
        
        await send_verification_email("test@example.com", "test_token")
        
        # エラーログとコンソール出力が呼ばれることを確認
        mock_error_logger.assert_called()
        mock_print.assert_called()


class TestEmailSenderHTMLFeatures:
    """HTMLメール機能テスト"""

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender.get_mail_config')
    @patch('utils.email_sender.FastMail')
    @patch('utils.email_sender.MessageSchema')
    @patch('utils.email_sender.create_logger')
    @patch('utils.email_sender.os.getenv')
    async def test_send_verification_email_html_format(self, mock_getenv, mock_logger, mock_msg, mock_fastmail, mock_config, mock_validate, mock_enabled):
        """HTMLメール送信テスト"""
        # メール送信有効、設定有効、HTMLメール有効
        mock_enabled.return_value = True
        mock_validate.return_value = True
        mock_getenv.side_effect = lambda key, default="false": "false" if key == "PREFER_PLAIN_TEXT_EMAIL" else default
        
        # モック設定
        mock_config.return_value = Mock()
        mock_fm_instance = AsyncMock()
        mock_fastmail.return_value = mock_fm_instance
        mock_message_instance = Mock()
        mock_msg.return_value = mock_message_instance
        
        from utils.email_sender import send_verification_email
        
        await send_verification_email("test@example.com", "test_token")
        
        # HTMLメールのメッセージが作成されることを確認
        mock_msg.assert_called_once()
        call_args = mock_msg.call_args[1]
        assert call_args['subtype'].value == 'html'
        assert "DOCTYPE html" in call_args['body']
        
        # メール送信が呼ばれることを確認
        mock_fm_instance.send_message.assert_called_once_with(mock_message_instance)

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender.get_mail_config')
    @patch('utils.email_sender.FastMail')
    @patch('utils.email_sender.MessageSchema')
    @patch('utils.email_sender.create_logger')
    @patch('utils.email_sender.os.getenv')
    async def test_send_verification_email_plain_text_format(self, mock_getenv, mock_logger, mock_msg, mock_fastmail, mock_config, mock_validate, mock_enabled):
        """プレーンテキストメール送信テスト"""
        # メール送信有効、設定有効、プレーンテキストメール有効
        mock_enabled.return_value = True
        mock_validate.return_value = True
        mock_getenv.side_effect = lambda key, default="false": "true" if key == "PREFER_PLAIN_TEXT_EMAIL" else default
        
        # モック設定
        mock_config.return_value = Mock()
        mock_fm_instance = AsyncMock()
        mock_fastmail.return_value = mock_fm_instance
        mock_message_instance = Mock()
        mock_msg.return_value = mock_message_instance
        
        from utils.email_sender import send_verification_email
        
        await send_verification_email("test@example.com", "test_token")
        
        # プレーンテキストメールのメッセージが作成されることを確認
        mock_msg.assert_called_once()
        call_args = mock_msg.call_args[1]
        assert call_args['subtype'].value == 'plain'
        assert "DOCTYPE html" not in call_args['body']
        
        # メール送信が呼ばれることを確認
        mock_fm_instance.send_message.assert_called_once_with(mock_message_instance)


class TestEmailSenderRegistrationEmail:
    """登録完了メール送信テスト"""

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender.get_mail_config')
    @patch('utils.email_sender.FastMail')
    @patch('utils.email_sender.MessageSchema')
    @patch('utils.email_sender.create_logger')
    @patch('utils.email_sender.os.getenv')
    async def test_send_registration_complete_email_real_sending_html(self, mock_getenv, mock_logger, mock_msg, mock_fastmail, mock_config, mock_validate, mock_enabled):
        """登録完了メール実際送信テスト（HTML）"""
        # メール送信有効、設定有効、HTMLメール有効
        mock_enabled.return_value = True
        mock_validate.return_value = True
        mock_getenv.side_effect = lambda key, default="false": "false" if key == "PREFER_PLAIN_TEXT_EMAIL" else default
        
        # モック設定
        mock_config.return_value = Mock()
        mock_fm_instance = AsyncMock()
        mock_fastmail.return_value = mock_fm_instance
        mock_message_instance = Mock()
        mock_msg.return_value = mock_message_instance
        
        from utils.email_sender import send_registration_complete_email
        
        await send_registration_complete_email("test@example.com", "testuser")
        
        # HTMLメールのメッセージが作成されることを確認
        mock_msg.assert_called_once()
        call_args = mock_msg.call_args[1]
        assert call_args['subject'] == "【Blog API】登録完了のお知らせ"
        assert call_args['recipients'] == ["test@example.com"]
        assert call_args['subtype'].value == 'html'
        assert "DOCTYPE html" in call_args['body']
        assert "testuser" in call_args['body']
        
        # メール送信が呼ばれることを確認
        mock_fm_instance.send_message.assert_called_once_with(mock_message_instance)

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender.get_mail_config')
    @patch('utils.email_sender.FastMail')
    @patch('utils.email_sender.MessageSchema')
    @patch('utils.email_sender.create_logger')
    @patch('utils.email_sender.os.getenv')
    async def test_send_registration_complete_email_real_sending_plain(self, mock_getenv, mock_logger, mock_msg, mock_fastmail, mock_config, mock_validate, mock_enabled):
        """登録完了メール実際送信テスト（プレーンテキスト）"""
        # メール送信有効、設定有効、プレーンテキストメール有効
        mock_enabled.return_value = True
        mock_validate.return_value = True
        mock_getenv.side_effect = lambda key, default="false": "true" if key == "PREFER_PLAIN_TEXT_EMAIL" else default
        
        # モック設定
        mock_config.return_value = Mock()
        mock_fm_instance = AsyncMock()
        mock_fastmail.return_value = mock_fm_instance
        mock_message_instance = Mock()
        mock_msg.return_value = mock_message_instance
        
        from utils.email_sender import send_registration_complete_email
        
        await send_registration_complete_email("test@example.com", "testuser")
        
        # プレーンテキストメールのメッセージが作成されることを確認
        mock_msg.assert_called_once()
        call_args = mock_msg.call_args[1]
        assert call_args['subject'] == "【Blog API】登録完了のお知らせ"
        assert call_args['recipients'] == ["test@example.com"]
        assert call_args['subtype'].value == 'plain'
        assert "DOCTYPE html" not in call_args['body']
        assert "testuser" in call_args['body']
        
        # メール送信が呼ばれることを確認
        mock_fm_instance.send_message.assert_called_once_with(mock_message_instance)

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender._print_dev_mode_email')
    @patch('utils.email_sender.create_error_logger')
    async def test_send_registration_complete_email_invalid_config(self, mock_error_logger, mock_print, mock_validate, mock_enabled):
        """登録完了メール設定無効テスト"""
        # メール送信有効、設定無効
        mock_enabled.return_value = True
        mock_validate.return_value = False
        
        from utils.email_sender import send_registration_complete_email
        
        await send_registration_complete_email("test@example.com", "testuser")
        
        # エラーログと開発モード出力が呼ばれることを確認
        mock_error_logger.assert_called()
        mock_print.assert_called()


class TestEmailSenderDeletionEmail:
    """退会完了メール送信テスト"""

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender.get_mail_config')
    @patch('utils.email_sender.FastMail')
    @patch('utils.email_sender.MessageSchema')
    @patch('utils.email_sender.create_logger')
    @patch('utils.email_sender.os.getenv')
    async def test_send_account_deletion_email_real_sending_html(self, mock_getenv, mock_logger, mock_msg, mock_fastmail, mock_config, mock_validate, mock_enabled):
        """退会完了メール実際送信テスト（HTML）"""
        # メール送信有効、設定有効、HTMLメール有効
        mock_enabled.return_value = True
        mock_validate.return_value = True
        mock_getenv.side_effect = lambda key, default="false": "false" if key == "PREFER_PLAIN_TEXT_EMAIL" else default
        
        # モック設定
        mock_config.return_value = Mock()
        mock_fm_instance = AsyncMock()
        mock_fastmail.return_value = mock_fm_instance
        mock_message_instance = Mock()
        mock_msg.return_value = mock_message_instance
        
        from utils.email_sender import send_account_deletion_email
        
        await send_account_deletion_email("test@example.com", "testuser")
        
        # HTMLメールのメッセージが作成されることを確認
        mock_msg.assert_called_once()
        call_args = mock_msg.call_args[1]
        assert call_args['subject'] == "【Blog API】退会完了のお知らせ"
        assert call_args['recipients'] == ["test@example.com"]
        assert call_args['subtype'].value == 'html'
        assert "DOCTYPE html" in call_args['body']
        assert "testuser" in call_args['body']
        
        # メール送信が呼ばれることを確認
        mock_fm_instance.send_message.assert_called_once_with(mock_message_instance)

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender.get_mail_config')
    @patch('utils.email_sender.FastMail')
    @patch('utils.email_sender.MessageSchema')
    @patch('utils.email_sender.create_logger')
    @patch('utils.email_sender.os.getenv')
    async def test_send_account_deletion_email_real_sending_plain(self, mock_getenv, mock_logger, mock_msg, mock_fastmail, mock_config, mock_validate, mock_enabled):
        """退会完了メール実際送信テスト（プレーンテキスト）"""
        # メール送信有効、設定有効、プレーンテキストメール有効
        mock_enabled.return_value = True
        mock_validate.return_value = True
        mock_getenv.side_effect = lambda key, default="false": "true" if key == "PREFER_PLAIN_TEXT_EMAIL" else default
        
        # モック設定
        mock_config.return_value = Mock()
        mock_fm_instance = AsyncMock()
        mock_fastmail.return_value = mock_fm_instance
        mock_message_instance = Mock()
        mock_msg.return_value = mock_message_instance
        
        from utils.email_sender import send_account_deletion_email
        
        await send_account_deletion_email("test@example.com", "testuser")
        
        # プレーンテキストメールのメッセージが作成されることを確認
        mock_msg.assert_called_once()
        call_args = mock_msg.call_args[1]
        assert call_args['subject'] == "【Blog API】退会完了のお知らせ"
        assert call_args['recipients'] == ["test@example.com"]
        assert call_args['subtype'].value == 'plain'
        assert "DOCTYPE html" not in call_args['body']
        assert "testuser" in call_args['body']
        
        # メール送信が呼ばれることを確認
        mock_fm_instance.send_message.assert_called_once_with(mock_message_instance)

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender._print_dev_mode_email')
    @patch('utils.email_sender.create_error_logger')
    async def test_send_account_deletion_email_invalid_config(self, mock_error_logger, mock_print, mock_validate, mock_enabled):
        """退会完了メール設定無効テスト"""
        # メール送信有効、設定無効
        mock_enabled.return_value = True
        mock_validate.return_value = False
        
        from utils.email_sender import send_account_deletion_email
        
        await send_account_deletion_email("test@example.com", "testuser")
        
        # エラーログと開発モード出力が呼ばれることを確認
        mock_error_logger.assert_called()
        mock_print.assert_called()


class TestEmailSenderMailConfigExceptions:
    """メール設定例外テスト"""

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender.get_mail_config')
    @patch('utils.email_sender.create_error_logger')
    @patch('utils.email_sender._print_dev_mode_email')
    async def test_send_verification_email_config_none(self, mock_print, mock_error_logger, mock_config, mock_validate, mock_enabled):
        """確認メール送信でメール設定がNoneの場合のテスト"""
        # メール送信有効、設定有効だがconfigがNone
        mock_enabled.return_value = True
        mock_validate.return_value = True
        mock_config.return_value = None
        
        from utils.email_sender import send_verification_email
        
        await send_verification_email("test@example.com", "test_token")
        
        # エラーログが呼ばれることを確認
        mock_error_logger.assert_called()
        # 開発モード出力が呼ばれることを確認
        mock_print.assert_called()

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender.get_mail_config')
    @patch('utils.email_sender.create_error_logger')
    @patch('utils.email_sender._print_dev_mode_email')
    async def test_send_registration_complete_email_config_none(self, mock_print, mock_error_logger, mock_config, mock_validate, mock_enabled):
        """登録完了メール送信でメール設定がNoneの場合のテスト"""
        # メール送信有効、設定有効だがconfigがNone
        mock_enabled.return_value = True
        mock_validate.return_value = True
        mock_config.return_value = None
        
        from utils.email_sender import send_registration_complete_email
        
        await send_registration_complete_email("test@example.com", "testuser")
        
        # エラーログが呼ばれることを確認
        mock_error_logger.assert_called()
        # 開発モード出力が呼ばれることを確認
        mock_print.assert_called()

    @patch('utils.email_sender._is_email_enabled')
    @patch('utils.email_sender._validate_mail_config')
    @patch('utils.email_sender.get_mail_config')
    @patch('utils.email_sender.create_error_logger')
    @patch('utils.email_sender._print_dev_mode_email')
    async def test_send_account_deletion_email_config_none(self, mock_print, mock_error_logger, mock_config, mock_validate, mock_enabled):
        """退会完了メール送信でメール設定がNoneの場合のテスト"""
        # メール送信有効、設定有効だがconfigがNone
        mock_enabled.return_value = True
        mock_validate.return_value = True
        mock_config.return_value = None
        
        from utils.email_sender import send_account_deletion_email
        
        await send_account_deletion_email("test@example.com", "testuser")
        
        # エラーログが呼ばれることを確認
        mock_error_logger.assert_called()
        # 開発モード出力が呼ばれることを確認
        mock_print.assert_called()