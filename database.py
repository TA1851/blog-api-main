"""データベース接続モジュール"""
import os
from pathlib import Path
from typing import Union, Optional, Dict, List, Generator
from typing_extensions import TypedDict
from dotenv import load_dotenv

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from fastapi import HTTPException
from exceptions import DatabaseConnectionError


class EnvironmentConfig(TypedDict, total=False):
    """環境変数設定の型定義"""
    environment: Optional[str]
    posgre_url: Optional[str]
    secret_key: Optional[str]
    algo: Optional[str]
    cors_origins: Optional[List[str]]


def check_env_file(
    default_env_path: Optional[Union[Path, str]] = None
    ) -> Optional[Path]:
    """・開発環境：.envファイルを使用する。

    ・本番環境：Renderから環境変数を取得する。
    """
    if default_env_path is None:
        default_env_path = Path(__file__).parent / '.env'
    else:
        default_env_path = Path(default_env_path) \
        if isinstance(default_env_path, str) \
        else default_env_path

    if not default_env_path.exists():
        print(
            "スタート"
            )
    else:
        print(
            "前処理の開始"
            )
    return default_env_path

env_var = check_env_file()


def read_env_var(env_path: Path) -> EnvironmentConfig:
    """環境変数の取得"""
    load_dotenv(dotenv_path=env_path)
    result: EnvironmentConfig = {}

    # TODO: 開発時に切り替える（環境変数）
    environment = os.getenv("ENVIRONMENT")
    posgre_database_url = os.getenv("POSGRE_URL")
    secret_key = os.getenv("SECRET_KEY")
    algo = os.getenv("ALGORITHM")
    cors_origins = os.getenv("CORS_ORIGINS")
    result["environment"] = environment


    # TODO: 本番環境に切り替える（データベースURL）
    if posgre_database_url:
        result["posgre_url"] = posgre_database_url
    else:
        print(
            "DB_URLが取得できませんでした。"
            )
    if secret_key:
        result["secret_key"] = secret_key
    else:
        print(
            "SECRET_KEYが取得できませんでした。"
            )
    if algo:
        result["algo"] = algo
    else:
        print(
            "ALGORITHMが取得できませんでした。"
            )
    if cors_origins:
        if "," in cors_origins:
            result["cors_origins"] = [
                origin.strip() \
                for origin in cors_origins.split(",")
                ]
        else:
            result["cors_origins"] = [
                cors_origins.strip()
                ]
    else:
        print(
            "CORS_ORIGINSが取得できませんでした。"
            )
    if not result:
        print(
            "環境変数の取得に失敗しました。"
            )
        return EnvironmentConfig()
    else:
        return result

db_env: EnvironmentConfig = read_env_var(env_var) \
    if env_var else EnvironmentConfig()


# データベースエンジンを作成
def create_database_engine() -> Engine:
    """データベースエンジンを作成する。

    ・開発環境ではSQLite、本番環境ではPostgreSQLを使用します。
    """
    try:
        environment = db_env.get("environment")
        if environment == "production":
            posgre_database_url = db_env.get("posgre_url")
            if not posgre_database_url:
                print(
                    "DBのURLが設定されていません。"
                    )
                raise DatabaseConnectionError(
                    "本番環境DBのURLが設定されていません。"
                    )
            if not posgre_database_url.startswith("postgresql"):
                print(
                    "DBのURLが不正です。"
                    )
                raise DatabaseConnectionError(
                    "DBのURLが不正です。"
                    )
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
            # 開発環境用SQLiteエンジンを作成
            sqlite_url = "sqlite:///blog.db"
            print(
                f"開発環境: SQLiteデータベースに接続します ({sqlite_url})"
            )
            engine = create_engine(
                sqlite_url,
                connect_args={"check_same_thread": False},
                echo=False
            )
            return engine
    except Exception as e:
        raise DatabaseConnectionError(
            f"データベース接続に失敗しました。: {str(e)}"
        )


# SQLAlchemy 2.0スタイルのベースクラス
class Base(DeclarativeBase):
    """SQLAlchemyのベースクラス"""
    pass
engine = create_database_engine()


# セッションを作成
def create_session(engine: Engine) -> sessionmaker[Session]:
    """SQLAlchemyのセッションを作成する。

    :param engine: SQLAlchemyのエンジンオブジェクト

    :param autocommit=False（デフォルト値）:
        CRUD操作をグループ化して、全ての処理が成功した場合、
        データベースに反映されるようにできます。

        エラーが発生した場合はrollback()を呼び出して全ての変更を取り消せます。

    :param autoflush=False:
        大量のオブジェクトを追加/更新する場合、
        各オペレーションでフラッシュが発生するのを避けられます。
        デフォルト値はTrueです。

    :param bind=engine: エンジンを生成する呼び出し可能オブジェクト
    """
    try:
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
            )
        return SessionLocal
    except Exception as e:
        print(
            f"セッション作成に失敗しました。: {str(e)}"
            )
        raise

session = create_session(engine)


def get_db() -> Generator[Session, None, None]:
    """データベースセッションを取得する

    :return: データベースセッション

    :rtype: Session
    """
    db = session()
    try:
        yield db
    except HTTPException:
        # HTTPExceptionは正常な処理フローの一部なので、ログ出力せずに再スロー
        raise
    except Exception as e:
        print(
            f"DBセッションのコミットに失敗しました。: {str(e)}"
            )
        raise
    finally:
        db.close()