"""schemasモジュールのテストコード"""
import pytest
from pydantic import ValidationError

# テスト対象のモジュールをインポート
from schemas import (
    LengthMismatchError,
    ArticleBase,
    Article,
    User,
    ShowUser,
    ShowArticle,
    Login,
    PasswordChange,
    Token,
    TokenData,
    PublicArticle,
    AccountDeletionRequest
)


class TestLengthMismatchError:
    """LengthMismatchErrorのテスト"""
    def test_custom_exception(self):
        """カスタム例外が正しく動作することをテスト"""
        with pytest.raises(LengthMismatchError):
            raise LengthMismatchError("長さが一致しません")


class TestArticleBase:
    """ArticleBaseモデルのテスト"""
    def test_valid_article_creation(self):
        """有効な記事データでモデルが作成できることをテスト"""
        article_data = {
            "article_id": 1,
            "title": "テストタイトル",
            "body": "テスト本文\n\n# 見出し\n\n内容",
            "user_id": 1
        }
        article = ArticleBase(**article_data)
        assert article.article_id == 1
        assert article.title == "テストタイトル"
        assert article.body == "テスト本文\n\n# 見出し\n\n内容"
        assert article.user_id == 1

    def test_required_fields(self):
        """必須フィールドが不足した場合のテスト"""
        with pytest.raises(ValidationError) as exc_info:
            ArticleBase()
        errors = exc_info.value.errors()
        error_fields = [error['loc'][0] for error in errors]
        assert 'title' in error_fields
        assert 'body' in error_fields

    def test_title_max_length_validation(self):
        """タイトルの最大文字数制限のテスト"""
        long_title = "あ" * 31  # 31文字
        with pytest.raises(ValidationError) as exc_info:
            ArticleBase(title=long_title, body="テスト本文")
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('title',) for error in errors)

    def test_body_max_length_validation(self):
        """本文の最大文字数制限のテスト"""
        long_body = "あ" * 1001  # 1001文字
        with pytest.raises(ValidationError) as exc_info:
            ArticleBase(title="テストタイトル", body=long_body)
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('body',) for error in errors)

    def test_body_html_conversion(self):
        """Markdown→HTML変換のテスト"""
        article = ArticleBase(
            title="テストタイトル",
            body="テスト本文\n\n# 見出し\n\n段落"
        )
        html_content = article.body_html
        assert "テスト本文" in html_content
        assert "見出し" in html_content

    def test_optional_fields(self):
        """オプションフィールドのテスト"""
        article = ArticleBase(title="テストタイトル", body="テスト本文")
        assert article.article_id is None
        assert article.user_id is None


class TestArticle:
    """Articleモデルのテスト"""
    def test_article_inheritance(self):
        """ArticleBaseを継承していることをテスト"""
        article = Article(title="テストタイトル", body="テスト本文")
        assert isinstance(article, ArticleBase)
        assert article.title == "テストタイトル"
        assert article.body == "テスト本文"


class TestUser:
    """Userモデルのテスト"""
    def test_valid_user_creation(self):
        """有効なユーザーデータでモデルが作成できることをテスト"""
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "is_active": True
        }
        user = User(**user_data)
        assert str(user.email) == "test@example.com"
        assert user.password == "password123"
        assert user.is_active is True

    def test_email_validation(self):
        """メールアドレスの形式チェックのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            User(email="invalid-email", password="password123")
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('email',) for error in errors)

    def test_email_max_length(self):
        """メールアドレスの最大文字数制限のテスト"""
        long_email = "a" * 45 + "@example.com"  # 50文字を超える
        with pytest.raises(ValidationError) as exc_info:
            User(email=long_email, password="password123")
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('email',) for error in errors)

    def test_password_max_length(self):
        """パスワードの最大文字数制限のテスト"""
        long_password = "a" * 101  # 101文字
        with pytest.raises(ValidationError) as exc_info:
            User(email="test@example.com", password=long_password)
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('password',) for error in errors)

    def test_optional_fields(self):
        """全フィールドがオプションであることをテスト"""
        user = User()
        assert user.email is None
        assert user.password is None
        assert user.is_active is None


class TestShowUser:
    """ShowUserモデルのテスト"""
    def test_show_user_with_blogs(self):
        """ブログ記事を含むユーザー表示モデルのテスト"""
        blog_article = ArticleBase(title="テスト記事", body="内容")
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "is_active": True,
            "blogs": [blog_article]
        }
        show_user = ShowUser(**user_data)
        assert show_user.id == 1
        assert str(show_user.email) == "test@example.com"
        assert show_user.is_active is True
        assert len(show_user.blogs) == 1
        assert show_user.blogs[0].title == "テスト記事"


class TestShowArticle:
    """ShowArticleモデルのテスト"""
    def test_show_article_with_body_html(self):
        """HTML変換を含む記事表示モデルのテスト"""
        article_data = {
            "id": 1,
            "title": "テストタイトル",
            "body": "テスト本文\n改行あり"
        }
        show_article = ShowArticle(**article_data)
        assert show_article.id == 1
        assert show_article.title == "テストタイトル"
        assert show_article.body == "テスト本文\n改行あり"
        html_content = show_article.body_html
        assert "テスト本文" in html_content
        assert "<p>" in html_content  # マークダウン変換でpタグが生成される

    def test_body_html_with_none_body(self):
        """bodyがNoneの場合のHTML変換のテスト"""
        show_article = ShowArticle(id=1, title="タイトル", body=None)
        assert show_article.body_html is None


class TestLogin:
    """Loginモデルのテスト"""
    def test_valid_login(self):
        """有効なログインデータのテスト"""
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        login = Login(**login_data)
        assert str(login.email) == "test@example.com"
        assert login.password == "password123"

    def test_login_email_validation(self):
        """Loginのメールアドレス形式チェックのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            Login(email="invalid.email", password="password123")
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('email',) for error in errors)


    def test_password_max_length(self):
        """パスワードの最大文字数制限のテスト"""
        long_password = "a" * 51  # 51文字
        with pytest.raises(ValidationError) as exc_info:
            Login(email="test@example.com", password=long_password)
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('password',) for error in errors)


class TestPasswordChange:
    """PasswordChangeモデルのテスト"""
    def test_valid_password_change(self):
        """有効なパスワード変更データのテスト"""
        password_data = {
            "username": "test@example.com",
            "temp_password": "temp123",
            "new_password": "newpassword123"
        }
        password_change = PasswordChange(**password_data)
        assert str(password_change.username) == "test@example.com"
        assert password_change.temp_password == "temp123"
        assert password_change.new_password == "newpassword123"

    def test_username_email_validation(self):
        """ユーザー名（メールアドレス）の形式チェックのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChange(
                username="invalid-email",
                temp_password="temp123",
                new_password="newpass123"
            )
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('username',) for error in errors)

    def test_new_password_min_length(self):
        """新しいパスワードの最小文字数制限のテスト"""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChange(
                username="test@example.com",
                temp_password="temp123",
                new_password="short"  # 8文字未満
            )
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('new_password',) for error in errors)

    def test_required_fields(self):
        """必須フィールドのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChange()
        errors = exc_info.value.errors()
        error_fields = [error['loc'][0] for error in errors]
        assert 'username' in error_fields
        assert 'temp_password' in error_fields
        assert 'new_password' in error_fields


class TestToken:
    """Tokenモデルのテスト"""
    def test_token_creation(self):
        """トークンモデルの作成テスト"""
        token = Token(access_token="abc123", token_type="bearer")
        assert token.access_token == "abc123"
        assert token.token_type == "bearer"


class TestTokenData:
    """TokenDataモデルのテスト"""
    def test_token_data_with_email(self):
        """メールアドレス付きトークンデータのテスト"""
        token_data = TokenData(email="test@example.com")
        assert token_data.email == "test@example.com"

    def test_token_data_without_email(self):
        """メールアドレスなしトークンデータのテスト"""
        token_data = TokenData()
        assert token_data.email is None


class TestPublicArticle:
    """PublicArticleモデルのテスト"""
    def test_public_article_creation(self):
        """パブリック記事モデルの作成テスト"""
        article_data = {
            "article_id": 1,
            "title": "パブリックタイトル",
            "body_html": "<p>HTML本文</p>"
        }
        public_article = PublicArticle(**article_data)
        assert public_article.article_id == 1
        assert public_article.title == "パブリックタイトル"
        assert public_article.body_html == "<p>HTML本文</p>"

    def test_required_fields(self):
        """必須フィールドのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            PublicArticle()
        errors = exc_info.value.errors()
        error_fields = [error['loc'][0] for error in errors]
        assert 'article_id' in error_fields
        assert 'title' in error_fields
        assert 'body_html' in error_fields


class TestAccountDeletionRequest:
    """AccountDeletionRequestモデルのテスト"""
    def test_valid_deletion_request(self):
        """有効な退会リクエストのテスト"""
        deletion_data = {
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
        deletion_request = AccountDeletionRequest(**deletion_data)
        assert str(deletion_request.email) == "test@example.com"
        assert deletion_request.password == "password123"
        assert deletion_request.confirm_password == "password123"

    def test_email_validation_for_deletion(self):
        """退会リクエストのメールアドレス形式チェックのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            AccountDeletionRequest(
                email="invalid.email.format",
                password="password123",
                confirm_password="password123"
            )
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('email',) for error in errors)

    def test_password_min_length(self):
        """パスワードの最小文字数制限のテスト"""
        with pytest.raises(ValidationError) as exc_info:
            AccountDeletionRequest(
                email="test@example.com",
                password="short",  # 8文字未満
                confirm_password="short"
            )
        errors = exc_info.value.errors()
        password_errors = [error for error in errors if 'password' in str(error['loc'])]
        assert len(password_errors) >= 1

    def test_validate_passwords_match_success(self):
        """パスワード一致検証の成功テスト"""
        deletion_request = AccountDeletionRequest(
            email="test@example.com",
            password="password123",
            confirm_password="password123"
        )
        assert deletion_request.validate_passwords_match() is True

    def test_validate_passwords_match_failure(self):
        """パスワード一致検証の失敗テスト"""
        deletion_request = AccountDeletionRequest(
            email="test@example.com",
            password="password123",
            confirm_password="different123"
        )
        with pytest.raises(ValueError, match="パスワードと確認用パスワードが一致しません"):
            deletion_request.validate_passwords_match()


# テスト実行用の設定
if __name__ == "__main__":
    pytest.main([__file__, "-v"])