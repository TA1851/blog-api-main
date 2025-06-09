"""ユーザ認証機能を実装するためのルーターモジュール"""
import traceback
import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, status, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4
from urllib.parse import unquote

from schemas import User as UserSchema, AccountDeletionRequest
from pydantic import BaseModel
from models import User as UserModel
from models import EmailVerification
from database import get_db
from hashing import Hash
from oauth2 import get_current_user
from utils.email_sender import send_verification_email, send_account_deletion_email
from utils.email_validator import is_valid_email_domain
from exceptions import UserNotFoundError, EmailVerificationError, DatabaseError


class IntegrityError(Exception):
    """主にユニーク制約違反（メールアドレスが既に使用されている場合など）を示すエラー"""
    pass


class SQLAlchemyError(Exception):
    """データベース関連のエラー"""
    pass

class ResendVerificationRequest(BaseModel):
    """再送信確認メールのリクエストスキーマ"""
    email: str


# APIレスポンスの型定義
UserCreateResponse = Dict[str, str]
UserDeleteResponse = Dict[str, str]
UserUpdateResponse = Dict[str, str]


router = APIRouter(
    prefix="/api/v1",
    tags=["user"],
)


# 環境変数の読み込む
ALLOWED_EMAIL_DOMAINS_RAW = os.getenv("ALLOWED_EMAIL_DOMAINS", "")
ALLOWED_EMAIL_DOMAINS = [domain.strip() for domain in ALLOWED_EMAIL_DOMAINS_RAW.split(",") if domain.strip()]
ENABLE_DOMAIN_RESTRICTION = os.getenv("ENABLE_DOMAIN_RESTRICTION", "true").lower() == "true"
ENABLE_EMAIL_VERIFICATION = os.getenv("ENABLE_EMAIL_VERIFICATION", "true").lower() == "true"


@router.post(
    "/user",
    status_code=status.HTTP_201_CREATED,
    response_model=UserSchema,
    summary="User Create",
    description="ユーザーを作成するエンドポイント。"
)
async def create_user(
    user: UserSchema,
    db: Session = Depends(get_db)
) -> UserCreateResponse:
    """ユーザーを作成するエンドポイント

    ユーザーは登録後にパスワード変更エンドポイントでパスワードを設定する必要があります。
    """
    try:
        # 入力データの検証
        if user.email is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="メールアドレスが必要です。"
            )
        print(f"ユーザー作成開始 - メール: {user.email}")

        # ドメイン制限チェック
        if ENABLE_DOMAIN_RESTRICTION and not is_valid_email_domain(user.email):
            print(f"ドメイン検証失敗 - メール: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"このメールアドレスのドメインは許可されていません。"
            )
        # メールアドレスの重複チェック
        existing_user = db.query(UserModel).filter(
            UserModel.email == user.email
        ).first()

        if existing_user:
            print(
                f"既存のメールアドレスが検出されました: {user.email}"
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="このメールアドレスは既に使用されています。"
            )
        # メール認証が有効な場合の従来の処理
        if ENABLE_EMAIL_VERIFICATION:
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
                    print(
                        f"既存の確認レコードを更新しました: {user.email}"
                        )
            else:
                verification = EmailVerification.create_verification(user.email)
                db.add(verification)
                print(
                    f"新しい確認レコードを作成しました: {user.email}"
                    )
            db.commit()
            await send_verification_email(
                user.email, verification.token
                )
            return {
                "message": "ユーザー登録を受け付けました。確認メールをお送りしましたので、 \
                メール内のリンクをクリックして登録を完了してください。",
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
            print(
                f"ユーザーを直接作成しました: {user.email}"
                )
            return {
                "message": "ユーザー登録が完了しました。 \
                仮パスワード 'temp_password_123' でログインして、パスワードを変更してください。",
                "email": user.email,
                "id": str(new_user.id),
                "is_active": str(new_user.is_active)
            }
    except DatabaseError as e:
        db.rollback()
        error_detail = traceback.format_exc()
        print(
            f"データベースエラーが発生しました: {error_detail}"
            )
        raise DatabaseError(
            message="データベースで予期しないエラーが発生しました。"
        )
    except Exception as e:
        db.rollback()
        error_detail = traceback.format_exc()
        print(
            f"予期しないエラーが発生しました: {error_detail}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー作成中に予期しないエラーが発生しました"
        )
    finally:
        print(
            "DBセッションをクローズします"
            )
        db.close()


@router.get(
    "/verify-email",
    summary="Email Verification",
    description="ユーザーのメールアドレスを確認するエンドポイント",
)
async def verify_email(
    token: str = Query(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    print(f"メール認証リクエスト受信 - 元のトークン: {token}")
    # URLデコード処理（安全性を確保）
    decoded_token = unquote(token)
    print(
        f"メール認証リクエスト受信 - デコード後トークン: {decoded_token}"
        )
    if not decoded_token or len(decoded_token) < 10:
        print(f"無効なトークン形式: {decoded_token}")
        raise HTTPException(
            status_code=400,
            detail="無効なトークン形式です。"
        )
    verification = db.query(EmailVerification).filter(
        EmailVerification.token == decoded_token
    ).first()
    # データベース内の全トークンを確認
    if not verification:
        all_verifications = db.query(EmailVerification).all()
        print(
            f"データベース内のトークン数: {len(all_verifications)}"
            )
        for v in all_verifications:
            print(
                f"DB内トークン: {v.token[:20]}..., Email: {v.email}, 確認済み: {v.is_verified}"
                )
        print(
            f"トークンが見つかりません: {decoded_token[:20]}..."
            )
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
    # 初期パスワード（固定値を使用）
    user_password = Hash.bcrypt("temp_password_123")

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
        print(
            f"User {current_user.id} \
            tried to access user {user_id}'s information"
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="他のユーザーの情報にはアクセスできません"
        )

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        print(
            f"User with id {user_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    print(
        f"認証されたユーザー {current_user.id} \
        がユーザー情報を取得しました: {user_id}"
        )
    # SQLAlchemyモデルをPydanticスキーマに変換
    return UserSchema(
        email=user.email,
        password=None,
        is_active=user.is_active
    )


@router.post(
"/resend-verification",
summary="Resend Verification Email",
description="登録確認メールを送信するエンドポイント（認証必須）"
)
async def resend_verification_email(
    email: str = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    request: ResendVerificationRequest = None
) -> Dict[str, str]:
    """登録確認メールを送信する（認証が必要）"""
    if email is not None and request is None:
        target_email = email
    elif request is not None:
        target_email = request.email
        # 認証されたユーザーが自分のメールアドレスでのみリクエスト可能にする
        if hasattr(current_user, 'email') and current_user.email != request.email:
            print(
                f"権限なし: 認証ユーザー({current_user.email}) \
                が他のユーザー({request.email})の確認メール再送信を試行"
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="自分のメールアドレスのみ確認メール再送信が可能です"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="メールアドレスまたはリクエストボディが必要です"
        )
    verification = db.query(EmailVerification).filter(
        EmailVerification.email == target_email,
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
    await send_verification_email(target_email, verification.token)
    return {"message": "確認メールを再送信しました。"}


@router.delete(
    "/user/delete-account",
    status_code=status.HTTP_200_OK,
    summary="Delete User Account",
    description="ユーザーアカウントに関連するデータを削除するエンドポイント"
)
async def delete_user_account(
    deletion_request: AccountDeletionRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, str]:
    """ユーザーアカウントを削除するエンドポイント（認証必須）

    このエンドポイントは認証されたユーザーのみアクセス可能で、
    ユーザーは自分のアカウントのみ削除できます。

    :param deletion_request: 退会リクエストデータ
    :type deletion_request: アカウント削除リクエスト
    :deletion_request.validate_passwords_match
    :パスワードの一致を検証するメソッド
    :type deletion_request.validate_passwords_match: method
    :param db: データベースセッション
    :type db: Session
    :param current_user: 現在の認証されたユーザー
    :type current_user: UserModel
    :return: 退会完了メッセージ
    :rtype: dict
    :raises HTTPException: ユーザーが見つからない場合
    """
    try:
        print(
            f"退会処理開始 - メール: \
            {deletion_request.email}, \
            認証ユーザー: {current_user.email}"
            )
        deletion_request.validate_passwords_match()
        # 認証されたユーザーが削除対象のユーザーと同じかチェック
        if current_user.email != deletion_request.email:
            print(
                f"権限なし: 認証ユーザー({current_user.email}) \
                が他のユーザー({deletion_request.email})のアカウント削除を試行"
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="自分のアカウントのみ削除できます"
            )
        # ユーザーの存在確認
        user = db.query(UserModel).filter(
            UserModel.email == deletion_request.email
        ).first()
        if not user:
            print(
                f"退会対象ユーザーが見つかりません: {deletion_request.email}"
                )
            raise UserNotFoundError(
                user_id=None,
                email=deletion_request.email
            )
        # パスワード検証
        if user.password is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ユーザーのパスワードが設定されていません"
            )
        if not Hash.verify(deletion_request.password, user.password):
            print(
                f"パスワード検証失敗: {deletion_request.email}"
                )
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
        print(
            f"ユーザー検証完了: {user_email}, ID: {user.id}"
            )
        # ユーザーの記事を削除
        try:
            from models import Article
            print(
                f"記事削除処理開始: ユーザーID {user.id}"
                )
            articles = db.query(Article) \
            .filter(Article.user_id == user.id).all()
            article_count = len(articles)

            for article in articles:
                db.delete(article)
            print(
                f"ユーザーの記事を削除しました: {article_count}件"
                )
        except Exception as article_error:
            print(
                f"記事削除処理でエラー: {str(article_error)}"
                )
            raise
        # メール認証テーブルからも削除
        try:
            print(
                f"メール認証レコード削除処理開始: {user_email}"
                )
            verification_records = db.query(EmailVerification).filter(
                EmailVerification.email == user_email
            ).all()

            for verification in verification_records:
                db.delete(verification)
            print(
                f"メール認証レコードを削除しました: \
                {len(verification_records)}件"
                )
        except Exception as verification_error:
            print(
                f"メール認証レコード削除処理でエラー: {str(verification_error)}"
                )
            raise
        # ユーザー削除とコミット
        try:
            print(
                f"ユーザー削除処理開始: {user_email}"
                )
            db.delete(user)
            db.commit()
            print(
                f"ユーザーアカウント削除完了: {user_email}"
                )
        except Exception as commit_error:
            print(
                f"データベースコミット処理でエラー: {str(commit_error)}"
                )
            raise
        # 退会完了メールを送信（メール送信失敗はログのみ）
        try:
            await send_account_deletion_email(user_email, username)
            print(
                f"退会完了メールを送信しました: {user_email}"
                )
            return {
                "message": "退会処理が完了しました。",
                "deleted_articles_count": str(article_count),
                "email": user_email
            }
        except Exception as email_error:
            print(
                f"退会完了メールの送信に失敗しました: {str(email_error)}"
                )
            # データベースの削除は成功しているので、メール送信失敗でも処理は完了とする
            return {
                "message": "退会処理が完了しました。メール送信に失敗しましたが、アカウントは正常に削除されました。",
                "deleted_articles_count": str(article_count),
                "email": user_email
            }
    except UserNotFoundError as e:
        db.rollback()
        print(f"ユーザーが見つかりません: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたメールアドレスのユーザーが見つかりません"
        )
    except ValueError as e:
        db.rollback()
        print(f"バリデーションエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    # パスワードが設定されていないケースと不一致のケースを明示的に処理
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        error_detail = traceback.format_exc()
        print(f"退会処理で予期しないエラーが発生しました: {error_detail}, {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="退会処理中に予期しないエラーが発生しました"
        )
    finally:
        print(
            "DBセッションをクローズします"
            )
        db.close()