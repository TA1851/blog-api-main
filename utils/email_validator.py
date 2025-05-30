from database import db_env
from logger.custom_logger import create_logger

def is_valid_email_domain(email: str) -> bool:
    """メールアドレスのドメインが許可されているかチェック
    
    :param email: チェックするメールアドレス
    :type email: str
    :return: 許可されている場合はTrue
    :rtype: bool
    """
    # ドメイン制限が無効の場合は常にTrue
    domain_restriction_enabled = db_env.get("ENABLE_DOMAIN_RESTRICTION", "false").lower() == "true"
    
    if not domain_restriction_enabled:
        create_logger(f"ドメイン制限は無効です。すべてのドメインを許可: {email}")
        return True
    
    # 許可されたドメインのリストを取得
    allowed_domains = db_env.get("ALLOWED_EMAIL_DOMAINS", "").split(",")
    allowed_domains = [domain.strip() for domain in allowed_domains if domain.strip()]
    
    if not allowed_domains:
        create_logger("許可されたドメインが設定されていません。すべてのドメインを許可")
        return True
    
    # メールアドレスからドメイン部分を抽出
    try:
        domain = email.split("@")[1].lower()
        is_allowed = domain in [d.lower() for d in allowed_domains]
        
        if is_allowed:
            create_logger(f"許可されたドメインです: {domain}")
        else:
            create_logger(f"許可されていないドメインです: {domain}, 許可リスト: {allowed_domains}")
        
        return is_allowed
        
    except IndexError:
        create_logger(f"不正なメールアドレス形式: {email}")
        return False