import pytest
from passlib.context import CryptContext
from hashing import Hash

def test_hash_bcrypt():
    # テスト用のパスワード
    test_password = "test_password123"
    
    # ハッシュを生成
    hashed_password = Hash.bcrypt(test_password)
    
    # ハッシュが生成されたことを確認
    assert hashed_password is not None
    assert isinstance(hashed_password, str)
    
    # 元のパスワードとハッシュが異なることを確認
    assert hashed_password != test_password
    
    # ハッシュが bcrypt 形式かどうかを確認
    assert hashed_password.startswith("$2")
    
    # 同じパスワードで再度ハッシュを生成し、異なることを確認（ソルトのため）
    second_hash = Hash.bcrypt(test_password)
    assert hashed_password != second_hash
    
    # パスワードが検証できることを確認
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    assert password_context.verify(test_password, hashed_password)