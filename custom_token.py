"""カスタムトークンの作成"""
import pprint
from typing import Optional
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from database import db_env
from models import User
from logger.custom_logger import create_logger, create_error_logger
from routers.user import get_db


router = APIRouter(
  tags=["Auth"]
)

# TODO:環境変数設定ファイルに移行する
print("")
pprint.pprint(db_env)
print("")


SECRET_KEY = db_env.get("secret_key")
ALGORITHM = db_env.get("algo")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(
  data: dict,
  expires_delta: Optional[timedelta] = None
  ):
  """アクセストークンを作成する関数

  :param data: トークンに含めるデータ
  :type data: dict
  :param expires_delta: トークンの有効期限
  :type expires_delta: timedelta
  :return: JWTトークン
  :rtype: str
  """
  to_encode = data.copy()
  # adding
  if expires_delta:
    expire = datetime.now(timezone.utc) + expires_delta
    print(f"expire: {expire}")
    create_logger(f"expire: {expire}")
  else:
      expire = datetime.now(timezone.utc) + timedelta(minutes=15)
      print(f"expire: {expire}")
      create_logger(f"expire: {expire}")
  to_encode.update({"exp": expire})
  # TODO:条件判定を入れる
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  return encoded_jwt

def verify_token(
  token: str,
  credentials_exception,
  db: Session = Depends(get_db)
  ):
  """トークンを検証する関数

  :param token: 検証するトークン
  :type token: str
  :param credentials_exception: 認証例外
  :type credentials_exception: HTTPException
  :param db: データベースセッション
  :type db: Session
  :return: ユーザー情報
  :rtype: User
  """
  try:
      payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
      email: str = payload.get("sub")
      id : int = payload.get("id")

      if email is None:
          print("emailがNoneです")
          raise credentials_exception

      from schemas import TokenData
      token_data = TokenData(email=email)
      print(f"token_data: {token_data}")
      create_logger(f"token_data: {token_data}")
  except JWTError:
      print("JWTErrorが発生しました")
      create_error_logger(f"token_data: {token_data}")
      raise credentials_exception
  user = get_user_by_id(id, db)
  return user

def get_user_by_id(id: int, db: Session):
    """ユーザーIDからユーザー情報を取得する関数

    :param id: ユーザーID
    :type id: int
    :param db: データベースセッション
    :type db: Session
    :return: ユーザー情報
    :rtype: User
    """
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND, \
          detail=f"User with id {id} not found"
          )
    return user
