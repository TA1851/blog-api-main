from models import Article
from unittest.mock import patch
import pytest


# fixture
@pytest.fixture
def mock_logger():
    """ロガー関数をモックするfixture
        1. patchでモックを作成
            patch("models.create_logger"): patch("module_name.function_name")を記述する。
        2. yieldでテスト関数に渡す
            yield mock_create_logger, mock_create_error_logger
        3. テスト関数が終了したら、モックを削除
        4. モックを削除するための処理は、yieldの後に記述する。
    """
    with patch("models.create_logger") as mock_create_logger:
        with patch("models.create_error_logger") as mock_create_error_logger:
            yield mock_create_logger, mock_create_error_logger


class TestArticle:
    """Articleクラスのテストクラス"""

    def test_article_initialization(self, mock_logger):
        """Articleクラスの初期化テスト
            1. MockDataを作成する
            article = Article(id=1, title="Test Title", body="Test Body")
            2. MockDataの属性を検証する
            assert article.id == 1
            assert article.title == "Test Title"
            assert article.body == "Test Body"
        """
        mock_create_logger, mock_create_error_logger = mock_logger
        article = Article(id=1, title="Test Title", body="Test Body")
        assert article.id == 1
        assert article.title == "Test Title"
        assert article.body == "Test Body"

        # ロガーが呼び出されたか確認
        mock_create_logger.assert_called_once_with("Articleインスタンスが作成されました。")
        mock_create_error_logger.assert_not_called()

    def test_article_class_attributes(self):
        """Articleクラスの属性テスト
            1. Articleクラスの型を確認する
                assert hasattr(Article, '__table__')
            2. __table__オブジェクトからカラム情報を取得する
                columns = Article.__table__.columns
            3. 各カラム名の確認
                assert 'id' in columns
                assert 'title' in columns
                assert 'body' in columns
            4. カラムのプロパティを確認する
                assert columns['id'].primary_key is True
                assert columns['id'].type.__class__.__name__ == "Integer"
                assert columns['title'].type.__class__.__name__ == "String"
                assert columns['body'].type.__class__.__name__ == "String"
            """
        assert hasattr(Article, '__table__')
        columns = Article.__table__.columns
        assert 'id' in columns
        assert 'title' in columns
        assert 'body' in columns
        assert columns['id'].primary_key is True
        assert columns['id'].type.__class__.__name__ == "Integer"
        assert columns['title'].type.__class__.__name__ == "String"
        assert columns['body'].type.__class__.__name__ == "String"

    def test_article_class_name(self):
        """Articleクラスのクラス名テスト
            1. Articleクラスのクラス名を確認する
                assert Article.__name__ == "Article"
            2. Articleクラスのテーブル名を確認する
                assert Article.__tablename__ == "articles"
        """
        assert Article.__name__ == "Article"
        assert Article.__tablename__ == "articles"