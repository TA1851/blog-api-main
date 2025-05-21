"""エンドポイントのルーティングを定義するモジュール"""
import pprint
from typing import Optional, List
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Article
from schemas import ArticleBase, ShowArticle, User
from database import session, db_env
from logger.custom_logger import create_logger, create_error_logger
from oauth2 import get_current_user


router = APIRouter(
    prefix="/api/v1",  # APIのバージョンを指定
    tags=["articles"],  # SwaggerUIのタグを指定
)


db_url = db_env.get("database_url")
key03 = db_env.get("file_id_03")
key07 = db_env.get("file_id_07")


def check_environment_variable():
    """環境変数を取得する

    :param key07: artile.pyの環境変数
    :type key07: str
    :return: 環境変数の値
    :rtype: str
    """
    if not key07:
        create_error_logger(f"環境変数:{key07}が設定されていません。{key07}")
        raise ValueError(f"環境変数が設定されていません。-> {key07}")
    else:
        print(f"STEP17：環境変数：{key07}を取得しました。 -> {key07}")
        create_logger(f"環境変数{key07}を取得しました。:")
    return key07

check_environment_variable()


def check_db_url():
    """データベースのURLを取得する

    :param db_url: データベースのURL
    :type db_url: str
    :return: データベースのURL
    :rtype: str
    """
    if not db_url:
        create_error_logger(f"環境変数:{db_url}が設定されていません。 -> {key03}")
        raise ValueError(f"環境変数が設定されていません。{key03}")
    else:
        print(f"STEP18：環境変数: {db_url}を読み込みました。")
    create_logger(f"環境変数: {db_url}を読み込みました。 -> {key03}")
    return db_url

check_db_url()
print("STEP19：ルートを取得しました。Swaggerを確認してください。")
print("---------------------------------------------------------------")


def get_db():
    """データベースセッションを取得する

    :return: データベースセッション
    :rtype: Session
    """
    db = session()
    try:
        yield db
        print("DBセッションをコミットしました")
        create_logger("DBセッションをコミットしました")
    except Exception as e:
        pprint.pprint(str(e))
        create_error_logger(f"DBセッションのコミットに失敗しました。: {str(e)}")
        raise
    finally:
        db.close()
        print("DBセッションをクローズしました")
        create_logger("DBセッションをクローズしました")


@router.get(
    "/articles",
    status_code=status.HTTP_200_OK,
    response_model=List[ArticleBase]
)
async def all_fetch(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), # 現在のユーザーを取得
    limit: Optional[int] = Query(
        None, ge=1,
        description="取得する最大記事数（指定しない場合は全件取得）"
        )
) -> List[ArticleBase]:
    """ログインユーザーが作成した記事のみを取得するエンドポイント

    :param db: データベースセッション
    :type db: Session
    :param current_user: 現在のユーザー
    :type current_user: User
    :param limit: 取得する最大記事数（指定しない場合は全件取得）
    :type limit: Optional[int]
    :return: 記事のリスト
    :rtype: List[ArticleBase]
    :raises HTTPException: 記事が見つからない場合
    :raises ValueError: データベースのクエリに失敗した場合
    """

    try:
        # 記事の総数を取得
        total_count = db.query(Article).filter(
            Article.user_id == current_user.id).count()

        # クエリ作成
        query = db.query(Article).filter(Article.user_id == current_user.id)

        # limitが指定されている場合のみ適用
        if limit:
            user_blogs = query.limit(limit).all()
            create_logger(
                f"ユーザーID: {current_user.id} のブログ記事を取得しました。 \
                全{total_count}件中{len(user_blogs)}件表示")
        else:
            # 制限なしで全件取得
            user_blogs = query.all()
            create_logger(
                f"ユーザーID: {current_user.id}  \
                のブログ記事を全件取得しました。全{total_count}件")
    except ValueError as e:
        pprint.pprint(str(e))
        create_error_logger(f"ブログ記事の取得に失敗しました。{key07}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Articles not found {key07}"
        )

    # 記事が見つからない場合は空のリストを返す
    if not user_blogs:
        print(f"ユーザーID: {current_user.id} の記事が見つかりませんでした")
        create_error_logger(
            f"ユーザーID: {current_user.id} のブログ記事が見つかりませんでした。"
            )
        return []

    # ログメッセージを条件によって変更
    if limit:
        print(
            f"ユーザーID: {current_user.id} のブログ記事 \
            {len(user_blogs)}件を取得しました。 \
            (制限: {limit}, 総数: {total_count})")
    else:
        print(
            f"ユーザーID: {current_user.id} のブログ記事 \
            全{len(user_blogs)}件を取得しました。(総数: {total_count})"
            )

    return user_blogs


@router.get(
    "/articles/{id}",
    status_code=status.HTTP_200_OK,
    response_model=ArticleBase
    )
async def get_article(
    id: int,
    db: Session = Depends(get_db)
    ) -> ArticleBase:
    """指定したIDのブログ記事を取得するエンドポイント

    :param id: 記事のID
    :type id: int
    :param db: データベースセッション
    :type db: Session
    :return: 記事の詳細
    :rtype: ArticleBase
    :raises HTTPException: 記事が見つからない場合
    """
    try:
        id_blog = db.query(Article).filter(Article.article_id == id).first()
        print(id_blog)
        create_logger("指定したIDのブログ記事を取得しました。")
    except ValueError as e:
        pprint.pprint(str(e))
        create_error_logger(f"指定したIDのブログ記事に失敗しました。{key07}")
        # エラー発生時に明示的な４０４を返す
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, \
            detail=f"Article not found {id}"
            )
    # id_blogがNoneの場合は、HTTPExceptionを発生させる
    if not id_blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, \
            detail=f"Article not found {id}"
            )
    return id_blog

@router.post(
    "/articles"
    )
async def create_article(
    blog: ArticleBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ) -> ArticleBase:
    """新しい記事を作成するエンドポイント

    :param blog: 記事の内容
    :type blog: ArticleBase
    :param db: データベースセッション
    :type db: Session
    :param current_user: 現在のユーザー
    :type current_user: User
    :return: 作成された記事
    :rtype: ArticleBase
    """
    # 自動採番処理
    max_article_id = db.query(func.max(Article.article_id)).scalar() or 0
    new_article_id = max_article_id + 1

    new_blog = Article(
        article_id=new_article_id,
        title=blog.title,
        body=blog.body,
        user_id=current_user.id
    )
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog

@router.put(
    "/articles",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ArticleBase
)
async def update_article(
    article_id: int,
    blog: ArticleBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ) -> ArticleBase:
    """指定したIDの記事を更新するエンドポイント

    :param article_id: 記事のID
    :type article_id: int
    :param blog: 更新する記事の内容
    :type blog: ArticleBase
    :param db: データベースセッション
    :type db: Session
    :param current_user: 現在のユーザー
    :type current_user: User
    :return: 更新された記事
    :rtype: ArticleBase
    :raises HTTPException: 記事が見つからない場合
    :raises ValueError: データベースのクエリに失敗した場合
    """
    try:
        # article_idとuser_idでフィルタリングして記事を取得(ログインユーザーの記事を更新)
        update_blog = db.query(Article).filter(
            Article.article_id == article_id,
            Article.user_id == current_user.id
        ).first()

        if not update_blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article not found or you do not have permission \
                -> Article_id:{article_id}"
            )
        # 記事の内容を更新
        update_blog.title = blog.title
        update_blog.body = blog.body

        # DBに反映
        db.commit()
        db.refresh(update_blog)

        print(f"記事を更新しました。article_id: {article_id}, {key07}")
        create_logger(
            f"記事を更新しました。article_id: {article_id}, \
            user_id: {current_user.id}, {key07}")

    except ValueError as e:
        pprint.pprint(str(e))
        create_error_logger(
            f"記事の更新に失敗しました。 \
            article_id: {article_id}, {key07}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article not updated. article_id: {article_id}, {key07}"
        )
    return update_blog

@router.delete(
    "/articles",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ) -> None:
    """指定したIDの記事を削除するエンドポイント

    :param article_id: 記事のID
    :type article_id: int
    :param db: データベースセッション
    :type db: Session
    :param current_user: 現在のユーザー
    :type current_user: User
    :return: None
    """
    try:
        delete_blog = db.query(Article).filter(
            Article.article_id == article_id,
            Article.user_id == current_user.id
        ).first()
        if not delete_blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article not found or you do not have permission \
                -> Article_id:{article_id}"
            )
        db.delete(delete_blog)
        db.commit()
        print(f"記事を削除しました。article_id: {article_id}, {key07}")
        create_logger(f"記事を削除しました。article_id: {article_id}, {key07}")
    except ValueError as e:
        pprint.pprint(str(e))
        create_error_logger(f"記事の削除に失敗しました。article_id: {article_id}, {key07}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article not deleted. article_id: {article_id}, {key07}"
        )
    return None