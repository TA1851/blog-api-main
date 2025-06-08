from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
import os
from urllib.parse import quote


CORS_ORIGINS = os.getenv("CORS_ORIGINS")
LOCAL_CORS_ORIGINS = os.getenv("LOCAL_CORS_ORIGINS")
SERVER_PORT = os.getenv("SERVER_PORT", "8080")


def get_mail_config() -> ConnectionConfig:
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


# def _is_email_enabled() -> bool:
#     """メール送信が有効かどうかを判定"""
#     return os.getenv("ENABLE_EMAIL_SENDING", "false").lower() == "true"


# def _validate_mail_config() -> bool:
#     """メール設定の妥当性をチェック"""
#     mail_username = os.getenv("MAIL_USERNAME")
#     mail_password = os.getenv("MAIL_PASSWORD")
#     mail_from = os.getenv("MAIL_FROM")
#     return all([mail_username, mail_password, mail_from])


async def send_verification_email(email: str, token: str) -> None:
    """確認メールを送信する"""
    print(f"メール送信開始 - 宛先: {email}, トークン: {token}")
    encoded_token = quote(token, safe='')
    if LOCAL_CORS_ORIGINS:
        verification_url = f"{CORS_ORIGINS}/api/v1/verify-email?token={encoded_token}"
    content = (
        "こんにちは！\n\n"
        "メールアドレスの確認をお願いします。\n\n"
        "下記のリンク先よりパスワードを変更して、登録を完了してください：\n\n"
        "初期パスワード：temp_password_123\n\n"
        "以下のリンクをクリックしてください：\n"
        f"{verification_url}\n\n"
        "このリンクの有効時間は24時間です。\n\n"
        "Blog API チーム"
    )
    try:
        conf = get_mail_config()
        if not conf:
            raise Exception("メール設定が正しく設定されていません")
        plain_body = content.replace('\n', '\r\n')
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
        <p>下記のリンク先よりパスワードを変更して、登録を完了してください：</p>
        <div style="background-color: #fff3cd; padding: 15px; border-radius: 4px; margin: 20px 0; border-left: 4px solid #ffc107;">
            <p style="margin: 0; font-weight: bold; color: #856404;">
                初期パスワード：temp_password_123
            </p>
        </div>
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
        PREFER_PLAIN_TEXT = os.getenv("PREFER_PLAIN_TEXT_EMAIL", "false").lower() == "true"
        message = MessageSchema(
            subject="【Blog API】メールアドレスの確認",
            recipients=[email],
            body=plain_body if PREFER_PLAIN_TEXT else html_body,
            subtype=MessageType.plain if PREFER_PLAIN_TEXT else MessageType.html,
            charset="utf-8"
        )
        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"確認メールを送信しました: {email}")
    except Exception as e:
        print(f"メール送信エラー: {str(e)}")


async def send_registration_complete_email(email: str, username: str) -> None:
    """登録完了メールを送信する"""
    print(f"登録完了メール送信開始 - 宛先: {email}, ユーザー名: {username}")
    content = (
        f"こんにちは、{username}さん！\n\n"
        "Blog APIへのご登録が完了しました。🎉\n\n"
        "これからBlog APIの全ての機能をお使いいただけます：\n"
        "• ブログ記事の作成・編集・削除\n"
        "• コメントの投稿・管理\n"
        "• プロフィールの管理\n"
        "• その他の便利な機能\n\n"
        "ご利用いただき、ありがとうございます。\n"
        "何かご不明な点がございましたら、お気軽にお問い合わせください。\n\n"
        "Blog API チーム"
    )
    try:
        conf = get_mail_config()
        if not conf:
            raise Exception("メール設定が正しく設定されていません")
        plain_body = content.replace('\n', '\r\n')
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
        PREFER_PLAIN_TEXT = os.getenv("PREFER_PLAIN_TEXT_EMAIL", "false").lower() == "true"
        message = MessageSchema(
            subject="【Blog API】登録完了のお知らせ",
            recipients=[email],
            body=plain_body if PREFER_PLAIN_TEXT else html_body,
            subtype=MessageType.plain if PREFER_PLAIN_TEXT else MessageType.html,
            charset="utf-8"
        )
        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"登録完了メールを送信しました: {email}")
    except Exception as e:
        print(f"登録完了メール送信エラー: {str(e)}")


async def send_account_deletion_email(email: str, username: str) -> None:
    """退会完了メールを送信する"""
    print(f"退会完了メール送信開始 - 宛先: {email}, ユーザー名: {username}")
    content = (
        f"こんにちは、{username}さん\n\n"
        "Blog APIからの退会手続きが完了いたしました。\n\n"
        "これまでBlog APIをご利用いただき、誠にありがとうございました。\n"
        "お客様の投稿された記事やデータは、ご要望に従って削除させていただきました。\n\n"
        "退会に関する詳細：\n"
        "• ユーザーアカウントの削除\n"
        "• 投稿された記事の削除\n"
        "• 個人情報の削除\n\n"
        "また何かの機会がございましたら、いつでもお気軽にご利用ください。\n"
        "新規登録はいつでも可能です。\n\n"
        "今後ともよろしくお願いいたします。\n\n"
        "Blog API チーム"
    )
    try:
        conf = get_mail_config()
        if not conf:
            raise Exception("メール設定が正しく設定されていません")
        plain_body = content.replace('\n', '\r\n')
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>退会完了のお知らせ</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #e74c3c; margin: 0;">👋 退会完了</h1>
        </div>
        <h2 style="color: #2c3e50;">こんにちは、{username}さん</h2>
        <p style="font-size: 16px; color: #e74c3c; font-weight: bold;">
            Blog APIからの退会手続きが完了いたしました。
        </p>
        <p>これまでBlog APIをご利用いただき、誠にありがとうございました。</p>
        <p>お客様の投稿された記事やデータは、ご要望に従って削除させていただきました。</p>
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #2c3e50; margin-top: 0;">退会に関する詳細：</h3>
            <ul style="margin: 0;">
                <li style="margin: 8px 0;">✅ ユーザーアカウントの削除</li>
                <li style="margin: 8px 0;">✅ 投稿された記事の削除</li>
                <li style="margin: 8px 0;">✅ 個人情報の削除</li>
            </ul>
        </div>
        <div style="background-color: #e8f5e8; padding: 20px; border-radius: 8px; border-left: 4px solid #27ae60; margin: 30px 0;">
            <p style="margin: 0; color: #2d5a2d;">
                <strong>また何かの機会がございましたら、いつでもお気軽にご利用ください。</strong><br>
                新規登録はいつでも可能です。
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
        PREFER_PLAIN_TEXT = os.getenv("PREFER_PLAIN_TEXT_EMAIL", "false").lower() == "true"
        message = MessageSchema(
            subject="【Blog API】退会完了のお知らせ",
            recipients=[email],
            body=plain_body if PREFER_PLAIN_TEXT else html_body,
            subtype=MessageType.plain if PREFER_PLAIN_TEXT else MessageType.html,
            charset="utf-8"
        )
        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"退会完了メールを送信しました: {email}")
    except Exception as e:
        print(f"退会完了メール送信エラー: {str(e)}")