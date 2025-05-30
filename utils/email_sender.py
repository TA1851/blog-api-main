from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from database import db_env
from logger.custom_logger import create_logger, create_error_logger
import os

def get_mail_config():
    """メール設定を取得する"""
    return ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
        MAIL_FROM=os.getenv("MAIL_FROM", ""),
        MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True").lower() == "true",
        MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )

async def send_verification_email(email: str, token: str):
    """確認メールを送信する"""
    ENABLE_EMAIL_SENDING = os.getenv("ENABLE_EMAIL_SENDING", "false").lower() == "true"
    
    if not ENABLE_EMAIL_SENDING:
        create_logger(f"[開発モード] 確認メール情報をコンソールに出力: {email}")
        print("📧 メール送信（開発モード）")
        print("=" * 60)
        print(f"宛先: {email}")
        print(f"件名: 【ブログサービス本人確認】メールアドレスの確認")
        print(f"確認URL: http://localhost:8000/api/v1/verify-email?token={token}")
        print("=" * 60)
        return

    try:
        # メール設定の検証
        mail_username = os.getenv("MAIL_USERNAME")
        mail_password = os.getenv("MAIL_PASSWORD")
        mail_from = os.getenv("MAIL_FROM")
        
        if not all([mail_username, mail_password, mail_from]):
            create_error_logger("メール設定が不完全です。開発モードでコンソール出力します。")
            print("📧 メール送信（開発モード - 設定不完全）")
            print("=" * 60)
            print(f"宛先: {email}")
            print(f"件名: 【ブログサービス本人確認】メールアドレスの確認")
            print(f"確認URL: http://localhost:8000/api/v1/verify-email?token={token}")
            print("=" * 60)
            return

        conf = get_mail_config()
        if not conf:
            raise Exception("メール設定が正しく設定されていません")
        
        message = MessageSchema(
            subject="【Blog API】メールアドレスの確認",
            recipients=[email],
            body=f"""
こんにちは！

メールアドレスの確認をお願いします。
以下のリンクをクリックしてください：

http://localhost:8000/api/v1/verify-email?token={token}

このリンクは24時間有効です。

Blog API チーム
            """,
            subtype="plain"
        )
        
        fm = FastMail(conf)
        await fm.send_message(message)
        create_logger(f"確認メールを送信しました: {email}")
        
    except Exception as e:
        create_error_logger(f"メール送信エラー: {str(e)}")
        # エラーが発生した場合は開発モードでコンソール出力
        print("📧 メール送信（エラー発生 - 開発モード）")
        print("=" * 60)
        print(f"宛先: {email}")
        print(f"件名: 【ブログサービス本人確認】メールアドレスの確認")
        print(f"確認URL: http://localhost:8000/api/v1/verify-email?token={token}")
        print("=" * 60)
