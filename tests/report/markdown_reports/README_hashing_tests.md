# ハッシュ化モジュールテストドキュメント

## 概要
`hashing.py`モジュールの包括的なテストスイートです。bcryptを使用したパスワードハッシュ化と検証機能、セキュリティ、パフォーマンス、エラーハンドリングをカバーしています。

## テスト結果
- **テスト総数**: 44個
- **成功率**: 100% (44/44)
- **コードカバレッジ**: 100%
- **実行時間**: 約43秒

## テストクラス構成

### 1. TestPasswordContext (4個のテスト)
password_contextの設定と動作テスト
- `test_password_context_creation`: CryptContext作成テスト
- `test_password_context_schemes`: スキーム設定確認
- `test_password_context_configuration`: 設定値確認
- `test_deprecated_schemes`: 非推奨スキーム設定確認

### 2. TestHashClass (2個のテスト)
Hashクラスの構造テスト
- `test_hash_class_exists`: クラス存在確認
- `test_hash_methods_are_static`: staticmethod確認

### 3. TestBcryptHashing (10個のテスト)
bcryptハッシュ化機能の詳細テスト
- `test_bcrypt_basic_hashing`: 基本的なハッシュ化
- `test_bcrypt_hash_format`: ハッシュ形式確認 ($2b$12$...)
- `test_bcrypt_rounds_configuration`: ラウンド数設定(12)確認
- `test_bcrypt_version_identifier`: バージョン識別子($2b$)確認
- `test_bcrypt_different_passwords_different_hashes`: 異なるパスワード→異なるハッシュ
- `test_bcrypt_same_password_different_salts`: 同じパスワード→異なるソルト
- `test_bcrypt_empty_password`: 空文字パスワード処理
- `test_bcrypt_unicode_password`: Unicode文字処理
- `test_bcrypt_long_password`: 長いパスワード処理
- `test_bcrypt_special_characters`: 特殊文字処理

### 4. TestPasswordVerification (6個のテスト)
パスワード検証機能テスト
- `test_verify_correct_password`: 正しいパスワード検証
- `test_verify_incorrect_password`: 間違ったパスワード検証
- `test_verify_case_sensitive`: 大文字小文字区別
- `test_verify_empty_password`: 空文字パスワード検証
- `test_verify_whitespace_password`: 空白文字を含むパスワード
- `test_verify_multiple_passwords`: 複数パスワードの検証

### 5. TestHashSecurity (4個のテスト)
セキュリティ関連テスト
- `test_hash_timing_consistency`: タイミング攻撃対策
- `test_verify_timing_consistency`: 検証時間の一貫性
- `test_salt_randomness`: ソルトのランダム性
- `test_hash_strength`: ハッシュ強度確認

### 6. TestErrorHandling (6個のテスト)
エラーハンドリングテスト
- `test_verify_invalid_hash_format`: 不正ハッシュ形式
- `test_verify_none_hash`: Noneハッシュ処理
- `test_bcrypt_none_password`: Noneパスワード処理
- `test_verify_none_password`: None平文パスワード処理
- `test_bcrypt_context_error_handling`: コンテキストエラー処理
- `test_verify_context_error_handling`: 検証エラー処理

### 7. TestPerformance (3個のテスト)
パフォーマンステスト
- `test_hashing_performance`: ハッシュ化性能(5秒以内)
- `test_verification_performance`: 検証性能(5秒以内)
- `test_multiple_operations_performance`: 複数操作性能

### 8. TestEdgeCases (6個のテスト)
エッジケーステスト
- `test_very_long_password`: 長いパスワード(200文字)
- `test_password_size_limit`: パスワードサイズ制限テスト
- `test_binary_like_password_safe`: 安全なバイナリ風パスワード
- `test_null_byte_password_error`: NULLバイト含有エラー
- `test_newline_password`: 改行を含むパスワード
- `test_numeric_only_password`: 数字のみパスワード

### 9. TestIntegration (3個のテスト)
統合テスト
- `test_full_password_lifecycle`: 完全なパスワードライフサイクル
- `test_cross_platform_compatibility`: クロスプラットフォーム互換性
- `test_concurrent_operations_simulation`: 並行操作シミュレーション

## bcrypt設定詳細

### ハッシュ設定
```python
password_context = CryptContext(
    schemes=["bcrypt"],           # bcryptのみ使用
    deprecated="auto",           # 自動非推奨化
    bcrypt__default_rounds=12,   # ラウンド数: 12
    bcrypt__ident="2b"          # バージョン: 2b
)
```

### ハッシュ形式
- パターン: `$2b$12$[22文字のソルト][31文字のハッシュ]`
- 総長: 60文字
- 例: `$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LpWeDYw.0SleR5LjC`

## テスト実行方法

### 基本実行
```bash
python -m pytest tests/test_hashing.py -v
```

### カバレッジ付き実行
```bash
python -m pytest tests/test_hashing.py --cov=hashing --cov-report=term-missing -v
```

### 特定のテストクラス実行
```bash
python -m pytest tests/test_hashing.py::TestBcryptHashing -v
```

### パフォーマンステストのみ
```bash
python -m pytest tests/test_hashing.py::TestPerformance -v
```

## セキュリティテスト観点

### パスワードハッシュセキュリティ
- **ソルト**: 各ハッシュで異なるランダムソルト生成
- **ラウンド数**: 12ラウンド（計算コスト調整）
- **アルゴリズム**: bcrypt 2b（最新版）
- **タイミング攻撃**: 一定時間内での処理完了確認

### 入力値検証
- 空文字、Unicode、特殊文字の適切な処理
- パスワード長制限の確認
- NULLバイト等の不正入力拒否

### エラーハンドリング
- 不正ハッシュ形式の適切な処理
- None値入力の安全な処理
- 例外の適切なキャッチと処理

## パフォーマンス基準

### 処理時間制限
- **ハッシュ化**: 5秒以内/回
- **検証**: 5秒以内/回
- **複数操作**: 25秒以内/5回

### セキュリティ vs パフォーマンス
- ラウンド数12: セキュリティと速度のバランス
- 最低処理時間: タイミング攻撃対策
- 計算コスト: 適切なCPU負荷

## 制限事項とエラー処理

### パスワード制限
- **最大長**: passlibの制限に従う（通常4096文字）
- **文字制限**: NULLバイト(\x00)は使用不可
- **エンコーディング**: UTF-8対応

### ハッシュ制限
- **形式**: bcrypt形式のみサポート
- **互換性**: $2b$バージョンを使用
- **長さ**: 固定60文字

## テスト環境要件

### 必要なパッケージ
```
pytest>=8.0.0
pytest-cov>=4.0.0
passlib[bcrypt]>=1.7.0
bcrypt>=4.0.0
```

### Pythonバージョン
- Python 3.8以降推奨
- bcryptの完全サポート

## 実際の使用例

### 基本的な使用方法
```python
from hashing import Hash

# パスワードをハッシュ化
password = "user_password_123"
hashed = Hash.bcrypt(password)

# パスワード検証
is_valid = Hash.verify(password, hashed)  # True
is_invalid = Hash.verify("wrong", hashed)  # False
```

### セキュリティベストプラクティス
1. **ソルト**: 自動生成（手動管理不要）
2. **ラウンド数**: 12（推奨値）
3. **バージョン**: 2b（最新）
4. **検証**: 必ずverifyメソッド使用

## 今後の拡張可能性

### セキュリティ強化
- Argon2サポート追加
- scryptサポート追加
- ペッパー（固定ソルト）の実装

### パフォーマンス改善
- 非同期ハッシュ化対応
- 並列処理対応
- キャッシュ機能

### 監視・ログ
- ハッシュ化回数統計
- 失敗ログ記録
- パフォーマンス監視

## トラブルシューティング

### よくある問題
1. **bcryptインストールエラー**: `pip install bcrypt`で解決
2. **パフォーマンス低下**: ラウンド数調整検討
3. **文字化け**: UTF-8エンコーディング確認

### デバッグ方法
1. ハッシュ形式確認: 正規表現テスト
2. パフォーマンス測定: time.time()使用
3. エラーログ確認: 例外キャッチで詳細確認
