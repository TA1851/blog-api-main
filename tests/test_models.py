#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
models.py用の包括的テストスイート
SQLAlchemyモデルの構造、リレーションシップ、メソッドをテストします。
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import Article, User, EmailVerification
from database import Base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError


class TestArticleModel:
    """Articleモデルのテストクラス"""
    
    def test_article_table_name(self):
        """テーブル名が正しく設定されていることを確認"""
        assert Article.__tablename__ == "articles"
    
    def test_article_columns_definition(self):
        """Articleモデルのカラム定義を確認"""
        # カラムの存在確認
        assert hasattr(Article, 'id')
        assert hasattr(Article, 'article_id')
        assert hasattr(Article, 'title')
        assert hasattr(Article, 'body')
        assert hasattr(Article, 'user_id')
        assert hasattr(Article, 'owner')
        
        # プライマリキーの確認
        assert Article.id.property.columns[0].primary_key is True
        assert Article.id.property.columns[0].index is True
        
        # NOT NULLカラムの確認
        assert Article.article_id.property.columns[0].nullable is False
        assert Article.title.property.columns[0].nullable is False
        assert Article.body.property.columns[0].nullable is False
        
        # 外部キーの確認
        foreign_keys = Article.user_id.property.columns[0].foreign_keys
        assert len(foreign_keys) > 0
        assert "users.id" in str(list(foreign_keys)[0])
    
    def test_article_creation(self):
        """Articleインスタンスの作成テスト"""
        article = Article(
            article_id=1,
            title="テスト記事",
            body="テスト記事の本文です。"
        )
        
        assert article.article_id == 1
        assert article.title == "テスト記事"
        assert article.body == "テスト記事の本文です。"
        assert article.user_id is None  # 初期値
    
    def test_article_with_user_id(self):
        """ユーザーIDを含むArticleインスタンスの作成テスト"""
        article = Article(
            article_id=2,
            title="ユーザー記事",
            body="ユーザーによる記事の本文です。",
            user_id=123
        )
        
        assert article.user_id == 123
    
    @patch('models.create_logger')
    def test_article_post_init(self, mock_logger):
        """__post_init__メソッドのテスト"""
        article = Article(
            article_id=1,
            title="テスト記事",
            body="本文"
        )
        
        # __post_init__が呼ばれた場合のロガー呼び出しを確認
        # 注意: SQLAlchemyモデルでは通常__post_init__は自動で呼ばれません
        article.__post_init__()
        mock_logger.assert_called_once_with("Articleインスタンスが作成されました。")
    
    def test_article_relationship_definition(self):
        """Articleモデルのリレーションシップ定義を確認"""
        # ownerリレーションシップの存在確認
        assert hasattr(Article, 'owner')
        
        # リレーションシップの設定確認
        relationship_property = Article.owner.property
        assert relationship_property.mapper.class_ == User
        assert relationship_property.back_populates == "blogs"


class TestUserModel:
    """Userモデルのテストクラス"""
    
    def test_user_table_name(self):
        """テーブル名が正しく設定されていることを確認"""
        assert User.__tablename__ == "users"
    
    def test_user_columns_definition(self):
        """Userモデルのカラム定義を確認"""
        # カラムの存在確認
        assert hasattr(User, 'id')
        assert hasattr(User, 'name')
        assert hasattr(User, 'email')
        assert hasattr(User, 'password')
        assert hasattr(User, 'is_active')
        assert hasattr(User, 'blogs')
        
        # プライマリキーの確認
        assert User.id.property.columns[0].primary_key is True
        assert User.id.property.columns[0].index is True
        
        # デフォルト値の確認
        assert User.is_active.property.columns[0].default.arg is True
    
    def test_user_creation(self):
        """Userインスタンスの作成テスト"""
        user = User(
            name="テストユーザー",
            email="test@example.com",
            password="hashed_password"
        )
        
        assert user.name == "テストユーザー"
        assert user.email == "test@example.com"
        assert user.password == "hashed_password"
        # is_activeはデータベースレベルでのデフォルト値なので、
        # インスタンス作成時点では None の場合がある
        assert user.is_active is None or user.is_active is True
    
    def test_user_optional_fields(self):
        """Userのオプショナルフィールドのテスト"""
        user = User()
        
        # オプショナルフィールドがNoneでも問題ないことを確認
        assert user.name is None
        assert user.email is None
        assert user.password is None
        # is_activeは明示的に設定されない限りNoneの場合がある
        assert user.is_active is None or user.is_active is True
    
    def test_user_is_active_custom_value(self):
        """is_activeフィールドのカスタム値テスト"""
        user = User(
            name="無効ユーザー",
            email="inactive@example.com",
            is_active=False
        )
        
        assert user.is_active is False
    
    def test_user_relationship_definition(self):
        """Userモデルのリレーションシップ定義を確認"""
        # blogsリレーションシップの存在確認
        assert hasattr(User, 'blogs')
        
        # リレーションシップの設定確認
        relationship_property = User.blogs.property
        assert relationship_property.mapper.class_ == Article
        assert relationship_property.back_populates == "owner"


class TestEmailVerificationModel:
    """EmailVerificationモデルのテストクラス"""
    
    def test_email_verification_table_name(self):
        """テーブル名が正しく設定されていることを確認"""
        assert EmailVerification.__tablename__ == 'email_verifications'
    
    def test_email_verification_columns_definition(self):
        """EmailVerificationモデルのカラム定義を確認"""
        # カラムの存在確認
        assert hasattr(EmailVerification, 'id')
        assert hasattr(EmailVerification, 'email')
        assert hasattr(EmailVerification, 'token')
        assert hasattr(EmailVerification, 'password_hash')
        assert hasattr(EmailVerification, 'is_verified')
        assert hasattr(EmailVerification, 'created_at')
        assert hasattr(EmailVerification, 'expires_at')
        
        # プライマリキーの確認
        assert EmailVerification.id.property.columns[0].primary_key is True
        
        # ユニーク制約の確認
        assert EmailVerification.email.property.columns[0].unique is True
        assert EmailVerification.token.property.columns[0].unique is True
        
        # NOT NULL制約の確認
        assert EmailVerification.email.property.columns[0].nullable is False
        assert EmailVerification.token.property.columns[0].nullable is False
        
        # デフォルト値の確認
        assert EmailVerification.is_verified.property.columns[0].default.arg is False
    
    def test_email_verification_creation(self):
        """EmailVerificationインスタンスの作成テスト"""
        verification = EmailVerification(
            email="test@example.com",
            token="test_token_123",
            password_hash="hashed_password"
        )
        
        assert verification.email == "test@example.com"
        assert verification.token == "test_token_123"
        assert verification.password_hash == "hashed_password"
        # is_verifiedはデータベースレベルでのデフォルト値なので、
        # インスタンス作成時点では None の場合がある
        assert verification.is_verified is None or verification.is_verified is False
    
    def test_email_verification_with_datetime(self):
        """日時フィールドを含むEmailVerificationのテスト"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=24)
        
        verification = EmailVerification(
            email="time@example.com",
            token="time_token",
            created_at=now,
            expires_at=expires
        )
        
        assert verification.created_at == now
        assert verification.expires_at == expires
    
    @patch('models.uuid4')
    @patch('models.datetime')
    def test_create_verification_class_method(self, mock_datetime, mock_uuid):
        """create_verificationクラスメソッドのテスト"""
        # モックの設定
        mock_now = datetime(2025, 6, 2, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "mocked-uuid-token"
        
        # メソッドの実行
        verification = EmailVerification.create_verification("test@example.com")
        
        # 結果の確認
        assert verification.email == "test@example.com"
        assert verification.token == "mocked-uuid-token"
        assert verification.expires_at == mock_now + timedelta(hours=24)
        
        # モックが正しく呼ばれたことを確認
        mock_datetime.utcnow.assert_called()
        mock_uuid.assert_called_once()
    
    def test_create_verification_returns_instance(self):
        """create_verificationが正しいインスタンスを返すことを確認"""
        verification = EmailVerification.create_verification("instance@example.com")
        
        assert isinstance(verification, EmailVerification)
        assert verification.email == "instance@example.com"
        assert verification.token is not None
        assert len(verification.token) > 0  # UUIDが生成されている
        assert verification.expires_at is not None
        
        # 有効期限が現在時刻より後であることを確認
        assert verification.expires_at > datetime.utcnow()


class TestModelRelationships:
    """モデル間のリレーションシップのテスト"""
    
    def test_article_user_relationship_consistency(self):
        """ArticleとUserのリレーションシップの整合性テスト"""
        # Articleのownerリレーションシップ
        article_relationship = Article.owner.property
        assert article_relationship.mapper.class_ == User
        assert article_relationship.back_populates == "blogs"
        
        # Userのblogsリレーションシップ
        user_relationship = User.blogs.property
        assert user_relationship.mapper.class_ == Article
        assert user_relationship.back_populates == "owner"
    
    def test_foreign_key_consistency(self):
        """外部キーの整合性テスト"""
        # Article.user_idがusers.idを参照していることを確認
        foreign_keys = Article.user_id.property.columns[0].foreign_keys
        assert len(foreign_keys) == 1
        
        foreign_key = list(foreign_keys)[0]
        assert foreign_key.column.table.name == "users"
        assert foreign_key.column.name == "id"


class TestModelTableStructure:
    """モデルのテーブル構造テスト"""
    
    def test_all_models_inherit_from_base(self):
        """すべてのモデルがBaseクラスを継承していることを確認"""
        assert issubclass(Article, Base)
        assert issubclass(User, Base)
        assert issubclass(EmailVerification, Base)
    
    def test_table_names_are_unique(self):
        """テーブル名がユニークであることを確認"""
        table_names = {
            Article.__tablename__,
            User.__tablename__,
            EmailVerification.__tablename__
        }
        
        assert len(table_names) == 3  # 3つのモデルで3つの異なるテーブル名
    
    def test_model_docstrings_exist(self):
        """各モデルにドキュメントが存在することを確認"""
        assert Article.__doc__ is not None
        assert User.__doc__ is not None
        assert EmailVerification.__doc__ is not None
        
        # ドキュメントが空でないことを確認
        assert len(Article.__doc__.strip()) > 0
        assert len(User.__doc__.strip()) > 0
        assert len(EmailVerification.__doc__.strip()) > 0


@pytest.mark.integration
class TestModelsIntegration:
    """モデルの統合テスト（データベース操作を含む）"""
    
    @pytest.fixture(scope="function")
    def test_engine(self):
        """テスト用のインメモリデータベースエンジン"""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        return engine
    
    @pytest.fixture(scope="function")
    def test_session(self, test_engine):
        """テスト用のデータベースセッション"""
        TestingSessionLocal = sessionmaker(bind=test_engine)
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def test_user_article_relationship_in_db(self, test_session):
        """データベースでのUser-Articleリレーションシップテスト"""
        # ユーザーを作成
        user = User(
            name="統合テストユーザー",
            email="integration@example.com",
            password="test_password"
        )
        test_session.add(user)
        test_session.flush()  # IDを取得するためにflush
        
        # 記事を作成
        article = Article(
            article_id=1,
            title="統合テスト記事",
            body="統合テストの本文",
            user_id=user.id
        )
        test_session.add(article)
        test_session.commit()
        
        # リレーションシップが正しく動作することを確認
        assert article.owner == user
        assert article in user.blogs
    
    def test_email_verification_in_db(self, test_session):
        """データベースでのEmailVerificationテスト"""
        verification = EmailVerification.create_verification("db@example.com")
        test_session.add(verification)
        test_session.commit()
        
        # データベースから取得
        retrieved = test_session.query(EmailVerification).filter_by(
            email="db@example.com"
        ).first()
        
        assert retrieved is not None
        assert retrieved.email == "db@example.com"
        assert retrieved.is_verified is False
        assert retrieved.token is not None
    
    def test_unique_constraints(self, test_session):
        """ユニーク制約のテスト"""
        # 最初のEmailVerificationを作成
        verification1 = EmailVerification(
            email="unique@example.com",
            token="unique_token_1"
        )
        test_session.add(verification1)
        test_session.commit()
        
        # 同じemailで2つ目を作成しようとする
        verification2 = EmailVerification(
            email="unique@example.com",  # 同じemail
            token="unique_token_2"
        )
        test_session.add(verification2)
        
        # ユニーク制約違反でエラーが発生することを確認
        with pytest.raises(IntegrityError):
            test_session.commit()
