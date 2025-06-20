"""カスタムトークンの作成"""
# import pprint
import os
from enum import Enum
from typing import Optional, Dict, Union
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from database import db_env, get_db
from models import User
from exceptions import UserNotFoundError


# JWTペイロードの型定義
JWTPayload = Dict[str, Union[str, int, float, datetime]]

router = APIRouter(
    tags=["Auth"]
)

SECRET_KEY = db_env.get("secret_key")
ALGORITHM: str = db_env.get("algo") or "HS256"
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
    data: JWTPayload,
    expires_delta: Optional[timedelta] = None,
    token_type: TokenType = TokenType.ACCESS
) -> str:
    """アクセストークンを作成する関数（改善版）

    :param data: トークンに含めるデータ
    :type data: JWTPayload
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
            "iat": datetime.now(timezone.utc),
            "type": token_type.value
        })

        # 環境変数の検証
        secret_key = SECRET_KEY
        algorithm = ALGORITHM

        if not secret_key:
            raise RuntimeError("SECRET_KEYが設定されていません")
        # JWTトークンをエンコード
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
        return encoded_jwt
    except JWTError as e:
        raise RuntimeError(
            f"トークン生成に失敗しました: {str(e)}"
            )
    except Exception as e:
        raise RuntimeError(
            f"トークン生成中に予期しないエラーが発生しました: {str(e)}"
            )


def verify_token_with_type(
    token: str,
    expected_type: TokenType,
    credentials_exception: Exception
    ) -> JWTPayload:
    """トークンタイプを検証する関数

    :param token: 検証するトークン
    :type token: str
    :param expected_type: 期待するトークンタイプ
    :type expected_type: TokenType
    :param credentials_exception: 認証例外
    :type credentials_exception: HTTPException
    :return: トークンのペイロード
    :rtype: JWTPayload
    :raises Exception: トークンが無効または期待と異なるタイプの場合
    """
    try:
        secret_key = SECRET_KEY
        if secret_key is None:
            print(
                "SECRET_KEYが設定されていません"
                )
            raise ValueError(
                "SECRET_KEYが設定されていません"
                )
        algorithm = ALGORITHM
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])

        # トークンタイプの検証
        token_type = payload.get("type")
        if token_type != expected_type.value:
            print(
                f"無効なトークンタイプ: 期待={expected_type.value}, \
                実際={token_type}"
                )
            raise credentials_exception
        return payload
    except JWTError as e:
        print(
            f"トークン検証エラー: {str(e)}"
            )
        raise credentials_exception


def verify_token(
    token: str,
    credentials_exception: HTTPException,
    db: Session = Depends(get_db)
    ) -> User:
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
        if SECRET_KEY is None:
            print("SECRET_KEYが設定されていません")
            raise credentials_exception
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email_raw = payload.get("sub")
        id_raw = payload.get("id")

        if email_raw is None:
            print(
                "トークンからemailが取得できませんでした"
                )
            raise credentials_exception
        if id_raw is None:
            print(
                "トークンからidが取得できませんでした"
                )
            raise credentials_exception
        email: str = str(email_raw)
        user_id: int = int(id_raw)

        from schemas import TokenData
        token_data = TokenData(email=email)
    except JWTError:
        print(
            "JWTErrorが発生しました。"
            )
        raise credentials_exception
    user = get_user_by_id(user_id, db)
    return user


def get_user_by_id(
    id: int, db: Session
    ) -> User:
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
        raise UserNotFoundError(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found"
        )
    return user