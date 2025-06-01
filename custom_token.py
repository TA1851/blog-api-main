"""カスタムトークンの作成"""
# import pprint
import os
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from database import db_env, get_db
from models import User
from logger.custom_logger import create_logger, create_error_logger


router = APIRouter(
    tags=["Auth"]
)


SECRET_KEY = db_env.get("secret_key")
ALGORITHM = db_env.get("algo")
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class TokenType(Enum):
    """トークンタイプの定義"""
    ACCESS = "access"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


class TokenConfig:
    """トークン設定の一元管理

    トークンの有効期限：
    - アクセス: 1時間
    - メール確認トークン: 1時間
    - パスワードリセットトークン: 30分
    """
    DEFAULT_EXPIRES = {
        TokenType.ACCESS: timedelta(hours=1),
        TokenType.EMAIL_VERIFICATION: timedelta(hours=1),
        TokenType.PASSWORD_RESET: timedelta(minutes=30)
    }


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    token_type: TokenType = TokenType.ACCESS
    ):
    """アクセストークンを作成する関数（改善版）

    :param data: トークンに含めるデータ
    :type data: dict
    :param expires_delta: トークンの有効期限
    :type expires_delta: timedelta
    :param token_type: トークンの種類
    :type token_type: TokenType
    :return: JWTトークン
    :rtype: str
    :raises ValueError: データが無効な場合
    :raises RuntimeError: トークン生成に失敗した場合
    """
    if not data:
        raise ValueError("データが空です")

    if not isinstance(data, dict):
        raise ValueError("データは辞書形式である必要があります")

    try:
        to_encode = data.copy()

        # 有効期限の決定（優先順位: カスタム > 設定 > デフォルト）
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            default_expire = TokenConfig.DEFAULT_EXPIRES.get(
                token_type,
                timedelta(minutes=30)
            )
            expire = datetime.now(timezone.utc) + default_expire

        # トークンタイプと有効期限を追加
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),  # 発行時刻
            "type": token_type.value  # トークンタイプ
        })

        # 環境変数の検証
        secret_key = os.getenv("SECRET_KEY")
        algorithm = os.getenv("ALGORITHM", "HS256")

        if not secret_key:
            raise RuntimeError("SECRET_KEYが設定されていません")

        # JWTトークンの生成
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)

        # 開発環境でのみログ出力
        if os.getenv("ENVIRONMENT") == "development":
            create_logger(f"トークン生成成功 - タイプ: {token_type.value}, 有効期限: {expire}")

        return encoded_jwt

    except JWTError as e:
        create_error_logger(f"JWTトークン生成エラー: {str(e)}")
        raise RuntimeError(f"トークン生成に失敗しました: {str(e)}")
    except Exception as e:
        create_error_logger(f"予期しないエラー: {str(e)}")
        raise RuntimeError(f"トークン生成中に予期しないエラーが発生しました: {str(e)}")


def verify_token_with_type(
    token: str,
    expected_type: TokenType,
    credentials_exception: Exception
    ) -> dict:
    """トークンタイプを検証する関数

    :param token: 検証するトークン
    :type token: str
    :param expected_type: 期待するトークンタイプ
    :type expected_type: TokenType
    :param credentials_exception: 認証例外
    :type credentials_exception: HTTPException
    :return: トークンのペイロード
    :rtype: dict
    :raises Exception: トークンが無効または期待と異なるタイプの場合
    """
    try:
        secret_key = os.getenv("SECRET_KEY")
        algorithm = os.getenv("ALGORITHM", "HS256")

        payload = jwt.decode(token, secret_key, algorithms=[algorithm])

        # トークンタイプの検証
        token_type = payload.get("type")
        if token_type != expected_type.value:
            create_error_logger(f"無効なトークンタイプ: 期待={expected_type.value}, 実際={token_type}")
            raise credentials_exception

        return payload

    except JWTError as e:
        create_error_logger(f"トークン検証エラー: {str(e)}")
        raise credentials_exception


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
        print("JWTErrorが発生しました。")
        create_error_logger(f"token_data: {token_data}")
        raise credentials_exception
    user = get_user_by_id(id, db)
    return user


def get_user_by_id(
    id: int, db: Session
    ):
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found"
        )
    return user