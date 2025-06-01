"""ユーザ認証機能を実装するためのルーターモジュール"""
# import pprint
import traceback
import os
from fastapi import APIRouter, status, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import ValidationError
from datetime import datetime, timedelta
from uuid import uuid4
from urllib.parse import unquote

from schemas import User as UserSchema
from models import User as UserModel
from mailmodels import EmailVerification
from database import db_env, session, get_db
from hashing import Hash
from models import User as UserModel
from logger.custom_logger import create_logger, create_error_logger
from utils.email_sender import send_verification_email, send_registration_complete_email
from utils.email_validator import is_valid_email_domain


router = APIRouter(
    prefix="/api/v1",  # APIのバージョンを指定
    tags=["user"],  # SwaggerUIのタグを指定
)


# データベースURLを取得（本番環境のPostgreSQLを優先、次に開発環境のSQLite）
db_url = db_env.get("posgre_url")
# db_url = db_env.get("sqlite_url")
# key03 = db_env.get("file_id_03")
# key08 = db_env.get("file_id_08")


def check_environment_variable():
    """環境変数を取得する

    :param key08: user.pyの環境変数
    :type key08: str
    :return: 環境変数の値
    :rtype: str
    """
    # if not key08:
    #     create_error_logger(f"環境変数:{key08}が設定されていません。{key08}")
    #     raise ValueError(f"環境変数が設定されていません。-> {key08}")
    # else:
    #     # print(f"STEP11：環境変数：{key08}を取得しました。 -> {key08}")
    #     create_logger(f"環境変数{key08}を取得しました。:")
    # return key08

check_environment_variable()


def check_db_url():
    """データベースURLを取得する

    :param key03: user.pyの環境変数
    :type key03: str
    :param db_url: user.pyの環境変数
    :type db_url: str
    :return: 環境変数の値
    :rtype: str
    """
    # if not db_url:
    #     create_error_logger(f"環境変数:database_urlが設定されていません。 -> {key03}")
    #     raise ValueError(f"環境変数が設定されていません。{key03}")
    # else:
    #     # print(f"STEP12：環境変数: {db_url}を読み込みました。")
    #     create_logger(f"環境変数: {db_url}を読み込みました。 -> {key03}")
    # return db_url

check_db_url()
# print(f"STEP13：ユーザを作成します。Swaggerで確認してください。")
# print("---------------------------------------------------------------")

get_db()

class IntegrityError(Exception):
    """主にユニーク制約違反（メールアドレスが既に使用されている場合など）を示すエラー"""
    pass

class SQLAlchemyError(Exception):
    """データベース関連のエラー"""
    pass

# 環境変数の読み込みを修正（直接os.environから読み込む）
ALLOWED_EMAIL_DOMAINS_RAW = os.getenv("ALLOWED_EMAIL_DOMAINS", "")
ALLOWED_EMAIL_DOMAINS = [domain.strip() for domain in ALLOWED_EMAIL_DOMAINS_RAW.split(",") if domain.strip()]
ENABLE_DOMAIN_RESTRICTION = os.getenv("ENABLE_DOMAIN_RESTRICTION", "true").lower() == "true"
ENABLE_EMAIL_VERIFICATION = os.getenv("ENABLE_EMAIL_VERIFICATION", "true").lower() == "true"

# デバッグ情報をログに出力
create_logger(f"[修正後] 環境変数ALLOWED_EMAIL_DOMAINS_RAW: '{ALLOWED_EMAIL_DOMAINS_RAW}'")
create_logger(f"[修正後] 解析後のALLOWED_EMAIL_DOMAINS: {ALLOWED_EMAIL_DOMAINS}")
create_logger(f"[修正後] ENABLE_DOMAIN_RESTRICTION: {ENABLE_DOMAIN_RESTRICTION}")

def is_valid_email_domain(email: str) -> bool:
    """メールアドレスのドメインが許可されたものかチェックする

    :param email: チェックするメールアドレス
    :type email: str
    :return: ドメインが許可されている場合True
    :rtype: bool
    """
    if not ENABLE_DOMAIN_RESTRICTION:
        create_logger(f"ドメイン制限が無効化されています。メール: {email}")
        return True
    
    if not ALLOWED_EMAIL_DOMAINS:
        create_error_logger("許可されたドメインが設定されていません。すべてのドメインを許可します。")
        return True
    
    domain = email.split('@')[-1].lower()
    is_valid = domain in ALLOWED_EMAIL_DOMAINS
    
    create_logger(f"メールドメイン検証 - メール: {email}, ドメイン: {domain}, 許可ドメイン: {ALLOWED_EMAIL_DOMAINS}, 結果: {is_valid}")
    
    return is_valid

class UserRouter:
    @router.post(
    "/user",
    status_code=status.HTTP_201_CREATED,
    response_model=UserSchema,
    summary="User Create",
    description="ユーザーを作成するエンドポイント（シンプル登録）",
    )
    async def create_user(
        user: UserSchema,
        db: Session = Depends(get_db)
    ) -> dict:
        """ユーザーを作成するエンドポイント（シンプル登録）"""
        try:
            create_logger(f"ユーザー作成開始 - メール: {user.email}")
            
            # ドメイン制限チェック（有効な場合のみ）
            if ENABLE_DOMAIN_RESTRICTION and not is_valid_email_domain(user.email):
                create_error_logger(f"ドメイン検証失敗 - メール: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"このメールアドレスのドメインは許可されていません。許可されたドメイン: {', '.join(ALLOWED_EMAIL_DOMAINS)}"
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
                        # 既存のレコードを更新（パスワードも保存）
                        existing_verification.token = str(uuid4())
                        existing_verification.created_at = datetime.utcnow()
                        existing_verification.expires_at = datetime.utcnow() + timedelta(hours=24)
                        existing_verification.password_hash = Hash.bcrypt(user.password)
                        verification = existing_verification
                        create_logger(f"既存の確認レコードを更新しました: {user.email}")
                else:
                    verification = EmailVerification.create_verification(user.email)
                    verification.password_hash = Hash.bcrypt(user.password)
                    db.add(verification)
                    create_logger(f"新しい確認レコードを作成しました: {user.email}")

                db.commit()
                await send_verification_email(user.email, verification.token)

                return {
                    "message": "ユーザー登録を受け付けました。確認メールをお送りしましたので、メール内のリンクをクリックして登録を完了してください。",
                    "email": user.email
                }
            else:
                # シンプル登録：直接ユーザーを作成
                new_user = UserModel(
                    email=user.email,
                    password=Hash.bcrypt(user.password),
                    is_active=True  # 直接アクティブ化
                )
                
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                
                create_logger(f"ユーザーを直接作成しました: {user.email}")
                
                return {
                    "message": "ユーザー登録が完了しました。ログインできます。",
                    "email": user.email,
                    "id": new_user.id,
                    "is_active": new_user.is_active
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
        token: str = Query(...),
        db: Session = Depends(get_db)
    ):
        # デバッグログを追加
        create_logger(f"メール認証リクエスト受信 - 元のトークン: {token}")
        
        # URLデコード処理（安全性を確保）
        decoded_token = unquote(token)
        create_logger(f"メール認証リクエスト受信 - デコード後トークン: {decoded_token}")
        
        verification = db.query(EmailVerification).filter(
            EmailVerification.token == decoded_token
        ).first()

        if not verification:
            # デバッグ：データベース内の全トークンを確認
            all_verifications = db.query(EmailVerification).all()
            create_logger(f"データベース内のトークン数: {len(all_verifications)}")
            for v in all_verifications:
                create_logger(f"DB内トークン: {v.token}, Email: {v.email}, 確認済み: {v.is_verified}")
            
            raise HTTPException(
                status_code=400,
                detail="無効なトークンです。"
            )

        if verification.is_verified:
            raise HTTPException(
                status_code=400,
                detail="このメールアドレスは既に確認済みです。"
            )

        if datetime.utcnow() > verification.expires_at:
            raise HTTPException(
                status_code=400,
                detail="トークンの有効期限が切れています。"
            )

        # 保存されたパスワードを使用してユーザーを作成
        user_password = verification.password_hash if hasattr(verification, 'password_hash') and verification.password_hash else Hash.bcrypt("temp_password_123")
        
        # ユーザーの作成
        new_user = UserModel(
            email=verification.email,
            password=user_password,
            is_active=True
        )

        verification.is_verified = True
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 登録完了メールを送信
        await send_registration_complete_email(verification.email, verification.email.split('@')[0])

        return {
            "message": "メールアドレスの確認が完了しました。登録が完了し、ログインできます。",
            "email": verification.email,
            "user_id": new_user.id,
            "is_active": new_user.is_active
        }


# カスタム例外クラスを定義するモジュール
class UserNotFoundError(Exception):
    """ユーザーが見つからない場合の例外"""
    def __init__(self, user_id: int = None, email: str = None):
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
    summary="Get User",
    description="ユーザー情報を取得するエンドポイント"
)

async def show_user(user_id: int, db: Session = Depends(get_db)):
    """ユーザー情報を取得する関数

    :param user_id: ユーザーID
    :type user_id: int
    :param db: データベースセッション
    :type db: Session
    :return: ユーザー情報
    :rtype: UserSchema
    :raises HTTPException: ユーザーが見つからない場合
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise UserNotFoundError(user_id=user_id)
    else:
        create_logger(f"ユーザー情報を取得しました: {user_id}"
        )
    if not user:
        raise EmailVerificationError(
            message=f"User with id {user_id} not found"
        )
    else:
        create_error_logger(f"User with id {user_id} not found"
        )
    return user


@router.post(
"/resend-verification",
summary="Resend Verification Email",
description="確認メールを再送信するエンドポイント"
)
async def resend_verification_email(
    email: str,
    db: Session = Depends(get_db)
):
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