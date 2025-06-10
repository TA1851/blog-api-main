from database import db_env
import os


def is_valid_email_domain(email: str) -> bool:
    """特定のメールアドレスが許可されているかチェック

    :param email: チェックするメールアドレス
    :type email: str
    :return: 許可されている場合はTrue
    :rtype: bool
    """
    # ドメイン制限が無効の場合は常にTrue
    domain_restriction_enabled = os.getenv(
        "ENABLE_DOMAIN_RESTRICTION", "false"
        ).lower() == "true"
    if not domain_restriction_enabled:
        print(
            f"ドメイン制限は無効です。すべてのドメインを許可: {email}"
            )
        return True
    # 許可されたメールアドレスのリストを取得
    allowed_emails = os.getenv(
        "ALLOWED_EMAIL_DOMAINS", ""
        ).split(",")
    allowed_emails = [email_addr.strip() for email_addr in allowed_emails if email_addr.strip()]
    if not allowed_emails:
        print(
            "許可されたメールアドレスが設定されていません。すべてのメールアドレスを許可"
            )
        return True
    
    # メールアドレスが許可リストに含まれているかチェック
    email_lower = email.lower()
    is_allowed = email_lower in [e.lower() for e in allowed_emails]
    
    if is_allowed:
        print(
            f"許可されたメールアドレスです: {email}"
            )
    else:
        print(
            f"許可されていないメールアドレスです: {email}, 許可リスト: {allowed_emails}"
            )
    
    return is_allowed