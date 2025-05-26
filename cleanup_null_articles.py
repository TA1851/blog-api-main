#!/usr/bin/env python
"""NULL値を持つ記事を削除するクリーンアップスクリプト"""
import sys
from sqlalchemy.orm import Session
from models import Article
from database import session

def cleanup_null_articles():
    """タイトルまたは本文がNULLの記事を削除する"""
    db = session()
    try:
        # NULLタイトルまたは本文を持つ記事を検索
        null_articles = db.query(Article).filter(
            (Article.title.is_(None)) | 
            (Article.body.is_(None)) |
            (Article.title == '') |
            (Article.body == '')
        ).all()
        
        if not null_articles:
            print("NULL値を持つ記事は見つかりませんでした。")
            return
        
        print(f"{len(null_articles)}件のNULL値を持つ記事が見つかりました。削除を開始します...")
        
        for article in null_articles:
            print(f"削除: ID={article.article_id}, タイトル={article.title}, ユーザーID={article.user_id}")
            db.delete(article)
        
        db.commit()
        print("クリーンアップが完了しました。")
    except Exception as e:
        db.rollback()
        print(f"エラーが発生しました: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_null_articles()
