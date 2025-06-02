# XMLファイル アーカイブ

このディレクトリは、Blog API プロジェクトの古いテスト結果やXMLファイルのアーカイブです。

## 📁 ディレクトリ構造

### ルートアーカイブファイル
プロジェクトルートから移動された古いXMLファイル群

#### メインテスト結果（廃止済み）
- `test_results_all.xml` - 古い全体テスト結果
- `test_results_database.xml` - データベーステスト結果
- `test_results_existing.xml` - 既存テスト結果
- `test_results_latest.xml` - 以前の最新テスト結果
- `test_results.xml` - 初期テスト結果

#### ルーターテスト結果（廃止済み）
- `test_results_routers_corrected.xml` - 修正版ルーターテスト結果
- `test_results_routers_final.xml` - 最終版ルーターテスト結果
- `test_results_auth_router.xml` - 認証ルーターテスト結果
- `test_results_auth_router_final.xml` - 認証ルーター最終テスト結果
- `test_results_user_router.xml` - ユーザールーターテスト結果

#### 統合テスト結果（廃止済み）
- `test_results_continuous.xml` - 継続的テスト結果
- `test_results_with_article_router.xml` - 記事ルーター統合テスト結果
- `test_results_all_with_user_router.xml` - ユーザールーター統合テスト結果
- `all_tests_results.xml` - 全テスト結果

### `component_tests/`
個別コンポーネントのテスト結果
- `email_validator_test_results.xml` - メールバリデーターテスト結果
- `email_sender_test_results.xml` - メール送信機能テスト結果
- `custom_token_test_results.xml` - カスタムトークンテスト結果
- `all_tests_with_email_sender.xml` - メール送信機能統合テスト結果

## 📋 アーカイブポリシー

### アーカイブされる条件
- 新しいバージョンに置き換えられたファイル
- 重複する内容のファイル
- 開発途中の中間結果ファイル
- 特定のコンポーネントのみのテスト結果

### 保持期間
- アーカイブファイルは3ヶ月間保持
- 重要なマイルストーンのファイルは永続保持
- 定期的な見直しとクリーンアップを実施

## 🔍 ファイル検索

特定のテスト結果を探す場合：
```bash
# ファイル名で検索
find . -name "*auth_router*" -type f

# 日付で検索
find . -newermt "2025-06-01" -type f

# 内容で検索
grep -r "specific_test_name" .
```

---
アーカイブ作成日: 2025年6月2日  
最終更新: 2025年6月2日
