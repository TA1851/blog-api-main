## プロジェクト概要（開発環境）

- デプロイ先： render
- 言語： python3.11
- フレームワーク： fastapi0.115.12
- データベース： sqlite3


## Render

- ファイルはルート直下に格納しないとエラーになる
- デプロイ時に、requirements.txt読み込む


## 開発
- デバッグ作業は、venvで仮想環境を構築して作業する
- Remote Development で立ち上げたコンテナに接続しても拡張機能を使ったデバッグはできないもよう


## 開発中に使うコマンド

サーバ起動
```bash
uvicorn  main:app --reload
```
ポートの指定
```bash
uvicorn main:app --reload --port 8080
```

バージョン管理
```bash
pip freeze > requirements.txt
```

## requirements.txt でインストールする

# 仮想環境の作成

コマンドパレットからpython3.11を選択してインストールする

```bash
cd .venv
source bin/activate
```

バージョンの確認
```bash
python3 --version
```

```bash
pip install -r requirements.txt
```

## テストコマンド

単体テスト（詳細を表示する）
```python
pytest [FILE_NAME] -v
```

警告を無視して実行
```python
pytest test_hashing.py -v --disable-warnings
```

カバレッジ集計
```python
coverage run -m pytest [FILE_NAME]
```

カバレッジレポート
```python
coverage report -m | coverage html
```


### コメントはdocstringで記述する
プロジェクトのドキュメントを作成する

---

[参考記事](https://techplay.jp/column/1842)

- help関数に渡すとドキュメントを閲覧できる。
- doc内に型を宣言すると補完、型チェックが適用される。
- ResStructuredTextで記述する。（TypeHint採用するため）

### 作成手順

１）sphinx install
```bash
pip install -U sphinx
```

２）設定ファイルの作成と雛形の作成
```bash
# プロジェクト直下で実行する
sphinx-apidoc -F -a -o ./doc .
```

３）ディレクトリに移動する
```bash
cd doc
make html
```

４）ファイルを開く
```bash
open _build/html/index.html
```

５）監視モード

インストール
```bash
pip install sphinx-autobuild
```

```bash
sphinx-autobuild \
  --port 8080 \
  --open-browser \
  --watch ../database.py \
  . _build/html
```


## 機能要件

---

### 機能ID A00　ログイン機能
メールアドレスとパスワードでログインする

### 機能ID A01　ロギング機能
デバック用にロガーを実装

### 機能ID A02　データベースセッション機能
設定ファイルを読み込んで、SQLAlchemyを使用してデータベース接続を確立し、セッションを作成する

venv削除
更新