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
    
    # サーバーのポート番号を環境変数から取得（デフォルト: 8000）
    SERVER_PORT = os.getenv("SERVER_PORT", "8000")
    
    if not ENABLE_EMAIL_SENDING:
        verification_url = f"http://localhost:{SERVER_PORT}/api/v1/verify-email?token={encoded_token}"
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
            verification_url = f"http://localhost:{SERVER_PORT}/api/v1/verify-email?token={encoded_token}"
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
        
        verification_url = f"http://localhost:{SERVER_PORT}/api/v1/verify-email?token={encoded_token}"
        
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
        verification_url = f"http://localhost:{SERVER_PORT}/api/v1/verify-email?token={encoded_token}"
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

async def send_registration_complete_email(email: str, username: str):
    """登録完了メールを送信する"""
    create_logger(f"登録完了メール送信開始 - 宛先: {email}, ユーザー名: {username}")
    
    ENABLE_EMAIL_SENDING = os.getenv("ENABLE_EMAIL_SENDING", "false").lower() == "true"
    
    if not ENABLE_EMAIL_SENDING:
        create_logger(f"[開発モード] 登録完了メール情報をコンソールに出力: {email}")
        print("🎉 登録完了メール送信（開発モード）")
        print("=" * 60)
        print(f"宛先: {email}")
        print(f"件名: 【Blog API】登録完了のお知らせ")
        print("メール内容:")
        print(f"こんにちは、{username}さん！")
        print("")
        print("Blog APIへのご登録が完了しました。🎉")
        print("")
        print("これからBlog APIの全ての機能をお使いいただけます：")
        print("• ブログ記事の作成・編集・削除")
        print("• コメントの投稿・管理")
        print("• プロフィールの管理")
        print("• その他の便利な機能")
        print("")
        print("ご利用いただき、ありがとうございます。")
        print("何かご不明な点がございましたら、お気軽にお問い合わせください。")
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
            create_error_logger("メール設定が不完全です。開発モードでコンソール出力します。")
            print("🎉 登録完了メール送信（開発モード - 設定不完全）")
            print("=" * 60)
            print(f"宛先: {email}")
            print(f"件名: 【Blog API】登録完了のお知らせ")
            print("メール内容:")
            print(f"こんにちは、{username}さん！")
            print("")
            print("Blog APIへのご登録が完了しました。🎉")
            print("")
            print("これからBlog APIの全ての機能をお使いいただけます：")
            print("• ブログ記事の作成・編集・削除")
            print("• コメントの投稿・管理")
            print("• プロフィールの管理")
            print("• その他の便利な機能")
            print("")
            print("ご利用いただき、ありがとうございます。")
            print("何かご不明な点がございましたら、お気軽にお問い合わせください。")
            print("")
            print("Blog API チーム")
            print("=" * 60)
            return

        conf = get_mail_config()
        if not conf:
            raise Exception("メール設定が正しく設定されていません")
        
        # プレーンテキストメール
        plain_body = (
            f"こんにちは、{username}さん！\r\n\r\n"
            "Blog APIへのご登録が完了しました。🎉\r\n\r\n"
            "これからBlog APIの全ての機能をお使いいただけます：\r\n"
            "• ブログ記事の作成・編集・削除\r\n"
            "• コメントの投稿・管理\r\n"
            "• プロフィールの管理\r\n"
            "• その他の便利な機能\r\n\r\n"
            "ご利用いただき、ありがとうございます。\r\n"
            "何かご不明な点がございましたら、お気軽にお問い合わせください。\r\n\r\n"
            "Blog API チーム"
        )

        # HTMLメール
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>登録完了のお知らせ</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #27ae60; margin: 0;">🎉 登録完了！</h1>
        </div>
        
        <h2 style="color: #2c3e50;">こんにちは、{username}さん！</h2>
        
        <p style="font-size: 16px; color: #27ae60; font-weight: bold;">
            Blog APIへのご登録が完了しました。🎉
        </p>
        
        <p>これからBlog APIの全ての機能をお使いいただけます：</p>
        
        <ul style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <li style="margin: 8px 0;">📝 ブログ記事の作成・編集・削除</li>
            <li style="margin: 8px 0;">💬 コメントの投稿・管理</li>
            <li style="margin: 8px 0;">👤 プロフィールの管理</li>
            <li style="margin: 8px 0;">⚡ その他の便利な機能</li>
        </ul>
        
        <div style="background-color: #e8f5e8; padding: 20px; border-radius: 8px; border-left: 4px solid #27ae60; margin: 30px 0;">
            <p style="margin: 0; color: #2d5a2d;">
                <strong>ご利用いただき、ありがとうございます。</strong><br>
                何かご不明な点がございましたら、お気軽にお問い合わせください。
            </p>
        </div>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        
        <p style="color: #666; font-size: 12px; text-align: center;">
            今後ともよろしくお願いいたします。<br><br>
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
                subject="【Blog API】登録完了のお知らせ",
                recipients=[email],
                body=plain_body,
                subtype="plain",
                charset="utf-8"
            )
        else:
            # HTMLメールとプレーンテキストの両方を送信
            message = MessageSchema(
                subject="【Blog API】登録完了のお知らせ",
                recipients=[email],
                body=plain_body,
                html=html_body,
                subtype="html",
                charset="utf-8"
            )
        
        fm = FastMail(conf)
        await fm.send_message(message)
        create_logger(f"登録完了メールを送信しました: {email}")
        
    except Exception as e:
        create_error_logger(f"登録完了メール送信エラー: {str(e)}")
        # エラーが発生した場合は開発モードでコンソール出力
        print("🎉 登録完了メール送信（エラー発生 - 開発モード）")
        print("=" * 60)
        print(f"宛先: {email}")
        print(f"件名: 【Blog API】登録完了のお知らせ")
        print("メール内容:")
        print(f"こんにちは、{username}さん！")
        print("")
        print("Blog APIへのご登録が完了しました。🎉")
        print("")
        print("これからBlog APIの全ての機能をお使いいただけます：")
        print("• ブログ記事の作成・編集・削除")
        print("• コメントの投稿・管理")
        print("• プロフィールの管理")
        print("• その他の便利な機能")
        print("")
        print("ご利用いただき、ありがとうございます。")
        print("何かご不明な点がございましたら、お気軽にお問い合わせください。")
        print("")
        print("Blog API チーム")
        print("=" * 60)
