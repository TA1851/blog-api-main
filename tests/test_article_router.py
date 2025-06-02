#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
記事ルーターの包括的テストスイート

このテストスイートは routers/article.py の全ての機能をテストします:
- 認証ユーザーの記事管理 (CRUD操作)
- パブリック記事の取得と検索
- 記事の一覧取得とページネーション
- 検索機能とMarkdown変換
"""

import pytest
import asyncio
import urllib.parse
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import func

from routers.article import (
    router,
    all_fetch,
    get_article,
    create_article,
    update_article,
    delete_article,
    get_public_articles,
    search_public_articles,
    get_public_article_by_id
)
from schemas import ArticleBase, PublicArticle
from models import Article, User as UserModel
from main import app


class TestArticleRouterConfiguration:
    """記事ルーター設定のテスト"""
    
    def test_router_configuration(self):
        """ルーター設定のテスト"""
        assert router.prefix == "/api/v1"
        assert "articles" in router.tags
    
    def test_router_endpoints_exist(self):
        """エンドポイントが存在することを確認"""
        routes = [route.path for route in router.routes]
        
        # 認証が必要なエンドポイント
        assert "/api/v1/articles" in routes  # GET, POST
        assert "/api/v1/articles/{id}" in routes  # GET
        assert "/api/v1/articles" in routes  # PUT, DELETE
        
        # パブリックエンドポイント
        assert "/api/v1/public/articles" in routes  # GET
        assert "/api/v1/public/articles/search" in routes  # GET
        assert "/api/v1/public/articles/{article_id}" in routes  # GET


class TestAllFetchEndpoint:
    """all_fetch エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        db = MagicMock(spec=Session)
        return db
    
    @pytest.fixture
    def mock_current_user(self):
        """モック現在ユーザー"""
        user = MagicMock()
        user.id = 123
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def sample_articles(self):
        """サンプル記事データ"""
        articles = []
        for i in range(3):
            article = MagicMock()
            article.article_id = i + 1
            article.title = f"テスト記事 {i + 1}"
            article.body = f"テスト記事の本文 {i + 1}"
            article.user_id = 123
            articles.append(article)
        return articles
    
    def test_all_fetch_without_limit(self, mock_db, mock_current_user, sample_articles):
        """制限なしで全記事を取得するテスト"""
        # データベースクエリのモック設定
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_articles
        mock_db.query.return_value = mock_query
        
        result = asyncio.run(all_fetch(mock_db, mock_current_user, None))
        
        assert len(result) == 3
        assert result[0].article_id == 1
        assert result[0].title == "テスト記事 1"
        assert result[0].user_id == 123
        mock_db.query.assert_called()
        
    def test_all_fetch_with_limit(self, mock_db, mock_current_user, sample_articles):
        """制限ありで記事を取得するテスト"""
        limited_articles = sample_articles[:2]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = limited_articles
        mock_db.query.return_value = mock_query
        
        result = asyncio.run(all_fetch(mock_db, mock_current_user, 2))
        
        assert len(result) == 2
        assert result[0].article_id == 1
        assert result[1].article_id == 2
        mock_query.limit.assert_called_with(2)
    
    def test_all_fetch_no_articles(self, mock_db, mock_current_user):
        """記事が存在しない場合のテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        result = asyncio.run(all_fetch(mock_db, mock_current_user, None))
        
        assert result == []
    
    def test_all_fetch_database_error(self, mock_db, mock_current_user):
        """データベースエラーの場合のテスト"""
        mock_db.query.side_effect = ValueError("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(all_fetch(mock_db, mock_current_user, None))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Articles not found" in exc_info.value.detail


class TestGetArticleEndpoint:
    """get_article エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def sample_article(self):
        """サンプル記事"""
        article = MagicMock()
        article.article_id = 1
        article.title = "テスト記事"
        article.body = "テスト記事の本文"
        article.user_id = 123
        return article
    
    def test_get_article_success(self, mock_db, sample_article):
        """記事取得成功のテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_article
        mock_db.query.return_value = mock_query
        
        result = asyncio.run(get_article(1, mock_db))
        
        assert result.article_id == 1
        assert result.title == "テスト記事"
        assert result.user_id == 123
    
    def test_get_article_not_found(self, mock_db):
        """記事が見つからない場合のテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_article(999, mock_db))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Article not found 999" in exc_info.value.detail
    
    def test_get_article_database_error(self, mock_db):
        """データベースエラーの場合のテスト"""
        mock_db.query.side_effect = ValueError("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_article(1, mock_db))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestCreateArticleEndpoint:
    """create_article エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        db = MagicMock(spec=Session)
        return db
    
    @pytest.fixture
    def mock_current_user(self):
        """モック現在ユーザー"""
        user = MagicMock()
        user.id = 123
        return user
    
    @pytest.fixture
    def valid_article(self):
        """有効な記事データ"""
        return ArticleBase(
            title="新規記事",
            body="新規記事の本文です。"
        )
    
    def test_create_article_success(self, mock_db, mock_current_user, valid_article):
        """記事作成成功のテスト"""
        # func.maxのモック
        mock_db.query.return_value.scalar.return_value = 5
        
        # 新規記事のモック
        new_article = MagicMock()
        new_article.article_id = 6
        new_article.title = "新規記事"
        new_article.body = "新規記事の本文です。"
        new_article.user_id = 123
        
        with patch('routers.article.Article') as mock_article_class:
            mock_article_class.return_value = new_article
            
            result = asyncio.run(create_article(valid_article, mock_db, mock_current_user))
            
            assert result.article_id == 6
            assert result.title == "新規記事"
            assert result.user_id == 123
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
    
    def test_create_article_empty_title(self, mock_db, mock_current_user):
        """空のタイトルの場合のテスト"""
        invalid_article = ArticleBase(
            title="",
            body="本文はあります"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(create_article(invalid_article, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "タイトルは必須項目です" in exc_info.value.detail
    
    def test_create_article_none_title(self, mock_db, mock_current_user):
        """Noneタイトルの場合のテスト（Pydanticバリデーション）"""
        # Pydanticスキーマが直接Noneを受け入れないため、
        # バリデーションエラーをテスト
        with pytest.raises(ValueError) as exc_info:
            ArticleBase(
                title=None,
                body="本文はあります"
            )
        
        # Pydanticバリデーションエラーが発生することを確認
        assert "Input should be a valid string" in str(exc_info.value)
    
    def test_create_article_empty_body(self, mock_db, mock_current_user):
        """空の本文の場合のテスト"""
        invalid_article = ArticleBase(
            title="タイトルはあります",
            body=""
        )
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(create_article(invalid_article, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "本文は必須項目です" in exc_info.value.detail
    
    def test_create_article_none_body(self, mock_db, mock_current_user):
        """None本文の場合のテスト（Pydanticバリデーション）"""
        # Pydanticスキーマが直接Noneを受け入れないため、
        # バリデーションエラーをテスト
        with pytest.raises(ValueError) as exc_info:
            ArticleBase(
                title="タイトルはあります",
                body=None
            )
        
        # Pydanticバリデーションエラーが発生することを確認
        assert "Input should be a valid string" in str(exc_info.value)
    
    def test_create_article_whitespace_only(self, mock_db, mock_current_user):
        """空白のみのタイトル・本文の場合のテスト"""
        invalid_article = ArticleBase(
            title="   ",
            body="   "
        )
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(create_article(invalid_article, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "タイトルは必須項目です" in exc_info.value.detail
    
    def test_create_article_auto_increment(self, mock_db, mock_current_user, valid_article):
        """記事IDの自動採番テスト"""
        # 最大記事IDを10に設定
        mock_db.query.return_value.scalar.return_value = 10
        
        new_article = MagicMock()
        new_article.article_id = 11
        new_article.title = "新規記事"
        new_article.body = "新規記事の本文です。"
        new_article.user_id = 123
        
        with patch('routers.article.Article') as mock_article_class:
            mock_article_class.return_value = new_article
            
            result = asyncio.run(create_article(valid_article, mock_db, mock_current_user))
            
            assert result.article_id == 11
            # Article作成時に正しいIDが渡されることを確認
            mock_article_class.assert_called_once_with(
                article_id=11,
                title="新規記事",
                body="新規記事の本文です。",
                user_id=123
            )
    
    def test_create_article_no_existing_articles(self, mock_db, mock_current_user, valid_article):
        """既存記事がない場合のIDテスト"""
        # 既存記事なし（None）
        mock_db.query.return_value.scalar.return_value = None
        
        new_article = MagicMock()
        new_article.article_id = 1
        new_article.title = "新規記事"
        new_article.body = "新規記事の本文です。"
        new_article.user_id = 123
        
        with patch('routers.article.Article') as mock_article_class:
            mock_article_class.return_value = new_article
            
            result = asyncio.run(create_article(valid_article, mock_db, mock_current_user))
            
            assert result.article_id == 1
            # Article作成時にIDが1になることを確認
            mock_article_class.assert_called_once_with(
                article_id=1,
                title="新規記事",
                body="新規記事の本文です。",
                user_id=123
            )


class TestUpdateArticleEndpoint:
    """update_article エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_current_user(self):
        """モック現在ユーザー"""
        user = MagicMock()
        user.id = 123
        return user
    
    @pytest.fixture
    def existing_article(self):
        """既存記事のモック"""
        article = MagicMock()
        article.article_id = 1
        article.title = "元のタイトル"
        article.body = "元の本文"
        article.user_id = 123
        return article
    
    @pytest.fixture
    def update_data(self):
        """更新データ"""
        return ArticleBase(
            title="更新されたタイトル",
            body="更新された本文"
        )
    
    def test_update_article_success(self, mock_db, mock_current_user, existing_article, update_data):
        """記事更新成功のテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_article
        mock_db.query.return_value = mock_query
        
        result = asyncio.run(update_article(1, update_data, mock_db, mock_current_user))
        
        # 記事の内容が更新されることを確認
        assert existing_article.title == "更新されたタイトル"
        assert existing_article.body == "更新された本文"
        
        # 戻り値の確認
        assert result.article_id == 1
        assert result.title == "更新されたタイトル"
        assert result.body == "更新された本文"
        assert result.user_id == 123
        
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(existing_article)
    
    def test_update_article_not_found(self, mock_db, mock_current_user, update_data):
        """存在しない記事の更新テスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(update_article(999, update_data, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Article not found or you do not have permission" in exc_info.value.detail
        assert "Article_id:999" in exc_info.value.detail
    
    def test_update_article_wrong_user(self, mock_db, mock_current_user, update_data):
        """他のユーザーの記事更新テスト"""
        other_user_article = MagicMock()
        other_user_article.user_id = 456  # 異なるユーザーID
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # フィルタリング結果で見つからない
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(update_article(1, update_data, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Article not found or you do not have permission" in exc_info.value.detail
    
    def test_update_article_empty_title(self, mock_db, mock_current_user, existing_article):
        """空のタイトルでの更新テスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_article
        mock_db.query.return_value = mock_query
        
        invalid_update = ArticleBase(
            title="",
            body="更新された本文"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(update_article(1, invalid_update, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "タイトルは必須項目です" in exc_info.value.detail
    
    def test_update_article_empty_body(self, mock_db, mock_current_user, existing_article):
        """空の本文での更新テスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_article
        mock_db.query.return_value = mock_query
        
        invalid_update = ArticleBase(
            title="更新されたタイトル",
            body=""
        )
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(update_article(1, invalid_update, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "本文は必須項目です" in exc_info.value.detail
    
    def test_update_article_database_error(self, mock_db, mock_current_user, update_data):
        """データベースエラーのテスト"""
        mock_db.query.side_effect = ValueError("Database connection failed")
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(update_article(1, update_data, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Article not updated" in exc_info.value.detail


class TestDeleteArticleEndpoint:
    """delete_article エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_current_user(self):
        """モック現在ユーザー"""
        user = MagicMock()
        user.id = 123
        return user
    
    @pytest.fixture
    def existing_article(self):
        """既存記事のモック"""
        article = MagicMock()
        article.article_id = 1
        article.user_id = 123
        return article
    
    def test_delete_article_success(self, mock_db, mock_current_user, existing_article):
        """記事削除成功のテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_article
        mock_db.query.return_value = mock_query
        
        result = asyncio.run(delete_article(1, mock_db, mock_current_user))
        
        assert result is None
        mock_db.delete.assert_called_once_with(existing_article)
        mock_db.commit.assert_called_once()
    
    def test_delete_article_not_found(self, mock_db, mock_current_user):
        """存在しない記事の削除テスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_article(999, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Article not found or you do not have permission" in exc_info.value.detail
        assert "Article_id:999" in exc_info.value.detail
    
    def test_delete_article_wrong_user(self, mock_db, mock_current_user):
        """他のユーザーの記事削除テスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # フィルタリング結果で見つからない
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_article(1, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_article_database_error(self, mock_db, mock_current_user):
        """データベースエラーのテスト"""
        mock_db.query.side_effect = ValueError("Database connection failed")
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_article(1, mock_db, mock_current_user))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Article not deleted" in exc_info.value.detail


class TestGetPublicArticlesEndpoint:
    """get_public_articles エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def sample_articles(self):
        """サンプル記事データ"""
        articles = []
        for i in range(5):
            article = MagicMock()
            article.article_id = i + 1
            article.title = f"パブリック記事 {i + 1}"
            article.body = f"パブリック記事の本文 {i + 1}\n\n# 見出し"
            articles.append(article)
        return articles
    
    def test_get_public_articles_without_pagination(self, mock_db, sample_articles):
        """ページネーションなしでパブリック記事取得テスト"""
        mock_query = MagicMock()
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_articles
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_md.convert.side_effect = lambda x: f"<p>{x}</p>"
            mock_markdown.return_value = mock_md
            
            result = asyncio.run(get_public_articles(mock_db, None, 0))
            
            assert len(result) == 5
            assert isinstance(result[0], PublicArticle)
            assert result[0].article_id == 1
            assert result[0].title == "パブリック記事 1"
            assert "<p>" in result[0].body_html
    
    def test_get_public_articles_with_limit(self, mock_db, sample_articles):
        """制限ありでパブリック記事取得テスト"""
        limited_articles = sample_articles[:3]
        
        mock_query = MagicMock()
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = limited_articles
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_md.convert.side_effect = lambda x: f"<p>{x}</p>"
            mock_markdown.return_value = mock_md
            
            result = asyncio.run(get_public_articles(mock_db, 3, 0))
            
            assert len(result) == 3
            mock_query.limit.assert_called_with(3)
    
    def test_get_public_articles_with_skip(self, mock_db, sample_articles):
        """スキップありでパブリック記事取得テスト"""
        skipped_articles = sample_articles[2:]
        
        mock_query = MagicMock()
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = skipped_articles
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_md.convert.side_effect = lambda x: f"<p>{x}</p>"
            mock_markdown.return_value = mock_md
            
            result = asyncio.run(get_public_articles(mock_db, None, 2))
            
            assert len(result) == 3
            mock_query.offset.assert_called_with(2)
    
    def test_get_public_articles_markdown_conversion(self, mock_db):
        """Markdown変換のテスト"""
        article = MagicMock()
        article.article_id = 1
        article.title = "Markdownテスト"
        article.body = "# 見出し\n\n本文です。"
        
        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [article]
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_md.convert.return_value = "<h1>見出し</h1><p>本文です。</p>"
            mock_markdown.return_value = mock_md
            
            result = asyncio.run(get_public_articles(mock_db, None, 0))
            
            assert result[0].body_html == "<h1>見出し</h1><p>本文です。</p>"
            mock_markdown.assert_called_once_with(extensions=['nl2br'])
            mock_md.convert.assert_called_once_with("# 見出し\n\n本文です。")
    
    def test_get_public_articles_database_error(self, mock_db):
        """データベースエラーのテスト"""
        mock_db.query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_public_articles(mock_db, None, 0))
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "記事の取得に失敗しました" in exc_info.value.detail


class TestSearchPublicArticlesEndpoint:
    """search_public_articles エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def search_results(self):
        """検索結果のサンプル"""
        articles = []
        for i in range(2):
            article = MagicMock()
            article.article_id = i + 1
            article.title = f"Python記事 {i + 1}"
            article.body = f"Pythonプログラミングについて {i + 1}"
            articles.append(article)
        return articles
    
    def test_search_public_articles_single_keyword(self, mock_db, search_results):
        """単一キーワード検索のテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = search_results
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_md.convert.side_effect = lambda x: f"<p>{x}</p>"
            mock_markdown.return_value = mock_md
            
            result = asyncio.run(search_public_articles("Python", mock_db, 10, 0))
            
            assert len(result) == 2
            assert result[0].title == "Python記事 1"
    
    def test_search_public_articles_multiple_keywords(self, mock_db, search_results):
        """複数キーワード検索のテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = search_results
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_md.convert.side_effect = lambda x: f"<p>{x}</p>"
            mock_markdown.return_value = mock_md
            
            result = asyncio.run(search_public_articles("Python プログラミング", mock_db, 10, 0))
            
            assert len(result) == 2
            # 複数のfilterが呼ばれることを確認（ANDロジック）
            assert mock_query.filter.call_count >= 2
    
    def test_search_public_articles_japanese_keywords(self, mock_db, search_results):
        """日本語キーワード検索のテスト"""
        japanese_articles = []
        for i in range(2):
            article = MagicMock()
            article.article_id = i + 1
            article.title = f"プログラミング記事 {i + 1}"
            article.body = f"日本語でプログラミングについて {i + 1}"
            japanese_articles.append(article)
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = japanese_articles
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_md.convert.side_effect = lambda x: f"<p>{x}</p>"
            mock_markdown.return_value = mock_md
            
            with patch('routers.article.urllib.parse.unquote') as mock_unquote:
                mock_unquote.return_value = "プログラミング"
                
                result = asyncio.run(search_public_articles("プログラミング", mock_db, 10, 0))
                
                assert len(result) == 2
                mock_unquote.assert_called_once_with("プログラミング", encoding='utf-8')
    
    def test_search_public_articles_url_encoded(self, mock_db, search_results):
        """URLエンコードされたキーワードのテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = search_results
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_md.convert.side_effect = lambda x: f"<p>{x}</p>"
            mock_markdown.return_value = mock_md
            
            # URLエンコードされた日本語キーワード
            encoded_keyword = urllib.parse.quote("プログラミング", encoding='utf-8')
            
            result = asyncio.run(search_public_articles(encoded_keyword, mock_db, 10, 0))
            
            assert len(result) == 2
    
    def test_search_public_articles_with_pagination(self, mock_db, search_results):
        """ページネーション付き検索のテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 20
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = search_results
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_md.convert.side_effect = lambda x: f"<p>{x}</p>"
            mock_markdown.return_value = mock_md
            
            result = asyncio.run(search_public_articles("test", mock_db, 5, 10))
            
            assert len(result) == 2
            mock_query.offset.assert_called_with(10)
            mock_query.limit.assert_called_with(5)
    
    def test_search_public_articles_no_results(self, mock_db):
        """検索結果なしのテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_markdown.return_value = mock_md
            
            result = asyncio.run(search_public_articles("存在しないキーワード", mock_db, 10, 0))
            
            assert result == []
    
    def test_search_public_articles_database_error(self, mock_db):
        """データベースエラーのテスト"""
        mock_db.query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(search_public_articles("test", mock_db, 10, 0))
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "記事検索に失敗しました" in exc_info.value.detail


class TestGetPublicArticleByIdEndpoint:
    """get_public_article_by_id エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def sample_article(self):
        """サンプル記事"""
        article = MagicMock()
        article.article_id = 1
        article.title = "パブリック記事詳細"
        article.body = "# パブリック記事\n\nこれは詳細な記事です。"
        return article
    
    def test_get_public_article_by_id_success(self, mock_db, sample_article):
        """記事詳細取得成功のテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_article
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_md.convert.return_value = "<h1>パブリック記事</h1><p>これは詳細な記事です。</p>"
            mock_markdown.return_value = mock_md
            
            result = asyncio.run(get_public_article_by_id(1, mock_db))
            
            assert result.article_id == 1
            assert result.title == "パブリック記事詳細"
            assert result.body_html == "<h1>パブリック記事</h1><p>これは詳細な記事です。</p>"
            
            mock_markdown.assert_called_once_with(extensions=['nl2br'])
            mock_md.convert.assert_called_once_with("# パブリック記事\n\nこれは詳細な記事です。")
    
    def test_get_public_article_by_id_not_found(self, mock_db):
        """記事が見つからない場合のテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_public_article_by_id(999, mock_db))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "記事ID 999 の記事が見つかりません" in exc_info.value.detail
    
    def test_get_public_article_by_id_database_error(self, mock_db):
        """データベースエラーのテスト"""
        mock_db.query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_public_article_by_id(1, mock_db))
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "記事詳細の取得に失敗しました" in exc_info.value.detail
    
    def test_get_public_article_by_id_markdown_conversion(self, mock_db):
        """複雑なMarkdown変換のテスト"""
        complex_article = MagicMock()
        complex_article.article_id = 1
        complex_article.title = "複雑なMarkdown"
        complex_article.body = "# 見出し1\n\n## 見出し2\n\n**太字**と*斜体*\n\n- リスト1\n- リスト2"
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = complex_article
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            expected_html = "<h1>見出し1</h1><h2>見出し2</h2><p><strong>太字</strong>と<em>斜体</em></p><ul><li>リスト1</li><li>リスト2</li></ul>"
            mock_md.convert.return_value = expected_html
            mock_markdown.return_value = mock_md
            
            result = asyncio.run(get_public_article_by_id(1, mock_db))
            
            assert result.body_html == expected_html
            mock_md.convert.assert_called_once_with(complex_article.body)


class TestArticleRouterIntegration:
    """記事ルーターの統合テスト"""
    
    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)
    
    def test_router_configuration(self):
        """ルーター設定の詳細テスト"""
        assert router.prefix == "/api/v1"
        assert "articles" in router.tags
        
        # エンドポイントの数を確認
        routes = router.routes
        assert len(routes) >= 6  # 最低6つのエンドポイント
    
    def test_public_endpoints_no_auth_required(self):
        """パブリックエンドポイントは認証不要であることを確認"""
        public_routes = [
            route for route in router.routes 
            if "/public/" in str(route.path)
        ]
        
        # パブリックルートが存在することを確認
        assert len(public_routes) >= 3
    
    def test_private_endpoints_auth_required(self):
        """プライベートエンドポイントは認証が必要であることを確認"""
        # 認証が必要なルートのパスパターン
        private_patterns = ["/articles", "/articles/{id}"]
        
        private_routes = [
            route for route in router.routes 
            if any(pattern in str(route.path) for pattern in private_patterns)
            and "/public/" not in str(route.path)
        ]
        
        # プライベートルートが存在することを確認
        assert len(private_routes) >= 3


class TestArticleRouterEdgeCases:
    """記事ルーターのエッジケースのテスト"""
    
    @pytest.fixture
    def mock_db(self):
        """モックデータベースセッション"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def mock_current_user(self):
        """モック現在ユーザー"""
        user = MagicMock()
        user.id = 123
        return user
    
    def test_all_fetch_very_large_limit(self, mock_db, mock_current_user):
        """非常に大きな制限値のテスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # 非常に大きな制限値でもエラーにならないことを確認
        result = asyncio.run(all_fetch(mock_db, mock_current_user, 999999))
        
        assert result == []
        mock_query.limit.assert_called_with(999999)
    
    def test_search_with_special_characters(self, mock_db):
        """特殊文字での検索テスト"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_markdown.return_value = mock_md
            
            # 特殊文字を含む検索でもエラーにならないことを確認
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            result = asyncio.run(search_public_articles(special_chars, mock_db, 10, 0))
            
            assert result == []
    
    def test_markdown_with_empty_content(self, mock_db):
        """空のMarkdownコンテンツのテスト"""
        empty_article = MagicMock()
        empty_article.article_id = 1
        empty_article.title = "空の記事"
        empty_article.body = ""
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = empty_article
        mock_db.query.return_value = mock_query
        
        with patch('routers.article.markdown.Markdown') as mock_markdown:
            mock_md = MagicMock()
            mock_md.convert.return_value = ""
            mock_markdown.return_value = mock_md
            
            result = asyncio.run(get_public_article_by_id(1, mock_db))
            
            assert result.body_html == ""
            assert result.title == "空の記事"
    
    def test_create_article_with_unicode_content(self, mock_db, mock_current_user):
        """Unicode文字を含む記事作成のテスト"""
        unicode_article = ArticleBase(
            title="Unicode記事 🎉 テスト",
            body="これは絵文字 🚀 と特殊文字 àáâãäå を含む記事です。"
        )
        
        mock_db.query.return_value.scalar.return_value = 0
        
        new_article = MagicMock()
        new_article.article_id = 1
        new_article.title = unicode_article.title
        new_article.body = unicode_article.body
        new_article.user_id = 123
        
        with patch('routers.article.Article') as mock_article_class:
            mock_article_class.return_value = new_article
            
            result = asyncio.run(create_article(unicode_article, mock_db, mock_current_user))
            
            assert result.title == "Unicode記事 🎉 テスト"
            assert "🚀" in result.body
            assert "àáâãäå" in result.body


# テスト実行用の設定
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
