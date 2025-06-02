"""レスポンスのスキーマを定義するモジュール"""
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, EmailStr, computed_field
from fastapi import Request
from fastapi.exceptions import RequestValidationError
import markdown


class LengthMismatchError(Exception):
    """文字列の長さが一致しないエラーを表すカスタム例外"""
    pass


class ArticleBase(BaseModel, validate_assignment=True):
    """pydanticのベースモデルを継承して、記事情報のスキーマを定義する。

    :param article_id: 記事のID
    :param title: 記事のタイトル
    :param body: 記事の本文
    :param body_html: 記事の本文（HTML形式）
    :param user_id: 記事を作成したユーザーのID
    :param ConfigDict: Pydantic v3.0で class Config が削除される予定のためConfigDictを使用
    :param model_config: Pydantic v3.0で class Config が削除される予定のためConfigDictを使用
    """
    article_id: Optional[int] = Field(
        None, title="記事ID", description="記事ID"
        )
    title: str = Field(
        ..., title="タイトル", max_length=30, \
        description="30文字以内で入力してください"
        )
    body: str = Field(
        ..., title="本文", max_length=1000, \
        description="1000文字以内で入力してください"
        )
    user_id: Optional[int] = None
    
    @computed_field
    def body_html(self) -> str:
        """MarkdownテキストをHTMLに変換

        :return: HTML形式の本文
        :rtype: str
        """
        # 改行を<br>タグに変換し、見出し（#）を太文字に変換
        md = markdown.Markdown(extensions=['nl2br'])
        html_content = md.convert(self.body)
        return html_content
    class ConfigDict:
        model_config = ConfigDict(from_attributes=True)


class Article(ArticleBase):
    """ArticleBaseを継承して、記事情報のスキーマを定義する。
    """
    class ConfigDict:
        model_config = ConfigDict(from_attributes=True)


# FastAPIのエンドポイントで使用する例外ハンドラ
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> Any:
    """RequestValidationErrorをキャッチしてログに記録する例外ハンドラ"""
    # バリデーションエラーの情報を取得してログとコンソールに記録
    for error in exc.errors():
        locations = error["loc"]
        if len(locations) > 1 and locations[0] == "body":
            field_parts = [str(loc) for loc in locations[1:]]
            field_name = ".".join(field_parts)
        else:
            field_name = ".".join(str(loc) for loc in locations)

        error_message = f"{field_name}の検証エラー: {error['msg']}"
        print(error_message)

    # デフォルトのエラーハンドラを呼び出す
    from fastapi.exception_handlers import request_validation_exception_handler
    return await request_validation_exception_handler(request, exc)


class User(BaseModel):
    """ユーザーモデル

    :param id: ユーザーのID
    :param name: ユーザー名
    :param email: メールアドレス
    :param password: パスワード
    :param is_active: ユーザーの有効状態
    """
    email: EmailStr | None = Field(
        None, title="メールアドレス", max_length=50, 
        description="50文字以内で入力してください")
    password: str | None = Field(
        None, title="パスワード", max_length=100, 
        description="10文字以内で入力してください"
        )
    is_active: bool | None = Field(
        None, title="アクティブ", 
        description="TrueまたはFalseで入力してください"
        )
    class ConfigDict:
        model_config = ConfigDict(from_attributes=True)


class ShowUser(BaseModel):
    """ユーザー表示用モデル

    :param id: ユーザーのID
    :param name: ユーザー名
    :param email: メールアドレス
    :param is_active: ユーザーの有効状態
    :param blogs: ユーザーが作成したブログ記事のリスト
    """
    id: int | None = Field(
        None, title="ID", description="ユーザーのID"
        )
    email: EmailStr | None = Field(
        None, title="メールアドレス", max_length=50, \
        description="50文字以内で入力してください"
        )
    is_active: bool | None = Field(
        None, title="アクティブ", \
        description="TrueまたはFalseで入力してください"
        )
    blogs: list[ArticleBase] | None = Field(
        None, title="ブログ記事", \
        description="ユーザーが作成したブログ記事のリスト"
        )
    class ConfigDict:
        model_config = ConfigDict(from_attributes=True)


class ShowArticle(BaseModel):
    """記事表示用モデル

    :param id: 記事のID
    :param title: 記事のタイトル
    :param body: 記事の本文
    :param body_html: 記事の本文（HTML形式）
    """
    id: int | None = Field(
        None, title="ID", description="記事のID"
        )
    title: str | None = Field(
        None, title="タイトル", max_length=30, \
        description="30文字以内で入力してください"
        )
    body: str | None = Field(
        None, title="本文", max_length=1000, \
        description="1000文字以内で入力してください"
        )

    @computed_field
    def body_html(self) -> str | None:
        """MarkdownテキストをHTMLに変換

        :return: HTML形式の本文
        :rtype: str | None
        """
        if self.body is None:
            return None
        # 改行を<br>タグに変換し、見出し（#）を太文字に変換
        md = markdown.Markdown(extensions=['nl2br'])
        html_content = md.convert(self.body)
        return html_content
    class ConfigDict:
        model_config = ConfigDict(from_attributes=True)


class Login(BaseModel):
    """ログイン用モデル

    :param email: メールアドレス
    :param password: パスワード
    """
    email: EmailStr | None = Field(
        None, title="メールアドレス", max_length=50, \
        description="50文字以内で入力してください"
        )
    password: str | None = Field(
        None, title="パスワード", max_length=50, \
        description="50文字以内で入力してください"
        )

    class ConfigDict:
        model_config = ConfigDict(from_attributes=True)


class PasswordChange(BaseModel):
    """パスワード変更用モデル

    :param username: ユーザー名（メールアドレス）
    :param temp_password: 仮パスワード
    :param new_password: 新しいパスワード
    """
    username: EmailStr = Field(
        ..., title="メールアドレス", max_length=50,
        description="メールアドレスを入力してください"
    )
    temp_password: str = Field(
        ..., title="仮パスワード", max_length=50,
        description="現在の仮パスワードを入力してください"
    )
    new_password: str = Field(
        ..., title="新しいパスワード", max_length=50, min_length=8,
        description="8文字以上50文字以内で新しいパスワードを入力してください"
    )
    class ConfigDict:
        model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """トークン用モデル

    :param access_token: アクセストークン
    :param token_type: トークンの種類
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """トークンデータ用モデル

    :param email: メールアドレス
    """
    email: Optional[str] = None


class PublicArticle(BaseModel):
    """パブリック記事表示用モデル（認証なしで閲覧可能）

    :param article_id: 記事のID
    :param title: 記事のタイトル
    :param body_html: 記事の本文（HTML形式）
    """
    article_id: int = Field(
        ..., title="記事ID", description="記事ID"
    )
    title: str = Field(
        ..., title="タイトル", max_length=30,
        description="30文字以内のタイトル"
    )
    body_html: str = Field(
        ..., title="本文（HTML）", description="Markdown変換済みのHTML形式本文"
    )

    class ConfigDict:
        model_config = ConfigDict(from_attributes=True)


class AccountDeletionRequest(BaseModel):
    """退会リクエストのスキーマ"""
    email: EmailStr = Field(..., description="退会するユーザーのメールアドレス")
    password: str = Field(..., min_length=8, description="現在のパスワード")
    confirm_password: str = Field(..., min_length=8, description="確認用パスワード")

    def validate_passwords_match(self) -> bool:
        """パスワードと確認用パスワードが一致するかチェック"""
        if self.password != self.confirm_password:
            raise ValueError("パスワードと確認用パスワードが一致しません")
        return True