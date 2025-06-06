"""utils/email_validator.pyの単体テスト"""
import pytest
from unittest.mock import patch, Mock
import os


class TestEmailValidatorDomainRestriction:
    """メールアドレスドメイン制限テスト"""

    @patch('utils.email_validator.os.getenv')
    @patch('utils.email_validator.create_logger')
    def test_domain_restriction_disabled(self, mock_logger, mock_getenv):
        """ドメイン制限無効時のテスト"""
        # ドメイン制限を無効に設定
        mock_getenv.side_effect = lambda key, default="": {
            "ENABLE_DOMAIN_RESTRICTION": "false"
        }.get(key, default)
        
        from utils.email_validator import is_valid_email_domain
        
        # どのドメインでもTrueが返される
        assert is_valid_email_domain("test@example.com") == True
        assert is_valid_email_domain("user@gmail.com") == True
        assert is_valid_email_domain("admin@company.org") == True
        
        # ログが出力されることを確認
        mock_logger.assert_called()

    @patch('utils.email_validator.os.getenv')
    @patch('utils.email_validator.create_logger')
    def test_domain_restriction_enabled_with_allowed_domains(self, mock_logger, mock_getenv):
        """ドメイン制限有効時（許可ドメインあり）のテスト"""
        # ドメイン制限を有効に設定
        mock_getenv.side_effect = lambda key, default="": {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com, gmail.com, company.org"
        }.get(key, default)
        
        from utils.email_validator import is_valid_email_domain
        
        # 許可されたドメイン
        assert is_valid_email_domain("test@example.com") == True
        assert is_valid_email_domain("user@gmail.com") == True
        assert is_valid_email_domain("admin@company.org") == True
        
        # 許可されていないドメイン
        assert is_valid_email_domain("test@yahoo.com") == False
        assert is_valid_email_domain("user@hotmail.com") == False

    @patch('utils.email_validator.os.getenv')
    @patch('utils.email_validator.create_logger')
    def test_domain_restriction_enabled_no_allowed_domains(self, mock_logger, mock_getenv):
        """ドメイン制限有効時（許可ドメインなし）のテスト"""
        # ドメイン制限を有効、許可ドメインを空に設定
        mock_getenv.side_effect = lambda key, default="": {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": ""
        }.get(key, default)
        
        from utils.email_validator import is_valid_email_domain
        
        # 許可ドメインが設定されていない場合はすべて許可
        assert is_valid_email_domain("test@example.com") == True
        assert is_valid_email_domain("user@gmail.com") == True
        
        # ログが出力されることを確認
        mock_logger.assert_called()

    @patch('utils.email_validator.os.getenv')
    @patch('utils.email_validator.create_logger')
    def test_case_insensitive_domain_matching(self, mock_logger, mock_getenv):
        """大文字小文字を区別しないドメインマッチングのテスト"""
        mock_getenv.side_effect = lambda key, default="": {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "Example.COM, Gmail.Com"
        }.get(key, default)
        
        from utils.email_validator import is_valid_email_domain
        
        # 大文字小文字混在でも正しくマッチング
        assert is_valid_email_domain("test@example.com") == True
        assert is_valid_email_domain("test@Example.COM") == True
        assert is_valid_email_domain("test@GMAIL.COM") == True
        assert is_valid_email_domain("test@gmail.com") == True

    @patch('utils.email_validator.os.getenv')
    @patch('utils.email_validator.create_logger')
    def test_invalid_email_format(self, mock_logger, mock_getenv):
        """不正なメールアドレス形式のテスト"""
        mock_getenv.side_effect = lambda key, default="": {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }.get(key, default)
        
        from utils.email_validator import is_valid_email_domain
        
        # @マークがない
        assert is_valid_email_domain("testexample.com") == False
        # @マークが複数
        assert is_valid_email_domain("test@domain@example.com") == False
        # ドメイン部分がない
        assert is_valid_email_domain("test@") == False
        # 空文字列
        assert is_valid_email_domain("") == False

    @patch('utils.email_validator.os.getenv')
    @patch('utils.email_validator.create_logger')
    def test_whitespace_handling_in_domains(self, mock_logger, mock_getenv):
        """ドメインリストの空白文字処理テスト"""
        mock_getenv.side_effect = lambda key, default="": {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": " example.com , gmail.com , yahoo.com "
        }.get(key, default)
        
        from utils.email_validator import is_valid_email_domain
        
        # 空白文字が正しく除去される
        assert is_valid_email_domain("test@example.com") == True
        assert is_valid_email_domain("test@gmail.com") == True
        assert is_valid_email_domain("test@yahoo.com") == True


class TestEmailValidatorEdgeCases:
    """メールバリデーターエッジケーステスト"""

    @patch('utils.email_validator.os.getenv')
    @patch('utils.email_validator.create_logger')
    def test_empty_domain_list_handling(self, mock_logger, mock_getenv):
        """空のドメインリスト処理テスト"""
        mock_getenv.side_effect = lambda key, default="": {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": ",,,"
        }.get(key, default)
        
        from utils.email_validator import is_valid_email_domain
        
        # 空のエントリはフィルタリングされ、すべて許可される
        assert is_valid_email_domain("test@example.com") == True

    @patch('utils.email_validator.os.getenv')
    @patch('utils.email_validator.create_logger')
    def test_single_domain(self, mock_logger, mock_getenv):
        """単一ドメイン設定のテスト"""
        mock_getenv.side_effect = lambda key, default="": {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "company.com"
        }.get(key, default)
        
        from utils.email_validator import is_valid_email_domain
        
        assert is_valid_email_domain("employee@company.com") == True
        assert is_valid_email_domain("user@external.com") == False

    @patch('utils.email_validator.os.getenv')
    @patch('utils.email_validator.create_logger')
    def test_unicode_domains(self, mock_logger, mock_getenv):
        """Unicode文字を含むドメインのテスト"""
        mock_getenv.side_effect = lambda key, default="": {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }.get(key, default)
        
        from utils.email_validator import is_valid_email_domain
        
        # 通常のASCIIドメイン
        assert is_valid_email_domain("test@example.com") == True
        # Unicode文字を含むメールアドレス（実際のケースに近い）
        # 注：実際のメールアドレスでは国際化ドメイン名は別の方法で処理される
        assert is_valid_email_domain("テスト@example.com") == True


class TestEmailValidatorLogging:
    """メールバリデーターログ出力テスト"""

    @patch('utils.email_validator.os.getenv')
    @patch('utils.email_validator.create_logger')
    def test_logging_for_allowed_domain(self, mock_logger, mock_getenv):
        """許可されたドメインのログ出力テスト"""
        mock_getenv.side_effect = lambda key, default="": {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }.get(key, default)
        
        from utils.email_validator import is_valid_email_domain
        
        is_valid_email_domain("test@example.com")
        
        # 許可ドメインのログが出力されることを確認
        mock_logger.assert_called()
        call_args = [call[0][0] for call in mock_logger.call_args_list]
        assert any("許可されたドメインです" in arg for arg in call_args)

    @patch('utils.email_validator.os.getenv')
    @patch('utils.email_validator.create_logger')
    def test_logging_for_disallowed_domain(self, mock_logger, mock_getenv):
        """許可されていないドメインのログ出力テスト"""
        mock_getenv.side_effect = lambda key, default="": {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }.get(key, default)
        
        from utils.email_validator import is_valid_email_domain
        
        is_valid_email_domain("test@notallowed.com")
        
        # 非許可ドメインのログが出力されることを確認
        mock_logger.assert_called()
        call_args = [call[0][0] for call in mock_logger.call_args_list]
        assert any("許可されていないドメインです" in arg for arg in call_args)

    @patch('utils.email_validator.os.getenv')
    @patch('utils.email_validator.create_logger')
    def test_logging_for_invalid_format(self, mock_logger, mock_getenv):
        """不正形式のメールアドレスのログ出力テスト"""
        mock_getenv.side_effect = lambda key, default="": {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }.get(key, default)
        
        from utils.email_validator import is_valid_email_domain
        
        is_valid_email_domain("invalid-email")
        
        # 不正形式のログが出力されることを確認
        mock_logger.assert_called()
        call_args = [call[0][0] for call in mock_logger.call_args_list]
        assert any("不正なメールアドレス形式" in arg for arg in call_args)