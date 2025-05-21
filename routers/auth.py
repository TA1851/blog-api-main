"""認証機能を実装するためのルーターモジュール"""
from typing import List, Set
import pprint
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from schemas import Login, ShowArticle
from database import session, db_env
from hashing import Hash
from custom_token import create_access_token
from models import User
from logger.custom_logger import create_logger, create_error_logger


router = APIRouter(
    prefix="/api/v1",
    tags=["auth"],
)


# 環境変数の取得
db_url = db_env.get("database_url")
key03 = db_env.get("file_id_03")
key09 = db_env.get("file_id_09")


def check_environment_variable():
    """環境変数を取得する

    :param key09: auth.pyの環境変数
    :type key09: str
    :return: 環境変数の値
    :rtype: str
    """
    if not key09:
        create_error_logger(f"環境変数:{key09}が設定されていません。{key09}")
        raise ValueError(f"環境変数が設定されていません。-> {key09}")
    else:
        print(f"STEP20：環境変数：{key09}を取得しました。 -> {key09}")
        create_logger(f"環境変数{key09}を取得しました。:")
    return key09

check_environment_variable()


def check_db_url():
    """データベースURLを取得する

    :param key03: auth.pyの環境変数
    :type key03: str
    :param db_url: auth.pyの環境変数
    :type db_url: str
    :return: 環境変数の値
    :rtype: str
    """
    if not db_url:
        create_error_logger(f"環境変数:{db_url}が設定されていません。 -> {key03}")
        raise ValueError(f"環境変数が設定されていません。{key03}")
    else:
        print(f"STEP21：環境変数: {db_url}を読み込みました。")
    create_logger(f"環境変数: {db_url}を読み込みました。 -> {key03}")
    return db_url

check_db_url()
print(f"STEP22：ログイン機能を検証します。Swaggerで確認してください。")
print("---------------------------------------------------------------")


def get_db():
    """データベースセッションを取得するための依存関数"""

    db = session()
    try:
        yield db
        print("DBセッションをコミットしました")
        create_logger("DBセッションをコミットしました")
    except Exception as e:
        pprint.pprint(str(e))
        create_error_logger(f"DBセッションのコミットに失敗しました。: {str(e)}")
        raise
    finally:
        db.close()
        print("DBセッションをクローズしました")
        create_logger("DBセッションをクローズしました")




@router.post('/login')
async def login(
    request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    description: str = "ログインエンドポイント"
    ) -> dict:
    """ログインエンドポイント

    :param request: OAuth2PasswordRequestForm

    :type request: OAuth2PasswordRequestForm

    :param db: データベースセッション

    :type db: Session

    :return: アクセストークンとトークンタイプ

    :rtype: dict

    :raises HTTPException: ユーザー名またはパスワードが無効な場合
    """
    print(f"Login attempt with username: {request.username}")


    user = db.query(User).filter(User.email == request.username).first()
    if not user:
        print(f"User not found with email: {request.username}")
        create_error_logger(f"無効なユーザー名です: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"無効なユーザー名です"
        )
    if not Hash.verify(
        user.password,
        request.password
    ):
        print("Password verification failed")
        create_error_logger(f"無効なパスワードです: {request.password}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="無効なパスワードです"
        )
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id}
    )
    print("==================================================")
    print(f"ログインしました。: {user.email}")
    print("==================================================")
    create_logger(f"ログインに成功しました: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}


# OAuth2スキームを定義
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


# ブラックリストを保持するセット（メモリ内）
token_blacklist: Set[str] = set()


def verify_token(
    token: str = Depends(
        oauth2_scheme
        )
    ):
    """トークンを検証し、無効化されたトークンを拒否する

    :param token: 認証トークン（ヘッダーから自動取得）
    :type token: str
    :raises HTTPException: トークンが無効な場合
    :return: トークンのペイロード
    :rtype: dict
    :raises HTTPException: トークンが無効化されている場合
    """
    if token in token_blacklist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンが無効化されています"
        )
    try:
        # トークンの検証ロジック（既存のコードがあれば利用）
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なトークンです"
            )
        return {"email": email}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なトークンです"
        )

@router.post(
    '/logout'
    )
async def logout(
    token: str = Depends(
        oauth2_scheme
        )
    ):
    """ログアウトエンドポイント

    :param token: 認証トークン（ヘッダーから自動取得）
    :type token: str
    :raises HTTPException: トークンが無効な場合
    :return: ログアウトメッセージ
    :rtype: dict
    :raises HTTPException: トークンが無効化されている場合
    """
    # トークンをブラックリストに追加して無効化
    token_blacklist.add(token)
    print(f"ログアウトしました。")
    create_logger("ログアウトに成功しました")
    return {"message": "ログアウトしました"}


@router.get(
    "/article",
    response_model=List[ShowArticle]
    )
async def get_all_blogs(
    db: Session = Depends(get_db)):
    """全てのブログ記事を取得するエンドポイント

    :param db: データベースセッション
    :type db: Session
    :return: 記事のリスト
    :rtype: List[ShowArticle]
    """
    return db.query(ShowArticle).all()