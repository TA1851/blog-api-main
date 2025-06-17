"""認証機能を実装するためのルーターモジュール"""
from typing import List, Set, Dict, Generator, Optional
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
import logging
from typing import Optional

from schemas import ShowArticle, PasswordChange
from database import session, get_db
from hashing import Hash
from custom_token import create_access_token
from models import User, Article
from oauth2 import get_current_user
from utils.email_sender import send_registration_complete_email
from utils.email_validator import is_valid_email_domain
from exceptions import DatabaseConnectionError


# 認証レスポンスの型定義
from typing_extensions import TypedDict


class LoginResponse(TypedDict):
    """ログインレスポンスの型定義"""
    access_token: str
    token_type: str


class TokenResponse(TypedDict):
    """トークンレスポンスの型定義"""
    access_token: str
    token_type: str
    user_id: str


# パスワード変更レスポンス型
class PasswordChangeResponse(TypedDict, total=False):
    """パスワード変更レスポンスの型定義"""
    message: str
    user_id: str
    access_token: str
    token_type: str
    email_sent: bool
    email_error: Optional[str]


router = APIRouter(
    prefix="/api/v1",
    tags=["auth"],
)


@router.post('/login')
async def login(
    request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
    ) -> LoginResponse:
    """ユーザー認証を行い、ログインする

    ログインエンドポイント：
    ```
    http://<環境のURL>/api/v1/login
    ```

    注意：仮パスワードから新パスワードへの変更は以下のエンドポイントを使用してください::

        http://<環境のURL>/api/v1/change-password

    パラメータ::

        username: ユーザー名（メールアドレス）
        password: パスワード

    レスポンス：成功時(200 OK), 失敗時(404 Not Found)::

        {
            "access_token": "JWTトークン文字列",
            "token_type": "bearer"
        }

    :param request: OAuth2PasswordRequestForm
    :type request: OAuth2PasswordRequestForm
    :param db: データベースセッション
    :type db: Session
    :return: アクセストークンを返します。token_type:bearer
    :rtype: dict
    :raises HTTPException: ユーザー名またはパスワードが無効な場合
    """


    # メールドメインの検証
    if not is_valid_email_domain(request.username):
        print(
            f"許可されていないドメインです: {request.username}"
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"無効なユーザー名です"
        )

    user = db.query(User).filter(User.email == request.username).first()
    if not user:
        print(
            f"無効なユーザー名です: {request.username}"
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"無効なユーザー名です"
        )
    if not user.password or not Hash.verify(
        request.password,
        user.password
    ):
        print(
            f"無効なパスワードです: {request.password}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無効なパスワードです"
        )
    try:
        access_token = create_access_token(
            data={"sub": user.email or "", "id": user.id}
        )
    except RuntimeError as token_error:
        print(
            f"アクセストークンの生成に失敗しました: {str(token_error)}"
            )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="アクセストークンの生成に失敗しました"
        )
    except Exception as unexpected_error:
        print(
            f"予期しないエラーが発生しました: {str(unexpected_error)}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="アクセストークンの生成に失敗しました"
        )
    try:
        db.commit()
    except Exception as db_error:
        db.rollback()
        print(
            f"DBセッションのコミットに失敗しました: {str(db_error)}"
            )
        raise DatabaseConnectionError(
            message="データベースエラーが発生しました"
        )
    print(
        f"ログインに成功しました: {user.email}"
        )
    return {"access_token": access_token, "token_type": "bearer"}


# OAuth2スキームを定義
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")
token_blacklist: Set[str] = set()


def verify_token(
    token: str = Depends(
        oauth2_scheme
        )
    ) -> Dict[str, str]:
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
        # トークンの検証ロジックを実装
        payload = jwt.decode(
            token, "SECRET_KEY", algorithms=["HS256"]
            )
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
    ) -> Dict[str, str]:
    """ログアウトエンドポイント:http://<環境のURL>/api/v1/logout

    リクエストヘッダー::

        Authorization: Bearer <token>
        Content-Type: application/json

    パラメータ::

        Authorizationヘッダーから自動取得

    レスポンス：成功時(200 OK), 失敗時(401 Unauthorized)::

        {
            "message": "ログアウトしました"
        }

    エラー時：
    401 Unauthorized：トークンが無効な場合
    422 Unprocessable Entity：トークンが既に無効化されている場合::

        {
            "detail": "トークンが無効化されています"
        }

    :param token: 認証トークン（ヘッダーから自動取得）
    :type token: str
    :raises HTTPException: トークンが無効な場合
    :return: ログアウト結果メッセージ
    :rtype: dict
    """
    # トークンをブラックリストに追加して無効化
    token_blacklist.add(token)
    print("ログアウトに成功しました")
    return {"message": "ログアウトしました"}


@router.get(
    "/article",
    response_model=List[ShowArticle]
    )
async def get_all_blogs(
    db: Session = Depends(get_db)
) -> List[ShowArticle]:
    """ログインユーザの全ての記事を取得するエンドポイント

    :param db: データベースセッション

    :type db: Session

    :return: 記事のリスト

    :rtype: List[ShowArticle]
    """
    articles = db.query(Article).all()
    return [
        ShowArticle(
            id=article.id,
            title=article.title,
            body=article.body
        ) for article in articles
    ]


@router.post('/change-password')
async def change_password(
    request: PasswordChange,
    db: Session = Depends(get_db)
) -> PasswordChangeResponse:
    """仮パスワードから新パスワードへの変更を行うエンドポイント（認証不要）"""
    print(f"Password change attempt for username: {request.username}")

    # ユーザーの存在確認
    user = db.query(User).filter(User.email == request.username).first()
    if not user:
        print(
            f"User not found: {request.username}"
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )

    # 仮パスワードの検証
    if not user.password or not Hash.verify(request.temp_password, user.password):
        print(
            f"Invalid temporary password for user: {request.username}"
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="仮パスワードが無効です"
        )

    # 新しいパスワードのハッシュ化と更新
    hashed_new_password = Hash.bcrypt(request.new_password)
    user.password = hashed_new_password

    try:
        db.commit()
        print(f"Password changed successfully for user: {request.username}")

        # 新しいアクセストークンを生成
        access_token = create_access_token(
            data={"sub": user.email or "", "id": user.id}
        )
        print(f"New access token created for user: {request.username}")

        # レスポンスデータの初期化
        response_data: PasswordChangeResponse = {
            "message": "パスワードが正常に変更されました。",
            "user_id": str(user.id),
            "access_token": access_token,
            "token_type": "bearer",
            "email_sent": False
        }
        # メール送信処理（改善されたエラーハンドリング）
        email_error_details: Optional[str] = None
        if user.email:
            try:
                user_name = user.name if user.name else user.email.split('@')[0]
                await send_registration_complete_email(user.email, user_name)
                print(
                    f"Registration complete email sent successfully to: {user.email}"
                    )
                response_data["email_sent"] = True
            except ConnectionError as conn_error:
                error_msg = "メールサーバーに接続できませんでした"
                email_error_details = f"Connection error: {str(conn_error)}"
                print(
                    f"Email connection error for {user.email}: {conn_error}"
                    )
            except TimeoutError as timeout_error:
                error_msg = "メール送信がタイムアウトしました"
                email_error_details = f"Timeout error: {str(timeout_error)}"
                print(
                    f"Email timeout error for {user.email}: {timeout_error}"
                    )
            except ValueError as value_error:
                error_msg = "無効なメールアドレスです"
                email_error_details = f"Invalid email format: {str(value_error)}"
                print(
                    f"Invalid email format for {user.email}: {value_error}"
                    )
            except Exception as email_error:
                error_msg = "メール送信中に予期しないエラーが発生しました"
                email_error_details = f"Unexpected error: {str(email_error)}"
                print(
                    f"Unexpected email error for {user.email}: {email_error}"
                    )
            # メール送信エラーの場合の処理
            if email_error_details:
                response_data["email_sent"] = False
                response_data["email_error"] = error_msg
                # 詳細なエラー情報はログに記録し、ユーザーには一般的なメッセージを返す
                print(
                    f"Email sending failed for {user.email}: {email_error_details}"
                    )
        else:
            print(
                f"No email address for user: {request.username}"
                )
            response_data["email_error"] = "ユーザーにメールアドレスが設定されていません"
        return response_data
    except Exception as db_error:
        db.rollback()
        print(
            f"Database error during password change for {request.username}: {str(db_error)}"
            )
        # データベースエラーの種類に応じた詳細なエラーハンドリング
        if "constraint" in str(db_error).lower():
            error_detail = "データベース制約違反が発生しました"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        elif "connection" in str(db_error).lower():
            error_detail = "データベース接続エラーが発生しました"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        else:
            error_detail = "パスワード変更中にエラーが発生しました"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code,
            detail=error_detail
        )