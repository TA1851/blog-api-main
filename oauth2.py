"""認証トークンモジュール"""
from jose import JWTError, jwt
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import db_env, get_db
from models import User
from schemas import TokenData
from custom_token import SECRET_KEY, ALGORITHM
from logger.custom_logger import create_logger, create_error_logger
from routers.user import show_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")

# データベースURLを取得（本番環境のPostgreSQLを優先、次に開発環境のSQLite）
db_url = db_env.get("posgre_url") or db_env.get("sqlite_url")
# key03 = db_env.get("file_id_03")
# key10 = db_env.get("file_id_10")


def check_environment_variable():
  """環境変数設定ファイルからデータベースのURLを取得する

  :param db_env: 環境変数設定ファイル
  :return: データベースURL
  """
  if not db_env:
    create_error_logger(f"環境変数:{db_env}が設定されていません。{db_env}")
    raise ValueError(f"環境変数が設定されていません。-> {db_env}")
  else:
    # print(f"STEP14：環境変数：{db_env}を取得しました。 -> {db_env}")
    # print(f"STEP14：環境変数：{key10}を取得しました。 -> {key10}")
    create_logger(f"環境変数{db_env}を取得しました。:")
  return db_env

check_environment_variable()


def check_db_url():
  """データベースURLを取得して、データベースと接続する

  :param db_url: データベースURL
  :return: データベースURL
  """
  if not db_url:
    create_error_logger(f"環境変数:{db_url}が設定されていません。 -> {db_url}")
    raise ValueError(f"環境変数が設定されていません。{db_url}")
  else:
    # print(f"STEP15：環境変数: {db_url}を読み込みました。")
    create_logger(f"環境変数: {db_url}を読み込みました。 -> {db_url}")
  return db_url


check_db_url()
# print(f"STEP16：ユーザを作成します。Swaggerで確認してください。")
# print("---------------------------------------------------------------")

get_db()


async def get_current_user(
  token: str = Depends(oauth2_scheme),
  db: Session = Depends(get_db)
  ):
  """トークンを検証し、現在のユーザーを取得する

  :param token: 認証トークン
  :param db: データベースセッション
  :param id: トークンから取得したユーザーID
  :return: ユーザー情報
  :raises HTTPException: 認証情報が無効な場合
  """
  credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="認証情報が無効です",
      headers={"WWW-Authenticate": "Bearer"},
  )
  try:
      # トークンを検証してペイロードを取得
      payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
      )
      email: str = payload.get("sub")
      id: int = payload.get("id")

      if email is None:
          print("emailがNoneです")
          create_error_logger("emailがNoneです")
          raise credentials_exception

      token_data = TokenData(email=email)
  except JWTError as e:
      print("JWTErrorが発生しました")
      create_error_logger(f"JWTErrorが発生しました: {str(e)}")
      raise credentials_exception

  user = await show_user(id, db)
  return user