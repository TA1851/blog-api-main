"""エンドポイントのルーティングを定義するモジュール"""
from typing import Optional, List
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
import urllib.parse
import markdown

from models import Article, User as UserModel
from schemas import ArticleBase, PublicArticle
from database import get_db
from oauth2 import get_current_user


# TODO:APIレスポンスの型定義
router = APIRouter(
    prefix="/api/v1",
    tags=["articles"],
)


@router.get(
    "/articles",
    status_code=status.HTTP_200_OK,
    response_model=List[ArticleBase]
)
async def all_fetch(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    limit: Optional[int] = Query(
        None, ge=1,
        description="取得する記事数（指定しない場合は全件取得）"
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

        query = db.query(Article).filter(Article.user_id == current_user.id)

        # 記事数を指定する場合
        if limit:
            user_blogs = query.limit(limit).all()
            print(
                f"ユーザーID: {current_user.id} のブログ記事を取得しました。 \
                全{total_count}件中{len(user_blogs)}件表示")
        else:
            # 全件取得
            user_blogs = query.all()
            print(
                f"ユーザーID: {current_user.id}  \
                のブログ記事を全件取得しました。全{total_count}件")
    except ValueError as e:
        print(f"ブログ記事の取得に失敗しました。")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Articles not found"
        )

    # 記事が見つからない場合は空のリストを返す
    if not user_blogs:
        print(
            f"ユーザーID: {current_user.id} のブログ記事が見つかりませんでした。"
            )
        return []

    # ログメッセージを条件によって変更
    if limit:
        print(
            f"ユーザーID: {current_user.id} のブログ記事 \
            {len(user_blogs)}件を取得しました。(制限: {limit}, 総数: {total_count})"
            )
    else:
        print(
            f"ユーザーID: {current_user.id} のブログ記事 \
            全{len(user_blogs)}件を取得しました。(総数: {total_count})"
            )

    return [
        ArticleBase(
            article_id=article.article_id,
            title=article.title,
            body=article.body,
            user_id=article.user_id
        ) for article in user_blogs
    ]


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
        print("指定したIDのブログ記事を取得しました。")
    except ValueError as e:
        print(f"指定したIDのブログ記事に失敗しました。")
        # エラー発生時に明示的な404を返す
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, \
            detail=f"Article not found {id}"
            )
    # 記事が見つからない場合は404エラーを返す
    if not id_blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, \
            detail=f"Article not found {id}"
            )
    return ArticleBase(
        article_id=id_blog.article_id,
        title=id_blog.title,
        body=id_blog.body,
        user_id=id_blog.user_id
    )

@router.post(
    "/articles"
    )
async def create_article(
    blog: ArticleBase,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
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
    # タイトルか本文が空だと400エラーを返す
    if blog.title is None or blog.title.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="タイトルは必須項目です"
        )
    if blog.body is None or blog.body.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="本文は必須項目です"
        )
    # 記事は自動採番する
    max_article_id = db.query(
        func.max(Article.article_id
                )).scalar() or 0
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
    return ArticleBase(
        article_id=new_blog.article_id,
        title=new_blog.title,
        body=new_blog.body,
        user_id=new_blog.user_id
    )


@router.post(
    "/articles",
    status_code=status.HTTP_201_CREATED,
    response_model=ArticleBase
)
async def update_article(
    article_id: int,
    blog: ArticleBase,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
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
        # ログインユーザーの記事を更新
        update_blog = db.query(Article).filter(
            Article.article_id == article_id,
            Article.user_id == current_user.id
        ).first()

        if not update_blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article not found \
                -> Article_id:{article_id}"
            )
        # タイトルと本文が空の場合は400エラーを返す
        if blog.title is None or blog.title.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="タイトルは必須項目です"
            )
        if blog.body is None or blog.body.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="本文は必須項目です"
            )
        update_blog.title = blog.title
        update_blog.body = blog.body
        db.commit()
        db.refresh(update_blog)
        print(
            f"記事を更新しました。article_id: {article_id}, \
            user_id: {current_user.id}")
    except ValueError as e:
        print(
            f"記事の更新に失敗しました。 \
            article_id: {article_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article not updated. article_id: {article_id}"
        )
    return ArticleBase(
        article_id=update_blog.article_id,
        title=update_blog.title,
        body=update_blog.body,
        user_id=update_blog.user_id
    )


@router.delete(
    "/articles",
    status_code=status.HTTP_200_OK
)
async def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
    ) -> dict:
    """記事を削除するエンドポイント

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
        print(f"記事を削除しました。article_id: {article_id}")
        print(f"記事を削除しました。article_id: {article_id}")
    except ValueError as e:
        print(
            f"記事の削除に失敗しました。article_id: {article_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article not deleted. article_id: {article_id}"
        )
    return None


@router.get(
    "/public/articles",
    status_code=status.HTTP_200_OK,
    response_model=List[PublicArticle]
)
async def get_public_articles(
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(
        None, ge=1,
        description="取得する記事数（指定しない場合は全件取得）"
    ),
    skip: Optional[int] = Query(
        0, ge=0,
        description="スキップする記事数（ページネーション用）"
    )
) -> List[PublicArticle]:
    """認証なしでパブリック記事を取得するエンドポイント

    :param db: データベースセッション

    :type db: Session

    :param limit: 取得する最大記事数

    :type limit: Optional[int]

    :param skip: スキップする記事数

    :type skip: Optional[int]

    :return: パブリック記事のリスト

    :rtype: List[PublicArticle]

    :raises HTTPException: データベースエラーが発生した場合
    """
    try:
        # 記事の総数を取得
        total_count = db.query(Article).count()
        # 記事ID順でソート
        query = db.query(Article).order_by(Article.article_id.desc())
        # skipが指定されている場合
        if skip:
            query = query.offset(skip)
        # limitが指定されている場合
        if limit:
            query = query.limit(limit)
        public_articles = query.all()
        # Markdown変換を行ってPublicArticleオブジェクトに変換
        md = markdown.Markdown(extensions=['nl2br'])
        result_articles = []
        for article in public_articles:
            body_html = md.convert(article.body)
            result_articles.append(PublicArticle(
                article_id=article.article_id,
                title=article.title,
                body_html=body_html
            ))
        if limit:
            print(
                f"パブリック記事を取得しました。 \
                全{total_count}件中{len(result_articles)}件表示 "
                f"(skip: {skip}, limit: {limit})"
            )
        else:
            print(
                f"パブリック記事を全件取得しました。 \
                全{total_count}件 (skip: {skip})"
            )
    except Exception as e:
        print(f"パブリック記事の取得に失敗しました: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="記事の取得に失敗しました"
        )
    return result_articles


@router.get(
    "/public/articles/search",
    status_code=status.HTTP_200_OK,
    response_model=List[PublicArticle]
)
async def search_public_articles(
    q: str = Query(..., min_length=1,
    description="検索キーワード（日本語対応）"),
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(
        10, ge=1, le=100,
        description="取得する最大記事数（デフォルト：10）"
    ),
    skip: Optional[int] = Query(
        0, ge=0,
        description="スキップする記事数（ページネーション用）"
    )
) -> List[PublicArticle]:
    """キーワードでパブリック記事を検索するエンドポイント（日本語対応）

    :param q: 検索キーワード（日本語・英語対応）

    :type q: str

    :param db: データベースセッション

    :type db: Session

    :param limit: 取得する最大記事数

    :type limit: Optional[int]

    :param skip: スキップする記事数

    :type skip: Optional[int]

    :return: 検索結果の記事リスト

    :rtype: List[PublicArticle]

    :raises HTTPException: データベースエラーが発生した場合
    """
    try:
        # URLデコードして日本語キーワードを正しく処理
        decoded_query = urllib.parse.unquote(q, encoding='utf-8')
        # 複数のキーワードに対応（スペース区切り）
        keywords = decoded_query.strip().split()
        query = db.query(Article)
        # 各キーワードでAND検索（タイトルまたは本文に含まれる）
        for keyword in keywords:
            search_filter = f"%{keyword}%"
            query = query.filter(
                or_(
                    Article.title.ilike(search_filter),
                    Article.body.ilike(search_filter)
                )
            )
        # 記事ID降順でソート
        query = query.order_by(Article.article_id.desc())
        # 検索結果の総数を取得
        total_count = query.count()
        # ページネーション適用
        if skip:
            query = query.offset(skip)
        query = query.limit(limit)
        search_results = query.all()
        # Markdown変換を行ってPublicArticleオブジェクトに変換
        md = markdown.Markdown(extensions=['nl2br'])
        result_articles = []
        for article in search_results:
            body_html = md.convert(article.body)
            result_articles.append(PublicArticle(
                article_id=article.article_id,
                title=article.title,
                body_html=body_html
            ))
        print(
            f"記事検索を実行しました。キーワード: '{decoded_query}' "
            f"(キーワード数: {len(keywords)}), "
            f"検索結果: {len(result_articles)}件/{total_count}件 "
            f"(skip: {skip}, limit: {limit})"
        )
    except Exception as e:
        print(f"記事検索に失敗しました。キーワード: '{q}', エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="記事検索に失敗しました"
        )
    return result_articles


@router.get(
    "/public/articles/{article_id}",
    status_code=status.HTTP_200_OK,
    response_model=PublicArticle
)
async def get_public_article_by_id(
    article_id: int,
    db: Session = Depends(get_db)
) -> PublicArticle:
    """指定されたIDのパブリック記事を取得するエンドポイント

    :param article_id: 取得する記事のID

    :type article_id: int

    :param db: データベースセッション

    :type db: Session

    :return: 指定されたIDの記事詳細

    :rtype: PublicArticle

    :raises HTTPException: 記事が見つからない場合や取得エラーが発生した場合
    """
    try:
        # 記事IDで記事を検索
        article = db.query(Article).filter \
        (Article.article_id == article_id).first()
        if not article:
            print(
                f"記事が見つかりません。ID: {article_id}"
                )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"記事ID {article_id} の記事が見つかりません"
            )
        # Markdown変換を行ってPublicArticleオブジェクトに変換
        md = markdown.Markdown(extensions=['nl2br'])
        body_html = md.convert(article.body)
        result_article = PublicArticle(
            article_id=article.article_id,
            title=article.title,
            body_html=body_html
        )
        print(
            f"記事詳細を取得しました。ID: {article_id}, \
            タイトル: {article.title}"
            )
    except Exception as e:
        print(
            f"記事詳細の取得に失敗しました。 \
            ID: {article_id}, エラー: {str(e)}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="記事詳細の取得に失敗しました"
        )
    return result_article