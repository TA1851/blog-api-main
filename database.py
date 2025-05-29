"""データベース接続モジュール"""
import os
# import pprint
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
    # print(
    #     f"STEP1：ENVファイルの初期化に成功しました。 \
    #     -> {default_env_path}"
    #    )

    if not default_env_path.exists():
        # print(".envファイルが見つかりません")
        create_error_logger(
            f".envファイルが見つかりません。PATHを確認して下さい。: \
            {default_env_path}"
            )
    else:
        # print(
        #     f"STEP2：.envファイルが見つかりました。 \
        #         -> {default_env_path}"
        #         )
        # create_logger(
        #     f".envファイルが見つかりました: {default_env_path}")
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

    # 環境変数を取得
    id_A003 = os.getenv("AA03")
    id_A005 = os.getenv("AA05")
    id_A006 = os.getenv("AA06")
    id_A007 = os.getenv("AA07")
    id_A008 = os.getenv("AA08")
    id_A009 = os.getenv("AA09")
    id_A010 = os.getenv("AA10")
    sqlite_url = os.getenv("SQLITE_URL")
    posgre_database_url = os.getenv("POSGRE_URL")
    secret_key = os.getenv("SECRET_KEY")
    algo = os.getenv("ALGORITHM")
    cors_origins = os.getenv("CORS_ORIGINS")
    # local_origin = os.getenv("LOCAL_CORS_ORIGINS")


    if id_A003:
        # print(f"STEP3：ファイルIDを取得しました。 -> {id_A003}")
        create_logger(f"ファイルIDを取得しました。: {id_A003}")
        result["file_id_03"] = id_A003
    else:
        print("ファイルIDが取得できませんでした。")
        create_error_logger("ファイルIDが取得できませんでした。")

    if id_A005:
        # print(f"STEP3：ファイルIDを取得しました。 -> {id_A005}")
        create_logger(f"ファイルIDを取得しました。: {id_A005}")
        result["file_id_05"] = id_A005
    else:
        print("ファイルIDが取得できませんでした。")
        create_error_logger("ファイルIDが取得できませんでした。")

    if id_A006:
        # print(f"STEP3：ファイルIDを取得しました。 -> {id_A006}")
        create_logger(f"ファイルIDを取得しました。: {id_A006}")
        result["file_id_06"] = id_A006
    else:
        print("ファイルIDが取得できませんでした。")
        create_error_logger("ファイルIDが取得できませんでした。")

    if id_A007:
        # print(f"STEP3：ファイルIDを取得しました。 -> {id_A007}")
        create_logger(f"ファイルIDを取得しました。: {id_A007}")
        result["file_id_07"] = id_A007
    else:
        print("ファイルIDが取得できませんでした。")
        create_error_logger("ファイルIDが取得できませんでした。")

    if id_A008:
        # print(f"STEP4：ファイルIDを取得しました。 -> {id_A008}")
        create_logger(f"ファイルIDを取得しました。: {id_A008}")
        result["file_id_08"] = id_A008
    else:
        print("ファイルIDが取得できませんでした。 -> {id_A008}")
        create_error_logger("ファイルIDが取得できませんでした。 {id_A008}")

    if id_A009:
        # print(f"STEP4：ファイルIDを取得しました。 -> {id_A009}")
        create_logger(f"ファイルIDを取得しました。: {id_A009}")
        result["file_id_09"] = id_A009

    if id_A010:
        # print(f"STEP4：ファイルIDを取得しました。 -> {id_A010}")
        create_logger(f"ファイルIDを取得しました。: {id_A010}")
        result["file_id_10"] = id_A010
    else:
        print("ファイルIDが取得できませんでした。 -> {id_A009}")
        create_error_logger("ファイルIDが取得できませんでした。 {id_A009}")

    if sqlite_url:
        # print(f"STEP4：DB_URLを取得しました。 -> {database_url}")
        create_logger(f"開発用のDB_URLを取得しました。: {sqlite_url}")
        result["database_url"] = sqlite_url
    else:
        print("開発用のDB_URLが取得できませんでした。")
        create_error_logger("開発用のDB_URLが取得できませんでした。")

    if posgre_database_url:
        # print(f"STEP4：DB_URLを取得しました。 -> {posgre_database_url}")
        create_logger(f"本番用のDB_URLを取得しました。: {posgre_database_url}")
        result["database_url"] = posgre_database_url
    else:
        print("本番用のDB_URLが取得できませんでした。")
        create_error_logger("本番用のDB_URLが取得できませんでした。")

    if secret_key:
        # print(f"STEP4：SECRET_KEYを取得しました。 -> {secret_key}")
        create_logger(f"SECRET_KEYを取得しました。: {secret_key}")
        result["secret_key"] = secret_key
    else:
        print("SECRET_KEYが取得できませんでした。")
        create_error_logger("SECRET_KEYが取得できませんでした。")

    if algo:
        # print(f"STEP4：ALGORITHMを取得しました。 -> {algo}")
        create_logger(f"ALGORITHMを取得しました。: {algo}")
        result["algo"] = algo
    else:
        print("ALGORITHMが取得できませんでした。")
        create_error_logger("ALGORITHMが取得できませんでした。")

    if cors_origins:
        # 文字列をリストに変換（カンマ区切りでURLを追加した場合）
        if "," in cors_origins:
            result["cors_origins"] = [origin.strip() for origin in cors_origins.split(",")]
        else:
            # print(f"STEP4：CORS_ORIGINSを取得しました。 -> {cors_origins}")
            create_logger(f"CORS_ORIGINSを取得しました。: {cors_origins}")
            # 単一の値の場合はリストに入れる（現在はこちらが処理される）
            result["cors_origins"] = [cors_origins.strip()]
    else:
        print("CORS_ORIGINSが取得できませんでした。")
        create_error_logger("CORS_ORIGINSが取得できませんでした。")

    # if local_origin:
    #     if "," in local_origin:
    #         result["local_origin"] = [origin.strip() for origin in local_origin.split(",")]
    #     else:
    #         print(f"STEP4：LOCAL_CORS_ORIGINSを取得しました。 -> {local_origin}")
    #         create_logger(f"LOCAL_CORS_ORIGINSを取得しました。: {local_origin}")
    #         # 単一の値の場合はリストに入れる（現在はこちらが処理される）
    #         result["local_origin"] = [local_origin.strip()]
    # else:
    #     print("LOCAL_CORS_ORIGINSが取得できませんでした。")
    #     create_error_logger("LOCAL_CORS_ORIGINSが取得できませんでした。")

    if not result:
        print("環境変数の取得に失敗しました。")
        create_error_logger("環境変数の取得に失敗しました。")
        return result
    else:
        # print(f"STEP5：環境変数の取得に成功しました")
        create_logger(f"環境変数の取得に成功しました。: {result}")

        # 環境変数を構造化して表示する
        # print("")
        # pprint.pprint(result)
        # print("")
        return result

db_env = read_env_var(env_var)


class DatabaseConnectionError(Exception):
    """データベース接続エラーを表すカスタム例外"""
    pass


# データベースエンジンを作成
def create_database_engine() -> Engine:
    """環境変数からデータベースURLを取得し、データベースエンジンを作成する。

    開発環境ではSQLite、本番環境ではPostgreSQLを使用します。
    データベースURLが設定されていない場合は、DatabaseConnectionErrorをスローします。

    connect_args:
    - SQLite: {"check_same_thread": False}
    - PostgreSQL: 接続プール設定
    """
    try:
        DB_URL = db_env.get("sqlite_url")
        if not DB_URL:
            print("DATABASE_URLが設定されていません。")
            create_error_logger("DATABASE_URLが設定されていません。")
            raise DatabaseConnectionError("DATABASE_URLが設定されていません。")
        else:
            create_logger(f"DB_URLを取得しました。環境: {DB_URL}")

        # 本番環境（PostgreSQL）の設定
        if not DB_URL.startswith("posgre_database_url"):
            create_error_logger("本番環境ではPostgreSQLのURL形式が必要です")
            raise DatabaseConnectionError("本番環境ではPostgreSQLのURL形式が必要です")
        if DB_URL.startswith("postgresql"):
            # PostgreSQL用の接続設定
            connect_args = {
                "pool_size": 10,          # 接続プールのサイズ
                "max_overflow": 20,      # プールを超える接続数
                "pool_timeout": 30,      # 接続取得のタイムアウト（秒）
                "pool_recycle": 1800     # 接続の再利用時間（秒）
            }
            engine = create_engine(
                DB_URL, 
                connect_args=connect_args,
                echo=False               # 本番環境ではSQLログを出力しない
            )
            create_logger("PostgreSQL（本番環境）でデータベース接続を確立しました")

        else:
            # 開発環境（SQLite）の設定
            if not DB_URL.startswith("sqlite"):
                create_logger("開発環境用にSQLiteを使用します")
                # 開発環境では強制的にSQLiteを使用
                DB_URL = ""

            # SQLite用の接続設定
            connect_args = {"check_same_thread": False}
            engine = create_engine(
                DB_URL, 
                connect_args=connect_args,
                echo=True               # 開発環境ではSQLログを出力
            )
            create_logger("SQLite（開発環境）でデータベース接続を確立しました")

        return engine

    except Exception as e:
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
            # print(f"STEP9：セッションを確立しました。 -> {session_id}")
            create_logger(f"セッションを確立しました。 -> {session_id}")
        return SessionLocal
    except Exception as e:
        # pprint.pprint(f"Error: {e}")
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
        # print("DBセッションをコミットしました")
        create_logger("DBセッションをコミットしました")
    except Exception as e:
        # pprint.pprint(str(e))
        create_error_logger(
            f"DBセッションのコミットに失敗しました。: {str(e)}"
            )
        raise
    finally:
        db.close()
        # print("DBセッションをクローズしました")
        create_logger("DBセッションをクローズしました")