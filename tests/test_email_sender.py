"""
Email Sender Module Test Suite

Comprehensive test coverage for utils/email_sender.py module including:
- Configuration validation
- Email sending functionality
- Error handling scenarios
- Environment variable handling
- Development mode testing
- Production mode simulation
- URL encoding and formatting
"""

import pytest
import os
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Optional

# Import the module under test
import sys
sys.path.append('/Users/tatu/Documents/GitHub/blog-api-main')

from utils.email_sender import (
    get_mail_config,
    send_verification_email,
    send_registration_complete_email,
    send_account_deletion_email,
    _print_dev_mode_email,
    _is_email_enabled,
    _validate_mail_config
)

from fastapi_mail import ConnectionConfig, MessageSchema, MessageType


class TestEmailSenderHelperFunctions:
    """Test helper functions for email configuration and validation"""
    
    def test_get_mail_config_with_default_values(self):
        """Test get_mail_config with default environment values"""
        # MAIL_FROM must be a valid email for ConnectionConfig validation
        env_vars = {
            "MAIL_FROM": "default@example.com"  # Valid email required
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = get_mail_config()
            
            assert isinstance(config, ConnectionConfig)
            assert config.MAIL_USERNAME == ""
            assert config.MAIL_PASSWORD == ""
            assert config.MAIL_FROM == "default@example.com"
            assert config.MAIL_PORT == 587
            assert config.MAIL_SERVER == "smtp.gmail.com"
            assert config.MAIL_STARTTLS is True
            assert config.MAIL_SSL_TLS is False
            assert config.USE_CREDENTIALS is True
            assert config.VALIDATE_CERTS is True
    
    def test_get_mail_config_with_custom_values(self):
        """Test get_mail_config with custom environment values"""
        env_vars = {
            "MAIL_USERNAME": "test@example.com",
            "MAIL_PASSWORD": "password123",
            "MAIL_FROM": "noreply@example.com",
            "MAIL_PORT": "465",
            "MAIL_SERVER": "smtp.example.com",
            "MAIL_STARTTLS": "false",
            "MAIL_SSL_TLS": "true"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = get_mail_config()
            
            assert config.MAIL_USERNAME == "test@example.com"
            assert config.MAIL_PASSWORD == "password123"
            assert config.MAIL_FROM == "noreply@example.com"
            assert config.MAIL_PORT == 465
            assert config.MAIL_SERVER == "smtp.example.com"
            assert config.MAIL_STARTTLS is False
            assert config.MAIL_SSL_TLS is True
    
    def test_get_mail_config_port_conversion(self):
        """Test port number conversion from string to integer"""
        env_vars = {
            "MAIL_PORT": "993",
            "MAIL_FROM": "test@example.com"  # Valid email required
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = get_mail_config()
            assert config.MAIL_PORT == 993
            assert isinstance(config.MAIL_PORT, int)
    
    def test_get_mail_config_boolean_conversion(self):
        """Test boolean conversion for STARTTLS and SSL_TLS"""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("invalid", False)
        ]
        
        for value, expected in test_cases:
            env_vars = {
                "MAIL_STARTTLS": value,
                "MAIL_FROM": "test@example.com"  # Valid email required
            }
            with patch.dict(os.environ, env_vars, clear=True):
                config = get_mail_config()
                assert config.MAIL_STARTTLS is expected
    
    def test_is_email_enabled_true(self):
        """Test _is_email_enabled returns True when enabled"""
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "true"}):
            assert _is_email_enabled() is True
    
    def test_is_email_enabled_false(self):
        """Test _is_email_enabled returns False when disabled"""
        test_cases = ["false", "False", "FALSE", "0", "no", "disabled", ""]
        
        for value in test_cases:
            with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": value}):
                assert _is_email_enabled() is False
    
    def test_is_email_enabled_default(self):
        """Test _is_email_enabled default behavior when env var not set"""
        with patch.dict(os.environ, {}, clear=True):
            assert _is_email_enabled() is False
    
    def test_validate_mail_config_valid(self):
        """Test _validate_mail_config with valid configuration"""
        env_vars = {
            "MAIL_USERNAME": "user@example.com",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            assert _validate_mail_config() is True
    
    def test_validate_mail_config_missing_username(self):
        """Test _validate_mail_config with missing username"""
        env_vars = {
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            assert _validate_mail_config() is False
    
    def test_validate_mail_config_missing_password(self):
        """Test _validate_mail_config with missing password"""
        env_vars = {
            "MAIL_USERNAME": "user@example.com",
            "MAIL_FROM": "from@example.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            assert _validate_mail_config() is False
    
    def test_validate_mail_config_missing_from(self):
        """Test _validate_mail_config with missing from address"""
        env_vars = {
            "MAIL_USERNAME": "user@example.com",
            "MAIL_PASSWORD": "password"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            assert _validate_mail_config() is False
    
    def test_validate_mail_config_empty_values(self):
        """Test _validate_mail_config with empty string values"""
        env_vars = {
            "MAIL_USERNAME": "",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            assert _validate_mail_config() is False
    
    def test_validate_mail_config_all_empty(self):
        """Test _validate_mail_config with all empty values"""
        with patch.dict(os.environ, {}, clear=True):
            assert _validate_mail_config() is False


class TestPrintDevModeEmail:
    """Test the development mode email printing function"""
    
    def test_print_dev_mode_email_basic(self, capsys):
        """Test basic dev mode email printing"""
        _print_dev_mode_email(
            "Test Title",
            "test@example.com",
            "Test Subject",
            "Test content"
        )
        
        captured = capsys.readouterr()
        assert "📧 Test Title" in captured.out
        assert "=" * 60 in captured.out
        assert "宛先: test@example.com" in captured.out
        assert "件名: Test Subject" in captured.out
        assert "メール内容:" in captured.out
        assert "Test content" in captured.out
    
    def test_print_dev_mode_email_with_verification_url(self, capsys):
        """Test dev mode email printing with verification URL"""
        verification_url = "http://localhost:8080/verify?token=abc123"
        
        _print_dev_mode_email(
            "Verification Email",
            "user@example.com",
            "Verify Your Email",
            "Please verify your email",
            verification_url
        )
        
        captured = capsys.readouterr()
        assert "📧 Verification Email" in captured.out
        assert f"確認URL: {verification_url}" in captured.out
    
    def test_print_dev_mode_email_without_verification_url(self, capsys):
        """Test dev mode email printing without verification URL"""
        _print_dev_mode_email(
            "Regular Email",
            "user@example.com",
            "Regular Subject",
            "Regular content"
        )
        
        captured = capsys.readouterr()
        assert "確認URL:" not in captured.out


class TestSendVerificationEmail:
    """Test the send_verification_email function"""
    
    @pytest.fixture
    def setup_env_vars(self):
        """Setup common environment variables for tests"""
        env_vars = {
            "CORS_ORIGINS": "https://example.com",
            "LOCAL_CORS_ORIGINS": "",
            "SERVER_PORT": "8080"
        }
        return env_vars
    
    @pytest.mark.asyncio
    async def test_send_verification_email_dev_mode_disabled(self, capsys):
        """Test verification email in development mode (email disabled)"""
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "false"}):
            with patch('utils.email_sender.create_logger') as mock_logger:
                await send_verification_email("test@example.com", "token123")
                
                # Check that logger was called
                mock_logger.assert_called()
                
                # Check console output
                captured = capsys.readouterr()
                assert "📧 メール送信（開発モード）" in captured.out
                assert "test@example.com" in captured.out
                assert "token123" in captured.out
    
    @pytest.mark.asyncio
    async def test_send_verification_email_invalid_config(self, capsys):
        """Test verification email with invalid mail configuration"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "true",
            "MAIL_USERNAME": "",  # Invalid config
            "MAIL_PASSWORD": "",
            "MAIL_FROM": ""
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.create_error_logger') as mock_error_logger:
                await send_verification_email("test@example.com", "token123")
                
                # Check that error logger was called
                mock_error_logger.assert_called_with("メール設定が不完全です。開発モードでコンソール出力します。")
                
                # Check console output for dev mode fallback
                captured = capsys.readouterr()
                assert "📧 メール送信（開発モード - 設定不完全）" in captured.out
    
    @pytest.mark.asyncio
    async def test_send_verification_email_url_generation_local(self):
        """Test verification URL generation for local environment"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "false",  # To avoid actual sending
            "LOCAL_CORS_ORIGINS": "http://localhost:3000",
            "SERVER_PORT": "8080"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.create_logger') as mock_logger:
                await send_verification_email("test@example.com", "token with spaces")
                
                # Check that URL generation log was called
                calls = [call.args[0] for call in mock_logger.call_args_list]
                url_log = next((call for call in calls if "生成された確認URL" in call), None)
                assert url_log is not None
                assert "127.0.0.1:8080" in url_log
                assert "token%20with%20spaces" in url_log  # URL encoded
    
    @pytest.mark.asyncio
    async def test_send_verification_email_url_generation_production(self):
        """Test verification URL generation for production environment"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "false",  # To avoid actual sending
            "CORS_ORIGINS": "https://production.com",
            "SERVER_PORT": "8080"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            # Need to patch the module-level variables since they're imported at module load
            with patch('utils.email_sender.LOCAL_CORS_ORIGINS', None):
                with patch('utils.email_sender.CORS_ORIGINS', "https://production.com"):
                    with patch('utils.email_sender.create_logger') as mock_logger:
                        await send_verification_email("test@example.com", "token123")
                        
                        # Check that URL generation log was called
                        calls = [call.args[0] for call in mock_logger.call_args_list]
                        url_log = next((call for call in calls if "生成された確認URL" in call), None)
                        assert url_log is not None
                        # When LOCAL_CORS_ORIGINS is None, should use CORS_ORIGINS
                        assert "https://production.com" in url_log
    
    @pytest.mark.asyncio
    async def test_send_verification_email_successful_sending(self):
        """Test successful email sending in production mode"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "true",
            "MAIL_USERNAME": "user@example.com",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com",
            "PREFER_PLAIN_TEXT_EMAIL": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.get_mail_config') as mock_config:
                with patch('utils.email_sender.FastMail') as mock_fastmail:
                    with patch('utils.email_sender.create_logger') as mock_logger:
                        # Setup mocks
                        mock_config.return_value = Mock(spec=ConnectionConfig)
                        mock_mail_instance = AsyncMock()
                        mock_fastmail.return_value = mock_mail_instance
                        
                        await send_verification_email("test@example.com", "token123")
                        
                        # Verify FastMail was called
                        mock_fastmail.assert_called_once()
                        mock_mail_instance.send_message.assert_called_once()
                        
                        # Verify success log
                        mock_logger.assert_called()
                        calls = [call.args[0] for call in mock_logger.call_args_list]
                        success_log = next((call for call in calls if "確認メールを送信しました" in call), None)
                        assert success_log is not None
    
    @pytest.mark.asyncio
    async def test_send_verification_email_plain_text_mode(self):
        """Test email sending in plain text mode"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "true",
            "MAIL_USERNAME": "user@example.com",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com",
            "PREFER_PLAIN_TEXT_EMAIL": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.get_mail_config') as mock_config:
                with patch('utils.email_sender.FastMail') as mock_fastmail:
                    with patch('utils.email_sender.MessageSchema') as mock_message_schema:
                        # Setup mocks
                        mock_config.return_value = Mock(spec=ConnectionConfig)
                        mock_mail_instance = AsyncMock()
                        mock_fastmail.return_value = mock_mail_instance
                        
                        await send_verification_email("test@example.com", "token123")
                        
                        # Verify MessageSchema was called with plain text subtype
                        mock_message_schema.assert_called_once()
                        call_kwargs = mock_message_schema.call_args[1]
                        assert call_kwargs['subtype'] == MessageType.plain
    
    @pytest.mark.asyncio
    async def test_send_verification_email_html_mode(self):
        """Test email sending in HTML mode"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "true",
            "MAIL_USERNAME": "user@example.com",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com",
            "PREFER_PLAIN_TEXT_EMAIL": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.get_mail_config') as mock_config:
                with patch('utils.email_sender.FastMail') as mock_fastmail:
                    with patch('utils.email_sender.MessageSchema') as mock_message_schema:
                        # Setup mocks
                        mock_config.return_value = Mock(spec=ConnectionConfig)
                        mock_mail_instance = AsyncMock()
                        mock_fastmail.return_value = mock_mail_instance
                        
                        await send_verification_email("test@example.com", "token123")
                        
                        # Verify MessageSchema was called with HTML subtype
                        mock_message_schema.assert_called_once()
                        call_kwargs = mock_message_schema.call_args[1]
                        assert call_kwargs['subtype'] == MessageType.html
    
    @pytest.mark.asyncio
    async def test_send_verification_email_exception_handling(self, capsys):
        """Test exception handling during email sending"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "true",
            "MAIL_USERNAME": "user@example.com",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.get_mail_config') as mock_config:
                with patch('utils.email_sender.create_error_logger') as mock_error_logger:
                    # Setup mock to raise exception
                    mock_config.side_effect = Exception("Connection failed")
                    
                    await send_verification_email("test@example.com", "token123")
                    
                    # Verify error was logged
                    mock_error_logger.assert_called_with("メール送信エラー: Connection failed")
                    
                    # Verify fallback to dev mode
                    captured = capsys.readouterr()
                    assert "📧 メール送信（エラー発生 - 開発モード）" in captured.out
    
    @pytest.mark.asyncio
    async def test_send_verification_email_config_none_exception(self, capsys):
        """Test handling when mail config returns None"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "true",
            "MAIL_USERNAME": "user@example.com",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.get_mail_config') as mock_config:
                with patch('utils.email_sender.create_error_logger') as mock_error_logger:
                    # Setup mock to return None
                    mock_config.return_value = None
                    
                    await send_verification_email("test@example.com", "token123")
                    
                    # Verify error was logged
                    mock_error_logger.assert_called_with("メール送信エラー: メール設定が正しく設定されていません")


class TestSendRegistrationCompleteEmail:
    """Test the send_registration_complete_email function"""
    
    @pytest.mark.asyncio
    async def test_send_registration_complete_email_dev_mode(self, capsys):
        """Test registration complete email in development mode"""
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "false"}):
            with patch('utils.email_sender.create_logger') as mock_logger:
                await send_registration_complete_email("test@example.com", "testuser")
                
                # Check console output
                captured = capsys.readouterr()
                assert "📧 登録完了メール送信（開発モード）" in captured.out
                assert "test@example.com" in captured.out
                assert "testuser" in captured.out
                assert "【Blog API】登録完了のお知らせ" in captured.out
    
    @pytest.mark.asyncio
    async def test_send_registration_complete_email_invalid_config(self, capsys):
        """Test registration complete email with invalid configuration"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "true",
            "MAIL_USERNAME": "",
            "MAIL_PASSWORD": "",
            "MAIL_FROM": ""
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.create_error_logger') as mock_error_logger:
                await send_registration_complete_email("test@example.com", "testuser")
                
                mock_error_logger.assert_called_with("メール設定が不完全です。開発モードでコンソール出力します。")
                
                captured = capsys.readouterr()
                assert "📧 登録完了メール送信（開発モード - 設定不完全）" in captured.out
    
    @pytest.mark.asyncio
    async def test_send_registration_complete_email_successful(self):
        """Test successful registration complete email sending"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "true",
            "MAIL_USERNAME": "user@example.com",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com",
            "PREFER_PLAIN_TEXT_EMAIL": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.get_mail_config') as mock_config:
                with patch('utils.email_sender.FastMail') as mock_fastmail:
                    with patch('utils.email_sender.create_logger') as mock_logger:
                        mock_config.return_value = Mock(spec=ConnectionConfig)
                        mock_mail_instance = AsyncMock()
                        mock_fastmail.return_value = mock_mail_instance
                        
                        await send_registration_complete_email("test@example.com", "testuser")
                        
                        mock_fastmail.assert_called_once()
                        mock_mail_instance.send_message.assert_called_once()
                        
                        calls = [call.args[0] for call in mock_logger.call_args_list]
                        success_log = next((call for call in calls if "登録完了メールを送信しました" in call), None)
                        assert success_log is not None
    
    @pytest.mark.asyncio
    async def test_send_registration_complete_email_exception(self, capsys):
        """Test exception handling in registration complete email"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "true",
            "MAIL_USERNAME": "user@example.com",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.get_mail_config') as mock_config:
                with patch('utils.email_sender.create_error_logger') as mock_error_logger:
                    mock_config.side_effect = Exception("SMTP error")
                    
                    await send_registration_complete_email("test@example.com", "testuser")
                    
                    mock_error_logger.assert_called_with("登録完了メール送信エラー: SMTP error")
                    
                    captured = capsys.readouterr()
                    assert "📧 登録完了メール送信（エラー発生 - 開発モード）" in captured.out


class TestSendAccountDeletionEmail:
    """Test the send_account_deletion_email function"""
    
    @pytest.mark.asyncio
    async def test_send_account_deletion_email_dev_mode(self, capsys):
        """Test account deletion email in development mode"""
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "false"}):
            with patch('utils.email_sender.create_logger') as mock_logger:
                await send_account_deletion_email("test@example.com", "testuser")
                
                captured = capsys.readouterr()
                assert "📧 退会完了メール送信（開発モード）" in captured.out
                assert "test@example.com" in captured.out
                assert "testuser" in captured.out
                assert "【Blog API】退会完了のお知らせ" in captured.out
    
    @pytest.mark.asyncio
    async def test_send_account_deletion_email_invalid_config(self, capsys):
        """Test account deletion email with invalid configuration"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "true",
            "MAIL_USERNAME": "",
            "MAIL_PASSWORD": "",
            "MAIL_FROM": ""
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.create_error_logger') as mock_error_logger:
                await send_account_deletion_email("test@example.com", "testuser")
                
                mock_error_logger.assert_called_with("メール設定が不完全です。開発モードでコンソール出力します。")
                
                captured = capsys.readouterr()
                assert "📧 退会完了メール送信（開発モード - 設定不完全）" in captured.out
    
    @pytest.mark.asyncio
    async def test_send_account_deletion_email_successful(self):
        """Test successful account deletion email sending"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "true",
            "MAIL_USERNAME": "user@example.com",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com",
            "PREFER_PLAIN_TEXT_EMAIL": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.get_mail_config') as mock_config:
                with patch('utils.email_sender.FastMail') as mock_fastmail:
                    with patch('utils.email_sender.MessageSchema') as mock_message_schema:
                        with patch('utils.email_sender.create_logger') as mock_logger:
                            mock_config.return_value = Mock(spec=ConnectionConfig)
                            mock_mail_instance = AsyncMock()
                            mock_fastmail.return_value = mock_mail_instance
                            
                            await send_account_deletion_email("test@example.com", "testuser")
                            
                            mock_fastmail.assert_called_once()
                            mock_mail_instance.send_message.assert_called_once()
                            
                            # Verify plain text mode
                            call_kwargs = mock_message_schema.call_args[1]
                            assert call_kwargs['subtype'] == MessageType.plain
                            
                            calls = [call.args[0] for call in mock_logger.call_args_list]
                            success_log = next((call for call in calls if "退会完了メールを送信しました" in call), None)
                            assert success_log is not None
    
    @pytest.mark.asyncio
    async def test_send_account_deletion_email_exception(self, capsys):
        """Test exception handling in account deletion email"""
        env_vars = {
            "ENABLE_EMAIL_SENDING": "true",
            "MAIL_USERNAME": "user@example.com",
            "MAIL_PASSWORD": "password",
            "MAIL_FROM": "from@example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_sender.get_mail_config') as mock_config:
                with patch('utils.email_sender.create_error_logger') as mock_error_logger:
                    mock_config.side_effect = Exception("Network timeout")
                    
                    await send_account_deletion_email("test@example.com", "testuser")
                    
                    mock_error_logger.assert_called_with("退会完了メール送信エラー: Network timeout")
                    
                    captured = capsys.readouterr()
                    assert "📧 退会完了メール送信（エラー発生 - 開発モード）" in captured.out


class TestEmailContentAndFormatting:
    """Test email content generation and formatting"""
    
    @pytest.mark.asyncio
    async def test_verification_email_content_includes_required_elements(self, capsys):
        """Test that verification email includes all required content elements"""
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "false"}):
            await send_verification_email("test@example.com", "token123")
            
            captured = capsys.readouterr()
            
            # Check for required content elements
            assert "メールアドレスの確認をお願いします" in captured.out
            assert "初期パスワード：temp_password_123" in captured.out
            assert "このリンクの有効時間は24時間です" in captured.out
            assert "Blog API チーム" in captured.out
    
    @pytest.mark.asyncio
    async def test_registration_complete_email_content(self, capsys):
        """Test registration complete email content elements"""
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "false"}):
            await send_registration_complete_email("test@example.com", "testuser")
            
            captured = capsys.readouterr()
            
            assert "こんにちは、testuser" in captured.out
            assert "Blog APIへのご登録が完了しました" in captured.out
            assert "ブログ記事の作成・編集・削除" in captured.out
            assert "コメントの投稿・管理" in captured.out
            assert "プロフィールの管理" in captured.out
    
    @pytest.mark.asyncio
    async def test_account_deletion_email_content(self, capsys):
        """Test account deletion email content elements"""
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "false"}):
            await send_account_deletion_email("test@example.com", "testuser")
            
            captured = capsys.readouterr()
            
            assert "こんにちは、testuser" in captured.out
            assert "退会手続きが完了いたしました" in captured.out
            assert "ユーザーアカウントの削除" in captured.out
            assert "投稿された記事の削除" in captured.out
            assert "個人情報の削除" in captured.out
            assert "新規登録はいつでも可能です" in captured.out


class TestEnvironmentVariableHandling:
    """Test environment variable handling and edge cases"""
    
    def test_cors_origins_handling(self):
        """Test CORS origins environment variable handling"""
        # Test with CORS_ORIGINS set
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://example.com"}):
            from utils import email_sender
            # This would be used in URL generation
            assert os.getenv("CORS_ORIGINS") == "https://example.com"
    
    def test_server_port_default(self):
        """Test SERVER_PORT default value"""
        with patch.dict(os.environ, {}, clear=True):
            from utils import email_sender
            assert os.getenv("SERVER_PORT", "8080") == "8080"
    
    def test_server_port_custom(self):
        """Test SERVER_PORT custom value"""
        with patch.dict(os.environ, {"SERVER_PORT": "3000"}):
            from utils import email_sender
            assert os.getenv("SERVER_PORT", "8080") == "3000"


class TestEdgeCasesAndErrorScenarios:
    """Test edge cases and error scenarios"""
    
    @pytest.mark.asyncio
    async def test_email_with_special_characters(self, capsys):
        """Test email sending with special characters in email and token"""
        special_email = "test+user@example.com"
        special_token = "token/with+special=chars&more"
        
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "false"}):
            await send_verification_email(special_email, special_token)
            
            captured = capsys.readouterr()
            assert special_email in captured.out
            # Token should be URL encoded in the URL
            assert "token%2Fwith%2Bspecial%3Dchars%26more" in captured.out
    
    @pytest.mark.asyncio
    async def test_empty_string_parameters(self, capsys):
        """Test functions with empty string parameters"""
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "false"}):
            await send_verification_email("", "")
            
            captured = capsys.readouterr()
            assert "宛先: " in captured.out  # Empty email
    
    @pytest.mark.asyncio
    async def test_unicode_characters_in_username(self, capsys):
        """Test email functions with unicode characters in username"""
        unicode_username = "テストユーザー"
        
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "false"}):
            await send_registration_complete_email("test@example.com", unicode_username)
            
            captured = capsys.readouterr()
            assert unicode_username in captured.out
    
    def test_mail_config_with_invalid_port(self):
        """Test mail config with non-numeric port"""
        env_vars = {
            "MAIL_PORT": "invalid",
            "MAIL_FROM": "test@example.com"
        }
        with patch.dict(os.environ, env_vars):
            with pytest.raises(ValueError):
                get_mail_config()
    
    def test_mail_config_with_invalid_email_format(self):
        """Test mail config with invalid email format"""
        env_vars = {
            "MAIL_FROM": "invalid-email-format"
        }
        with patch.dict(os.environ, env_vars):
            with pytest.raises(Exception):  # Pydantic validation error
                get_mail_config()


class TestIntegrationScenarios:
    """Test integration scenarios and realistic use cases"""
    
    @pytest.mark.asyncio
    async def test_complete_user_registration_flow(self, capsys):
        """Test complete user registration email flow"""
        email = "newuser@example.com"
        token = "verification_token_123"
        username = "newuser"
        
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "false"}):
            # Step 1: Send verification email
            await send_verification_email(email, token)
            
            # Step 2: Send registration complete email
            await send_registration_complete_email(email, username)
            
            captured = capsys.readouterr()
            
            # Verify both emails were processed
            assert "メール送信（開発モード）" in captured.out
            assert "登録完了メール送信（開発モード）" in captured.out
            assert email in captured.out
            assert username in captured.out
    
    @pytest.mark.asyncio
    async def test_user_deletion_flow(self, capsys):
        """Test user account deletion email flow"""
        email = "deleteme@example.com"
        username = "deleteme"
        
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "false"}):
            await send_account_deletion_email(email, username)
            
            captured = capsys.readouterr()
            
            assert "退会完了メール送信（開発モード）" in captured.out
            assert email in captured.out
            assert username in captured.out


# Performance and Load Testing Helpers
class TestPerformanceConsiderations:
    """Test performance-related aspects"""
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_emails(self):
        """Test handling multiple concurrent email requests"""
        tasks = []
        
        for i in range(10):
            task = send_verification_email(f"user{i}@example.com", f"token{i}")
            tasks.append(task)
        
        with patch.dict(os.environ, {"ENABLE_EMAIL_SENDING": "false"}):
            # All should complete without errors
            await asyncio.gather(*tasks)
    
    def test_config_creation_efficiency(self):
        """Test that config creation is efficient for repeated calls"""
        # Multiple calls should not cause issues
        for _ in range(100):
            config = get_mail_config()
            assert isinstance(config, ConnectionConfig)


if __name__ == "__main__":
    # Run specific test groups
    pytest.main([__file__, "-v", "--tb=short"])
