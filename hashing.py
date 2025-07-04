"""パスワードのハッシュ化と検証を行うためのクラスを定義。"""
from passlib.context import CryptContext

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


class Hash:
    """パスワードのハッシュ化と検証を行うクラス"""
    @staticmethod
    def bcrypt(password: str) -> str:
        """パスワードをハッシュ化

        :param password: ハッシュ化するパスワード
        """
        return password_context.hash(password)

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """平文のパスワードとハッシュ化されたパスワードを比較

        :param plain_password: 平文のパスワード
        :param hashed_password: ハッシュ化されたパスワード
        :return: 一致する場合は True, それ以外は False
        """
        return password_context.verify(plain_password, hashed_password)