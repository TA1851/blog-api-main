"""FastAPIのエントリーポイント"""
# import pprint
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

# デバッグ用にオリジンの値を表示
# print(f"CORS origins: {origins}")
# print(f"Local origin: {local_origin}")

# 両方のオリジンリストを結合
allowed_origins = []
if origins:
    allowed_origins.extend(origins)
if local_origin:
    allowed_origins.extend(local_origin)

# デフォルト値の設定
if not allowed_origins:
    # print("CORS_ORIGINSとLOCAL_ORIGINの両方が取得できませんでした。")
    create_error_logger("CORS_ORIGINSとLOCAL_ORIGINの両方が取得できませんでした。")
else:
    # print(f"STEP4：CORS_ORIGINSとLOCAL_ORIGINを取得しました。 -> {allowed_origins}")
    print(f"処理が完了しました。")

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
    request:Request,
    exc:RequestValidationError):
    # pprint.pprint(exc.errors())
    create_error_logger(
        f"バリデーションエラー: {exc.errors()}"
        )
    return JSONResponse(
        content={},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


app.include_router(article.router)
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
    )
app.include_router(user.router)
app.include_router(auth.router)