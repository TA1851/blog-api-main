# Archives Directory

このディレクトリには、ルートディレクトリから移動された古いテスト結果とカバレッジファイルが格納されています。

## ディレクトリ構造

### coverage_json/
- 過去のカバレッジレポート（JSON形式）
- タイムスタンプ付きのファイル名で保存
- 最新のファイル（coverage_20250605_213356.json）はルートディレクトリに残されています

### test_results_xml/
- 過去のテスト結果（XML形式）
- タイムスタンプ付きのファイル名で保存
- 最新のファイル（test_results_20250605_213356.xml）はルートディレクトリに残されています

## ルートディレクトリに残されているファイル

### JSONファイル
- `bug_history.json` - バグ履歴
- `coverage_20250605_213356.json` - 最新のカバレッジレポート
- `coverage_exceptions.json` - 例外のカバレッジレポート
- `coverage_exclude_tests.json` - テスト除外のカバレッジレポート
- `coverage_history.json` - カバレッジ履歴

### XMLファイル
- `coverage.xml` - 現在のカバレッジレポート
- `test_results_20250605_213356.xml` - 最新のテスト結果
- `test_results_continuous.xml` - 継続的テストの結果
- `test_results_exceptions.xml` - 例外テストの結果
- `test_results_latest.xml` - 最新のテスト結果

## 注意事項
- 必要に応じて古いファイルを参照できるよう、アーカイブファイルは保持されています
- ディスクスペースが必要な場合は、古いファイルを削除することも可能です
