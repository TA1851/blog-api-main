# Blog API パブリックエンドポイント仕様書

## 概要

ブログ記事の認証なしでの閲覧を可能にするパブリックAPIエンドポイントの仕様書です。
日本語検索機能、Markdown→HTML変換、ページネーション機能を提供します。

## ベースURL

```
http://localhost:8000/api/v1
```

## 共通レスポンス仕様

### 成功時のレスポンス形式

```json
[
  {
    "article_id": 1,
    "title": "記事のタイトル",
    "body_html": "<h1>見出し</h1><p>本文内容<br>改行も含まれます</p>"
  }
]
```

### エラー時のレスポンス形式

```json
{
  "detail": "エラーメッセージ"
}
```

---

## エンドポイント一覧

### 1. パブリック記事一覧取得

**エンドポイント:** `GET /public/articles`

**概要:** 認証なしで全ての記事を取得します。ページネーション機能付き。

#### リクエストパラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|-----|----------|-----|
| `limit` | integer | No | なし | 取得する最大記事数（1以上）。指定しない場合は全件取得 |
| `skip` | integer | No | 0 | スキップする記事数（0以上）。ページネーション用 |

#### レスポンス

**ステータスコード:** `200 OK`

**レスポンスボディ:**

```json
[
  {
    "article_id": 3,
    "title": "最新の記事",
    "body_html": "<h2>見出し2</h2><p>最新記事の内容です。<br>改行も正しく表示されます。</p>"
  },
  {
    "article_id": 2,
    "title": "2番目の記事", 
    "body_html": "<p>記事の本文がここに表示されます。</p>"
  },
  {
    "article_id": 1,
    "title": "最初の記事",
    "body_html": "<p>最初に投稿された記事です。</p>"
  }
]
```

#### 使用例

```bash
# 全記事を取得
curl "http://localhost:8000/api/v1/public/articles"

# 最新5件を取得
curl "http://localhost:8000/api/v1/public/articles?limit=5"

# 6件目から10件目を取得（ページネーション）
curl "http://localhost:8000/api/v1/public/articles?skip=5&limit=5"
```

#### JavaScript使用例

```javascript
// 記事一覧取得（最新10件）
async function getArticles(limit = 10, skip = 0) {
  try {
    const response = await fetch(
      `http://localhost:8000/api/v1/public/articles?limit=${limit}&skip=${skip}`
    );
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const articles = await response.json();
    return articles;
  } catch (error) {
    console.error('記事取得エラー:', error);
    throw error;
  }
}

// 使用例
getArticles(5, 0).then(articles => {
  articles.forEach(article => {
    console.log(`ID: ${article.article_id}, タイトル: ${article.title}`);
    // article.body_html を使ってHTMLを表示
    document.getElementById('content').innerHTML = article.body_html;
  });
});
```

---

### 2. パブリック記事詳細取得

**エンドポイント:** `GET /public/articles/{article_id}`

**概要:** 指定されたIDの記事詳細を認証なしで取得します。

#### パスパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|-----|-----|
| `article_id` | integer | Yes | 取得する記事のID |

#### レスポンス

**ステータスコード:** `200 OK`

**レスポンスボディ:**

```json
{
  "article_id": 1,
  "title": "記事のタイトル",
  "body_html": "<h1>見出し1</h1><p>記事の詳細な内容がここに表示されます。<br>改行も正しく反映されます。</p><h2>サブ見出し</h2><p>さらなる詳細内容...</p>"
}
```

#### エラーレスポンス

**ステータスコード:** `404 Not Found` - 記事が存在しない場合

```json
{
  "detail": "記事ID 999 の記事が見つかりません"
}
```

#### 使用例

```bash
# 記事ID 1の詳細を取得
curl "http://localhost:8000/api/v1/public/articles/1"

# 記事ID 5の詳細を取得
curl "http://localhost:8000/api/v1/public/articles/5"
```

#### JavaScript使用例

```javascript
// 記事詳細取得関数
async function getArticleDetail(articleId) {
  try {
    const response = await fetch(
      `http://localhost:8000/api/v1/public/articles/${articleId}`
    );
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('記事が見つかりませんでした');
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const article = await response.json();
    return article;
  } catch (error) {
    console.error('記事詳細取得エラー:', error);
    throw error;
  }
}

// 使用例
getArticleDetail(1).then(article => {
  console.log(`タイトル: ${article.title}`);
  // 記事詳細をHTMLで表示
  document.getElementById('article-title').textContent = article.title;
  document.getElementById('article-content').innerHTML = article.body_html;
}).catch(error => {
  if (error.message.includes('見つかりません')) {
    document.getElementById('error-message').textContent = '記事が見つかりませんでした';
  } else {
    document.getElementById('error-message').textContent = '記事の取得に失敗しました';
  }
});

// URLパラメータから記事IDを取得して表示
function displayArticleFromUrl() {
  const urlParams = new URLSearchParams(window.location.search);
  const articleId = urlParams.get('id');
  
  if (articleId) {
    getArticleDetail(parseInt(articleId))
      .then(article => displayArticleDetail(article))
      .catch(error => showErrorMessage(error.message));
  }
}

// 記事詳細表示関数
function displayArticleDetail(article) {
  document.title = article.title; // ページタイトルを設定
  document.getElementById('article-title').textContent = article.title;
  document.getElementById('article-content').innerHTML = article.body_html;
  document.getElementById('article-id').textContent = `記事ID: ${article.article_id}`;
}
```

---

### 3. パブリック記事検索

**エンドポイント:** `GET /public/articles/search`

**概要:** キーワードで記事を検索します。日本語検索対応、複数キーワードによるAND検索機能付き。

#### リクエストパラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|-----|----------|-----|
| `q` | string | Yes | - | 検索キーワード（日本語・英語対応）。複数キーワードはスペース区切り |
| `limit` | integer | No | 10 | 取得する最大記事数（1-100） |
| `skip` | integer | No | 0 | スキップする記事数（0以上）。ページネーション用 |

#### レスポンス

**ステータスコード:** `200 OK`

**レスポンスボディ:**

```json
[
  {
    "article_id": 5,
    "title": "React開発の基礎",
    "body_html": "<h1>React開発</h1><p>React開発の基礎について説明します。<br>コンポーネントの作成方法を学びましょう。</p>"
  },
  {
    "article_id": 2,
    "title": "フロントエンド開発",
    "body_html": "<p>フロントエンド開発にはReactが人気です。</p>"
  }
]
```

#### 検索仕様

- **検索対象:** 記事のタイトル（`title`）と本文（`body`）
- **検索方式:** 部分一致検索（大文字小文字区別なし）
- **複数キーワード:** スペース区切りでAND検索
- **日本語対応:** URLエンコードされた日本語キーワードを自動デコード
- **ソート順:** 記事ID降順（新しい記事が先頭）

#### 使用例

```bash
# 単一キーワード検索
curl "http://localhost:8000/api/v1/public/articles/search?q=React"

# 複数キーワード検索（AND検索）
curl "http://localhost:8000/api/v1/public/articles/search?q=React%20%E9%96%8B%E7%99%BA"

# 日本語検索（URLエンコード）
curl "http://localhost:8000/api/v1/public/articles/search?q=%E3%83%95%E3%83%AD%E3%83%B3%E3%83%88%E3%82%A8%E3%83%B3%E3%83%89"

# ページネーション付き検索
curl "http://localhost:8000/api/v1/public/articles/search?q=開発&limit=5&skip=0"
```

#### JavaScript使用例

```javascript
// 記事検索関数
async function searchArticles(query, limit = 10, skip = 0) {
  try {
    // 日本語キーワードを適切にエンコード
    const encodedQuery = encodeURIComponent(query);
    const url = `http://localhost:8000/api/v1/public/articles/search?q=${encodedQuery}&limit=${limit}&skip=${skip}`;
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const articles = await response.json();
    return articles;
  } catch (error) {
    console.error('記事検索エラー:', error);
    throw error;
  }
}

// 使用例
searchArticles('React 開発', 5, 0).then(articles => {
  if (articles.length === 0) {
    console.log('検索結果が見つかりませんでした');
    return;
  }
  
  articles.forEach(article => {
    console.log(`ID: ${article.article_id}, タイトル: ${article.title}`);
    // HTMLを安全に表示
    const articleDiv = document.createElement('div');
    articleDiv.innerHTML = article.body_html;
    document.getElementById('search-results').appendChild(articleDiv);
  });
});

// 検索フォームの実装例
document.getElementById('search-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const query = document.getElementById('search-input').value.trim();
  
  if (query) {
    try {
      const results = await searchArticles(query);
      displaySearchResults(results);
    } catch (error) {
      alert('検索エラーが発生しました');
    }
  }
});
```

---

## データモデル

### PublicArticle

パブリックAPIで返される記事データの構造

| フィールド | 型 | 説明 |
|-----------|---|-----|
| `article_id` | integer | 記事の一意識別子 |
| `title` | string | 記事のタイトル（最大30文字） |
| `body_html` | string | Markdown変換済みのHTML形式本文 |

#### 注意事項

- `body_html`フィールドには、元のMarkdown形式の本文が自動的にHTMLに変換されたものが含まれます
- 改行は`<br>`タグに変換されます
- Markdownの見出し（`#`）は適切なHTMLタグ（`<h1>`, `<h2>`など）に変換されます
- 元の`body`フィールド（Markdown形式）はパブリックAPIには含まれません

---

## エラーハンドリング

### エラーレスポンス

| ステータスコード | 説明 | 対処法 |
|-----------------|-----|-------|
| `400 Bad Request` | リクエストパラメータが不正 | パラメータの形式を確認 |
| `422 Unprocessable Entity` | バリデーションエラー | 必須パラメータや制約を確認 |
| `500 Internal Server Error` | サーバー内部エラー | しばらく時間をおいて再試行 |

### エラーレスポンス例

```json
{
  "detail": "記事の取得に失敗しました"
}
```

### JavaScript エラーハンドリング例

```javascript
async function safeApiCall(apiFunction) {
  try {
    return await apiFunction();
  } catch (error) {
    if (error.message.includes('400')) {
      alert('リクエストに問題があります。パラメータを確認してください。');
    } else if (error.message.includes('500')) {
      alert('サーバーエラーが発生しました。しばらく時間をおいて再試行してください。');
    } else {
      alert('通信エラーが発生しました。');
    }
    console.error('API Error:', error);
    throw error;
  }
}

// 使用例
safeApiCall(() => getArticles(10, 0))
  .then(articles => {
    // 成功時の処理
    console.log('記事取得成功:', articles);
  })
  .catch(error => {
    // エラーハンドリングは上記関数で実行済み
  });
```

---

## ページネーション実装ガイド

### 基本的なページネーション

```javascript
class ArticlePagination {
  constructor(articlesPerPage = 10) {
    this.articlesPerPage = articlesPerPage;
    this.currentPage = 1;
    this.totalArticles = 0;
  }

  // 記事一覧の取得
  async getPage(page = 1) {
    const skip = (page - 1) * this.articlesPerPage;
    const articles = await getArticles(this.articlesPerPage, skip);
    
    this.currentPage = page;
    return articles;
  }

  // 検索結果のページネーション
  async searchPage(query, page = 1) {
    const skip = (page - 1) * this.articlesPerPage;
    const articles = await searchArticles(query, this.articlesPerPage, skip);
    
    this.currentPage = page;
    return articles;
  }

  // 次のページ
  async nextPage(query = null) {
    const nextPage = this.currentPage + 1;
    return query ? 
      await this.searchPage(query, nextPage) : 
      await this.getPage(nextPage);
  }

  // 前のページ
  async prevPage(query = null) {
    if (this.currentPage > 1) {
      const prevPage = this.currentPage - 1;
      return query ? 
        await this.searchPage(query, prevPage) : 
        await this.getPage(prevPage);
    }
    return [];
  }
}

// 使用例
const pagination = new ArticlePagination(5);

// 最初のページを取得
pagination.getPage(1).then(articles => {
  console.log('1ページ目:', articles);
});
```

---

## HTML表示の実装例

### 記事の安全な表示

```javascript
function displayArticle(article) {
  // 記事コンテナを作成
  const articleElement = document.createElement('article');
  articleElement.className = 'blog-article';
  
  // タイトルを安全にエスケープして表示
  const titleElement = document.createElement('h2');
  titleElement.textContent = article.title;
  
  // HTMLコンテンツを表示（Markdown変換済み）
  const contentElement = document.createElement('div');
  contentElement.className = 'article-content';
  contentElement.innerHTML = article.body_html;
  
  // 記事ID表示
  const idElement = document.createElement('span');
  idElement.className = 'article-id';
  idElement.textContent = `記事ID: ${article.article_id}`;
  
  // 要素を組み合わせ
  articleElement.appendChild(titleElement);
  articleElement.appendChild(contentElement);
  articleElement.appendChild(idElement);
  
  return articleElement;
}

// 記事リストの表示
function displayArticleList(articles, containerId = 'articles-container') {
  const container = document.getElementById(containerId);
  container.innerHTML = ''; // 既存のコンテンツをクリア
  
  if (articles.length === 0) {
    container.innerHTML = '<p>記事が見つかりませんでした。</p>';
    return;
  }
  
  articles.forEach(article => {
    const articleElement = displayArticle(article);
    container.appendChild(articleElement);
  });
}
```

### CSS スタイル例

```css
.blog-article {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  background-color: #fff;
}

.blog-article h2 {
  color: #333;
  margin-top: 0;
  margin-bottom: 15px;
}

.article-content {
  line-height: 1.6;
  color: #666;
  margin-bottom: 15px;
}

.article-content h1,
.article-content h2,
.article-content h3 {
  color: #333;
  margin-top: 20px;
  margin-bottom: 10px;
}

.article-id {
  font-size: 0.9em;
  color: #999;
  font-style: italic;
}

/* 検索結果のハイライト */
.search-highlight {
  background-color: #fff3cd;
  padding: 2px 4px;
  border-radius: 3px;
}
```

---

## セキュリティ考慮事項

### XSS対策

- `body_html`フィールドには信頼されたMarkdown変換結果が含まれますが、表示時には適切なサニタイズを行ってください
- ユーザー入力（検索キーワードなど）は適切にエスケープしてください

### CORS設定

現在の実装では適切なCORS設定がされていますが、本番環境では必要に応じて制限してください。

---

## パフォーマンス最適化

### 推奨事項

1. **ページネーション**: 大量のデータを一度に取得せず、適切なページサイズ（10-20件）を使用
2. **検索最適化**: 短すぎるキーワード（1文字）での検索は避ける
3. **キャッシュ**: 頻繁に変更されない記事一覧はブラウザキャッシュを活用
4. **デバウンス**: 検索入力にはデバウンス処理を実装して無駄なAPIコールを削減

### デバウンス実装例

```javascript
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// 検索入力のデバウンス
const debouncedSearch = debounce(async (query) => {
  if (query.trim().length > 0) {
    const results = await searchArticles(query);
    displayArticleList(results);
  }
}, 300);

document.getElementById('search-input').addEventListener('input', (e) => {
  debouncedSearch(e.target.value);
});
```

---

## まとめ

このAPIを使用することで、以下の機能を持つフロントエンドアプリケーションを構築できます：

1. **記事一覧表示**: ページネーション付きの記事リスト
2. **記事検索**: 日本語対応の高度な検索機能
3. **リッチコンテンツ**: Markdown形式の記事をHTML形式で表示
4. **レスポンシブ対応**: 必要なデータのみを取得する効率的な設計

各エンドポイントは認証なしで利用でき、フロントエンドからの直接アクセスが可能です。
