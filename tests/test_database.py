# filepath: /Users/tatu/Documents/GitHub/blog-api-main/tests/test_database.py
"""database.pyのテストモジュール"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker, Session

from database import (
    check_env_file,
    read_env_var,
    create_database_engine,
    create_session,
    get_db,
    DatabaseConnectionError,
    EnvironmentConfig,
    Base
)


class TestCheckEnvFile:
    """check_env_file関数のテスト"""

    def test_check_env_file_default_path(self):
        """デフォルトパスでの.envファイル検出テスト"""
        # デフォルトパスは__file__の親ディレクトリ/.env
        result = check_env_file()
        expected_path = Path(__file__).parent.parent / '.env'
        assert result == expected_path

    def test_check_env_file_custom_str_path(self):
        """カスタム文字列パスでの.envファイル検出テスト"""
        custom_path = "/tmp/test.env"
        result = check_env_file(custom_path)
        assert result == Path(custom_path)

    def test_check_env_file_custom_path_object(self):
        """カスタムPathオブジェクトでの.envファイル検出テスト"""
        custom_path = Path("/tmp/test.env")
        result = check_env_file(custom_path)
        assert result == custom_path

    def test_check_env_file_existing_file(self, tmp_path):
        """存在する.envファイルのテスト"""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value")
        
        with patch('builtins.print') as mock_print:
            result = check_env_file(env_file)
            mock_print.assert_called_with("処理を開始します。")
        assert result == env_file

    def test_check_env_file_non_existing_file(self, tmp_path):
        """存在しない.envファイルのテスト"""
        env_file = tmp_path / "nonexistent.env"
        
        with patch('builtins.print') as mock_print:
            result = check_env_file(env_file)
            mock_print.assert_called_with("スキップ処理")
        assert result == env_file


class TestReadEnvVar:
    """read_env_var関数のテスト"""

    @patch.dict(os.environ, {}, clear=True)
    def test_read_env_var_all_variables_set(self, tmp_path):
        """全ての環境変数が設定されている場合のテスト"""
        env_file = tmp_path / ".env"
        env_content = """ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@localhost:5432/testdb
SECRET_KEY=test_secret_key
ALGORITHM=HS256
CORS_ORIGINS=http://localhost:3000,https://example.com"""
        env_file.write_text(env_content)
        
        result = read_env_var(env_file)
        
        assert result["environment"] == "production"
        assert result["posgre_url"] == "postgresql://user:pass@localhost:5432/testdb"
        assert result["secret_key"] == "test_secret_key"
        assert result["algo"] == "HS256"
        assert result["cors_origins"] == ["http://localhost:3000", "https://example.com"]

    @patch.dict(os.environ, {}, clear=True)
    def test_read_env_var_single_cors_origin(self, tmp_path):
        """単一のCORS_ORIGINのテスト"""
        env_file = tmp_path / ".env"
        env_content = """ENVIRONMENT=development
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=test_key
ALGORITHM=HS256
CORS_ORIGINS=http://localhost:3000"""
        env_file.write_text(env_content)
        
        result = read_env_var(env_file)
        
        assert result["cors_origins"] == ["http://localhost:3000"]

    @patch.dict(os.environ, {}, clear=True)
    def test_read_env_var_posgre_url_fallback(self, tmp_path):
        """POSGRE_URLが設定されていない場合のDATABASE_URLフォールバックテスト"""
        env_file = tmp_path / ".env"
        env_content = """ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@localhost:5432/testdb
SECRET_KEY=test_secret_key
ALGORITHM=HS256"""
        env_file.write_text(env_content)
        
        result = read_env_var(env_file)
        
        assert result["posgre_url"] == "postgresql://user:pass@localhost:5432/testdb"

    @patch.dict(os.environ, {}, clear=True)
    def test_read_env_var_missing_variables(self, tmp_path):
        """一部の環境変数が未設定の場合のテスト"""
        env_file = tmp_path / ".env"
        env_content = """ENVIRONMENT=development
SECRET_KEY=test_key"""
        env_file.write_text(env_content)
        
        with patch('builtins.print') as mock_print:
            result = read_env_var(env_file)
            
            # 各種エラーメッセージが出力されることを確認
            mock_print.assert_any_call("DB_URLが取得できませんでした。")
            mock_print.assert_any_call("ALGORITHMが取得できませんでした。")
            mock_print.assert_any_call("CORS_ORIGINSが取得できませんでした。")
        
        assert result["environment"] == "development"
        assert result["secret_key"] == "test_key"
        assert "posgre_url" not in result
        assert "algo" not in result
        assert "cors_origins" not in result

    @patch.dict(os.environ, {}, clear=True)
    def test_read_env_var_empty_file(self, tmp_path):
        """空の.envファイルのテスト"""
        env_file = tmp_path / ".env"
        env_file.write_text("")
        
        with patch('builtins.print') as mock_print:
            result = read_env_var(env_file)
            
            # 全ての環境変数取得失敗メッセージが出力されることを確認
            mock_print.assert_any_call("DB_URLが取得できませんでした。")
            mock_print.assert_any_call("SECRET_KEYが取得できませんでした。")
            mock_print.assert_any_call("ALGORITHMが取得できませんでした。")
            mock_print.assert_any_call("CORS_ORIGINSが取得できませんでした。")
            # "環境変数の取得に失敗しました。"は出力されない（environmentがNoneでも辞書に追加されるため）
        
        # environmentにNoneが設定された辞書が返されることを確認
        assert result["environment"] is None
        assert "posgre_url" not in result
        assert "secret_key" not in result
        assert "algo" not in result
        assert "cors_origins" not in result


class TestCreateDatabaseEngine:
    """create_database_engine関数のテスト"""

    @patch('database.db_env', {"environment": "production", "posgre_url": "postgresql://user:pass@localhost:5432/testdb"})
    @patch('database.create_engine')
    def test_create_database_engine_production(self, mock_create_engine):
        """本番環境でのデータベースエンジン作成テスト"""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        result = create_database_engine()
        
        mock_create_engine.assert_called_once_with(
            "postgresql://user:pass@localhost:5432/testdb",
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
            echo=False
        )
        assert result == mock_engine

    @patch('database.db_env', {"environment": "development"})
    @patch('database.create_engine')
    def test_create_database_engine_development(self, mock_create_engine):
        """開発環境でのデータベースエンジン作成テスト"""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        result = create_database_engine()
        
        mock_create_engine.assert_called_once_with(
            "sqlite:///./blog.db",
            connect_args={"check_same_thread": False},
            echo=False
        )
        assert result == mock_engine

    @patch('database.db_env', {})
    @patch('database.create_engine')
    def test_create_database_engine_no_environment(self, mock_create_engine):
        """環境変数未設定でのデータベースエンジン作成テスト（デフォルトで開発環境）"""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        result = create_database_engine()
        
        mock_create_engine.assert_called_once_with(
            "sqlite:///./blog.db",
            connect_args={"check_same_thread": False},
            echo=False
        )
        assert result == mock_engine

    @patch('database.db_env', {"environment": "production"})
    @patch('builtins.print')
    def test_create_database_engine_production_no_url(self, mock_print):
        """本番環境でURLが未設定の場合のテスト"""
        with pytest.raises(DatabaseConnectionError, match="本番環境DBのURLが設定されていません。"):
            create_database_engine()
        
        mock_print.assert_called_with("DBのURLが設定されていません。")

    @patch('database.db_env', {"environment": "production", "posgre_url": "invalid_url"})
    @patch('builtins.print')
    def test_create_database_engine_production_invalid_url(self, mock_print):
        """本番環境で不正なURLの場合のテスト"""
        with pytest.raises(DatabaseConnectionError, match="DBのURLが不正です。"):
            create_database_engine()
        
        mock_print.assert_called_with("DBのURLが不正です。")

    @patch('database.db_env', {"environment": "development"})
    @patch('database.create_engine')
    def test_create_database_engine_exception_handling(self, mock_create_engine):
        """データベースエンジン作成時の例外処理テスト"""
        mock_create_engine.side_effect = Exception("Connection failed")
        
        with pytest.raises(DatabaseConnectionError, match="データベース接続に失敗しました。: Connection failed"):
            create_database_engine()


class TestCreateSession:
    """create_session関数のテスト"""

    def test_create_session_success(self):
        """正常なセッション作成テスト"""
        mock_engine = MagicMock(spec=Engine)
        
        result = create_session(mock_engine)
        
        # sessionmakerのインスタンスが返されることを確認
        assert callable(result)
        # セッションメーカーの設定を確認
        session_instance = result()
        assert session_instance is not None

    @patch('database.sessionmaker')
    @patch('builtins.print')
    def test_create_session_exception(self, mock_print, mock_sessionmaker):
        """セッション作成時の例外処理テスト"""
        mock_engine = MagicMock(spec=Engine)
        mock_sessionmaker.side_effect = Exception("Session creation failed")
        
        with pytest.raises(Exception, match="Session creation failed"):
            create_session(mock_engine)
        
        mock_print.assert_called_once()


class TestGetDb:
    """get_db関数のテスト"""

    @patch('database.session')
    def test_get_db_success(self, mock_session_factory):
        """正常なデータベースセッション取得テスト"""
        mock_session_instance = MagicMock(spec=Session)
        mock_session_factory.return_value = mock_session_instance
        
        # ジェネレータをテストするためにlist()で実行
        db_sessions = list(get_db())
        
        assert len(db_sessions) == 1
        assert db_sessions[0] == mock_session_instance
        mock_session_instance.close.assert_called_once()

    @patch('database.session')
    @patch('builtins.print')
    def test_get_db_exception_handling(self, mock_print, mock_session_factory):
        """データベースセッション取得時の例外処理テスト"""
        mock_session_instance = MagicMock(spec=Session)
        mock_session_factory.return_value = mock_session_instance
        
        # ジェネレータ内で例外を発生させる
        def generator_with_exception():
            gen = get_db()
            next(gen)  # セッションを取得
            raise Exception("Database operation failed")
        
        with pytest.raises(Exception, match="Database operation failed"):
            generator_with_exception()
        
        # セッションがクローズされることを確認
        mock_session_instance.close.assert_called_once()


class TestDatabaseConnectionError:
    """DatabaseConnectionErrorカスタム例外のテスト"""

    def test_database_connection_error(self):
        """DatabaseConnectionErrorカスタム例外のテスト"""
        error_message = "データベースに接続できません"
        
        with pytest.raises(DatabaseConnectionError, match=error_message):
            raise DatabaseConnectionError(error_message)


class TestEnvironmentConfig:
    """EnvironmentConfig TypedDictのテスト"""

    def test_environment_config_type_structure(self):
        """EnvironmentConfig型の構造テスト"""
        # 正常な設定
        valid_config: EnvironmentConfig = {
            "environment": "production",
            "posgre_url": "postgresql://localhost:5432/db",
            "secret_key": "secret",
            "algo": "HS256",
            "cors_origins": ["http://localhost:3000"]
        }
        
        assert valid_config["environment"] == "production"
        assert valid_config["posgre_url"] == "postgresql://localhost:5432/db"
        assert valid_config["secret_key"] == "secret"
        assert valid_config["algo"] == "HS256"
        assert valid_config["cors_origins"] == ["http://localhost:3000"]

    def test_environment_config_optional_fields(self):
        """EnvironmentConfig型のオプションフィールドテスト"""
        # 一部のフィールドのみを持つ設定
        partial_config: EnvironmentConfig = {
            "environment": "development"
        }
        
        assert partial_config["environment"] == "development"
        assert "posgre_url" not in partial_config
        assert "secret_key" not in partial_config

    def test_environment_config_empty(self):
        """EnvironmentConfig型の空設定テスト"""
        empty_config: EnvironmentConfig = {}
        
        assert len(empty_config) == 0


class TestBase:
    """SQLAlchemyベースクラスのテスト"""

    def test_base_class_inheritance(self):
        """Baseクラスの継承テスト"""
        from sqlalchemy.orm import DeclarativeBase
        from sqlalchemy import Column, Integer
        
        assert issubclass(Base, DeclarativeBase)
        
        # テスト用のモデルクラスを作成してベースクラスの動作を確認（プライマリキーを追加）
        class TestModel(Base):
            __tablename__ = 'test_table'
            id = Column(Integer, primary_key=True)
            
        assert hasattr(TestModel, '__tablename__')
        assert TestModel.__tablename__ == 'test_table'
        assert hasattr(TestModel, 'id')


class TestIntegration:
    """統合テスト"""

    @patch.dict(os.environ, {}, clear=True)
    def test_full_database_setup_development(self):
        """開発環境での完全なデータベースセットアップテスト"""
        # 実際の環境変数を使用してテスト
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / '.env'
            env_content = """ENVIRONMENT=development
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=test_key
ALGORITHM=HS256
CORS_ORIGINS=http://localhost:3000"""
            env_file.write_text(env_content)
            
            # 環境変数読み込み
            config = read_env_var(env_file)
            
            assert config["environment"] == "development"
            assert config["posgre_url"] == "sqlite:///./test.db"
            assert config["secret_key"] == "test_key"
            assert config["algo"] == "HS256"
            assert config["cors_origins"] == ["http://localhost:3000"]