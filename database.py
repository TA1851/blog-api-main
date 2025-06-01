"""データベース接続モジュール"""
import os
from pathlib import Path
from typing import Union, Optional
from dotenv import load_dotenv

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

def check_env_file(
    default_env_path: Union[Path, str] = None
    ) -> Optional[Path]:
    """ENVファイルを検出し、PATHモジュールでENVファイルのパスを設定する。

    :param default_env_path: str | Path
    """
    if default_env_path is None:
        default_env_path = Path(__file__).parent / '.env'
    else:
        default_env_path = Path(default_env_path) \
        if isinstance(default_env_path, str) \
        else default_env_path

    if not default_env_path.exists():
        print(".envファイルが見つかりません")
    else:
        print("処理を開始します。")
    return default_env_path

env_var = check_env_file()


def read_env_var(env_path: Path) -> dict:
    """dotenvモジュールのload_dotenv関数でENVファイルから環境変数を取得し、ログに記録する。

    file_id: 環境変数から取得したファイルID

    database_url: 環境変数から取得したDB_URL
    """
    load_dotenv(dotenv_path=env_path)
    result = {}

    # TODO: 開発時に切り替える（環境変数）
    environment = os.getenv("ENVIRONMENT")
    posgre_database_url = os.getenv("POSGRE_URL") or os.getenv("DATABASE_URL")  # DATABASE_URLもサポート
    secret_key = os.getenv("SECRET_KEY")
    algo = os.getenv("ALGORITHM")
    cors_origins = os.getenv("CORS_ORIGINS")
    result["environment"] = environment


    # TODO: 本番環境に切り替える（データベースURL）
    if posgre_database_url:
        result["posgre_url"] = posgre_database_url
    else:
        print("DB_URLが取得できませんでした。")
    if secret_key:
        result["secret_key"] = secret_key
    else:
        print("SECRET_KEYが取得できませんでした。")
    if algo:
        result["algo"] = algo
    else:
        print("ALGORITHMが取得できませんでした。")
    if cors_origins:
        if "," in cors_origins:
            result["cors_origins"] = [origin.strip() for origin in cors_origins.split(",")]
        else:
            result["cors_origins"] = [cors_origins.strip()]
    else:
        print("CORS_ORIGINSが取得できませんでした。")
    if not result:
        print("環境変数の取得に失敗しました。")
        # 空の辞書でも返すように修正（エラーで停止させない）
        return {}
    else:
        return result

db_env = read_env_var(env_var)


class DatabaseConnectionError(Exception):
    """データベース接続エラーを表すカスタム例外"""
    pass


# データベースエンジンを作成
def create_database_engine() -> Engine:
    """環境変数からデータベースURLを取得し、データベースエンジンを作成する。

    開発環境（development）ではSQLite、本番環境（production）ではPostgreSQLを使用します。
    ENVIRONMENTが未設定の場合は開発環境として扱います。

    connect_args:
    - SQLite: {"check_same_thread": False}
    - PostgreSQL: 接続プール設定
    """
    try:
        environment = db_env.get("environment")
        if environment == "production":
            posgre_database_url = db_env.get("posgre_url")
            if not posgre_database_url:
                print("DBのURLが設定されていません。")
                raise DatabaseConnectionError("本番環境DBのURLが設定されていません。")

            if not posgre_database_url.startswith("postgresql"):
                print(f"DBのURLが不正です。")
                raise DatabaseConnectionError("DBのURLが不正です。")
            engine = create_engine(
                posgre_database_url,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=1800,
                echo=False
            )
            return engine
        else:
            # 開発環境またはENVIRONMENTが未設定の場合はSQLiteを使用
            sqlite_path = "sqlite:///./blog.db"
            engine = create_engine(
                sqlite_path,
                connect_args={"check_same_thread": False},
                echo=False
            )
            return engine
    except Exception as e:
        raise DatabaseConnectionError(f"データベース接続に失敗しました。: {str(e)}")


# テーブルオブジェクトを生成するベースクラス
Base = declarative_base()
engine = create_database_engine()


# セッションを作成
def create_session(engine: Engine) -> Session:
    """SQLAlchemyのセッションを作成：データベースに接続し、データの操作を行う前処理を行う。

    :param engine: SQLAlchemyのエンジンオブジェクト

    :param SessionLocal:
        ・autocommit=False（デフォルト値）:
        CRUD操作をグループ化して、全ての処理が成功した場合、データベースに反映されるようにできます。

        　エラーが発生した場合はrollback()を呼び出して全ての変更を取り消せます。

        ・autoflush=False:
        大量のオブジェクトを追加/更新する場合、各オペレーションでフラッシュが発生するのを避けられます。
        デフォルト値はTrueです。

        ・bind=engine: エンジンを生成する呼び出し可能オブジェクト
    """
    try:
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
            )
        return SessionLocal
    except Exception as e:
        print("セッション作成に失敗しました。: {str(e)}")
        raise

session = create_session(engine)


def get_db():
    """データベースセッションを取得する

    :return: データベースセッション

    :rtype: Session
    """
    db = session()
    try:
        yield db
    except Exception as e:
        print(f"DBセッションのコミットに失敗しました。: {str(e)}")
        raise
    finally:
        db.close()