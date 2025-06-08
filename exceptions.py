"""カスタム例外クラスの定義モジュール"""
from typing import Optional


class DatabaseConnectionError(Exception):
    """データベース接続エラーを表すカスタム例外
    
    データベースへの接続が失敗した場合、または
    データベース操作中に予期しないエラーが発生した場合に
    発生させる例外クラスです。
    
    Attributes:
        message (str): エラーメッセージ
        
    Example:
        >>> raise DatabaseConnectionError("データベースに接続できません")
    """
    
    def __init__(self, message: str = "データベース接続エラーが発生しました"):
        """DatabaseConnectionErrorを初期化します
        
        Args:
            message (str): エラーメッセージ
        """
        self.message = message
        super().__init__(self.message)


class AuthenticationError(Exception):
    """認証エラーを表すカスタム例外
    
    ユーザー認証に失敗した場合に発生させる例外クラスです。
    
    Attributes:
        message (str): エラーメッセージ
    """
    
    def __init__(self, message: str = "認証に失敗しました"):
        """AuthenticationErrorを初期化します
        
        Args:
            message (str): エラーメッセージ
        """
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    """バリデーションエラーを表すカスタム例外
    
    入力データの検証に失敗した場合に発生させる例外クラスです。
    
    Attributes:
        message (str): エラーメッセージ
    """
    
    def __init__(self, message: str = "バリデーションエラーが発生しました"):
        """ValidationErrorを初期化します
        
        Args:
            message (str): エラーメッセージ
        """
        self.message = message
        super().__init__(self.message)


# カスタム例外クラス（ユーザ関連）
class UserNotFoundError(Exception):
    """ユーザーが見つからない場合の例外"""
    def __init__(self, user_id: Optional[int] = None, email: Optional[str] = None):
        if user_id:
            self.message = f"User with id {user_id} not found"
        elif email:
            self.message = f"User with email {email} not found"
        else:
            self.message = "User not found"
        super().__init__(self.message)


class EmailVerificationError(Exception):
    """メール確認に関する例外"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DatabaseError(Exception):
    """データベース関連の例外"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
