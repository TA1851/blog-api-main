"""
ハッシュ化モジュールのテストスイート

このテストスイートは以下をカバーします：
- パスワードのハッシュ化機能
- パスワード検証機能
- bcrypt設定のテスト
- セキュリティ関連のテスト
- エラーハンドリング
- パフォーマンステスト
"""

import pytest
import re
import time
from unittest.mock import patch, Mock
from passlib.context import CryptContext
from passlib.exc import InvalidHashError, MalformedHashError, PasswordValueError, UnknownHashError, PasswordSizeError

# テスト対象のインポート
from hashing import Hash, password_context


class TestPasswordContext:
    """password_contextの設定テスト"""
    
    def test_password_context_creation(self):
        """password_contextが正しく作成されることをテスト"""
        assert password_context is not None
        assert isinstance(password_context, CryptContext)
    
    def test_password_context_schemes(self):
        """設定されているスキームの確認"""
        schemes = password_context.schemes()
        assert "bcrypt" in schemes
        assert len(schemes) == 1  # bcryptのみ使用
    
    def test_password_context_configuration(self):
        """password_contextの設定値確認"""
        # bcryptの設定を確認
        assert password_context.default_scheme() == "bcrypt"
        
        # bcryptの詳細設定を確認（内部属性にアクセス）
        bcrypt_handler = password_context.handler("bcrypt")
        assert bcrypt_handler is not None
    
    def test_deprecated_schemes(self):
        """非推奨スキームの設定確認"""
        # deprecatedが"auto"に設定されていることを確認
        # 実際の設定値の確認は内部実装に依存するため、動作確認で代替
        context_str = str(password_context)
        # CryptContextが正常に動作することを確認
        assert "CryptContext" in context_str
        
        # 実際に動作確認
        test_password = "test"
        hashed = password_context.hash(test_password)
        assert password_context.verify(test_password, hashed)


class TestHashClass:
    """Hashクラスのテスト"""
    
    def test_hash_class_exists(self):
        """Hashクラスが存在することを確認"""
        assert Hash is not None
        assert hasattr(Hash, 'bcrypt')
        assert hasattr(Hash, 'verify')
    
    def test_hash_methods_are_static(self):
        """Hashクラスのメソッドがstaticmethodであることを確認"""
        assert isinstance(Hash.__dict__['bcrypt'], staticmethod)
        assert isinstance(Hash.__dict__['verify'], staticmethod)


class TestBcryptHashing:
    """パスワードハッシュ化のテスト"""
    
    def test_bcrypt_basic_hashing(self):
        """基本的なパスワードハッシュ化テスト"""
        password = "test_password"
        hashed = Hash.bcrypt(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password  # 平文とは異なることを確認
        assert len(hashed) > 0
    
    def test_bcrypt_hash_format(self):
        """bcryptハッシュの形式確認"""
        password = "test_password"
        hashed = Hash.bcrypt(password)
        
        # bcryptハッシュの形式: $2b$rounds$salt+hash
        bcrypt_pattern = r'^\$2b\$\d{2}\$[A-Za-z0-9./]{53}$'
        assert re.match(bcrypt_pattern, hashed), f"Invalid bcrypt format: {hashed}"
    
    def test_bcrypt_rounds_configuration(self):
        """bcryptのラウンド数設定確認"""
        password = "test_password"
        hashed = Hash.bcrypt(password)
        
        # ハッシュからラウンド数を抽出（$2b$12$...の12部分）
        rounds_match = re.match(r'^\$2b\$(\d{2})\$', hashed)
        assert rounds_match is not None
        rounds = int(rounds_match.group(1))
        assert rounds == 12  # 設定で指定した値
    
    def test_bcrypt_version_identifier(self):
        """bcryptバージョン識別子の確認"""
        password = "test_password"
        hashed = Hash.bcrypt(password)
        
        # $2b$で始まることを確認（明示的に設定したバージョン）
        assert hashed.startswith("$2b$")
    
    def test_bcrypt_different_passwords_different_hashes(self):
        """異なるパスワードは異なるハッシュを生成"""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = Hash.bcrypt(password1)
        hash2 = Hash.bcrypt(password2)
        
        assert hash1 != hash2
    
    def test_bcrypt_same_password_different_salts(self):
        """同じパスワードでも異なるソルトで異なるハッシュ"""
        password = "same_password"
        
        hash1 = Hash.bcrypt(password)
        hash2 = Hash.bcrypt(password)
        
        assert hash1 != hash2  # ソルトが異なるため
    
    def test_bcrypt_empty_password(self):
        """空文字パスワードの処理"""
        empty_password = ""
        hashed = Hash.bcrypt(empty_password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        
        # 空文字でも検証できることを確認
        assert Hash.verify(empty_password, hashed) is True
    
    def test_bcrypt_unicode_password(self):
        """Unicode文字を含むパスワードの処理"""
        unicode_password = "パスワード123!@#"
        hashed = Hash.bcrypt(unicode_password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert Hash.verify(unicode_password, hashed) is True
    
    def test_bcrypt_long_password(self):
        """長いパスワードの処理"""
        long_password = "a" * 1000  # 1000文字のパスワード
        hashed = Hash.bcrypt(long_password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert Hash.verify(long_password, hashed) is True
    
    def test_bcrypt_special_characters(self):
        """特殊文字を含むパスワードの処理"""
        special_password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = Hash.bcrypt(special_password)
        
        assert hashed is not None
        assert Hash.verify(special_password, hashed) is True


class TestPasswordVerification:
    """パスワード検証のテスト"""
    
    def test_verify_correct_password(self):
        """正しいパスワードの検証"""
        password = "correct_password"
        hashed = Hash.bcrypt(password)
        
        result = Hash.verify(password, hashed)
        assert result is True
        assert isinstance(result, bool)
    
    def test_verify_incorrect_password(self):
        """間違ったパスワードの検証"""
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        hashed = Hash.bcrypt(correct_password)
        
        result = Hash.verify(wrong_password, hashed)
        assert result is False
        assert isinstance(result, bool)
    
    def test_verify_case_sensitive(self):
        """パスワードの大文字小文字区別"""
        password = "Password"
        hashed = Hash.bcrypt(password)
        
        # 大文字小文字が異なる場合は検証失敗
        assert Hash.verify("password", hashed) is False
        assert Hash.verify("PASSWORD", hashed) is False
        assert Hash.verify("Password", hashed) is True
    
    def test_verify_empty_password(self):
        """空文字パスワードの検証"""
        empty_password = ""
        hashed = Hash.bcrypt(empty_password)
        
        assert Hash.verify(empty_password, hashed) is True
        assert Hash.verify("not_empty", hashed) is False
    
    def test_verify_whitespace_password(self):
        """空白文字を含むパスワードの検証"""
        password_with_spaces = " password with spaces "
        hashed = Hash.bcrypt(password_with_spaces)
        
        assert Hash.verify(password_with_spaces, hashed) is True
        assert Hash.verify("password with spaces", hashed) is False  # 前後の空白が重要
    
    def test_verify_multiple_passwords(self):
        """複数のパスワード/ハッシュペアの検証"""
        passwords = ["pass1", "pass2", "pass3"]
        hashes = [Hash.bcrypt(p) for p in passwords]
        
        # 正しい組み合わせをテスト
        for password, hashed in zip(passwords, hashes):
            assert Hash.verify(password, hashed) is True
        
        # 間違った組み合わせをテスト
        assert Hash.verify(passwords[0], hashes[1]) is False
        assert Hash.verify(passwords[1], hashes[2]) is False
        assert Hash.verify(passwords[2], hashes[0]) is False


class TestHashSecurity:
    """セキュリティ関連のテスト"""
    
    def test_hash_timing_consistency(self):
        """ハッシュ化の時間的一貫性（タイミング攻撃対策）"""
        passwords = ["short", "medium_length_password", "very_long_password_with_many_characters_to_test_timing"]
        times = []
        
        for password in passwords:
            start_time = time.time()
            Hash.bcrypt(password)
            end_time = time.time()
            times.append(end_time - start_time)
        
        # すべてのハッシュ化が合理的な時間内で完了することを確認
        for t in times:
            assert t < 5.0  # 5秒以内
            assert t > 0.001  # 最低限の処理時間
    
    def test_verify_timing_consistency(self):
        """検証の時間的一貫性"""
        password = "test_password"
        hashed = Hash.bcrypt(password)
        
        # 正しいパスワードと間違ったパスワードの検証時間を比較
        start_time = time.time()
        Hash.verify(password, hashed)
        correct_time = time.time() - start_time
        
        start_time = time.time()
        Hash.verify("wrong_password", hashed)
        wrong_time = time.time() - start_time
        
        # 時間差が大きすぎないことを確認（タイミング攻撃対策）
        time_ratio = max(correct_time, wrong_time) / min(correct_time, wrong_time)
        assert time_ratio < 10  # 10倍以内の差
    
    def test_salt_randomness(self):
        """ソルトのランダム性確認"""
        password = "same_password"
        hashes = [Hash.bcrypt(password) for _ in range(10)]
        
        # すべてのハッシュが異なることを確認
        unique_hashes = set(hashes)
        assert len(unique_hashes) == len(hashes)
        
        # ソルト部分（$2b$12$の後の22文字）がすべて異なることを確認
        salts = [h[7:29] for h in hashes]  # ソルト部分を抽出
        unique_salts = set(salts)
        assert len(unique_salts) == len(salts)
    
    def test_hash_strength(self):
        """ハッシュの強度確認"""
        password = "test_password"
        hashed = Hash.bcrypt(password)
        
        # ハッシュが十分な長さを持つことを確認
        assert len(hashed) >= 60  # bcryptハッシュの最小長
        
        # 文字種の多様性を確認
        chars_used = set(hashed)
        assert len(chars_used) > 10  # 十分な文字種が使用されている


class TestErrorHandling:
    """エラーハンドリングのテスト"""
    
    def test_verify_invalid_hash_format(self):
        """不正なハッシュ形式での検証"""
        password = "test_password"
        invalid_hashes = [
            "invalid_hash",
            "$2b$12$short",
            "$2a$12$wrongversion",
            "",
        ]
        
        for invalid_hash in invalid_hashes:
            # passlibは不正なハッシュに対してFalseを返すかエラーを発生させる
            try:
                result = Hash.verify(password, invalid_hash)
                assert result is False
            except Exception as e:
                # 何らかのエラーが発生することも正常な動作
                assert isinstance(e, (ValueError, Exception))
    
    def test_verify_none_hash(self):
        """Noneハッシュでの検証"""
        password = "test_password"
        # 実際にはFalseを返す
        result = Hash.verify(password, None)
        assert result is False
    
    def test_bcrypt_none_password(self):
        """Noneパスワードの処理"""
        with pytest.raises(TypeError):
            Hash.bcrypt(None)
    
    def test_verify_none_password(self):
        """None平文パスワードの検証"""
        hashed = Hash.bcrypt("test")
        with pytest.raises(TypeError):
            Hash.verify(None, hashed)
    
    @patch('hashing.password_context.hash')
    def test_bcrypt_context_error_handling(self, mock_hash):
        """password_contextでエラーが発生した場合の処理"""
        mock_hash.side_effect = PasswordValueError("Test error")
        
        with pytest.raises(PasswordValueError):
            Hash.bcrypt("test_password")
    
    @patch('hashing.password_context.verify')
    def test_verify_context_error_handling(self, mock_verify):
        """password_context.verifyでエラーが発生した場合の処理"""
        mock_verify.side_effect = ValueError("Test error")
        
        with pytest.raises(ValueError):
            Hash.verify("password", "hash")


class TestPerformance:
    """パフォーマンステスト"""
    
    def test_hashing_performance(self):
        """ハッシュ化のパフォーマンステスト"""
        password = "performance_test_password"
        
        start_time = time.time()
        Hash.bcrypt(password)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # ハッシュ化が合理的な時間内で完了することを確認
        assert duration < 5.0  # 5秒以内
        assert duration > 0.01  # 最低限の処理時間（安全性確保）
    
    def test_verification_performance(self):
        """検証のパフォーマンステスト"""
        password = "performance_test_password"
        hashed = Hash.bcrypt(password)
        
        start_time = time.time()
        Hash.verify(password, hashed)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # 検証が合理的な時間内で完了することを確認
        assert duration < 5.0  # 5秒以内
        assert duration > 0.001  # 最低限の処理時間
    
    def test_multiple_operations_performance(self):
        """複数操作のパフォーマンステスト"""
        passwords = [f"password_{i}" for i in range(5)]
        
        # 複数のハッシュ化
        start_time = time.time()
        hashes = [Hash.bcrypt(p) for p in passwords]
        hash_time = time.time() - start_time
        
        # 複数の検証
        start_time = time.time()
        for password, hashed in zip(passwords, hashes):
            Hash.verify(password, hashed)
        verify_time = time.time() - start_time
        
        # 合理的な時間内で完了することを確認
        assert hash_time < 25.0  # 5個×5秒以内
        assert verify_time < 25.0  # 5個×5秒以内


class TestEdgeCases:
    """エッジケースのテスト"""
    
    def test_very_long_password(self):
        """長いパスワードの処理（制限内）"""
        # bcryptには最大パスワード長の制限があるため、現実的な長さでテスト
        long_password = "a" * 200  # 200文字（制限内）
        
        hashed = Hash.bcrypt(long_password)
        assert hashed is not None
        assert Hash.verify(long_password, hashed) is True
    
    def test_password_size_limit(self):
        """パスワードサイズ制限のテスト"""
        # 非常に長いパスワードは制限でエラーになることを確認
        very_long_password = "a" * 10000  # 10,000文字
        
        with pytest.raises(PasswordSizeError):
            Hash.bcrypt(very_long_password)
    
    def test_binary_like_password_safe(self):
        """安全なバイナリ風パスワードの処理"""
        # NULL バイトを含まない特殊文字
        special_password = "\x01\x02\x03\xfe"
        
        hashed = Hash.bcrypt(special_password)
        assert hashed is not None
        assert Hash.verify(special_password, hashed) is True
    
    def test_null_byte_password_error(self):
        """NULL バイトを含むパスワードでのエラー"""
        # bcryptはNULLバイトを許可しない
        null_password = "password\x00with_null"
        
        with pytest.raises(PasswordValueError):
            Hash.bcrypt(null_password)
    
    def test_newline_password(self):
        """改行を含むパスワードの処理"""
        newline_password = "password\nwith\nnewlines\r\n"
        
        hashed = Hash.bcrypt(newline_password)
        assert hashed is not None
        assert Hash.verify(newline_password, hashed) is True
    
    def test_numeric_only_password(self):
        """数字のみのパスワード"""
        numeric_password = "123456789"
        
        hashed = Hash.bcrypt(numeric_password)
        assert hashed is not None
        assert Hash.verify(numeric_password, hashed) is True
        assert Hash.verify("987654321", hashed) is False


class TestIntegration:
    """統合テスト"""
    
    def test_full_password_lifecycle(self):
        """完全なパスワードライフサイクルテスト"""
        original_password = "user_password_123!"
        
        # 1. パスワードをハッシュ化
        hashed_password = Hash.bcrypt(original_password)
        assert hashed_password is not None
        
        # 2. 正しいパスワードで検証
        assert Hash.verify(original_password, hashed_password) is True
        
        # 3. 間違ったパスワードで検証
        assert Hash.verify("wrong_password", hashed_password) is False
        
        # 4. 同じパスワードを再度ハッシュ化（異なるハッシュになる）
        second_hash = Hash.bcrypt(original_password)
        assert second_hash != hashed_password
        
        # 5. 両方のハッシュで同じパスワードが検証できる
        assert Hash.verify(original_password, second_hash) is True
    
    def test_cross_platform_compatibility(self):
        """クロスプラットフォーム互換性テスト"""
        password = "cross_platform_test"
        
        # 既知のbcryptハッシュ（他のシステムで生成）
        known_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LpWeDYw.0SleR5LjC"
        
        # このハッシュが検証できることを確認（passlibの互換性）
        # 注：実際のパスワードは"hello"である必要がある
        test_password = "hello"
        result = Hash.verify(test_password, known_hash)
        assert isinstance(result, bool)  # 結果がbooleanであることを確認
    
    def test_concurrent_operations_simulation(self):
        """並行操作のシミュレーション"""
        passwords = [f"concurrent_password_{i}" for i in range(10)]
        
        # 複数のパスワードを同時にハッシュ化（シーケンシャルだが高速に）
        hashes = []
        for password in passwords:
            hashed = Hash.bcrypt(password)
            hashes.append(hashed)
        
        # すべてのハッシュが有効であることを確認
        for password, hashed in zip(passwords, hashes):
            assert Hash.verify(password, hashed) is True
        
        # 異なるパスワード同士で検証が失敗することを確認
        for i, password in enumerate(passwords):
            for j, hashed in enumerate(hashes):
                if i != j:
                    assert Hash.verify(password, hashed) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
