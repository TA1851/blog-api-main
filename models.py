"""テーブル定義モジュール"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base, db_env

from logger.custom_logger import create_logger


class Article(Base):
    """SQLAlchemyのBaseクラスを継承して、記事情報のテーブルを定義する。

    :param id: 自動付与されるDBのID
    :param article_id: 記事のID
    :param title: 記事のタイトル
    :param body: 記事の本文
    :param user_id: 記事を作成したユーザーのID
    :param owner: 特定の記事を作成したユーザーの情報を取得するためのリレーションシップ
    """

    __tablename__ = "articles"

    # データベースカラムを定義
    id: int = Column(Integer, primary_key=True, index=True)
    article_id: int = Column(Integer, nullable=False)
    title: str = Column(String, nullable=False)
    body: str = Column(String, nullable=False)
    # Userクラスのidを外部キーとして指定する
    user_id = Column(Integer, ForeignKey("users.id"))
    # 特定の記事を作成したユーザーの情報を取得する
    owner = relationship("User", back_populates="blogs")
    create_logger(f"Articleインスタンスが作成されました。")

key_05 = db_env.get("file_id_05")
# print(f"STEP10：Articleインスタンスが作成されました。 -> {key_05}")


class User(Base):
    """SQLAlchemyのBaseクラスを継承して、ユーザー情報のテーブルを定義する。

    :param id: 自動付与されるDBのID
    :param name: ユーザー名
    :param email: メールアドレス
    :param password: パスワード
    :param is_active: ユーザーの有効状態
    :param blogs: 特定のユーザーが作成した記事の情報を全て取得するためのリレーションシップ
    :param owner: 特定の記事を作成したユーザーの情報を取得するためのリレーションシップ
    """

    __tablename__ = "users"

    # データベースカラムを定義
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    email: str = Column(String)
    password: str = Column(String)
    is_active: bool = Column(Boolean, default=True)
    # 特定のユーザーが作成した記事の情報を全て取得する
    blogs = relationship("Article", back_populates="owner")

key_08 = db_env.get("file_id_08")
# print(f"STEP10：Articleインスタンスが作成されました。 -> {key_08}")
# print("---------------------------------------------------------------")