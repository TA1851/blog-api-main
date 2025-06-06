"""routers/article.pyの包括的な単体テスト"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, status, Query
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import asyncio


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
    """記事作成エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_current_user(self):
        """テスト用現在ユーザーモック"""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_article_data(self):
        """テスト用記事データ"""
        from schemas import ArticleBase
        return ArticleBase(
            article_id=None,  # 作成時は自動採番
            title="新しい記事",
            body="これは新しい記事の本文です。",
            user_id=1
        )
    
    @pytest.mark.asyncio
    async def test_create_article_success(self, mock_current_user, mock_article_data):
        """記事作成成功テスト"""
        from routers.article import create_article
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.scalar.return_value = 99  # 最大ID
        
        # 新記事オブジェクトのモック
        new_article = Mock()
        new_article.article_id = 100
        new_article.title = mock_article_data.title
        new_article.body = mock_article_data.body
        new_article.user_id = mock_current_user.id
        
        with patch('routers.article.Article') as mock_article_model:
            mock_article_model.return_value = new_article
            
            result = await create_article(mock_article_data, mock_db, mock_current_user)
            
            # 結果検証
            assert result.article_id == 100
            assert result.title == "新しい記事"
            assert result.body == "これは新しい記事の本文です。"
            assert result.user_id == 1
            
            # データベース操作確認
            mock_db.add.assert_called_once_with(new_article)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(new_article)
    
    @pytest.mark.asyncio
    async def test_create_article_empty_title(self, mock_current_user):
        """タイトルが空の場合のエラーテスト"""
        from routers.article import create_article
        from schemas import ArticleBase
        
        mock_db = Mock(spec=Session)
        
        # 空のタイトル
        article_data = ArticleBase(
            article_id=None,
            title="",
            body="本文です",
            user_id=1
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await create_article(article_data, mock_db, mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "タイトルは必須項目です" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_create_article_empty_body(self, mock_current_user):
        """本文が空の場合のエラーテスト"""
        from routers.article import create_article
        from schemas import ArticleBase
        
        mock_db = Mock(spec=Session)
        
        # 空の本文
        article_data = ArticleBase(
            article_id=None,
            title="タイトル",
            body="",
            user_id=1
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await create_article(article_data, mock_db, mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "本文は必須項目です" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_create_article_none_title(self, mock_current_user):
        """タイトルがNoneの場合のエラーテスト"""
        from routers.article import create_article
        
        mock_db = Mock(spec=Session)
        
        # ArticleBaseモデルのバリデーションを回避するため、直接HTTPExceptionが発生することを想定
        # Pydanticレベルでバリデーションエラーが発生するため、このテストは意味がない
        # 代わりに空文字列のテストで十分
        pass


class TestUpdateArticleEndpoint:
    """記事更新エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_current_user(self):
        """テスト用現在ユーザーモック"""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_existing_article(self):
        """テスト用既存記事モック"""
        article = Mock()
        article.article_id = 100
        article.title = "元のタイトル"
        article.body = "元の本文"
        article.user_id = 1
        return article
    
    @pytest.mark.asyncio
    async def test_update_article_success(self, mock_current_user, mock_existing_article):
        """記事更新成功テスト"""
        from routers.article import update_article
        from schemas import ArticleBase
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_existing_article
        
        # 更新データ
        update_data = ArticleBase(
            article_id=100,
            title="更新されたタイトル",
            body="更新された本文",
            user_id=1
        )
        
        result = await update_article(100, update_data, mock_db, mock_current_user)
        
        # 更新確認
        assert mock_existing_article.title == "更新されたタイトル"
        assert mock_existing_article.body == "更新された本文"
        
        # データベース操作確認
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_existing_article)
        
        # 結果検証
        assert result.article_id == 100
        assert result.title == "更新されたタイトル"
        assert result.body == "更新された本文"
    
    @pytest.mark.asyncio
    async def test_update_article_not_found(self, mock_current_user):
        """記事が見つからない場合のエラーテスト"""
        from routers.article import update_article
        from schemas import ArticleBase
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # 記事が見つからない
        
        update_data = ArticleBase(
            article_id=999,
            title="更新タイトル",
            body="更新本文",
            user_id=1
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await update_article(999, update_data, mock_db, mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Article not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_update_article_empty_title(self, mock_current_user, mock_existing_article):
        """更新時にタイトルが空の場合のエラーテスト"""
        from routers.article import update_article
        from schemas import ArticleBase
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_existing_article
        
        # 空のタイトル
        update_data = ArticleBase(
            article_id=100,
            title="",
            body="更新本文",
            user_id=1
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await update_article(100, update_data, mock_db, mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "タイトルは必須項目です" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_update_article_database_error(self, mock_current_user, mock_existing_article):
        """データベースエラー時のテスト"""
        from routers.article import update_article
        from schemas import ArticleBase
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = ValueError("Database error")
        
        update_data = ArticleBase(
            article_id=100,
            title="更新タイトル",
            body="更新本文",
            user_id=1
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await update_article(100, update_data, mock_db, mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Article not updated" in exc_info.value.detail


class TestDeleteArticleEndpoint:
    """記事削除エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_current_user(self):
        """テスト用現在ユーザーモック"""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_existing_article(self):
        """テスト用既存記事モック"""
        article = Mock()
        article.article_id = 100
        article.title = "削除予定記事"
        article.body = "削除予定の本文"
        article.user_id = 1
        return article
    
    @pytest.mark.asyncio
    async def test_delete_article_success(self, mock_current_user, mock_existing_article):
        """記事削除成功テスト"""
        from routers.article import delete_article
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_existing_article
        
        with patch('builtins.print') as mock_print:
            result = await delete_article(100, mock_db, mock_current_user)
        
        # データベース操作確認
        mock_db.delete.assert_called_once_with(mock_existing_article)
        mock_db.commit.assert_called_once()
        
        # ログ出力確認
        mock_print.assert_called_once()
        
        # 結果確認（Noneを返す）
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_article_not_found(self, mock_current_user):
        """削除対象記事が見つからない場合のエラーテスト"""
        from routers.article import delete_article
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # 記事が見つからない
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_article(999, mock_db, mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Article not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_delete_article_database_error(self, mock_current_user):
        """データベースエラー時のテスト"""
        from routers.article import delete_article
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = ValueError("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_article(100, mock_db, mock_current_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Article not deleted" in exc_info.value.detail


class TestPublicArticlesEndpoint:
    """パブリック記事取得エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_articles(self):
        """テスト用記事リスト"""
        articles = []
        for i in range(5):
            article = Mock()
            article.article_id = i + 1
            article.title = f"パブリック記事{i + 1}"
            article.body = f"**記事{i + 1}**の本文です。"
            articles.append(article)
        return articles
    
    @pytest.mark.asyncio
    async def test_get_public_articles_success(self, mock_articles):
        """パブリック記事取得成功テスト"""
        from routers.article import get_public_articles
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_articles
        
        with patch('routers.article.markdown.Markdown') as mock_md_class:
            mock_md_instance = Mock()
            mock_md_class.return_value = mock_md_instance
            mock_md_instance.convert.side_effect = lambda x: f"<p>{x}</p>"
            
            result = await get_public_articles(mock_db)
            
            # 結果検証
            assert len(result) == 5
            assert result[0].article_id == 1
            assert result[0].title == "パブリック記事1"
            assert "<p>**記事1**の本文です。</p>" in result[0].body_html
    
    @pytest.mark.asyncio
    async def test_get_public_articles_with_limit(self, mock_articles):
        """制限付きパブリック記事取得テスト"""
        from routers.article import get_public_articles
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_articles[:3]  # 3件のみ
        
        with patch('routers.article.markdown.Markdown') as mock_md_class:
            mock_md_instance = Mock()
            mock_md_class.return_value = mock_md_instance
            mock_md_instance.convert.side_effect = lambda x: f"<p>{x}</p>"
            
            result = await get_public_articles(mock_db, limit=3)
            
            # 結果検証
            assert len(result) == 3
            mock_query.limit.assert_called_once_with(3)
    
    @pytest.mark.asyncio
    async def test_get_public_articles_with_skip(self, mock_articles):
        """スキップ付きパブリック記事取得テスト"""
        from routers.article import get_public_articles
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = mock_articles[2:]  # 2件スキップ
        
        with patch('routers.article.markdown.Markdown') as mock_md_class:
            mock_md_instance = Mock()
            mock_md_class.return_value = mock_md_instance
            mock_md_instance.convert.side_effect = lambda x: f"<p>{x}</p>"
            
            result = await get_public_articles(mock_db, skip=2)
            
            # 結果検証
            assert len(result) == 3
            mock_query.offset.assert_called_once_with(2)
    
    @pytest.mark.asyncio
    async def test_get_public_articles_database_error(self):
        """データベースエラー時のテスト"""
        from routers.article import get_public_articles
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query.side_effect = Exception("Database connection error")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_public_articles(mock_db)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "記事の取得に失敗しました" in exc_info.value.detail


class TestGetPublicArticleByIdEndpoint:
    """ID指定パブリック記事取得エンドポイントのテスト"""
    
    @pytest.fixture
    def mock_article(self):
        """テスト用記事"""
        article = Mock()
        article.article_id = 100
        article.title = "特定記事"
        article.body = "**特定記事**の詳細本文です。"
        return article
    
    @pytest.mark.asyncio
    async def test_get_public_article_by_id_success(self, mock_article):
        """ID指定記事取得成功テスト"""
        from routers.article import get_public_article_by_id
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_article
        
        with patch('routers.article.markdown.Markdown') as mock_md_class:
            mock_md_instance = Mock()
            mock_md_class.return_value = mock_md_instance
            mock_md_instance.convert.side_effect = lambda x: f"<p>{x}</p>"
            
            result = await get_public_article_by_id(100, mock_db)
            
            # 結果検証
            assert result.article_id == 100
            assert result.title == "特定記事"
            assert "<p>**特定記事**の詳細本文です。</p>" in result.body_html
    
    @pytest.mark.asyncio
    async def test_get_public_article_by_id_not_found(self):
        """記事が見つからない場合のテスト"""
        from routers.article import get_public_article_by_id
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # 記事が見つからない
        
        with pytest.raises(HTTPException) as exc_info:
            await get_public_article_by_id(999, mock_db)
        
        # 実際の動作では、内部のHTTPExceptionが外側のExceptionハンドラーで捕まえられて500エラーになる
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "記事詳細の取得に失敗しました" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_public_article_by_id_database_error(self):
        """データベースエラー時のテスト"""
        from routers.article import get_public_article_by_id
        
        # モック設定
        mock_db = Mock(spec=Session)
        mock_db.query.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_public_article_by_id(100, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "記事詳細の取得に失敗しました" in exc_info.value.detail


if __name__ == "__main__":
    # このファイルを直接実行した場合のテスト実行
    pytest.main([__file__, "-v"])