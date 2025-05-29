"""ユーザ認証機能を実装するためのルーターモジュール"""
# import pprint
import traceback
from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import ValidationError

from schemas import User as UserSchema
from models import User as UserModel
from database import db_env, session, get_db
from hashing import Hash
from logger.custom_logger import create_logger, create_error_logger


router = APIRouter(
    prefix="/api/v1",  # APIのバージョンを指定
    tags=["user"],  # SwaggerUIのタグを指定
)


# データベースURLを取得（本番環境のPostgreSQLを優先、次に開発環境のSQLite）
db_url = db_env.get("posgre_url") or db_env.get("sqlite_url")
key03 = db_env.get("file_id_03")
key08 = db_env.get("file_id_08")


def check_environment_variable():
    """環境変数を取得する

    :param key08: user.pyの環境変数
    :type key08: str
    :return: 環境変数の値
    :rtype: str
    """
    if not key08:
        create_error_logger(f"環境変数:{key08}が設定されていません。{key08}")
        raise ValueError(f"環境変数が設定されていません。-> {key08}")
    else:
        # print(f"STEP11：環境変数：{key08}を取得しました。 -> {key08}")
        create_logger(f"環境変数{key08}を取得しました。:")
    return key08

check_environment_variable()


def check_db_url():
    """データベースURLを取得する

    :param key03: user.pyの環境変数
    :type key03: str
    :param db_url: user.pyの環境変数
    :type db_url: str
    :return: 環境変数の値
    :rtype: str
    """
    if not db_url:
        create_error_logger(f"環境変数:database_urlが設定されていません。 -> {key03}")
        raise ValueError(f"環境変数が設定されていません。{key03}")
    else:
        # print(f"STEP12：環境変数: {db_url}を読み込みました。")
        create_logger(f"環境変数: {db_url}を読み込みました。 -> {key03}")
    return db_url

check_db_url()
# print(f"STEP13：ユーザを作成します。Swaggerで確認してください。")
# print("---------------------------------------------------------------")

get_db()

class IntegrityError(Exception):
    """主にユニーク制約違反（メールアドレスが既に使用されている場合など）を示すエラー"""
    pass

class SQLAlchemyError(Exception):
    """データベース関連のエラー"""
    pass


class UserRouter:
    @router.post(
    "/user",
    status_code=status.HTTP_201_CREATED,
    response_model=UserSchema,
    summary="User Create",
    description="ユーザーを作成するエンドポイント",
    )
    async def create_user(
        user: UserSchema,
        db: Session = Depends(get_db)
    ) -> UserModel:
        """ユーザーを作成するエンドポイント

        :param user: ユーザー情報を含むPydanticモデル
        :type user: UserSchema
        :param db: データベースセッション
        :type db: Session
        :return: 作成されたユーザー情報を含むSQLAlchemyモデル
        :rtype: UserModel
        :raises HTTPException: ユーザーの作成に失敗した場合
        :raises IntegrityError: ユーザーの作成に失敗した場合
        :raises SQLAlchemyError: データベースエラーが発生した場合
        :raises Exception: その他のエラーが発生した場合
        """
        try:
            # メールアドレスの重複チェック
            existing_user = db.query(UserModel).filter(
                UserModel.email == user.email
            ).first()

            if existing_user:
                print(f"STEP17：既存のメールアドレスが検出されました: {user.email}")
                create_error_logger(f"既存のメールアドレスが検出されました: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="このメールアドレスは既に使用されています。"
                )

            new_user = UserModel(
                # name=user.name,
                email=user.email,
                password=Hash.bcrypt(user.password)
            )
            # print(f"STEP17：新規ユーザーを作成します。: {new_user}")
            create_logger(f"新規ユーザーを作成します。: {new_user}")

            # if not new_user.name \
            #     or not new_user.email \
            #     or not new_user.password:
                # print(
                #     "ユーザーの作成に失敗しました。必須フィールドが不足しています。"
                # )
            if not new_user.email \
                or not new_user.password:
                create_error_logger(
                    "ユーザーの作成に失敗しました。必須フィールドが不足しています。"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ユーザー情報が不足しています。"
                )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            print(f"STEP17：ユーザーが作成されました。: {new_user}")
            create_logger(f"ユーザーが作成されました。: {new_user}")
            return new_user

        except HTTPException:
            # HTTPExceptionはそのまま再発生
            db.rollback()
            raise

        except IntegrityError as e:
            # データベースレベルでの重複エラーもキャッチ（二重保護）
            db.rollback()
            print(f"データベース制約違反: {str(e)}")
            create_error_logger(f"データベース制約違反（メールアドレス重複など）: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="このメールアドレスは既に使用されています。"
            )

        except ValidationError as e:
            db.rollback()
            print(f"パスワードが不正です: {str(e)}")
            create_error_logger(f"パスワードが不正です: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="パスワードが不正です。"
            )

        except SQLAlchemyError as e:
            db.rollback()
            print(f"データベースエラーが発生しました: {str(e)}")
            create_error_logger(f"データベースエラーが発生しました: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="データベースエラーが発生しました。"
            )

        except Exception as e:
            db.rollback()
            error_detail = traceback.format_exc()
            print(f"不明なエラーが発生しました: {error_detail}")
            create_error_logger(f"不明なエラーが発生しました: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="予期しないエラーが発生しました。"
            )

        finally:
            create_logger("DBセッションをクローズします")
            db.close()


@router.get(
    "/user/{id}",
    response_model=UserSchema,
    summary="User Show",
    description="ユーザー情報を表示するエンドポイント",
    )
async def show_user(
    id: int, db:
    Session = Depends(get_db)
    ) -> UserModel:
    """ユーザー情報を表示するエンドポイント

    :param id: ユーザーID
    :type id: int
    :param db: データベースセッション
    :type db: Session
    :return: ユーザー情報を含むSQLAlchemyモデル
    :rtype: UserModel
    :raises HTTPException: ユーザーが見つからない場合
    """
    user = db.query(UserModel).filter(UserModel.id == id).first()
    if not user:
        print(f"ユーザーが見つかりません。: {id}")
        create_error_logger(f"ユーザーが見つかりません。: {id}")
        raise HTTPException(
            status_code=404,
            detail="ユーザーが見つかりません。"
        )
    return user