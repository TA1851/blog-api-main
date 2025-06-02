"""ユーザ認証機能を実装するためのルーターモジュール"""
import traceback
import os
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, status, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4
from urllib.parse import unquote

from schemas import User as UserSchema, AccountDeletionRequest
from models import User as UserModel
from models import EmailVerification
from database import get_db
from hashing import Hash
from oauth2 import get_current_user
from logger.custom_logger import create_logger, create_error_logger
from utils.email_sender import send_verification_email, send_account_deletion_email
from utils.email_validator import is_valid_email_domain


# APIレスポンスの型定義
UserCreateResponse = Dict[str, str]
UserDeleteResponse = Dict[str, str]
UserUpdateResponse = Dict[str, str]


router = APIRouter(
    prefix="/api/v1",
    tags=["user"],
)


def check_environment_variable() -> None:
    """環境変数を取得する

    :param key08: user.pyの環境変数
    :type key08: str
    :return: 環境変数の値
    :rtype: str
    """

check_environment_variable()


def check_db_url() -> None:
    """データベースURLを取得する

    :param key03: user.pyの環境変数
    :type key03: str
    :param db_url: user.pyの環境変数
    :type db_url: str
    :return: 環境変数の値
    :rtype: str
    """

check_db_url()
get_db()


class IntegrityError(Exception):
    """主にユニーク制約違反（メールアドレスが既に使用されている場合など）を示すエラー"""
    pass


class SQLAlchemyError(Exception):
    """データベース関連のエラー"""
    pass


# 環境変数の読み込む
ALLOWED_EMAIL_DOMAINS_RAW = os.getenv("ALLOWED_EMAIL_DOMAINS", "")
ALLOWED_EMAIL_DOMAINS = [domain.strip() for domain in ALLOWED_EMAIL_DOMAINS_RAW.split(",") if domain.strip()]
ENABLE_DOMAIN_RESTRICTION = os.getenv("ENABLE_DOMAIN_RESTRICTION", "true").lower() == "true"
ENABLE_EMAIL_VERIFICATION = os.getenv("ENABLE_EMAIL_VERIFICATION", "true").lower() == "true"

# デバッグ情報
create_logger(f"[修正後] 環境変数ALLOWED_EMAIL_DOMAINS_RAW: '{ALLOWED_EMAIL_DOMAINS_RAW}'")
create_logger(f"[修正後] 解析後のALLOWED_EMAIL_DOMAINS: {ALLOWED_EMAIL_DOMAINS}")
create_logger(f"[修正後] ENABLE_DOMAIN_RESTRICTION: {ENABLE_DOMAIN_RESTRICTION}")


class UserRouter:
    @router.post(
    "/user",
    status_code=status.HTTP_201_CREATED,
    response_model=UserSchema,
    summary="User Create (Email Only)",
    description="メールアドレスのみでユーザーを作成するエンドポイント。パスワードは仮パスワードが自動設定されます。",
    )
    async def create_user(
        self,
        user: UserSchema,
        db: Session = Depends(get_db)
    ) -> UserCreateResponse:
        """メールアドレスのみでユーザーを作成するエンドポイント
        
        パスワードは自動的に仮パスワード 'temp_password_123' が設定されます。
        ユーザーは登録後にパスワード変更エンドポイントでパスワードを設定する必要があります。
        """
        try:
            # 入力データの検証
            if user.email is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="メールアドレスが必要です。"
                )
                
            create_logger(f"ユーザー作成開始 - メール: {user.email}")

            # ドメイン制限チェック
            if ENABLE_DOMAIN_RESTRICTION and not is_valid_email_domain(user.email):
                create_error_logger(f"ドメイン検証失敗 - メール: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"このメールアドレスのドメインは許可されていません。許可されたドメイン: \
                    {', '.join(ALLOWED_EMAIL_DOMAINS)}"
                )

            # メールアドレスの重複チェック
            existing_user = db.query(UserModel).filter(
                UserModel.email == user.email
            ).first()

            if existing_user:
                create_error_logger(f"既存のメールアドレスが検出されました: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="このメールアドレスは既に使用されています。"
                )

            if ENABLE_EMAIL_VERIFICATION:
                # メール認証が有効な場合の従来の処理
                existing_verification = db.query(EmailVerification).filter(
                    EmailVerification.email == user.email
                ).first()

                if existing_verification:
                    if existing_verification.is_verified:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="このメールアドレスは既に確認済みです。"
                        )
                    else:
                        # 既存のレコードを更新（メールアドレスのみ）
                        existing_verification.token = str(uuid4())
                        existing_verification.created_at = datetime.utcnow()
                        existing_verification.expires_at = datetime.utcnow() + timedelta(hours=24)
                        verification = existing_verification
                        create_logger(f"既存の確認レコードを更新しました: {user.email}")
                else:
                    verification = EmailVerification.create_verification(user.email)
                    db.add(verification)
                    create_logger(f"新しい確認レコードを作成しました: {user.email}")

                db.commit()
                await send_verification_email(user.email, verification.token)

                return {
                    "message": "ユーザー登録を受け付けました。確認メールをお送りしましたので、メール内のリンクをクリックして登録を完了してください。",
                    "email": user.email
                }
            else:
                # メール認証が無効な場合の直接ユーザー作成
                if user.email is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="メールアドレスが必要です。"
                    )
                
                # 仮パスワードを生成
                temp_password = "temp_password_123"
                
                new_user = UserModel(
                    name=user.name if hasattr(user, 'name') and user.name else user.email.split('@')[0],
                    email=user.email,
                    password=Hash.bcrypt(temp_password),
                    is_active=True
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                create_logger(f"ユーザーを直接作成しました: {user.email}")

                return {
                    "message": "ユーザー登録が完了しました。仮パスワード 'temp_password_123' でログインして、パスワードを変更してください。",
                    "email": user.email,
                    "id": str(new_user.id),
                    "is_active": str(new_user.is_active)
                }

        except HTTPException:
            db.rollback()
            raise

        except Exception as e:
            db.rollback()
            error_detail = traceback.format_exc()
            create_error_logger(f"不明なエラーが発生しました: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="予期しないエラーが発生しました。"
            )
        finally:
            create_logger("DBセッションをクローズします")
            db.close()


    @router.get(
        "/verify-email",
        summary="Email Verification",
        description="ユーザーのメールアドレスを確認するエンドポイント",
    )
    async def verify_email(
        self,
        token: str = Query(...),
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        # デバッグログを追加
        create_logger(f"メール認証リクエスト受信 - 元のトークン: {token}")

        # URLデコード処理（安全性を確保）
        decoded_token = unquote(token)
        create_logger(
            f"メール認証リクエスト受信 - デコード後トークン: {decoded_token}"
            )
        # トークンの形式チェック
        if not decoded_token or len(decoded_token) < 10:
            create_error_logger(f"無効なトークン形式: {decoded_token}")
            raise HTTPException(
                status_code=400,
                detail="無効なトークン形式です。"
            )

        verification = db.query(EmailVerification).filter(
            EmailVerification.token == decoded_token
        ).first()

        if not verification:
            # データベース内の全トークンを確認
            all_verifications = db.query(EmailVerification).all()
            create_logger(f"データベース内のトークン数: {len(all_verifications)}")
            for v in all_verifications:
                create_logger(
                    f"DB内トークン: {v.token[:20]}..., Email: {v.email}, 確認済み: {v.is_verified}"
                    )
            create_error_logger(f"トークンが見つかりません: {decoded_token[:20]}...")
            raise HTTPException(
                status_code=400,
                detail="無効なトークンです。"
            )
        if verification.is_verified:
            raise HTTPException(
                status_code=400,
                detail="このメールアドレスは既に確認済みです。"
            )
        if verification.expires_at is not None and datetime.utcnow() > verification.expires_at:
            raise HTTPException(
                status_code=400,
                detail="トークンの有効期限が切れています。"
            )

        # 初期パスワード
        user_password = verification.password_hash if hasattr(
            verification, 'password_hash') and verification.password_hash \
            else Hash.bcrypt("temp_password_123")

        # ユーザーの作成
        new_user = UserModel(
            name=verification.email.split('@')[0],  # @の前の部分をユーザー名に設定
            email=verification.email,
            password=user_password,
            is_active=True
        )

        verification.is_verified = True
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "メールアドレスの確認が完了しました。仮パスワードを変更して登録を完了してください。",
            "email": verification.email,
            "user_id": new_user.id,
            "is_active": new_user.is_active
        }


# カスタム例外クラス（ユーザ関連）
class UserNotFoundError(Exception):
    """ユーザーが見つからない場合の例外"""
    def __init__(self, user_id: Optional[int] = None, email: Optional[str] = None):
        if user_id:
            self.message = f"User with id {user_id} not found"
        elif email:
            self.message = f"User with email {email} not found"
        else:
            self.message = "User not found"
        super().__init__(self.message)


class EmailVerificationError(Exception):
    """メール確認に関する例外"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DatabaseError(Exception):
    """データベース関連の例外"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


@router.get(
    "/user/{user_id}",
    response_model=UserSchema,
    summary="Get User (Authentication Required)",
    description="認証が必要なユーザー情報取得エンドポイント。ユーザーは自分自身の情報のみ取得可能。"
)

async def show_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> UserSchema:
    """ユーザー情報を取得する関数（認証が必要）

    :param user_id: ユーザーID
    :type user_id: int
    :param db: データベースセッション
    :type db: Session
    :param current_user: 現在ログインしているユーザー
    :type current_user: UserModel
    :return: ユーザー情報
    :rtype: UserSchema
    :raises HTTPException: ユーザーが見つからない場合
    """
    # 認証されたユーザーが自分以外の情報にアクセスしようとしていないかチェック
    if current_user.id != user_id:
        create_error_logger(f"User {current_user.id} tried to access user {user_id}'s information")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="他のユーザーの情報にはアクセスできません"
        )
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        create_error_logger(f"User with id {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    create_logger(f"認証されたユーザー {current_user.id} がユーザー情報を取得しました: {user_id}")
    
    # SQLAlchemyモデルをPydanticスキーマに変換
    return UserSchema(
        email=user.email,
        password=None,  # パスワードは返さない
        is_active=user.is_active
    )


@router.post(
"/resend-verification",
summary="Resend Verification Email",
description="確認メールを再送信するエンドポイント"
)
async def resend_verification_email(
    email: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """確認メールを再送信する"""
    verification = db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.is_verified == False
    ).first()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="確認待ちのメールアドレスが見つかりません。"
        )

    # 新しいトークンを生成
    verification.token = str(uuid4())
    verification.created_at = datetime.utcnow()
    verification.expires_at = datetime.utcnow() + timedelta(hours=24)

    db.commit()

    await send_verification_email(email, verification.token)

    return {"message": "確認メールを再送信しました。"}


@router.delete(
    "/user/delete-account",
    status_code=status.HTTP_200_OK,
    summary="Delete User Account",
    description="ユーザーアカウントと関連データを完全に削除するエンドポイント"
)
async def delete_user_account(
    deletion_request: AccountDeletionRequest,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """ユーザーアカウントを削除するエンドポイント

    :param deletion_request: 退会リクエストデータ
    :type deletion_request: AccountDeletionRequest
    :param db: データベースセッション
    :type db: Session
    :return: 退会完了メッセージ
    :rtype: dict
    :raises HTTPException: ユーザーが見つからない、パスワードが間違っている場合
    """
    try:
        create_logger(f"退会処理開始 - メール: {deletion_request.email}")

        # パスワード一致チェック
        deletion_request.validate_passwords_match()

        # ユーザーの存在確認
        user = db.query(UserModel).filter(
            UserModel.email == deletion_request.email
        ).first()

        if not user:
            create_error_logger(f"退会対象ユーザーが見つかりません: {deletion_request.email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたメールアドレスのユーザーが見つかりません"
            )

        # パスワード検証
        if user.password is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ユーザーのパスワードが設定されていません"
            )
        if not Hash.verify(deletion_request.password, user.password):
            create_error_logger(f"パスワード検証失敗: {deletion_request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="パスワードが正しくありません"
            )

        # ユーザー名を保存（メール送信用）
        if user.email is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ユーザーのメールアドレスが見つかりません。"
            )
        username = user.email.split('@')[0]
        user_email = user.email

        create_logger(f"ユーザー検証完了: {user_email}, ID: {user.id}")

        # ユーザーの記事を削除
        from models import Article
        articles = db.query(Article).filter(Article.user_id == user.id).all()
        article_count = len(articles)

        for article in articles:
            db.delete(article)

        create_logger(f"ユーザーの記事を削除しました: {article_count}件")

        # メール認証テーブルからも削除
        verification_records = db.query(EmailVerification).filter(
            EmailVerification.email == user_email
        ).all()

        for verification in verification_records:
            db.delete(verification)

        create_logger(f"メール認証レコードを削除しました: {len(verification_records)}件")

        # ユーザーアカウントを削除
        db.delete(user)

        # 変更をコミット
        db.commit()

        create_logger(f"ユーザーアカウント削除完了: {user_email}")

        # 退会完了メールを送信
        await send_account_deletion_email(user_email, username)

        return {
            "message": "退会処理が完了しました。退会完了メールをお送りしました。",
            "deleted_articles_count": str(article_count),
            "email": user_email
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as e:
        db.rollback()
        create_error_logger(f"バリデーションエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        db.rollback()
        error_detail = traceback.format_exc()
        create_error_logger(f"退会処理で予期しないエラーが発生しました: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="退会処理中に予期しないエラーが発生しました"
        )

    finally:
        create_logger("DBセッションをクローズします")
        db.close()