"""データベース接続モジュール"""
import os
import pprint
from pathlib import Path
from dotenv import load_dotenv

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from logger.custom_logger import create_logger, create_error_logger


def check_env_file(
    default_env_path: Path | str=None
    ) -> Path | None:
    """ENVファイルを検出し、PATHモジュールでENVファイルのパスを設定する。

    :param default_env_path: str | Path
    """
    if default_env_path is None:
        default_env_path = Path(__file__).parent / '.env'
    else:
        default_env_path = Path(default_env_path) \
        if isinstance(default_env_path, str) \
        else default_env_path
    print(
        f"STEP1：ENVファイルの初期化に成功しました。 \
        -> {default_env_path}"
        )

    if not default_env_path.exists():
        print(".envファイルが見つかりません")
        create_error_logger(
            f".envファイルが見つかりません。PATHを確認して下さい。: \
            {default_env_path}"
            )
    else:
        print(
            f"STEP2：.envファイルが見つかりました。 \
                -> {default_env_path}"
                )
        create_logger(
            f".envファイルが見つかりました: {default_env_path}")
    return default_env_path


env_var = check_env_file()

def read_env_var(env_path: Path) -> dict:
    """dotenvモジュールのload_dotenv関数でENVファイルから環境変数を取得し、ログに記録する。

    file_id: 環境変数から取得したファイルID

    database_url: 環境変数から取得したDB_URL
    """
    load_dotenv(dotenv_path=env_path)
    result = {}

    id_A003 = os.getenv("AA03")
    if id_A003:
        print(f"STEP3：ファイルIDを取得しました。 -> {id_A003}")
        create_logger(f"ファイルIDを取得しました。: {id_A003}")
        result["file_id_03"] = id_A003
    else:
        print("ファイルIDが取得できませんでした。")
        create_error_logger("ファイルIDが取得できませんでした。")

    id_A005 = os.getenv("AA05")
    if id_A005:
        print(f"STEP3：ファイルIDを取得しました。 -> {id_A005}")
        create_logger(f"ファイルIDを取得しました。: {id_A005}")
        result["file_id_05"] = id_A005
    else:
        print("ファイルIDが取得できませんでした。")
        create_error_logger("ファイルIDが取得できませんでした。")

    id_A006 = os.getenv("AA06")
    if id_A006:
        print(f"STEP3：ファイルIDを取得しました。 -> {id_A006}")
        create_logger(f"ファイルIDを取得しました。: {id_A006}")
        result["file_id_06"] = id_A006
    else:
        print("ファイルIDが取得できませんでした。")
        create_error_logger("ファイルIDが取得できませんでした。")

    id_A007 = os.getenv("AA07")
    if id_A007:
        print(f"STEP3：ファイルIDを取得しました。 -> {id_A007}")
        create_logger(f"ファイルIDを取得しました。: {id_A007}")
        result["file_id_07"] = id_A007
    else:
        print("ファイルIDが取得できませんでした。")
        create_error_logger("ファイルIDが取得できませんでした。")

    id_A008 = os.getenv("AA08")
    if id_A008:
        print(f"STEP4：ファイルIDを取得しました。 -> {id_A008}")
        create_logger(f"ファイルIDを取得しました。: {id_A008}")
        result["file_id_08"] = id_A008
    else:
        print("ファイルIDが取得できませんでした。 -> {id_A008}")
        create_error_logger("ファイルIDが取得できませんでした。 {id_A008}")

    id_A009 = os.getenv("AA09")
    if id_A009:
        print(f"STEP4：ファイルIDを取得しました。 -> {id_A009}")
        create_logger(f"ファイルIDを取得しました。: {id_A009}")
        result["file_id_09"] = id_A009

    id_A010 = os.getenv("AA10")
    if id_A010:
        print(f"STEP4：ファイルIDを取得しました。 -> {id_A010}")
        create_logger(f"ファイルIDを取得しました。: {id_A010}")
        result["file_id_10"] = id_A010
    else:
        print("ファイルIDが取得できませんでした。 -> {id_A009}")
        create_error_logger("ファイルIDが取得できませんでした。 {id_A009}")

    database_url = os.getenv("DATABASE_URL")
    secret_key = os.getenv("SECRET_KEY")
    algo = os.getenv("ALGORITHM")

    if database_url:
        print(f"STEP4：DB_URLを取得しました。 -> {database_url}")
        create_logger(f"DB_URLを取得しました。: {database_url}")
        result["database_url"] = database_url
    else:
        print("DB_URLが取得できませんでした。")
        create_error_logger("DB_URLが取得できませんでした。")

    if secret_key:
        print(f"STEP4：SECRET_KEYを取得しました。 -> {secret_key}")
        create_logger(f"SECRET_KEYを取得しました。: {secret_key}")
        result["secret_key"] = secret_key
    else:
        print("SECRET_KEYが取得できませんでした。")
        create_error_logger("SECRET_KEYが取得できませんでした。")
    if algo:
        print(f"STEP4：ALGORITHMを取得しました。 -> {algo}")
        create_logger(f"ALGORITHMを取得しました。: {algo}")
        result["algo"] = algo
    else:
        print("ALGORITHMが取得できませんでした。")
        create_error_logger("ALGORITHMが取得できませんでした。")
    if not result:
        print("環境変数の取得に失敗しました。")
        create_error_logger("環境変数の取得に失敗しました。")
        return result
    else:
        print(f"STEP5：環境変数の取得に成功しました")
        create_logger(f"環境変数の取得に成功しました。: {result}")

        # 環境変数を構造化して表示する
        print("")
        pprint.pprint(result)
        print("")
        return result

db_env = read_env_var(env_var)


class DatabaseConnectionError(Exception):
    """データベース接続エラーを表すカスタム例外"""
    pass


# データベースエンジンを作成
def create_database_engine() -> Engine:
    """環境変数からデータベースURLを取得し、データベースエンジンを作成する。

    データベースURLが設定されていない場合は、DatabaseConnectionErrorをスローします。

    connect_args = {"check_same_thread": False} : SQLite固有の接続オプション
    """
    try:
        DB_URL = db_env.get("database_url")
        if not DB_URL:
            # print("DATABASE_URLが設定されていません。")
            create_error_logger("DATABASE_URLが設定されていません。")
            raise DatabaseConnectionError("DATABASE_URLが設定されていません。")
        else:
            print(f"STEP7：DB_URLを取得しました。 -> {DB_URL}")
            create_logger(f"DB_URLを取得しました。: {DB_URL}")

        # データベースエンジンを作成
        connect_args = {"check_same_thread": False}
        engine = create_engine(DB_URL, connect_args=connect_args)
        print(f"STEP8：データベースエンジンを作成しました。 -> {engine}")
        create_logger("データベース接続に成功しました。")
        return engine

    except Exception as e:
        pprint.pprint(f"Error: {e}")
        create_error_logger(f"データベース接続に失敗しました。: {str(e)}")
        raise

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
        session_id = os.getenv("AA03")
        if not session_id:
            create_error_logger(
                f"{session_id}が環境変数に設定されていません。"
                )
        else:
            print(f"STEP9：セッションを確立しました。 -> {session_id}")
            create_logger(f"セッションを確立しました。 -> {session_id}")
        return SessionLocal
    except Exception as e:
        pprint.pprint(f"Error: {e}")
        create_error_logger(f"セッション作成に失敗しました。: {str(e)}")
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
        print("DBセッションをコミットしました")
        create_logger("DBセッションをコミットしました")
    except Exception as e:
        pprint.pprint(str(e))
        create_error_logger(
            f"DBセッションのコミットに失敗しました。: {str(e)}"
            )
        raise
    finally:
        db.close()
        print("DBセッションをクローズしました")
        create_logger("DBセッションをクローズしました")