#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
models.pyの単体テスト
SQLAlchemy 2.0スタイルのモデルクラスをテストします。
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

# テスト対象のモジュールをインポート
from database import Base
from models import Article, User, EmailVerification


class TestDatabaseModels:
    """データベースモデルのテストクラス"""
    
    @pytest.fixture(scope="function")
    def test_db(self):
        """テスト用のインメモリデータベースを作成"""
        # SQLiteのインメモリデータベースを使用
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)
        
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestingSessionLocal()
        
        yield session
        
        session.close()
    
    @pytest.fixture
    def sample_user(self, test_db: Session):
        """テスト用ユーザーデータを作成"""
        user = User(
            name="テストユーザー",
            email="test@example.com", 
            password="hashed_password",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        return user
    
    @pytest.fixture
    def sample_article(self, test_db: Session, sample_user: User):
        """テスト用記事データを作成"""
        article = Article(
            article_id=1,
            title="テスト記事",
            body="これはテスト記事の本文です。",
            user_id=sample_user.id
        )
        test_db.add(article)
        test_db.commit()
        test_db.refresh(article)
        return article


class TestUserModel(TestDatabaseModels):
    """Userモデルのテストクラス"""
    
    def test_user_creation(self, test_db: Session):
        """Userインスタンスの作成をテスト"""
        user = User(
            name="新規ユーザー",
            email="newuser@example.com",
            password="secure_password",
            is_active=True
        )
        
        # データベースに保存
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        # 作成されたユーザーの検証
        assert user.id is not None
        assert user.name == "新規ユーザー"
        assert user.email == "newuser@example.com"
        assert user.password == "secure_password"
        assert user.is_active is True
        assert isinstance(user.blogs, list)
    
    def test_user_default_values(self, test_db: Session):
        """Userのデフォルト値をテスト"""
        user = User()
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        assert user.id is not None
        assert user.name is None
        assert user.email is None
        assert user.password is None
        assert user.is_active is True  # デフォルト値
        assert isinstance(user.blogs, list)
        assert len(user.blogs) == 0
    
    def test_user_optional_fields(self, test_db: Session):
        """Userのオプショナルフィールドをテスト"""
        # 最小限の情報でユーザーを作成
        user = User(name="最小ユーザー")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        assert user.name == "最小ユーザー"
        assert user.email is None
        assert user.password is None
        assert user.is_active is True
    
    def test_user_with_blogs_relationship(self, test_db: Session, sample_user: User):
        """Userと記事のリレーションシップをテスト"""
        # 記事を作成してユーザーに関連付け
        article1 = Article(
            article_id=1,
            title="記事1", 
            body="記事1の本文",
            user_id=sample_user.id
        )
        article2 = Article(
            article_id=2,
            title="記事2",
            body="記事2の本文", 
            user_id=sample_user.id
        )
        
        test_db.add(article1)
        test_db.add(article2)
        test_db.commit()
        
        # リレーションシップの確認
        test_db.refresh(sample_user)
        assert len(sample_user.blogs) == 2
        assert article1 in sample_user.blogs
        assert article2 in sample_user.blogs
    
    def test_user_inactive_state(self, test_db: Session):
        """非アクティブユーザーのテスト"""
        user = User(
            name="非アクティブユーザー",
            email="inactive@example.com",
            is_active=False
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        assert user.is_active is False


class TestArticleModel(TestDatabaseModels):
    """Articleモデルのテストクラス"""
    
    def test_article_creation(self, test_db: Session, sample_user: User):
        """Articleインスタンスの作成をテスト"""
        article = Article(
            article_id=123,
            title="新しい記事",
            body="これは新しい記事の本文です。",
            user_id=sample_user.id
        )
        
        test_db.add(article)
        test_db.commit()
        test_db.refresh(article)
        
        # 作成された記事の検証
        assert article.id is not None
        assert article.article_id == 123
        assert article.title == "新しい記事"
        assert article.body == "これは新しい記事の本文です。"
        assert article.user_id == sample_user.id
        assert article.owner is not None
        assert article.owner.id == sample_user.id
    
    def test_article_without_user(self, test_db: Session):
        """ユーザーIDなしの記事作成をテスト"""
        article = Article(
            article_id=456,
            title="匿名記事",
            body="ユーザーIDなしの記事です。"
        )
        
        test_db.add(article)
        test_db.commit()
        test_db.refresh(article)
        
        assert article.id is not None
        assert article.article_id == 456
        assert article.title == "匿名記事"
        assert article.body == "ユーザーIDなしの記事です。"
        assert article.user_id is None
        assert article.owner is None
    
    def test_article_owner_relationship(self, test_db: Session, sample_article: Article, sample_user: User):
        """記事とユーザーのリレーションシップをテスト"""
        # リレーションシップの確認
        assert sample_article.owner is not None
        assert sample_article.owner.id == sample_user.id
        assert sample_article.owner.name == sample_user.name
        assert sample_article.owner.email == sample_user.email
    
    def test_multiple_articles_same_user(self, test_db: Session, sample_user: User):
        """同一ユーザーの複数記事をテスト"""
        articles = []
        for i in range(3):
            article = Article(
                article_id=100 + i,
                title=f"記事{i+1}",
                body=f"記事{i+1}の本文です。",
                user_id=sample_user.id
            )
            articles.append(article)
            test_db.add(article)
        
        test_db.commit()
        
        # 全ての記事が正しく作成されていることを確認
        for i, article in enumerate(articles):
            test_db.refresh(article)
            assert article.article_id == 100 + i
            assert article.owner.id == sample_user.id
        
        # ユーザーから記事を確認
        test_db.refresh(sample_user)
        assert len(sample_user.blogs) == 3


class TestEmailVerificationModel(TestDatabaseModels):
    """EmailVerificationモデルのテストクラス"""
    
    def test_email_verification_creation(self, test_db: Session):
        """EmailVerificationインスタンスの作成をテスト"""
        now = datetime.utcnow()
        verification = EmailVerification(
            email="verify@example.com",
            token="test-token-123",
            password_hash="hashed_password",
            is_verified=False,
            created_at=now,
            expires_at=now + timedelta(hours=24)
        )
        
        test_db.add(verification)
        test_db.commit()
        test_db.refresh(verification)
        
        assert verification.id is not None
        assert verification.email == "verify@example.com"
        assert verification.token == "test-token-123"
        assert verification.password_hash == "hashed_password"
        assert verification.is_verified is False
        assert verification.created_at == now
        assert verification.expires_at == now + timedelta(hours=24)
    
    def test_email_verification_defaults(self, test_db: Session):
        """EmailVerificationのデフォルト値をテスト"""
        verification = EmailVerification(
            email="default@example.com",
            token="default-token"
        )
        
        test_db.add(verification)
        test_db.commit()
        test_db.refresh(verification)
        
        assert verification.email == "default@example.com"
        assert verification.token == "default-token"
        assert verification.password_hash is None
        assert verification.is_verified is False  # デフォルト値
        assert verification.created_at is not None
        assert isinstance(verification.created_at, datetime)
        assert verification.expires_at is None
    
    def test_create_verification_classmethod(self, test_db: Session):
        """create_verification クラスメソッドをテスト"""
        email = "classmethod@example.com"
        verification = EmailVerification.create_verification(email)
        
        test_db.add(verification)
        test_db.commit()
        test_db.refresh(verification)
        
        assert verification.email == email
        assert verification.token is not None
        assert len(verification.token) > 0
        # UUIDフォーマットの確認
        assert UUID(verification.token)  # 有効なUUIDであることを確認
        assert verification.expires_at is not None
        assert verification.expires_at > datetime.utcnow()
        # 24時間後に設定されていることを確認（±1分の誤差を許容）
        expected_expiry = datetime.utcnow() + timedelta(hours=24)
        time_diff = abs((verification.expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # 1分以内の誤差


if __name__ == "__main__":
    # このファイルを直接実行した場合のテスト実行
    pytest.main([__file__, "-v"])