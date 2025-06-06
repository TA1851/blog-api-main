import pytest
import os
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
    EnvironmentConfig
)
from exceptions import DatabaseConnectionError


class TestCheckEnvFile:
    """環境ファイルチェック機能のテスト"""
    
    def test_check_env_file_not_exists_production(self, tmp_path):
        """本番環境で環境ファイルが存在しない場合のテスト"""
        non_existent_file = tmp_path / ".env"
        
        result = check_env_file(non_existent_file)
        assert result == non_existent_file
        assert not result.exists()
    
    def test_check_env_file_default_path_production(self):
        """本番環境でのデフォルトパス環境ファイルチェック"""
        result = check_env_file()
        assert isinstance(result, Path)
        # 本番環境では.envファイルは存在しない想定


class TestReadEnvVar:
    """環境変数読み込み機能のテスト（Renderから取得）"""
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'production',
        'POSGRE_URL': 'postgresql://user:pass@localhost/prod_db',
        'SECRET_KEY': 'production_secret',
        'ALGORITHM': 'HS256',
        'CORS_ORIGINS': 'https://example.com,https://api.example.com'
    })
    def test_read_env_var_from_render(self, tmp_path):
        """Renderから環境変数を取得する場合のテスト"""
        # 存在しない.envファイルパスを指定
        non_existent_env = tmp_path / "nonexistent.env"
        
        result = read_env_var(non_existent_env)
        
        assert result["environment"] == "production"
        assert result["posgre_url"] == "postgresql://user:pass@localhost/prod_db"
        assert result["secret_key"] == "production_secret"
        assert result["algo"] == "HS256"
        assert result["cors_origins"] == ["https://example.com", "https://api.example.com"]
    
    @patch.dict(os.environ, {
        'CORS_ORIGINS': 'https://dummy-frontend.example.com'
    })
    def test_read_env_var_single_cors_origin_dummy(self, tmp_path):
        """ダミーデータでの単一CORS_ORIGINSテスト"""
        non_existent_env = tmp_path / "nonexistent.env"
        
        result = read_env_var(non_existent_env)
        
        assert result["cors_origins"] == ["https://dummy-frontend.example.com"]
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'production'
    }, clear=True)
    def test_read_env_var_missing_values_production(self, tmp_path):
        """本番環境で一部の環境変数が不足している場合のテスト"""
        non_existent_env = tmp_path / "nonexistent.env"
        
        result = read_env_var(non_existent_env)
        
        assert result["environment"] == "production"
        assert "posgre_url" not in result
        assert "secret_key" not in result
    
    @patch.dict(os.environ, {
        'CORS_ORIGINS': 'https://dummy1.example.com,https://dummy2.example.com,https://dummy3.example.com'
    })
    def test_read_env_var_multiple_cors_origins_dummy(self, tmp_path):
        """ダミーデータでの複数CORS_ORIGINSテスト"""
        non_existent_env = tmp_path / "nonexistent.env"
        
        result = read_env_var(non_existent_env)
        
        expected_origins = [
            "https://dummy1.example.com",
            "https://dummy2.example.com", 
            "https://dummy3.example.com"
        ]
        assert result["cors_origins"] == expected_origins


class TestCreateDatabaseEngine:
    """データベースエンジン作成のテスト"""
    
    @patch('database.db_env')
    def test_create_database_engine_production_render(self, mock_db_env):
        """Render本番環境でのデータベースエンジン作成テスト"""
        mock_db_env.get.side_effect = lambda key: {
            "environment": "production",
            "posgre_url": "postgresql://render_user:render_pass@render_host/render_db"
        }.get(key)
        
        engine = create_database_engine()
        
        assert isinstance(engine, Engine)
        assert "postgresql" in str(engine.url)
    
    @patch('database.db_env')
    def test_create_database_engine_development_fallback(self, mock_db_env):
        """開発環境フォールバック時のデータベースエンジン作成テスト"""
        mock_db_env.get.side_effect = lambda key: {
            "environment": "development"
        }.get(key)
        
        engine = create_database_engine()
        
        assert isinstance(engine, Engine)
        assert "sqlite" in str(engine.url)
    
    @patch('database.db_env')
    def test_create_database_engine_no_postgres_url_render(self, mock_db_env):
        """Render環境でPostgreSQLのURL未設定の場合のテスト"""
        mock_db_env.get.side_effect = lambda key: {
            "environment": "production",
            "posgre_url": None
        }.get(key)
        
        with pytest.raises(DatabaseConnectionError, match="本番環境DBのURLが設定されていません"):
            create_database_engine()


class TestCreateSession:
    """セッション作成のテスト"""
    
    def test_create_session_success(self):
        """セッション作成成功のテスト"""
        mock_engine = MagicMock(spec=Engine)
        
        session_maker = create_session(mock_engine)
        
        assert isinstance(session_maker, sessionmaker)
    
    @patch('database.sessionmaker')
    def test_create_session_failure(self, mock_sessionmaker):
        """セッション作成失敗のテスト"""
        mock_sessionmaker.side_effect = Exception("Session creation failed")
        mock_engine = MagicMock(spec=Engine)
        
        with pytest.raises(Exception, match="Session creation failed"):
            create_session(mock_engine)


class TestGetDb:
    """データベースセッション取得のテスト"""
    
    @patch('database.session')
    def test_get_db_success(self, mock_session_factory):
        """正常なデータベースセッション取得のテスト"""
        mock_session = MagicMock(spec=Session)
        mock_session_factory.return_value = mock_session
        
        db_generator = get_db()
        db = next(db_generator)
        
        assert db == mock_session
        mock_session.close.assert_not_called()
        
        # ジェネレータを終了
        try:
            next(db_generator)
        except StopIteration:
            pass
        
        mock_session.close.assert_called_once()
    
    @patch('database.session')
    def test_get_db_exception(self, mock_session_factory):
        """セッション使用中に例外が発生した場合のテスト"""
        mock_session = MagicMock(spec=Session)
        mock_session_factory.return_value = mock_session
        
        db_generator = get_db()
        db = next(db_generator)
        
        # 例外を発生させる
        try:
            db_generator.throw(Exception("Database error"))
        except Exception:
            pass
        
        mock_session.close.assert_called_once()


class TestEnvironmentConfig:
    """環境設定型定義のテスト"""
    
    def test_environment_config_render_production(self):
        """Render本番環境用EnvironmentConfig作成のテスト"""
        config: EnvironmentConfig = {
            "environment": "production",
            "posgre_url": "postgresql://render_user:render_pass@render_host/render_db",
            "secret_key": "render_production_key",
            "algo": "HS256",
            "cors_origins": [
                "https://dummy-frontend.herokuapp.com",
                "https://dummy-admin.herokuapp.com"
            ]
        }
        
        assert config["environment"] == "production"
        assert "render" in config["posgre_url"]
        assert config["secret_key"] == "render_production_key"
        assert config["algo"] == "HS256"
        assert len(config["cors_origins"]) == 2
        assert all("dummy" in origin for origin in config["cors_origins"])
    
    def test_environment_config_no_env_file(self):
        """環境ファイル無しのEnvironmentConfigのテスト"""
        config: EnvironmentConfig = {}
        
        assert isinstance(config, dict)
        assert len(config) == 0
        # Renderから環境変数を取得する想定
