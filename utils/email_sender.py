from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from database import db_env
from logger.custom_logger import create_logger, create_error_logger
import os
from urllib.parse import quote

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
    # トークンをログに記録
    create_logger(f"メール送信開始 - 宛先: {email}, トークン: {token}")
    
    # トークンを安全にURLエンコード
    encoded_token = quote(token, safe='')
    
    ENABLE_EMAIL_SENDING = os.getenv("ENABLE_EMAIL_SENDING", "false").lower() == "true"
    
    if not ENABLE_EMAIL_SENDING:
        verification_url = f"http://localhost:8000/api/v1/verify-email?token={encoded_token}"
        create_logger(f"[開発モード] 確認メール情報をコンソールに出力: {email}")
        print("📧 メール送信（開発モード）")
        print("=" * 60)
        print(f"宛先: {email}")
        print(f"件名: 【ブログサービス本人確認】メールアドレスの確認")
        print(f"確認URL: {verification_url}")
        print("メール内容:")
        print("こんにちは！")
        print("")
        print("メールアドレスの確認をお願いします。")
        print("")
        print("以下のリンクをクリックしてください：")
        print(f"{verification_url}")
        print("")
        print("このリンクの有効時間は1時間です。")
        print("")
        print("Blog API チーム")
        print("=" * 60)
        return

    try:
        # メール設定の検証
        mail_username = os.getenv("MAIL_USERNAME")
        mail_password = os.getenv("MAIL_PASSWORD")
        mail_from = os.getenv("MAIL_FROM")
        
        if not all([mail_username, mail_password, mail_from]):
            verification_url = f"http://localhost:8000/api/v1/verify-email?token={encoded_token}"
            create_error_logger("メール設定が不完全です。開発モードでコンソール出力します。")
            print("📧 メール送信（開発モード - 設定不完全）")
            print("=" * 60)
            print(f"宛先: {email}")
            print(f"件名: 【ブログサービス本人確認】メールアドレスの確認")
            print(f"確認URL: {verification_url}")
            print("メール内容:")
            print("こんにちは！")
            print("")
            print("メールアドレスの確認をお願いします。")
            print("")
            print("以下のリンクをクリックしてください：")
            print(f"{verification_url}")
            print("")
            print("このリンクの有効時間は1時間です。")
            print("")
            print("Blog API チーム")
            print("=" * 60)
            return

        conf = get_mail_config()
        if not conf:
            raise Exception("メール設定が正しく設定されていません")
        
        verification_url = f"http://localhost:8000/api/v1/verify-email?token={encoded_token}"
        
        # プレーンテキストメール（mixedパターン - \r\n\r\n を使用）
        plain_body = (
            "こんにちは！\r\n\r\n"
            "メールアドレスの確認をお願いします。\r\n\r\n"
            "以下のリンクをクリックしてください：\r\n"
            f"{verification_url}\r\n\r\n"
            "このリンクの有効時間は1時間です。\r\n\r\n"
            "Blog API チーム"
        )

        # HTMLメール（URLが確実にクリック可能）
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>メールアドレスの確認</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">メールアドレスの確認</h2>
        
        <p>こんにちは！</p>
        <p>メールアドレスの確認をお願いします。😊</p>
        
        <p>以下のボタンをクリックし、登録を完了してください：</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_url}"
               style="background-color: #3498db; color: white; padding: 12px 24px;
                      text-decoration: none; border-radius: 4px; display: inline-block;
                      font-weight: bold;">メールアドレスを確認する</a>
        </div>
        
        <p>または、以下のURLをコピーして<br>
        ブラウザのアドレスバーに貼り付けてください：</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin: 20px 0;">
            <p style="word-break: break-all; font-family: monospace; margin: 0; font-size: 12px;">
                {verification_url}
            </p>
        </div>
        
        <p>ご不明な点がございましたら、<br>
        お気軽にお問い合わせください。</p>
        
        <p style="margin-top: 30px;">
            <small style="background-color: #fff3cd; padding: 5px 10px; border-radius: 3px; color: #856404;">
                ⏰ このリンクの有効時間は1時間です。
            </small>
        </p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        
        <p style="color: #666; font-size: 12px; text-align: center;">
            よろしくお願いいたします。<br><br>
            <strong>Blog API チーム</strong>
        </p>
    </div>
</body>
</html>"""
        
        # プレーンテキストメールを優先する場合のオプション
        PREFER_PLAIN_TEXT = os.getenv("PREFER_PLAIN_TEXT_EMAIL", "false").lower() == "true"
        
        if PREFER_PLAIN_TEXT:
            # プレーンテキストメールのみを送信
            message = MessageSchema(
                subject="【Blog API】メールアドレスの確認",
                recipients=[email],
                body=plain_body,
                subtype="plain",
                charset="utf-8"
            )
        else:
            # HTMLメールとプレーンテキストの両方を送信
            message = MessageSchema(
                subject="【Blog API】メールアドレスの確認",
                recipients=[email],
                body=plain_body,
                html=html_body,
                subtype="html",
                charset="utf-8"
            )
        
        fm = FastMail(conf)
        await fm.send_message(message)
        create_logger(f"確認メールを送信しました: {email}")
        
    except Exception as e:
        verification_url = f"http://localhost:8000/api/v1/verify-email?token={encoded_token}"
        create_error_logger(f"メール送信エラー: {str(e)}")
        # エラーが発生した場合は開発モードでコンソール出力
        print("📧 メール送信（エラー発生 - 開発モード）")
        print("=" * 60)
        print(f"宛先: {email}")
        print(f"件名: 【ブログサービス本人確認】メールアドレスの確認")
        print(f"確認URL: {verification_url}")
        print("メール内容:")
        print("こんにちは！")
        print("")
        print("メールアドレスの確認をお願いします。")
        print("")
        print("以下のリンクをクリックしてください：")
        print(f"{verification_url}")
        print("")
        print("このリンクの有効時間は1時間です。")
        print("")
        print("Blog API チーム")
        print("=" * 60)
