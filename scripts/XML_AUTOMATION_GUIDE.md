# XMLファイル整理の自動化設定

## GitHub Actions用ワークフロー
```yaml
name: XML File Organization
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  organize-xml:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Organize XML files
        run: |
          python scripts/organize_xml_files.py
          
      - name: Commit organized files
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add test_results/ test_archives/
          git diff --staged --quiet || git commit -m "自動整理: XMLファイルを適切なディレクトリに移動"
          git push
```

## Pre-commit Hook設定
プロジェクトルートに`.pre-commit-config.yaml`を作成:

```yaml
repos:
  - repo: local
    hooks:
      - id: organize-xml
        name: XML File Organization
        entry: python scripts/organize_xml_files.py
        language: python
        files: '\.xml$'
        pass_filenames: false
```

## 手動実行方法

### 基本的な整理
```bash
python scripts/organize_xml_files.py
```

### 古いファイルの自動削除付き
```bash
python scripts/organize_xml_files.py --cleanup-days 30
```

### 特定のディレクトリを対象
```bash
python scripts/organize_xml_files.py /path/to/project
```

## テスト実行時の自動整理

`pytest.ini`または`pyproject.toml`に以下を追加:

```ini
[tool:pytest]
addopts = --junit-xml=test_results/current/latest_test_results.xml
testpaths = tests
```

この設定により、テスト実行後に結果が自動的に適切なディレクトリに保存されます。

## メンテナンス規則

1. **日次**: 新しいXMLファイルの自動整理
2. **週次**: アーカイブディレクトリのサイズチェック
3. **月次**: 30日以上古いアーカイブファイルの削除
4. **四半期**: ディレクトリ構造の見直し

## 緊急時の復旧

もし誤ってファイルを削除した場合:

```bash
# Gitの履歴から復旧
git log --oneline test_results/ test_archives/
git checkout <commit-hash> -- test_results/ test_archives/

# またはGitから特定のファイルを復旧
git checkout HEAD~1 -- test_results/coverage/coverage.xml
```
