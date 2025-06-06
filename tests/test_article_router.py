"""routers/article.pyの包括的な単体テスト"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, status, Query
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import List, Optional


class TestArticleRouterDependencies:
    """記事ルーターの依存関数テスト"""
    
    @pytest.fixture
    def mock_current_user(self):
        """テスト用現在ユーザーモック"""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        user.name = "テストユーザー"
        return user
    
    @pytest.fixture
    def mock_articles(self):
        """テスト用記事リスト"""
        articles = []
        for i in range(5):
            article = Mock()
            article.id = i + 1
            article.article_id = i + 100
            article.title = f"記事{i + 1}"
            article.body = f"記事{i + 1}の本文です。"
            article.user_id = 1
            articles.append(article)
        return articles


class TestAllFetchEndpoint:
    """全記事取得エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_current_user(self):
        """テスト用現在ユーザーモック"""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_articles(self):
        """テスト用記事リスト"""
        articles = []
        for i in range(3):
            article = Mock()
            article.id = i + 1
            article.article_id = i + 100
            article.title = f"記事{i + 1}"
            article.body = f"記事{i + 1}の本文です。"
            article.user_id = 1
            articles.append(article)
        return articles
    
    @patch('routers.article.create_logger')
    def test_all_fetch_success_without_limit(self, mock_logger, mock_current_user, mock_articles):
        """制限なしでの全記事取得成功テスト"""
        from routers.article import all_fetch
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.all.return_value = mock_articles
        
        # 非同期関数のテスト
        async def test_fetch():
            result = await all_fetch(mock_db, mock_current_user, None)
            return result
        
        result = asyncio.run(test_fetch())
        
        # 結果検証
        assert len(result) == 3
        for i, article in enumerate(result):
            assert article.article_id == i + 100
            assert article.title == f"記事{i + 1}"
            assert article.body == f"記事{i + 1}の本文です。"
            assert article.user_id == 1
        
        # データベース呼び出し検証
        mock_db.query.assert_called()
        mock_logger.assert_called()
    
    @patch('routers.article.create_logger')
    def test_all_fetch_success_with_limit(self, mock_logger, mock_current_user, mock_articles):
        """制限ありでの記事取得成功テスト"""
        from routers.article import all_fetch
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_articles[:2]  # 制限で2件のみ
        
        # 非同期関数のテスト
        async def test_fetch():
            result = await all_fetch(mock_db, mock_current_user, 2)
            return result
        
        result = asyncio.run(test_fetch())
        
        # 結果検証
        assert len(result) == 2
        
        # limit呼び出し検証
        mock_query.limit.assert_called_with(2)
        mock_logger.assert_called()
    
    @patch('routers.article.create_error_logger')
    def test_all_fetch_no_articles_found(self, mock_error_logger, mock_current_user):
        """記事が見つからない場合のテスト"""
        from routers.article import all_fetch
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []
        
        # 非同期関数のテスト
        async def test_fetch():
            result = await all_fetch(mock_db, mock_current_user, None)
            return result
        
        result = asyncio.run(test_fetch())
        
        # 結果検証
        assert result == []
        mock_error_logger.assert_called()
    
    @patch('routers.article.create_error_logger')
    def test_all_fetch_database_error(self, mock_error_logger, mock_current_user):
        """データベースエラーの場合のテスト"""
        from routers.article import all_fetch
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query.side_effect = ValueError("Database error")
        
        # 非同期関数のテスト
        async def test_fetch():
            with pytest.raises(HTTPException) as exc_info:
                await all_fetch(mock_db, mock_current_user, None)
            return exc_info.value
        
        exception = asyncio.run(test_fetch())
        
        # 例外検証
        assert exception.status_code == status.HTTP_404_NOT_FOUND
        assert "Articles not found" in str(exception.detail)
        mock_error_logger.assert_called()


class TestGetArticleEndpoint:
    """特定記事取得エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_article(self):
        """テスト用記事モック"""
        article = Mock()
        article.id = 1
        article.article_id = 100
        article.title = "テスト記事"
        article.body = "テスト記事の本文です。"
        article.user_id = 1
        return article
    
    @patch('routers.article.create_logger')
    def test_get_article_success(self, mock_logger, mock_article):
        """記事取得成功テスト"""
        from routers.article import get_article
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_article
        
        # 非同期関数のテスト
        async def test_get():
            result = await get_article(100, mock_db)
            return result
        
        result = asyncio.run(test_get())
        
        # 結果検証
        assert result.article_id == 100
        assert result.title == "テスト記事"
        assert result.body == "テスト記事の本文です。"
        assert result.user_id == 1
        
        # データベース呼び出し検証
        mock_db.query.assert_called()
        mock_logger.assert_called()
    
    def test_get_article_not_found(self):
        """記事が見つからない場合のテスト"""
        from routers.article import get_article
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # 非同期関数のテスト
        async def test_get():
            with pytest.raises(HTTPException) as exc_info:
                await get_article(999, mock_db)
            return exc_info.value
        
        exception = asyncio.run(test_get())
        
        # 例外検証
        assert exception.status_code == status.HTTP_404_NOT_FOUND
        assert "Article not found" in str(exception.detail)
    
    @patch('routers.article.create_error_logger')
    def test_get_article_database_error(self, mock_error_logger):
        """データベースエラーの場合のテスト"""
        from routers.article import get_article
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query.side_effect = ValueError("Database error")
        
        # 非同期関数のテスト
        async def test_get():
            with pytest.raises(HTTPException) as exc_info:
                await get_article(100, mock_db)
            return exc_info.value
        
        exception = asyncio.run(test_get())
        
        # 例外検証
        assert exception.status_code == status.HTTP_404_NOT_FOUND
        assert "Article not found" in str(exception.detail)
        mock_error_logger.assert_called()


class TestCreateArticleEndpoint:
    """記事作成エンドポイントのテスト（存在する場合）"""
    
    def test_article_router_prefix_and_tags(self):
        """ルーターのprefix and tagsのテスト"""
        from routers.article import router
        
        # ルーター設定の確認
        assert router.prefix == "/api/v1"
        assert "articles" in router.tags


class TestArticleRouterIntegration:
    """記事ルーターの統合テスト"""
    
    @pytest.fixture
    def mock_current_user(self):
        """テスト用現在ユーザーモック"""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_articles(self):
        """テスト用記事リスト"""
        articles = []
        for i in range(2):
            article = Mock()
            article.id = i + 1
            article.article_id = i + 100
            article.title = f"統合テスト記事{i + 1}"
            article.body = f"統合テスト記事{i + 1}の本文です。"
            article.user_id = 1
            articles.append(article)
        return articles
    
    @patch('routers.article.create_logger')
    def test_article_lifecycle_flow(self, mock_logger, mock_current_user, mock_articles):
        """記事のライフサイクルフローテスト"""
        from routers.article import all_fetch, get_article
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        
        # all_fetch用のモック
        mock_query_all = Mock()
        mock_db.query.return_value = mock_query_all
        mock_query_all.filter.return_value = mock_query_all
        mock_query_all.count.return_value = 2
        mock_query_all.all.return_value = mock_articles
        
        # get_article用のモック設定
        def setup_get_article_mock():
            mock_query_get = Mock()
            mock_db.query.return_value = mock_query_get
            mock_query_get.filter.return_value = mock_query_get
            mock_query_get.first.return_value = mock_articles[0]
        
        # 統合テスト実行
        async def test_flow():
            # 全記事取得
            all_articles = await all_fetch(mock_db, mock_current_user, None)
            
            # 特定記事取得用にモックを再設定
            setup_get_article_mock()
            specific_article = await get_article(100, mock_db)
            
            return all_articles, specific_article
        
        all_articles, specific_article = asyncio.run(test_flow())
        
        # 結果検証
        assert len(all_articles) == 2
        assert specific_article.article_id == 100
        assert specific_article.title == "統合テスト記事1"
        
        # ログが呼ばれることを確認
        assert mock_logger.called


class TestArticleBaseModel:
    """ArticleBaseモデルのテスト"""
    
    def test_article_base_creation(self):
        """ArticleBaseモデルの作成テスト"""
        from schemas import ArticleBase
        
        # モデル作成
        article = ArticleBase(
            article_id=100,
            title="テストタイトル",
            body="テスト本文",
            user_id=1
        )
        
        # フィールド検証
        assert article.article_id == 100
        assert article.title == "テストタイトル"
        assert article.body == "テスト本文"
        assert article.user_id == 1


class TestQueryParameters:
    """クエリパラメータのテスト"""
    
    def test_limit_parameter_validation(self):
        """limit パラメータのバリデーションテスト"""
        from routers.article import all_fetch
        import asyncio
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_current_user = Mock()
        mock_current_user.id = 1
        
        # 正常なlimit値のテスト
        valid_limits = [1, 5, 10, 100]
        
        for limit in valid_limits:
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 0
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            
            # 非同期関数のテスト
            async def test_limit():
                result = await all_fetch(mock_db, mock_current_user, limit)
                return result
            
            result = asyncio.run(test_limit())
            
            # 空の結果が返されることを確認
            assert result == []


if __name__ == "__main__":
    # このファイルを直接実行した場合のテスト実行
    pytest.main([__file__, "-v"])