import os
import pytest
import time
from pathlib import Path
from typing import Callable
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import Engine

from database import check_env_file, create_database_engine, read_env_var, DatabaseConnectionError, create_session

# fixtures
@pytest.fixture
def temp_env_file(tmp_path):
    """テスト用の.envファイルを作成するfixture
    tmp_path: pytestが提供する一時ディレクトリ
    with open: 一時的な.envファイルを作成
    f.write: テスト用の環境変数をファイルに書き込む
    """
    env_file = tmp_path / ".env"
    with open(env_file, "w") as f:
        f.write("TEST_VAR=test_value\n")
        f.write("ANOTHER_VAR=another_value\n")
    return env_file

@pytest.fixture
def mock_logger():
    """ロガー関数をモックするfixture
    create_logger: ロガー関数をモック
    create_error_logger: エラーロガー関数をモック"""
    with patch("database.create_logger") as mock_create_logger:
        with patch("database.create_error_logger") as mock_create_error_logger:
            yield mock_create_logger, mock_create_error_logger

@pytest.fixture
def mock_dotenv_load():
    """python-dotenvのload_dotenv関数をモックするfixture"""
    with patch("dotenv.load_dotenv") as mock_load:
        yield mock_load

@pytest.fixture
def mock_db_env():
    """db_envをモックするfixture"""
    with patch("database.db_env") as mock_env:
        yield mock_env


@pytest.fixture
def mock_create_engine():
    """SQLAlchemyのcreate_engine関数をモックするfixture"""
    with patch("database.create_engine") as mock_engine:
        yield mock_engine


@pytest.fixture
def mock_pprint():
    """pprintモジュールをモックするfixture"""
    with patch("database.pprint.pprint") as mock_print:
        yield mock_print


class TestInitEnv:
    """環境変数の初期化をテストするクラス"""

    def test_env_file_exists(self, temp_env_file, mock_logger):
        """環境変数ファイルが存在する場合のテスト
        temp_env_file: テスト用の.envファイル
        mock_logger: ロガー関数をモック
        check_env_file: 環境変数ファイルの存在を確認する関数
        assert: テストの結果を確認
        result: check_env_file関数の戻り値
        result.exists(): .envファイルが存在するか確認
        mock_create_logger: ロガー関数が正しく呼ばれたか確認
        mock_create_error_logger: エラーロガー関数が呼ばれなかったか確認
        """
        mock_create_logger, mock_create_error_logger = mock_logger
        result = check_env_file(temp_env_file)
        assert result == temp_env_file
        assert result.exists()
        mock_create_logger.assert_called_once_with(f".envファイルが見つかりました: {temp_env_file}")
        mock_create_error_logger.assert_not_called()


    def test_env_file_not_exists(self, tmp_path, mock_logger):
        """環境変数ファイルが存在しない場合のテスト
        tmp_path / "non_existent.env": 存在しない.envファイルのパス
        result: check_env_file関数の戻り値
        assert: テストの結果を確認
        result.exists(): .envファイルが存在しないか確認
        mock_create_logger: ロガー関数が呼ばれなかったか確認
        mock_create_error_logger: エラーロガー関数が正しく呼ばれたか確認
        """
        mock_create_logger, mock_create_error_logger = mock_logger
        non_existent_file = tmp_path / "non_existent.env"

        result = check_env_file(non_existent_file)

        assert result == non_existent_file
        assert not result.exists()
        mock_create_error_logger.assert_called_once_with(f".envファイルが見つかりません: {non_existent_file}")
        mock_create_logger.assert_not_called()


    def test_default_env_path(self):
        """デフォルトのパスが正しく設定されるかテスト
        check_env_fileの内部でPath(__file__)を使っているので、__file__自体をモックして、パスの構築をコントロールする。
        mock_path: モックされたパス
        assert: テストの結果を確認
        database.__file__: モジュールの__file__属性をモック
        patch.object: オブジェクトの属性をモック
        patch("database.create_logger"): ロガー関数をモック
        check_env_file: 環境変数ファイルの存在を確認する関数
        Path("/fake/path") / ".env": モックされたパスと.envファイルを結合
        """
        original_file = Path(__file__)
        mock_path = Path("/fake/path/module.py")

        with patch("database.__file__", mock_path):
            with patch.object(Path, "exists", return_value=True):
                with patch("database.create_logger"):
                    result = check_env_file()
                    assert result == Path("/fake/path") / ".env"


# カスタム例外クラス
class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors"""
    pass

# Mockクラス
class MockEngine:
    """モック化されたデータベースエンジン"""
    pass


@pytest.fixture
def mock_engine(self):
    """モック化されたデータベースエンジンを返すfixture"""
    return MockEngine()

@pytest.fixture
def mock_session(self):
    """モック化されたセッションを返すfixture"""
    return MagicMock(spec=Session)

class TestCreateDatabaseEngine:
    """データベースエンジンを作成するケース"""

    def test_create_database_engine_success(self, mock_db_env, mock_create_engine, mock_logger):
        """データベースのURLの取得に成功して接続できるケースのテスト
        Args:
            mock_db_env: モック化されたdb_env
            mock_create_engine: モック化されたcreate_engine関数
            mock_logger: モック化されたロガー関数
            mock_pprint: モック化されたpprint関数
        """
        # モックの設定
        mock_create_logger, mock_create_error_logger = mock_logger
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        test_db_url = "sqlite:///test.db"
        mock_db_env.get.return_value = test_db_url
        engine = create_database_engine()
        mock_db_env.get.assert_called_once_with("database_url")
        mock_create_logger.assert_any_call(f"DB_URLを取得しました。: {test_db_url}")
        mock_create_logger.assert_any_call("データベース接続に成功しました。")
        mock_create_engine.assert_called_once_with(
            test_db_url,
            connect_args={"check_same_thread": False}
        )
        mock_create_error_logger.assert_not_called()
        assert engine == mock_engine

    def test_create_database_engine_no_url(self, mock_db_env, mock_create_engine):
        """データベースのURLが設定されていない場合のテスト
        Args:
            mock_db_env: モック化されたdb_env
            mock_create_engine: モック化されたcreate_engine関数
            mock_logger: モック化されたロガー関数
        """
        # モックの設定
        mock_db_env.get.return_value = None

        try:
            create_database_engine()
            pytest.fail("例外が発生しませんでした")
        except Exception as e:
            assert "DATABASE_URLが設定されていません。" in str(e)

        mock_db_env.get.assert_called_once_with("database_url")
        mock_create_engine.assert_not_called()

    def test_discover_exception_type(self, mock_db_env, mock_logger):
        """例外の詳細情報を表示するテスト
        mock_db_env: モック化されたdb_env
        try文で例外の詳細情報を表示
        except文で例外をキャッチして、型、モジュール、文字列表現を表示
        assert True: テストは常に成功させる（情報収集が目的）
        """
        # モックの設定
        mock_create_logger, mock_create_error_logger = mock_logger
        mock_db_env.get.return_value = None

        try:
            create_database_engine()
            pytest.fail("例外が発生しませんでした")
        except Exception as e:
            print(f"\n実際の例外の型: {type(e).__name__}")
            print(f"例外のモジュール: {type(e).__module__}")
            print(f"例外の文字列表現: {str(e)}")

            assert True

class TestCreateSession:
    """環境変数を取得してセッションを確立するテスト"""

    @pytest.fixture
    def mock_sessionmaker(self):
        """sessionmakerのモック"""
        with patch("database.sessionmaker") as mock:
            session_factory = MagicMock()
            mock.return_value = session_factory
            yield mock

    @pytest.fixture
    def mock_getenv(self):
        """os.getenvのモック"""
        with patch("os.getenv") as mock:
            mock.return_value = "test_session_id"
            yield mock

    @pytest.fixture
    def mock_create_logger(self):
        """create_loggerのモック"""
        with patch("database.create_logger") as mock:
            yield mock

    @pytest.fixture
    def mock_create_error_logger(self):
        """create_error_loggerのモック"""
        with patch("database.create_error_logger") as mock:
            yield mock

    @pytest.fixture
    def mock_engine(self):
        """モック化されたデータベースエンジンを返すfixture"""
        return MockEngine()

    def test_create_session_success(
        self, mock_sessionmaker, mock_getenv, mock_create_logger, mock_create_error_logger
    ):
        """セッションの作成に成功するケースのテスト
        MagicMock(spec=Engine): モックエンジンを作成
        create_session(mock_engine)create_session関数を呼び出し
        mock_sessionmaker.assert_called_once_with(mock_engine): sessionmakerが正しく呼び出されたか検証
        mock_getenv.assert_called_once_with("AA03"): 環境変数が取得されたか検証
        mock_create_logger.assert_called_once_with: ログが記録されたか検証
        mock_create_error_logger.assert_not_called(): エラーログが記録されていないか検証
        assert session_factory == mock_sessionmaker.return_value: 返されたセッションファクトリが正しいか検証
        """
        mock_engine = MagicMock(spec=Engine)
        session_factory = create_session(mock_engine)
        mock_sessionmaker.assert_called_once_with(mock_engine)
        mock_getenv.assert_called_once_with("AA03")
        mock_create_logger.assert_called_once_with(
            "セッションを確立しました。 -> test_session_id"
        )
        mock_create_error_logger.assert_not_called()
        assert session_factory == mock_sessionmaker.return_value

    def test_create_session_missing_env_var(
        self, mock_sessionmaker, mock_getenv, mock_create_logger, mock_create_error_logger
    ):
        """セッションIDの環境変数が設定されていない場合のテスト
        mock_getenv: 環境変数をモック
        MagicMock(spec=Engine): モックエンジンを作成
        create_session(mock_engine): create_session関数を呼び出し
        mock_sessionmaker.assert_called_once_with(mock_engine): sessionmakerが正しく呼び出されたか検証
        mock_create_logger.assert_not_called(): ログが記録されていないか検証
        mock_create_error_logger.assert_called_once(): エラーログが記録されたか検証
        assert session_factory == mock_sessionmaker.return_value: 返されたセッションファクトリが正しいか検証
        """
        mock_getenv.return_value = None
        mock_engine = MagicMock(spec=Engine)
        session_factory = create_session(mock_engine)
        mock_sessionmaker.assert_called_once_with(mock_engine)
        mock_create_error_logger.assert_called_once()
        mock_create_logger.assert_not_called()
        assert session_factory == mock_sessionmaker.return_value

    def test_create_session_exception(
        self, mock_sessionmaker, mock_getenv, mock_create_logger, mock_create_error_logger
    ):
        """セッション作成時に例外が発生した場合のテスト
        mock_sessionmaker.side_effect: sessionmakerが例外を発生させるように設定
        MagicMock(spec=Engine): モックエンジンを作成
        pytest.raises: 例外が発生することを確認
        mock_create_error_logger.assert_called_once(): エラーログが記録されたか検証
        mock_create_logger.assert_not_called(): 通常のログが記録されていないか検証
        """
        mock_sessionmaker.side_effect = Exception("テスト例外")
        mock_engine = MagicMock(spec=Engine)
        with pytest.raises(Exception):
            create_session(mock_engine)
        mock_create_error_logger.assert_called_once()
        mock_create_logger.assert_not_called()
