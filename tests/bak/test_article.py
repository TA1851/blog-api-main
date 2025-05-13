import pytest
from unittest.mock import patch, MagicMock, call
import sys
import os
import io
import contextlib
from fastapi import HTTPException, status


# テスト対象のモジュールをインポートするための準備
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# テスト対象の関数をインポート
from routers.article import check_environment_variable, check_db_url, get_db, all_fetch, \
  Article, ArticleBase, get_article, Session, create_article, update_article, delete_article

class TestEnvironmentChecks:
    """環境変数チェック関数のテストクラス"""

    @patch("routers.article.key07", "test_key07")
    @patch("routers.article.create_logger")
    @patch("routers.article.create_error_logger")
    def test_check_environment_variable_success(
        self, mock_error_logger, mock_logger
    ):
        """環境変数key07が設定されている場合のテスト"""
        result = check_environment_variable()

        assert result == "test_key07"
        mock_logger.assert_called_once_with("環境変数test_key07を取得しました。:")
        mock_error_logger.assert_not_called()

    @patch("routers.article.key07", None)
    @patch("routers.article.create_logger")
    @patch("routers.article.create_error_logger")
    def test_check_environment_variable_failure(
        self, mock_error_logger, mock_logger
    ):
        """環境変数key07が設定されていない場合のテスト"""
        with pytest.raises(ValueError) as excinfo:
            check_environment_variable()
        assert "環境変数が設定されていません。-> None" in str(excinfo.value)

        mock_error_logger.assert_called_once_with("環境変数:Noneが設定されていません。None")
        mock_logger.assert_not_called()

    @patch("routers.article.db_url", "test_db_url")
    @patch("routers.article.key03", "test_key03")
    @patch("routers.article.create_logger")
    @patch("routers.article.create_error_logger")
    def test_check_db_url_success(self, mock_error_logger, mock_logger):
        """DB URLが設定されている場合のテスト"""
        result = check_db_url()

        assert result == "test_db_url"
        mock_logger.assert_called_once_with("環境変数: test_db_urlを読み込みました。 -> test_key03")
        mock_error_logger.assert_not_called()

    @patch("routers.article.db_url", None)
    @patch("routers.article.key03", "test_key03")
    @patch("routers.article.create_logger")
    @patch("routers.article.create_error_logger")
    def test_check_db_url_failure(self, mock_error_logger, mock_logger):
        """DB URLが設定されていない場合のテスト"""
        with pytest.raises(ValueError) as excinfo:
            check_db_url()

        assert "環境変数が設定されていません。test_key03" in str(excinfo.value)

        mock_error_logger.assert_called_once_with("環境変数:Noneが設定されていません。 -> test_key03")
        mock_logger.assert_not_called()


class TestGetDB:
    """get_db関数のテストクラス"""

    @patch("routers.article.session")
    @patch("routers.article.create_logger")
    @patch("routers.article.create_error_logger")
    def test_get_db_success(self, mock_error_logger, mock_logger, mock_session):
        """正常系: DBセッションが正常に取得され、クローズされることを検証"""
        # モックセッションの設定
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # 標準出力をキャプチャするための設定
        captured_output = io.StringIO()

        # 関数を実行し、標準出力をキャプチャ
        with contextlib.redirect_stdout(captured_output):
            # get_db()を呼び出して変数に格納し、ジェネレータオブジェクトを使用してテスト
            db_gen = get_db()
            db = next(db_gen)

            # セッションの検証
            assert db == mock_db

            # ジェネレータが完了するまで実行（finallyブロックの実行）
            try:
                # send(None)を使用して次のyieldまで進める
                # ただしこのケースではもうyieldがないのでStopIterationが発生する
                db_gen.send(None) # StopIterationを意図的に発生させるために next() ではなく send(None) を使用
            except StopIteration:
                pass

        # 標準出力の検証
        output = captured_output.getvalue()
        assert "DBセッションをコミットしました" in output
        assert "DBセッションをクローズしました" in output

        # ログ記録の検証
        mock_logger.assert_has_calls([
            call("DBセッションをコミットしました"),
            call("DBセッションをクローズしました")
        ], any_order=True)

        # エラーログが記録されていないことを確認
        mock_error_logger.assert_not_called()

        # セッションのcloseが呼ばれたことを確認
        mock_db.close.assert_called_once()

    @patch("routers.article.session")
    @patch("routers.article.create_logger")
    @patch("routers.article.create_error_logger")
    @patch("routers.article.pprint.pprint")
    def test_get_db_with_exception(self, mock_pprint, mock_error_logger, mock_logger, mock_session):
        """異常系: 例外が発生した場合のテスト"""
        # モックセッションの設定
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # 例外を発生させる
        test_exception = Exception("テスト用例外")

        # 標準出力をキャプチャするための設定
        captured_output = io.StringIO()

        # コンテキストマネージャを使用して、例外をテスト
        with contextlib.redirect_stdout(captured_output):
            # ジェネレータを取得
            db_gen = get_db()

            # 最初のyieldまで進める
            db = next(db_gen)

            # セッションが返されることを確認
            assert db == mock_db

            # 例外を発生させる（tryブロック内でのエラー）
            with pytest.raises(Exception) as excinfo:
                # send()を使用して例外を発生させる
                db_gen.throw(test_exception)

            # 発生した例外の検証
            assert excinfo.value == test_exception

        # 標準出力の検証（コミットメッセージは出ないはず）
        output = captured_output.getvalue()
        assert "DBセッションをコミットしました" not in output
        assert "DBセッションをクローズしました" in output

        # エラーログの検証
        mock_error_logger.assert_called_once()
        error_log_args = mock_error_logger.call_args[0][0]
        assert "DBセッションのコミットに失敗しました。: テスト用例外" in error_log_args

        # pprintが呼ばれたことを確認
        mock_pprint.assert_called_once_with("テスト用例外")

        # クローズログの検証
        close_log_call = [call for call in mock_logger.call_args_list if call[0][0] == "DBセッションをクローズしました"]
        assert len(close_log_call) == 1

        # セッションのcloseが呼ばれたことを確認
        mock_db.close.assert_called_once()

    @patch("routers.article.session")
    @patch("routers.article.create_logger")
    @patch("routers.article.create_error_logger")
    def test_get_db_as_context_manager(self, mock_error_logger, mock_logger, mock_session):
        """contextlibを使用したコンテキストマネージャとしてのテスト"""
        # モックセッションの設定
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # 標準出力をキャプチャするための設定
        captured_output = io.StringIO()

        # contextlib.closingを使用してwithステートメントで使用する
        with contextlib.redirect_stdout(captured_output):
            from contextlib import closing
            with closing(get_db()) as db_gen:
                db = next(db_gen)
                assert db == mock_db

        # 標準出力の検証
        output = captured_output.getvalue()
        assert "DBセッションをクローズしました" in output

        # # ログ記録の検証
        mock_logger.assert_has_calls([
            call("DBセッションをクローズしました")
        ], any_order=True)

        # セッションのcloseが呼ばれたことを確認
        mock_db.close.assert_called_once()

"""FastAPIの TestClient は内部的に非同期処理を同期処理に変換するので、通常の同期テストとして記述できます"""
class TestAllFetch:
    """all_fetch関数のテストクラス"""
    @pytest.mark.asyncio # 非同期関数を実行するためのマーカー
    @patch("routers.article.create_logger")
    @patch("routers.article.create_error_logger")
    async def test_all_fetch_success(self, mock_error_logger, mock_logger):
        """
        正常系: ブログ記事が存在する場合のテスト
        """
        # モックデータ
        mock_articles = [
            MagicMock(id=1, title="テスト記事1", content="テスト内容1"),
            MagicMock(id=2, title="テスト記事2", content="テスト内容2"),
        ]

        # モックセッション
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = mock_articles
        print(mock_articles)
        # 標準出力をキャプチャ
        captured_output = io.StringIO()

        # 関数を実行し、標準出力をキャプチャ
        with contextlib.redirect_stdout(captured_output):
            result = await all_fetch(db=mock_db)
        # print(f"result：{result}")

        # 戻り値の検証
        assert result == mock_articles

        # ログの検証
        mock_logger.assert_called_once_with("ブログ記事を全件取得しました。")
        mock_error_logger.assert_not_called()

        # 標準出力の検証
        output = captured_output.getvalue()
        assert mock_articles.__str__() in output
        assert "ブログ記事を全件取得しました。" in output

        # データベースクエリの検証
        mock_db.query.assert_called_once_with(Article)
        mock_db.query.return_value.all.assert_called_once()


    @pytest.mark.asyncio
    @patch("routers.article.key07", "test_key07")
    @patch("routers.article.create_logger")
    @patch("routers.article.create_error_logger")
    async def test_all_fetch_not_found(self, mock_error_logger, mock_logger):
        """
        異常系: ブログ記事が存在しない場合のテスト
        """
        # モックセッションの準備 - 空のリストを返す
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        # 標準出力をキャプチャ
        captured_output = io.StringIO()

        # HTTPExceptionがスローされることを検証
        with contextlib.redirect_stdout(captured_output):
            with pytest.raises(HTTPException) as excinfo:
                await all_fetch(db=mock_db)  # awaitを使用

        # 例外の詳細を検証
        assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
        assert f"Article not found test_key07" in excinfo.value.detail

        # ログの検証
        mock_logger.assert_called_once_with("ブログ記事を全件取得しました。")
        mock_error_logger.assert_not_called()

        # データベースクエリの検証
        mock_db.query.assert_called_once_with(Article)
        mock_db.query.return_value.all.assert_called_once()

    @pytest.mark.asyncio
    @patch("routers.article.key07", "test_key07")
    @patch("routers.article.create_logger")
    @patch("routers.article.create_error_logger")
    @patch("routers.article.pprint.pprint")
    async def test_all_fetch_value_error(self, mock_pprint, mock_error_logger, mock_logger):
        """
        異常系: ValueError例外が発生する場合のテスト
        """
        # モックセッションの準備 - 例外を発生させる
        mock_db = MagicMock()
        test_error = ValueError("テスト用エラー")
        mock_db.query.return_value.all.side_effect = test_error

        # 標準出力をキャプチャ
        captured_output = io.StringIO()

        # HTTPExceptionがスローされることを検証
        with contextlib.redirect_stdout(captured_output):
            with pytest.raises(HTTPException) as excinfo:
                await all_fetch(db=mock_db)  # awaitを使用

        # 例外の詳細を検証
        assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
        assert f"Article not found test_key07" in excinfo.value.detail

        # ログの検証
        mock_logger.assert_not_called()
        mock_error_logger.assert_called_once_with("ブログ記事の全件取得に失敗しました。test_key07")

        # pprintが呼ばれたことを確認
        mock_pprint.assert_called_once_with("テスト用エラー")

        # データベースクエリの検証
        mock_db.query.assert_called_once_with(Article)
        mock_db.query.return_value.all.assert_called_once()


class TestGetArticle:
    """記事取得API関数のテストクラス"""

    @pytest.mark.asyncio
    @patch("routers.article.get_db")
    @patch("routers.article.create_logger")
    async def test_get_article_success(self, mock_logger, mock_get_db):
        """指定したIDのブログ記事を正常に取得できる場合のテスト"""
        # テスト用のデータ準備
        article_id = 1
        expected_article = Article(
            id=article_id,
            title="テスト記事",
            body="これはテスト記事です",
        )

        # モックの設定
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = expected_article
        mock_get_db.return_value = mock_db

        # 関数を直接呼び出し
        result = await get_article(id=article_id, db=mock_db)

        # 検証
        assert result.id == article_id
        assert result.title == "テスト記事"
        assert result.body == "これはテスト記事です"

        # モックの呼び出し確認
        mock_db.query.assert_called_once_with(Article)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()
        mock_logger.assert_called_once_with("指定したIDのブログ記事を取得しました。")

class TestCreateArticle:
    """記事作成API関数のテストクラス"""

    @pytest.mark.asyncio
    @patch("routers.article.create_error_logger")
    @patch("routers.article.create_logger")
    @patch("routers.article.get_db")
    async def test_create_article_success(self, mock_get_db, mock_create_logger, mock_create_error_logger):
        """記事作成が成功するケースのテスト"""
        # テスト用のモックDBセッションを作成
        mock_session = MagicMock(spec=Session)
        mock_get_db.return_value = mock_session

        # テスト用の記事データ
        test_article = ArticleBase(title="テストタイトル", body="テスト本文")

        # DBから返される記事オブジェクトをモック
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, "id", 1))

        # テスト対象の関数を実行
        result = await create_article(blog=test_article, db=mock_session)

        # 検証
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        mock_create_logger.assert_called_once()

        # 戻り値の検証
        assert result.id == 1
        assert result.title == "テストタイトル"
        assert result.body == "テスト本文"

        # create_loggerが呼ばれていることを確認
        mock_create_logger.assert_called_once()
        # create_error_loggerは呼ばれていないことを確認
        mock_create_error_logger.assert_not_called()


class TestUpdateArticle:
    """記事更新API関数のテストクラス"""

    @pytest.mark.asyncio
    async def test_update_article_success(self):
        """記事更新の成功ケースをテスト"""
        # モックの設定
        mock_db = MagicMock(spec=Session)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_article = mock_filter.first.return_value

        # テストデータ
        article_id = 1
        article_data = ArticleBase(title="更新タイトル", body="更新本文")

        # テスト用の記事オブジェクトを設定
        mock_article.id = article_id

        # create_loggerのモック
        with patch('routers.article.create_logger') as mock_create_logger:
            # 関数の実行
            result = await update_article(article_id, article_data, mock_db)

            # アサーション
            assert result == mock_article
            assert result.title == article_data.title
            assert result.body == article_data.body
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_article)
            # ロガーが呼ばれたことを確認
            mock_create_logger.assert_called_once()
            assert "記事を更新しました" in mock_create_logger.call_args[0][0]


    @pytest.mark.asyncio
    async def test_update_article_not_found(self):
        """記事がない場合は404を返すことをテスト"""
        # モックの設定
        mock_db = MagicMock(spec=Session)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        # 記事が見つからない状況を設定
        mock_filter.first.return_value = None

        # テストデータ
        article_id = 999  # 存在しないID
        article_data = ArticleBase(title="更新タイトル", body="更新本文")

        # HTTPExceptionが発生することを検証
        with pytest.raises(HTTPException) as exc_info:
            await update_article(article_id, article_data, mock_db)

        # アサーション
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert f"Article not found -> Article_id:{article_id}" in exc_info.value.detail


    @pytest.mark.asyncio
    async def test_update_article_logger_verification(self):
        """更新が成功したらcreate_loggerの検証をする"""
        # モックの設定
        mock_db = MagicMock(spec=Session)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_article = mock_filter.first.return_value

        # テストデータ
        article_id = 1
        article_data = ArticleBase(title="更新タイトル", body="更新本文")

        # create_loggerのモック
        with patch('routers.article.create_logger') as mock_logger:
            # 関数の実行
            await update_article(article_id, article_data, mock_db)

            # ロガーの呼び出しを検証
            mock_logger.assert_called_once()
            log_message = mock_logger.call_args[0][0]
            assert "記事を更新しました" in log_message
            assert "articles.py" in log_message


    @pytest.mark.asyncio
    async def test_no_error_log_on_success(self):
        """正常終了時にエラーログは発生しないことをテスト"""
        # モックの設定
        mock_db = MagicMock(spec=Session)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_article = mock_filter.first.return_value

        # テストデータ
        article_id = 1
        article_data = ArticleBase(title="更新タイトル", body="更新本文")

        # ロガーのモック
        with patch('routers.article.create_logger') as mock_logger, \
            patch('routers.article.create_error_logger') as mock_error_logger:

            # 関数の実行
            await update_article(article_id, article_data, mock_db)

            # 通常のログは呼ばれるがエラーログは呼ばれないことを確認
            mock_logger.assert_called_once()
            mock_error_logger.assert_not_called()


class TestDeleteArticle:
    """記事削除API関数のテストクラス"""

    @pytest.mark.asyncio
    async def test_delete_article_success(self):
        """記事の削除が成功するケースのテスト"""
        # モックの設定
        mock_db = MagicMock()
        mock_article = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_article

        # key07 が何かを定義（実際のコードに合わせて調整）
        with patch('routers.article.key07', 'test_key'):
            with patch('routers.article.create_logger') as mock_logger:
                # 関数を呼び出し
                from routers.article import delete_article
                result = await delete_article(id=1, db=mock_db)

                # アサーション
                mock_db.delete.assert_called_once_with(mock_article, synchronize_session=False)
                mock_db.commit.assert_called_once()
                mock_logger.assert_called_once()
                assert result == mock_article

    @pytest.mark.asyncio
    async def test_delete_article_not_found(self):
        """存在しない記事を削除しようとして404エラーを返すケース"""
        # モックの設定
        mock_db = MagicMock()
        # 記事が見つからない状況をシミュレート
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 関数をインポート
        from routers.article import delete_article

        # key07 の値をパッチ
        with patch('routers.article.key07', 'test_key'):
            # HTTPException が発生することを確認
            with pytest.raises(HTTPException) as excinfo:
                await delete_article(id=999, db=mock_db)

            # 例外の詳細を確認
            assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Article not found" in str(excinfo.value.detail)

            # delete や commit が呼ばれていないことを確認
            mock_db.delete.assert_not_called()
            mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_article_failure(self):
        """削除処理中にエラーが発生して400を返すケース"""
        # モックの設定
        mock_db = MagicMock()
        mock_article = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_article

        # delete で例外を発生させる
        mock_db.delete.side_effect = ValueError("Test error")

        # 関数をインポート
        from routers.article import delete_article

        # key07 の値をパッチ
        with patch('routers.article.key07', 'test_key'):
            with patch('routers.article.create_error_logger') as mock_error_logger:
                with patch('routers.article.pprint.pprint') as mock_pprint:
                    # HTTPException が発生することを確認
                    with pytest.raises(HTTPException) as excinfo:
                        await delete_article(id=1, db=mock_db)

                    # 例外の詳細を確認
                    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
                    assert "Article not deleted" in str(excinfo.value.detail)

                    # エラーログが呼ばれたことを確認
                    mock_error_logger.assert_called_once()
                    mock_pprint.assert_called_once()


# TODO: Articleのテストクラスを作成する