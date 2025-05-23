"""パスワードのハッシュ化と検証を行うためのクラスを定義。"""
from passlib.context import CryptContext

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__default_rounds=12,
    bcrypt__ident="2b" # 明示的に bcrypt バージョンを指定
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
    def verify(hashed_password: str, plain_password: str) -> bool:
        """平文のパスワードとハッシュ化されたパスワードを比較

        :param hashed_password: ハッシュ化されたパスワード
        :param plain_password: 平文のパスワード
        :return: 一致する場合は True, それ以外は False
        """
        return password_context.verify(plain_password, hashed_password)