"""FastAPIのエントリーポイント"""
from fastapi import FastAPI, Depends, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine, db_env
from schemas import validation_exception_handler
from routers import article, user, auth
from logger.custom_logger import create_logger, create_error_logger

app = FastAPI()

# 環境変数から取得したCORS_ORIGINSリストを使用
origins = db_env.get("cors_origins", [])
local_origin = db_env.get("local_origin", [])

# テスト環境用のデフォルトのオリジンリスト
test_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "https://example.com"
]

# 両方のオリジンリストを結合
allowed_origins = []
if origins and isinstance(origins, list):
    allowed_origins.extend(origins)
if local_origin and isinstance(local_origin, list):
    allowed_origins.extend(local_origin)

# テスト実行時には、デフォルトでテスト環境用オリジンを追加
# 本番環境ではこれらは使用されない
import sys
if "pytest" in sys.modules:
    allowed_origins.extend(test_origins)

# デフォルト値の設定
if not allowed_origins:
    create_error_logger("CORS_ORIGINSとLOCAL_ORIGINの両方が取得できませんでした。")
    # テスト実行時のフォールバック
    allowed_origins = test_origins
else:
    create_logger(f"CORS_ORIGIN -> OK")

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # 結合したオリジンリストを使用
    allow_credentials=True,  # Cookieを含むリクエストを許可
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 許可するHTTPメソッド
    allow_headers=["*"],  # 許可するHTTPヘッダー
)

Base.metadata.create_all(engine)


@app.exception_handler(
    RequestValidationError
    )
async def handler(
    request: Request,
    exc: RequestValidationError) -> JSONResponse:
    # pprint.pprint(exc.errors())
    create_error_logger(
        f"バリデーションエラー: {exc.errors()}"
        )
    # メールアドレス形式エラーを検出
    for error in exc.errors():
        # エラーの場所（フィールド名）を確認
        location = error.get("loc", [])
        error_type = error.get("type", "")
        error_msg = error.get("msg", "")
        # メールアドレスフィールドのエラーかどうかを判定
        is_email_field = any("email" in str(loc).lower() for loc in location)
        # メールアドレス関連のエラータイプを検出
        email_error_types = [
            "value_error.email",
            "value_error",
            "type_error.str",
            "missing"
        ]
        # メールアドレスエラーの条件判定
        if is_email_field and (
            any(et in error_type for et in email_error_types) or
            "email" in error_msg.lower() or
            "valid email" in error_msg.lower() or
            "@" in str(error.get("input", ""))
        ):
            create_error_logger(f"メールアドレス形式エラーを検出: {error}")
            return JSONResponse(
                content={"detail": "メールアドレスの形式が不正です。"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
    # その他のバリデーションエラーはデフォルトのまま
    return JSONResponse(
        content={"detail": "入力データが無効です。"},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


app.include_router(article.router)
app.include_router(user.router)
app.include_router(auth.router)