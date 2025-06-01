"""認証機能を実装するためのルーターモジュール"""
# import pprint
from typing import List, Set
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from schemas import Login, ShowArticle, PasswordChange
from database import session, db_env
from hashing import Hash
from custom_token import create_access_token
from models import User, Article
from logger.custom_logger import create_logger, create_error_logger
from utils.email_sender import send_registration_complete_email


router = APIRouter(
    prefix="/api/v1",
    tags=["auth"],
)

# データベース設定は database.py で管理されているため、
# auth.py では個別の URL チェックは不要です。
# print(f"STEP22：ログイン機能を検証します。Swaggerで確認してください。")
# print("---------------------------------------------------------------")


def get_db():
    """データベースセッションを取得するための依存関数"""

    db = session()
    try:
        yield db
        # print("DBセッションをコミットしました")
        create_logger("DBセッションをコミットしました")
    except Exception as e:
        # pprint.pprint(str(e))
        create_error_logger(f"DBセッションのコミットに失敗しました。: {str(e)}")
        raise
    finally:
        db.close()
        # print("DBセッションをクローズしました")
        create_logger("DBセッションをクローズしました")


@router.post('/login')
async def login(
    request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
    ) -> dict:
    """ユーザー認証を行い、認証に成功した場合はアクセストークン（JWT）を返します。

    ログインエンドポイント：
    ```
    http://127.0.0.1:8080/api/v1/login
    ```

    注意：仮パスワードから新パスワードへの変更は以下のエンドポイントを使用してください：
    ```
    http://127.0.0.1:8080/api/v1/change-password
    ```

    パラメータ：
    ```
    username: ユーザー名（メールアドレス）
    password: パスワード
    ```

    レスポンス：成功時(200 OK), 失敗時(404 Not Found)
    ```
    {
        "access_token": "JWTトークン文字列",
        "token_type": "bearer"
    }
    ```

    :param request: OAuth2PasswordRequestForm

    :type request: OAuth2PasswordRequestForm

    :param db: データベースセッション

    :type db: Session

    :return: アクセストークンを返します。token_type:bearer

    :rtype: dict

    :raises HTTPException: ユーザー名またはパスワードが無効な場合
    """
    print(f"Login attempt with username: {request.username}")


    user = db.query(User).filter(User.email == request.username).first()
    if not user:
        # print(f"User not found with email: {request.username}")
        create_error_logger(f"無効なユーザー名です: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"無効なユーザー名です"
        )
    if not Hash.verify(
        request.password,
        user.password
    ):
        # print("Password verification failed")
        create_error_logger(f"無効なパスワードです: {request.password}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="無効なパスワードです"
        )
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id}
    )
    # print("==================================================")
    # print(f"ログインしました。: {user.email}")
    # print("==================================================")
    create_logger(f"ログインに成功しました: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}


# OAuth2スキームを定義
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


# ブラックリストを保持するセット
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
        # トークンの検証ロジックを実装
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
    """ログアウトエンドポイント:https://127.0.0.1:8000/api/v1/logout

    リクエストヘッダー
    ```
    Authorization: Bearer <token>
    Content-Type: application/json
    ```
    パラメータ：
    ```
    Authorizationヘッダーから自動取得
    ```
    
    レスポンス：成功時(200 OK), 失敗時(401 Unauthorized)
    ```
    {
        "message": "ログアウトしました"
    }
    ```
    エラー時：
    401 Unauthorized：トークンが無効な場合
    422 Unprocessable Entity：トークンが既に無効化されている場合
    ```
    {
        "detail": "トークンが無効化されています"
    }
    ```

    :param token: 認証トークン（ヘッダーから自動取得）

    :type token: Bearer

    :raises HTTPException: トークンが無効な場合

    :return: ログアウトしました。

    :rtype: dict

    :raises HTTPException: トークンが無効化されている場合
    """
    # トークンをブラックリストに追加して無効化
    token_blacklist.add(token)
    # print(f"ログアウトしました。")
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
    return db.query(Article).all()


@router.post('/change-password')
async def change_password(
    request: PasswordChange,
    db: Session = Depends(get_db)
) -> dict:
    """仮パスワードから新パスワードへの変更を行うエンドポイント

    パスワード変更エンドポイント：
    ```
    http://127.0.0.1:8080/api/v1/change-password
    ```

    パラメータ：
    ```
    username: ユーザー名（メールアドレス）
    temp_password: 現在の仮パスワード
    new_password: 新しいパスワード
    ```

    レスポンス：成功時(200 OK), 失敗時(404 Not Found/400 Bad Request)
    ```
    {
        "access_token": "JWTトークン文字列",
        "token_type": "bearer",
        "message": "パスワードが正常に変更されました。登録完了メールを送信しました。"
    }
    ```
    
    注意：パスワード変更成功後、登録完了メールが自動的に送信されます。

    :param request: PasswordChange
    :type request: PasswordChange
    :param db: データベースセッション
    :type db: Session
    :return: アクセストークンとメッセージを返します
    :rtype: dict
    :raises HTTPException: ユーザー名または仮パスワードが無効な場合
    """
    print(f"Password change attempt for username: {request.username}")
    create_logger(f"パスワード変更試行: {request.username}")

    # ユーザーの存在確認
    user = db.query(User).filter(User.email == request.username).first()
    if not user:
        create_error_logger(f"無効なユーザー名です: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="無効なユーザー名です"
        )

    # 仮パスワードの検証
    if not Hash.verify(request.temp_password, user.password):
        create_error_logger(f"無効な仮パスワードです: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無効な仮パスワードです"
        )

    # 新しいパスワードのハッシュ化と更新
    hashed_new_password = Hash.bcrypt(request.new_password)
    user.password = hashed_new_password

    try:
        db.commit()
        create_logger(f"パスワード変更成功: {request.username}")

        # 登録完了メールを送信
        try:
            # user.nameがNoneの場合はメールアドレスのローカル部分を使用
            user_name = user.name if user.name else user.email.split('@')[0]
            await send_registration_complete_email(user.email, user_name)
            create_logger(f"登録完了メールを送信しました: {user.email}")
        except Exception as email_error:
            create_error_logger(f"登録完了メール送信に失敗しました: {user.email}, エラー: {str(email_error)}")

        # 新しいアクセストークンを生成
        access_token = create_access_token(
            data={"sub": user.email, "id": user.id}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "message": "パスワードが正常に変更されました。"
        }
    except Exception as e:
        db.rollback()
        create_error_logger(f"パスワード変更失敗: {request.username}, エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="パスワード変更中にエラーが発生しました"
        )