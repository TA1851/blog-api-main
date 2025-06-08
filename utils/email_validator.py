from database import db_env
import os


def is_valid_email_domain(email: str) -> bool:
    """メールアドレスのドメインが許可されているかチェック

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
    # 許可されたドメインのリストを取得
    allowed_domains = os.getenv(
        "ALLOWED_EMAIL_DOMAINS", ""
        ).split(",")
    allowed_domains = [domain.strip() for domain in allowed_domains if domain.strip()]
    if not allowed_domains:
        print(
            "許可されたドメインが設定されていません。すべてのドメインを許可"
            )
        return True
    # メールアドレスからドメイン部分を抽出
    try:
        domain = email.split("@")[1].lower()
        is_allowed = domain in [d.lower() for d in allowed_domains]
        if is_allowed:
            print(
                f"許可されたドメインです: {domain}"
                )
        else:
            print(
                f"許可されていないドメインです: {domain}, 許可リスト: {allowed_domains}"
                )
        return is_allowed
    except IndexError:
        print(
            f"不正なメールアドレス形式: {email}"
            )
        return False