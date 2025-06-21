.. Blog API Documentation master file

Blog API ドキュメント
=====================

このドキュメントは、Blog APIプロジェクトの技術文書です。
FastAPIとSQLAlchemyを使用したRESTful APIの実装について説明します。

概要
----

Blog APIは以下の機能を提供します：

* ユーザー認証とアカウント管理
* 記事の作成・編集・削除・検索
* JWT認証によるセキュアなAPI
* メール認証機能
* 包括的なテストスイート

フロントエンド開発者向け
-----------------------

.. toctree::
   :maxdepth: 2
   :caption: 🚀 クイックスタート

   frontend_api_guide

主要コンポーネント
------------------

.. toctree::
   :maxdepth: 2
   :caption: 🔐 認証システム

   routers.auth
   oauth2
   custom_token
   hashing

.. toctree::
   :maxdepth: 2
   :caption: 📝 APIエンドポイント

   routers.user
   routers.article
   routers

.. toctree::
   :maxdepth: 2
   :caption: 💾 データベース

   database
   models
   schemas

.. toctree::
   :maxdepth: 2
   :caption: 🛠️ ユーティリティ

   utils
   exceptions
   logger

.. toctree::
   :maxdepth: 2
   :caption: 🧪 テスト

   tests
   update_main_bug_history
   utils
