"""
Email Validator Module Test Suite

Comprehensive test coverage for utils/email_validator.py module including:
- Domain restriction functionality
- Environment variable handling
- Valid and invalid email domain checking
- Configuration scenarios
- Edge cases and error handling
- Logging verification
"""

import pytest
import os
from unittest.mock import patch, Mock

# Import the module under test
import sys
sys.path.append('/Users/tatu/Documents/GitHub/blog-api-main')

from utils.email_validator import is_valid_email_domain


class TestEmailValidatorDomainRestrictionDisabled:
    """Test email validation when domain restriction is disabled"""
    
    def test_domain_restriction_disabled_returns_true_for_any_email(self):
        """Test that any email is allowed when domain restriction is disabled"""
        with patch.dict(os.environ, {"ENABLE_DOMAIN_RESTRICTION": "false"}):
            with patch('utils.email_validator.create_logger') as mock_logger:
                result = is_valid_email_domain("test@example.com")
                
                assert result is True
                mock_logger.assert_called_once_with("ドメイン制限は無効です。すべてのドメインを許可: test@example.com")
    
    def test_domain_restriction_disabled_by_default(self):
        """Test that domain restriction is disabled by default"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('utils.email_validator.create_logger') as mock_logger:
                result = is_valid_email_domain("user@anydomain.org")
                
                assert result is True
                mock_logger.assert_called_once_with("ドメイン制限は無効です。すべてのドメインを許可: user@anydomain.org")
    
    def test_domain_restriction_disabled_various_values(self):
        """Test various ways to disable domain restriction"""
        disable_values = ["false", "False", "FALSE", "0", "no", "disabled", ""]
        
        for value in disable_values:
            with patch.dict(os.environ, {"ENABLE_DOMAIN_RESTRICTION": value}):
                with patch('utils.email_validator.create_logger'):
                    result = is_valid_email_domain("test@example.com")
                    assert result is True, f"Failed for value: {value}"
    
    def test_domain_restriction_disabled_with_invalid_email_format(self):
        """Test disabled restriction with invalid email format"""
        with patch.dict(os.environ, {"ENABLE_DOMAIN_RESTRICTION": "false"}):
            with patch('utils.email_validator.create_logger') as mock_logger:
                result = is_valid_email_domain("invalid-email")
                
                assert result is True
                mock_logger.assert_called_once_with("ドメイン制限は無効です。すべてのドメインを許可: invalid-email")


class TestEmailValidatorDomainRestrictionEnabled:
    """Test email validation when domain restriction is enabled"""
    
    def test_domain_restriction_enabled_with_valid_domain(self):
        """Test email validation with allowed domain"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com,test.org"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger') as mock_logger:
                result = is_valid_email_domain("user@example.com")
                
                assert result is True
                mock_logger.assert_called_once_with("許可されたドメインです: example.com")
    
    def test_domain_restriction_enabled_with_invalid_domain(self):
        """Test email validation with disallowed domain"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com,test.org"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger') as mock_logger:
                result = is_valid_email_domain("user@notallowed.com")
                
                assert result is False
                mock_logger.assert_called_once_with("許可されていないドメインです: notallowed.com, 許可リスト: ['example.com', 'test.org']")
    
    def test_domain_restriction_enabled_case_insensitive(self):
        """Test that domain checking is case insensitive"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "Example.COM,Test.ORG"
        }
        
        test_cases = [
            ("user@example.com", True),
            ("user@EXAMPLE.COM", True),
            ("user@Example.Com", True),
            ("user@test.org", True),
            ("user@TEST.ORG", True),
            ("user@other.com", False)
        ]
        
        for email, expected in test_cases:
            with patch.dict(os.environ, env_vars):
                with patch('utils.email_validator.create_logger'):
                    result = is_valid_email_domain(email)
                    assert result == expected, f"Failed for {email}, expected {expected}"
    
    def test_domain_restriction_enabled_various_enable_values(self):
        """Test various ways to enable domain restriction"""
        enable_values = ["true", "True", "TRUE", "1", "yes", "enabled"]
        
        for value in enable_values:
            env_vars = {
                "ENABLE_DOMAIN_RESTRICTION": value,
                "ALLOWED_EMAIL_DOMAINS": "example.com"
            }
            
            with patch.dict(os.environ, env_vars):
                with patch('utils.email_validator.create_logger'):
                    result = is_valid_email_domain("user@example.com")
                    assert result is True, f"Failed for enable value: {value}"
    
    def test_domain_restriction_enabled_multiple_domains(self):
        """Test with multiple allowed domains"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "gmail.com,yahoo.com,outlook.com,company.co.jp"
        }
        
        valid_emails = [
            "user@gmail.com",
            "test@yahoo.com", 
            "admin@outlook.com",
            "employee@company.co.jp"
        ]
        
        invalid_emails = [
            "user@hotmail.com",
            "test@protonmail.com",
            "admin@aol.com"
        ]
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                for email in valid_emails:
                    result = is_valid_email_domain(email)
                    assert result is True, f"Should be valid: {email}"
                
                for email in invalid_emails:
                    result = is_valid_email_domain(email)
                    assert result is False, f"Should be invalid: {email}"


class TestEmailValidatorDomainConfiguration:
    """Test domain configuration scenarios"""
    
    def test_no_allowed_domains_configured(self):
        """Test behavior when no allowed domains are configured"""
        with patch.dict(os.environ, {"ENABLE_DOMAIN_RESTRICTION": "true", "ALLOWED_EMAIL_DOMAINS": ""}):
            with patch('utils.email_validator.create_logger') as mock_logger:
                result = is_valid_email_domain("user@example.com")
                
                assert result is True
                mock_logger.assert_called_once_with("許可されたドメインが設定されていません。すべてのドメインを許可")
    
    def test_allowed_domains_not_set(self):
        """Test behavior when ALLOWED_EMAIL_DOMAINS environment variable is not set"""
        env_vars = {"ENABLE_DOMAIN_RESTRICTION": "true"}
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('utils.email_validator.create_logger') as mock_logger:
                result = is_valid_email_domain("user@example.com")
                
                assert result is True
                mock_logger.assert_called_once_with("許可されたドメインが設定されていません。すべてのドメインを許可")
    
    def test_allowed_domains_with_whitespace(self):
        """Test domain list with extra whitespace"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": " example.com , test.org ,  company.com  "
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                # Should work with properly trimmed domains
                assert is_valid_email_domain("user@example.com") is True
                assert is_valid_email_domain("user@test.org") is True
                assert is_valid_email_domain("user@company.com") is True
                assert is_valid_email_domain("user@other.com") is False
    
    def test_allowed_domains_with_empty_entries(self):
        """Test domain list with empty entries"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com,,test.org,,"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                assert is_valid_email_domain("user@example.com") is True
                assert is_valid_email_domain("user@test.org") is True
                assert is_valid_email_domain("user@other.com") is False
    
    def test_single_domain_configuration(self):
        """Test configuration with single domain"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "company.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                assert is_valid_email_domain("employee@company.com") is True
                assert is_valid_email_domain("user@external.com") is False


class TestEmailValidatorInvalidEmailFormats:
    """Test handling of invalid email formats"""
    
    def test_email_without_at_symbol(self):
        """Test email without @ symbol"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger') as mock_logger:
                result = is_valid_email_domain("userexample.com")
                
                assert result is False
                mock_logger.assert_called_once_with("不正なメールアドレス形式: userexample.com")
    
    def test_email_with_multiple_at_symbols(self):
        """Test email with multiple @ symbols"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                # Should use the second part after splitting by @
                result = is_valid_email_domain("user@test@example.com")
                assert result is False  # Gets "test" as domain, not "example.com"
    
    def test_empty_email(self):
        """Test empty email string"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger') as mock_logger:
                result = is_valid_email_domain("")
                
                assert result is False
                mock_logger.assert_called_once_with("不正なメールアドレス形式: ")
    
    def test_email_ending_with_at(self):
        """Test email ending with @"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger') as mock_logger:
                result = is_valid_email_domain("user@")
                
                assert result is False
                # The domain becomes empty string "", which is not in allowed domains
                mock_logger.assert_called_once_with("許可されていないドメインです: , 許可リスト: ['example.com']")
    
    def test_email_starting_with_at(self):
        """Test email starting with @"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                result = is_valid_email_domain("@example.com")
                # This actually works as split("@")[1] gives "example.com"
                assert result is True


class TestEmailValidatorEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_unicode_domain(self):
        """Test email with unicode domain"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "テスト.jp,example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                result = is_valid_email_domain("user@テスト.jp")
                assert result is True
    
    def test_subdomain_handling(self):
        """Test how subdomains are handled"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                # Subdomain should not match parent domain
                result = is_valid_email_domain("user@mail.example.com")
                assert result is False
    
    def test_subdomain_explicitly_allowed(self):
        """Test subdomain that is explicitly allowed"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "mail.example.com,example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                assert is_valid_email_domain("user@mail.example.com") is True
                assert is_valid_email_domain("user@example.com") is True
                assert is_valid_email_domain("user@other.example.com") is False
    
    def test_very_long_domain(self):
        """Test very long domain name"""
        long_domain = "a" * 50 + ".com"
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": long_domain
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                result = is_valid_email_domain(f"user@{long_domain}")
                assert result is True
    
    def test_domain_with_special_characters(self):
        """Test domain with special characters"""
        special_domains = [
            "ex-ample.com",
            "example123.com", 
            "ex_ample.com",
            "123example.com"
        ]
        
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": ",".join(special_domains)
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                for domain in special_domains:
                    result = is_valid_email_domain(f"user@{domain}")
                    assert result is True, f"Failed for domain: {domain}"
    
    def test_international_domain_extensions(self):
        """Test various international domain extensions"""
        international_domains = [
            "example.co.uk",
            "example.co.jp",
            "example.com.au",
            "example.org.br",
            "example.edu.cn"
        ]
        
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": ",".join(international_domains)
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                for domain in international_domains:
                    result = is_valid_email_domain(f"user@{domain}")
                    assert result is True, f"Failed for domain: {domain}"


class TestEmailValidatorLogging:
    """Test logging functionality"""
    
    def test_logging_for_disabled_restriction(self):
        """Test logging when domain restriction is disabled"""
        with patch.dict(os.environ, {"ENABLE_DOMAIN_RESTRICTION": "false"}):
            with patch('utils.email_validator.create_logger') as mock_logger:
                is_valid_email_domain("test@example.com")
                
                mock_logger.assert_called_once_with("ドメイン制限は無効です。すべてのドメインを許可: test@example.com")
    
    def test_logging_for_missing_configuration(self):
        """Test logging when no domains are configured"""
        with patch.dict(os.environ, {"ENABLE_DOMAIN_RESTRICTION": "true", "ALLOWED_EMAIL_DOMAINS": ""}):
            with patch('utils.email_validator.create_logger') as mock_logger:
                is_valid_email_domain("test@example.com")
                
                mock_logger.assert_called_once_with("許可されたドメインが設定されていません。すべてのドメインを許可")
    
    def test_logging_for_allowed_domain(self):
        """Test logging for allowed domain"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger') as mock_logger:
                is_valid_email_domain("user@example.com")
                
                mock_logger.assert_called_once_with("許可されたドメインです: example.com")
    
    def test_logging_for_disallowed_domain(self):
        """Test logging for disallowed domain"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com,test.org"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger') as mock_logger:
                is_valid_email_domain("user@notallowed.com")
                
                mock_logger.assert_called_once_with("許可されていないドメインです: notallowed.com, 許可リスト: ['example.com', 'test.org']")
    
    def test_logging_for_invalid_email_format(self):
        """Test logging for invalid email format"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger') as mock_logger:
                is_valid_email_domain("invalid-email")
                
                mock_logger.assert_called_once_with("不正なメールアドレス形式: invalid-email")


class TestEmailValidatorIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    def test_corporate_email_restriction_scenario(self):
        """Test typical corporate email restriction scenario"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "company.com,partner.org,contractor.net"
        }
        
        # Valid corporate emails
        valid_emails = [
            "employee@company.com",
            "manager@company.com",
            "partner@partner.org",
            "contractor@contractor.net"
        ]
        
        # Invalid external emails
        invalid_emails = [
            "user@gmail.com",
            "test@yahoo.com",
            "external@external.com"
        ]
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                for email in valid_emails:
                    assert is_valid_email_domain(email) is True, f"Corporate email should be valid: {email}"
                
                for email in invalid_emails:
                    assert is_valid_email_domain(email) is False, f"External email should be invalid: {email}"
    
    def test_educational_institution_scenario(self):
        """Test educational institution email restriction"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "university.edu,student.university.edu,staff.university.edu"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                assert is_valid_email_domain("professor@university.edu") is True
                assert is_valid_email_domain("student@student.university.edu") is True
                assert is_valid_email_domain("admin@staff.university.edu") is True
                assert is_valid_email_domain("external@gmail.com") is False
    
    def test_multi_environment_configuration(self):
        """Test different configurations for different environments"""
        # Development environment - no restrictions
        with patch.dict(os.environ, {"ENABLE_DOMAIN_RESTRICTION": "false"}):
            with patch('utils.email_validator.create_logger'):
                assert is_valid_email_domain("dev@anywhere.com") is True
                assert is_valid_email_domain("test@example.org") is True
        
        # Production environment - strict restrictions
        prod_env = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "company.com"
        }
        
        with patch.dict(os.environ, prod_env):
            with patch('utils.email_validator.create_logger'):
                assert is_valid_email_domain("user@company.com") is True
                assert is_valid_email_domain("user@external.com") is False


class TestEmailValidatorPerformance:
    """Test performance-related aspects"""
    
    def test_large_domain_list_performance(self):
        """Test performance with large domain list"""
        # Create a list of 100 domains
        large_domain_list = [f"domain{i}.com" for i in range(100)]
        
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": ",".join(large_domain_list)
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                # Test validation should still be fast
                assert is_valid_email_domain("user@domain50.com") is True
                assert is_valid_email_domain("user@notindomain.com") is False
    
    def test_repeated_validation_calls(self):
        """Test repeated validation calls"""
        env_vars = {
            "ENABLE_DOMAIN_RESTRICTION": "true",
            "ALLOWED_EMAIL_DOMAINS": "example.com,test.org"
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('utils.email_validator.create_logger'):
                # Multiple calls should work consistently
                for _ in range(50):
                    assert is_valid_email_domain("user@example.com") is True
                    assert is_valid_email_domain("user@invalid.com") is False


if __name__ == "__main__":
    # Run specific test groups
    pytest.main([__file__, "-v", "--tb=short"])
