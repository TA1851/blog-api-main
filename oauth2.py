"""認証トークンモジュール"""
from jose import JWTError, jwt
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import db_env, get_db
from models import User
from schemas import TokenData
from custom_token import SECRET_KEY, ALGORITHM


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")

# TODO: 開発時に切り替える
db_url = db_env.get("posgre_url")


def check_environment_variable():
  """環境変数設定ファイルからデータベースのURLを取得する

  :param db_env: 環境変数設定ファイル
  :return: データベースURL
  """
  if not db_env:
    raise ValueError(f"環境変数が設定されていません。-> {db_env}")
  else:
    return db_env

check_environment_variable()


def check_db_url():
  """データベースURLを取得して、データベースと接続する

  :param db_url: データベースURL
  :return: データベースURL
  """
  if not db_url:
    raise ValueError(f"環境変数が設定されていません。{db_url}")
  else:
    return db_url

check_db_url()
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
      print(f"JWTErrorが発生しました: {str(e)}")
      raise credentials_exception
  # 直接データベースからユーザーを取得
  user = db.query(User).filter(User.email == token_data.email).first()
  if user is None:
      raise credentials_exception
  return user