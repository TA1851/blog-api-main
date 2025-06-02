# 🔒 認証要件の追加: GET /api/v1/user/{user_id}

## 変更概要
エンドポイント `GET /api/v1/user/{user_id}` に認証機能を追加し、セキュリティを強化しました。

## 🔄 変更前後の比較

### **変更前:**
```python
@router.get("/user/{user_id}")
async def show_user(user_id: int, db: Session = Depends(get_db)) -> UserSchema:
    # 認証なしでユーザー情報を取得
```

### **変更後:**
```python
@router.get("/user/{user_id}")
async def show_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)  # 🔒 認証追加
) -> UserSchema:
    # 認証されたユーザーのみアクセス可能
    # 自分以外の情報へのアクセスを禁止
```

## 🛡️ セキュリティ機能

### 1. **JWT トークン認証**
- `Authorization: Bearer <token>` ヘッダーが必須
- 有効なJWTトークンなしではアクセス不可

### 2. **アクセス制御**
- ユーザーは自分自身の情報のみ取得可能
- 他のユーザーの情報にアクセスしようとすると `403 Forbidden`

### 3. **エラーハンドリング**
```python
# 認証エラー
401 Unauthorized - 無効または欠けているトークン

# アクセス制御エラー  
403 Forbidden - 他のユーザーの情報へのアクセス試行

# データエラー
404 Not Found - 存在しないユーザーID
```

## 📋 APIリクエスト例

### **認証あり（正常）:**
```bash
curl -X GET "http://localhost:8000/api/v1/user/123" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### **認証なし（エラー）:**
```bash
curl -X GET "http://localhost:8000/api/v1/user/123"
# → 401 Unauthorized
```

### **他のユーザー情報アクセス（エラー）:**
```bash
# ユーザーID=123でログインしているが、ID=456の情報を要求
curl -X GET "http://localhost:8000/api/v1/user/456" \
  -H "Authorization: Bearer <user_123_token>"
# → 403 Forbidden
```

## ✅ 実装済み機能

- [x] JWT認証の追加
- [x] アクセス制御ロジック
- [x] 適切なエラーレスポンス
- [x] セキュリティログ記録
- [x] 型安全性の維持
- [x] OpenAPI/Swaggerドキュメント更新

## 🎯 セキュリティ向上効果

1. **個人情報保護**: ユーザーは自分のデータのみアクセス可能
2. **不正アクセス防止**: 認証なしでの情報取得を防止
3. **監査ログ**: すべてのアクセス試行をログ記録
4. **API仕様明確化**: ドキュメントで認証要件を明示

---
**変更日**: 2025年6月2日
**影響範囲**: `routers/user.py`
**型安全性**: ✅ mypy 0エラー維持
