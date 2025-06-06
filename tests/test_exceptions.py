"""exceptions.pyの単体テスト"""
import pytest

# テスト対象のインポート
from exceptions import (
    DatabaseConnectionError,
    AuthenticationError,
    ValidationError
)


class TestDatabaseConnectionError:
    """DatabaseConnectionErrorクラスのテスト"""

    def test_database_connection_error_default_message(self):
        """デフォルトメッセージでの例外生成テスト"""
        error = DatabaseConnectionError()
        assert str(error) == "データベース接続エラーが発生しました"
        assert error.message == "データベース接続エラーが発生しました"

    def test_database_connection_error_custom_message(self):
        """カスタムメッセージでの例外生成テスト"""
        custom_message = "PostgreSQLサーバーに接続できません"
        error = DatabaseConnectionError(custom_message)
        assert str(error) == custom_message
        assert error.message == custom_message

    def test_database_connection_error_inheritance(self):
        """Exceptionクラスの継承確認テスト"""
        error = DatabaseConnectionError()
        assert isinstance(error, Exception)

    def test_database_connection_error_raise(self):
        """例外の発生確認テスト"""
        with pytest.raises(DatabaseConnectionError) as exc_info:
            raise DatabaseConnectionError("テスト用エラーメッセージ")
        
        assert str(exc_info.value) == "テスト用エラーメッセージ"

    def test_database_connection_error_empty_message(self):
        """空文字列メッセージでの例外生成テスト"""
        error = DatabaseConnectionError("")
        assert str(error) == ""
        assert error.message == ""

    def test_database_connection_error_none_message(self):
        """None値によるメッセージでの動作確認テスト"""
        # Noneを渡すとstr(None)が設定される
        error = DatabaseConnectionError(None)
        assert str(error) == "None"
        assert error.message is None


class TestAuthenticationError:
    """AuthenticationErrorクラスのテスト"""

    def test_authentication_error_default_message(self):
        """デフォルトメッセージでの例外生成テスト"""
        error = AuthenticationError()
        assert str(error) == "認証に失敗しました"
        assert error.message == "認証に失敗しました"

    def test_authentication_error_custom_message(self):
        """カスタムメッセージでの例外生成テスト"""
        custom_message = "無効なユーザー名またはパスワードです"
        error = AuthenticationError(custom_message)
        assert str(error) == custom_message
        assert error.message == custom_message

    def test_authentication_error_inheritance(self):
        """Exceptionクラスの継承確認テスト"""
        error = AuthenticationError()
        assert isinstance(error, Exception)

    def test_authentication_error_raise(self):
        """例外の発生確認テスト"""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError("JWT トークンが無効です")
        
        assert str(exc_info.value) == "JWT トークンが無効です"

    def test_authentication_error_long_message(self):
        """長いメッセージでの例外生成テスト"""
        long_message = "認証に失敗しました。" * 10
        error = AuthenticationError(long_message)
        assert str(error) == long_message
        assert error.message == long_message

    def test_authentication_error_unicode_message(self):
        """Unicode文字を含むメッセージでの例外生成テスト"""
        unicode_message = "認証エラー: ユーザー「山田太郎」のログインに失敗 🔒"
        error = AuthenticationError(unicode_message)
        assert str(error) == unicode_message
        assert error.message == unicode_message


class TestValidationError:
    """ValidationErrorクラスのテスト"""

    def test_validation_error_default_message(self):
        """デフォルトメッセージでの例外生成テスト"""
        error = ValidationError()
        assert str(error) == "バリデーションエラーが発生しました"
        assert error.message == "バリデーションエラーが発生しました"

    def test_validation_error_custom_message(self):
        """カスタムメッセージでの例外生成テスト"""
        custom_message = "メールアドレスの形式が正しくありません"
        error = ValidationError(custom_message)
        assert str(error) == custom_message
        assert error.message == custom_message

    def test_validation_error_inheritance(self):
        """Exceptionクラスの継承確認テスト"""
        error = ValidationError()
        assert isinstance(error, Exception)

    def test_validation_error_raise(self):
        """例外の発生確認テスト"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("必須フィールドが入力されていません")
        
        assert str(exc_info.value) == "必須フィールドが入力されていません"

    def test_validation_error_multiple_fields(self):
        """複数フィールドのバリデーションエラーテスト"""
        message = "以下のフィールドにエラーがあります: email, password, name"
        error = ValidationError(message)
        assert str(error) == message
        assert error.message == message

    def test_validation_error_json_like_message(self):
        """JSON形式のようなメッセージでの例外生成テスト"""
        json_message = '{"field": "email", "error": "Invalid format"}'
        error = ValidationError(json_message)
        assert str(error) == json_message
        assert error.message == json_message


class TestCustomExceptionsInteraction:
    """カスタム例外クラス間の相互作用テスト"""

    def test_different_exception_types(self):
        """異なる例外タイプの区別確認テスト"""
        db_error = DatabaseConnectionError("DB error")
        auth_error = AuthenticationError("Auth error")
        val_error = ValidationError("Validation error")

        assert type(db_error) != type(auth_error)
        assert type(auth_error) != type(val_error)
        assert type(db_error) != type(val_error)

    def test_exception_hierarchy(self):
        """例外階層の確認テスト"""
        db_error = DatabaseConnectionError()
        auth_error = AuthenticationError()
        val_error = ValidationError()

        # すべての例外がExceptionクラスのサブクラスであることを確認
        assert issubclass(DatabaseConnectionError, Exception)
        assert issubclass(AuthenticationError, Exception)
        assert issubclass(ValidationError, Exception)

        # インスタンスがExceptionのインスタンスであることを確認
        assert isinstance(db_error, Exception)
        assert isinstance(auth_error, Exception)
        assert isinstance(val_error, Exception)

    def test_exception_catching(self):
        """例外キャッチの動作確認テスト"""
        # 特定の例外タイプをキャッチ
        with pytest.raises(DatabaseConnectionError):
            raise DatabaseConnectionError("Database issue")

        # 基底クラスでキャッチ
        with pytest.raises(Exception):
            raise AuthenticationError("Auth issue")

        # ValidationErrorは指定した例外タイプではないため、pytest.raisesで確認
        with pytest.raises(ValidationError):
            raise ValidationError("This should be caught as ValidationError")

    def test_exception_message_attributes_consistency(self):
        """各例外クラスのmessage属性の一貫性テスト"""
        test_message = "テストメッセージ"
        
        db_error = DatabaseConnectionError(test_message)
        auth_error = AuthenticationError(test_message)
        val_error = ValidationError(test_message)

        assert db_error.message == test_message
        assert auth_error.message == test_message
        assert val_error.message == test_message

        assert str(db_error) == test_message
        assert str(auth_error) == test_message
        assert str(val_error) == test_message


class TestExceptionUsageScenarios:
    """実際の使用シナリオに基づくテスト"""

    def test_database_error_scenario(self):
        """データベースエラーのシナリオテスト"""
        def simulate_database_operation():
            # データベース操作をシミュレート
            connection_failed = True
            if connection_failed:
                raise DatabaseConnectionError("PostgreSQL接続タイムアウト")

        with pytest.raises(DatabaseConnectionError) as exc_info:
            simulate_database_operation()
        
        assert "PostgreSQL接続タイムアウト" in str(exc_info.value)

    def test_authentication_error_scenario(self):
        """認証エラーのシナリオテスト"""
        def simulate_login(username, password):
            # ログイン処理をシミュレート
            valid_users = {"admin": "password123"}
            if username not in valid_users or valid_users[username] != password:
                raise AuthenticationError(f"ユーザー '{username}' の認証に失敗しました")

        with pytest.raises(AuthenticationError) as exc_info:
            simulate_login("hacker", "wrongpassword")
        
        assert "ユーザー 'hacker' の認証に失敗しました" in str(exc_info.value)

    def test_validation_error_scenario(self):
        """バリデーションエラーのシナリオテスト"""
        def validate_email(email):
            # メールアドレス検証をシミュレート
            if "@" not in email or "." not in email:
                raise ValidationError(f"無効なメールアドレス形式: {email}")

        with pytest.raises(ValidationError) as exc_info:
            validate_email("invalid-email")
        
        assert "無効なメールアドレス形式: invalid-email" in str(exc_info.value)

    def test_nested_exception_handling(self):
        """ネストした例外処理のテスト"""
        def complex_operation():
            try:
                raise DatabaseConnectionError("DB接続失敗")
            except DatabaseConnectionError as db_err:
                # データベースエラーを認証エラーとして再発生
                raise AuthenticationError(f"認証処理中にエラー: {db_err.message}")

        with pytest.raises(AuthenticationError) as exc_info:
            complex_operation()
        
        assert "認証処理中にエラー: DB接続失敗" in str(exc_info.value)
