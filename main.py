"""FastAPIのエントリーポイント"""
import pprint
from fastapi import FastAPI, Depends, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from schemas import validation_exception_handler
# from logger.custom_logger import create_logger, create_error_logger
from routers import article, user, auth

app = FastAPI()

# 許可するオリジン（フロントエンドのURLを指定）
origins = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "https://nextjs-app-khaki-two.vercel.app",
]

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 指定したオリジンのみ許可
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
    pprint.pprint(exc.errors())
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