フロントエンド開発者向けAPI ガイド
=====================================

.. contents:: 目次
   :local:
   :depth: 2

概要
----

このガイドは、Blog APIを利用するフロントエンド開発者向けに、実用的なAPI使用方法を説明します。

ベースURL
---------

**開発環境:** ``http://localhost:8000/api/v1``
**本番環境:** ``https://your-production-domain.com/api/v1``

認証
----

認証方式
~~~~~~~~

Blog APIはJWT（JSON Web Token）による Bearer認証を使用します。

.. code-block:: text

   Authorization: Bearer <access_token>

ログイン
~~~~~~~~

**エンドポイント:** ``POST /login``

**Content-Type:** ``application/x-www-form-urlencoded``

**リクエスト例:**

.. code-block:: javascript

   const response = await fetch('/api/v1/login', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/x-www-form-urlencoded',
     },
     body: new URLSearchParams({
       username: 'user@example.com',
       password: 'password123'
     })
   });
   
   const data = await response.json();
   localStorage.setItem('access_token', data.access_token);

**レスポンス例:**

.. code-block:: json

   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer"
   }

ログアウト
~~~~~~~~~~

**エンドポイント:** ``POST /logout``

**リクエスト例:**

.. code-block:: javascript

   const token = localStorage.getItem('access_token');
   
   const response = await fetch('/api/v1/logout', {
     method: 'POST',
     headers: {
       'Authorization': `Bearer ${token}`,
       'Content-Type': 'application/json',
     }
   });

ユーザー管理
-----------

ユーザー登録
~~~~~~~~~~~~

**エンドポイント:** ``POST /user``

**リクエスト例:**

.. code-block:: javascript

   const response = await fetch('/api/v1/user', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
     },
     body: JSON.stringify({
       email: 'newuser@example.com',
       name: 'New User'
     })
   });

パスワード変更
~~~~~~~~~~~~~~

**エンドポイント:** ``POST /change-password``

**リクエスト例:**

.. code-block:: javascript

   const response = await fetch('/api/v1/change-password', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
     },
     body: JSON.stringify({
       username: 'user@example.com',
       temp_password: 'temp_password_123',
       new_password: 'new_secure_password'
     })
   });

記事管理
--------

記事一覧取得（認証付き）
~~~~~~~~~~~~~~~~~~~~~~~~

**エンドポイント:** ``GET /articles``

**リクエスト例:**

.. code-block:: javascript

   const token = localStorage.getItem('access_token');
   
   const response = await fetch('/api/v1/articles', {
     method: 'GET',
     headers: {
       'Authorization': `Bearer ${token}`,
     }
   });
   
   const articles = await response.json();

記事作成
~~~~~~~~

**エンドポイント:** ``POST /articles``

**リクエスト例:**

.. code-block:: javascript

   const token = localStorage.getItem('access_token');
   
   const response = await fetch('/api/v1/articles', {
     method: 'POST',
     headers: {
       'Authorization': `Bearer ${token}`,
       'Content-Type': 'application/json',
     },
     body: JSON.stringify({
       title: '新しい記事のタイトル',
       body: '# 記事の内容\n\nMarkdown形式で記述'
     })
   });

パブリック記事一覧
~~~~~~~~~~~~~~~~~~

**エンドポイント:** ``GET /public/articles``

**リクエスト例:**

.. code-block:: javascript

   // 認証不要
   const response = await fetch('/api/v1/public/articles?limit=10&skip=0');
   const articles = await response.json();

記事検索
~~~~~~~~

**エンドポイント:** ``GET /public/articles/search``

**リクエスト例:**

.. code-block:: javascript

   const keyword = encodeURIComponent('検索キーワード');
   const response = await fetch(`/api/v1/public/articles/search?q=${keyword}&limit=10`);
   const searchResults = await response.json();

エラーハンドリング
-----------------

HTTPステータスコード
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   
   * - ステータス
     - 説明
     - 対応
   * - 200
     - 成功
     - 正常処理
   * - 401
     - 認証エラー
     - ログイン画面にリダイレクト
   * - 403
     - 権限エラー
     - アクセス権限なしメッセージ
   * - 404
     - 見つからない
     - 該当データなしメッセージ
   * - 503
     - サービス利用不可
     - 一時的なエラー、再試行推奨

エラーレスポンス例
~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "detail": "エラーメッセージ"
   }

実装サンプル
-----------

React フック例
~~~~~~~~~~~~~~

.. code-block:: javascript

   // hooks/useAuth.js
   import { useState, useEffect } from 'react';
   
   export function useAuth() {
     const [user, setUser] = useState(null);
     const [loading, setLoading] = useState(true);
     
     const login = async (email, password) => {
       try {
         const response = await fetch('/api/v1/login', {
           method: 'POST',
           headers: {
             'Content-Type': 'application/x-www-form-urlencoded',
           },
           body: new URLSearchParams({ username: email, password })
         });
         
         if (response.ok) {
           const data = await response.json();
           localStorage.setItem('access_token', data.access_token);
           setUser({ email });
           return true;
         }
         return false;
       } catch (error) {
         console.error('Login failed:', error);
         return false;
       }
     };
     
     const logout = async () => {
       const token = localStorage.getItem('access_token');
       if (token) {
         await fetch('/api/v1/logout', {
           method: 'POST',
           headers: { 'Authorization': `Bearer ${token}` }
         });
       }
       localStorage.removeItem('access_token');
       setUser(null);
     };
     
     return { user, loading, login, logout };
   }

TypeScript 型定義
~~~~~~~~~~~~~~~~

.. code-block:: typescript

   // types/api.ts
   export interface LoginResponse {
     access_token: string;
     token_type: string;
   }
   
   export interface Article {
     article_id: number;
     title: string;
     body: string;
     user_id: number;
   }
   
   export interface PublicArticle {
     article_id: number;
     title: string;
     body_html: string;
   }
   
   export interface User {
     email: string;
     name?: string;
     is_active: boolean;
   }

開発のベストプラクティス
-----------------------

トークン管理
~~~~~~~~~~~~

- アクセストークンは ``localStorage`` に保存
- 401エラー時は自動ログアウト
- セキュリティを考慮して適切な有効期限設定

エラーハンドリング
~~~~~~~~~~~~~~~~~

- 全てのAPIコールで適切なエラーハンドリング
- ユーザーフレンドリーなエラーメッセージ表示
- ネットワークエラーに対する再試行機能

パフォーマンス
~~~~~~~~~~~~~

- ページネーションの活用
- 必要なデータのみを取得
- 適切なキャッシュ戦略

関連リンク
----------

- :doc:`routers.auth` - 認証エンドポイントの詳細
- :doc:`routers.user` - ユーザー管理エンドポイント
- :doc:`routers.article` - 記事管理エンドポイント
- :doc:`schemas` - データモデル定義
