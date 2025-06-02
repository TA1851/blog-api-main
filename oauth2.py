"""認証トークンモジュール"""
from jose import JWTError, jwt
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import db_env, get_db
from models import User
from schemas import TokenData
from custom_token import SECRET_KEY
from database import db_env

ALGORITHM: str = db_env.get("algo") or "HS256"
from logger.custom_logger import create_error_logger


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")


async def get_current_user(
  token: str = Depends(oauth2_scheme),
  db: Session = Depends(get_db)
  ) -> User:
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
      # SECRET_KEYがNoneでないことを確認
      if SECRET_KEY is None:
          raise credentials_exception
      # トークンがNoneでないことを確認
      if token is None:
          raise credentials_exception
      # トークンを検証してペイロードを取得
      payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
      )
      email_raw = payload.get("sub")
      id_raw = payload.get("id")
      if email_raw is None or id_raw is None:
          raise credentials_exception
      email: str = str(email_raw)
      try:
          user_id: int = int(id_raw)
      except (ValueError, TypeError):
          raise credentials_exception
      token_data = TokenData(email=email)
  except JWTError as e:
      print(f"JWTErrorが発生しました: {str(e)}")
      raise credentials_exception

  # 直接データベースからユーザーを取得
  user = db.query(User).filter(User.id == user_id).first()
  if user is None:
      raise credentials_exception
  return user