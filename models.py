"""テーブル定義モジュール"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database import Base
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

    # SQLAlchemy 2.0スタイルでデータベースカラムを定義
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    article_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(String, nullable=False)
    # Userクラスのidを外部キーとして指定する
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    # 特定の記事を作成したユーザーの情報を取得する
    owner: Mapped[Optional["User"]] = relationship("User", back_populates="blogs")


    def __post_init__(self) -> None:
        create_logger(f"Articleインスタンスが作成されました。")


class User(Base):
    """SQLAlchemy2.0スタイルでテーブルを定義する。

    :param id: 自動付与されるDBのID

    :param name: ユーザー名

    :param email: メールアドレス

    :param password: パスワード

    :param is_active: ユーザーの有効状態

    :param blogs: 特定のユーザーが作成した記事の情報を全て取得するためのリレーションシップ
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String)
    password: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # 特定のユーザーが作成した記事の情報を全て取得する
    blogs: Mapped[List["Article"]] = relationship("Article", back_populates="owner")


class EmailVerification(Base):
    """メール確認用のモデル"""
    __tablename__ = 'email_verifications'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    @classmethod
    def create_verification(cls, email: str) -> "EmailVerification":
        """新しい確認レコードを作成"""
        return cls(
            email=email,
            token=str(uuid4()),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )