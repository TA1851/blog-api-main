#!/usr/bin/env python3
"""
テストユーザー作成スクリプト

このスクリプトは動作確認用のテストユーザーを直接データベースに作成します。
本番環境では使用しないでください。
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User as UserModel, Base
from hashing import Hash


def create_test_user():
    """テストユーザーを作成する関数"""
    
    # データベースURL取得
    database_url = os.getenv("POSGRE_URL")
    
    # SQLAlchemyエンジンとセッション作成
    engine = create_engine(database_url)
    
    # テーブルが存在しない場合は作成
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # テストユーザーの情報
        test_email = "testuser@example.com"
        test_password = "testuser"  # 平文パスワード
        test_name = "Test User"
        
        print(f"テストユーザー作成開始: {test_email}")
        
        # 既存のユーザーをチェック
        existing_user = session.query(UserModel).filter(
            UserModel.email == test_email
        ).first()
        
        if existing_user:
            print(f"テストユーザーは既に存在します: {test_email}")
            print(f"ユーザーID: {existing_user.id}")
            print(f"名前: {existing_user.name}")
            print(f"アクティブ: {existing_user.is_active}")
            return existing_user
        
        # パスワードをハッシュ化
        hashed_password = Hash.bcrypt(test_password)
        print(f"パスワードをハッシュ化しました")
        
        # テストユーザーを作成
        test_user = UserModel(
            name=test_name,
            email=test_email,
            password=hashed_password,
            is_active=True
        )
        
        # データベースに保存
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        
        print(f"✅ テストユーザーを作成しました:")
        print(f"   ID: {test_user.id}")
        print(f"   名前: {test_user.name}")
        print(f"   メール: {test_user.email}")
        print(f"   アクティブ: {test_user.is_active}")
        print(f"   ログイン用パスワード: {test_password}")
        print()
        print("ログインテスト用cURLコマンド:")
        print(f"curl -X 'POST' \\")
        print(f"  'http://localhost:8000/api/v1/login' \\")
        print(f"  -H 'Content-Type: application/x-www-form-urlencoded' \\")
        print(f"  -d 'grant_type=password&username={test_email}&password={test_password}'")
        
        return test_user
        
    except Exception as e:
        session.rollback()
        print(f"❌ エラーが発生しました: {str(e)}")
        raise
    finally:
        session.close()


def delete_test_user():
    """テストユーザーを削除する関数"""
    
    # データベースURL取得
    database_url = os.getenv("DATABASE_URL", "sqlite:///./blog.db")
    
    # SQLAlchemyエンジンとセッション作成
    engine = create_engine(database_url)
    
    # テーブルが存在しない場合は作成
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        test_email = "testuser@example.com"
        
        # テストユーザーを検索
        test_user = session.query(UserModel).filter(
            UserModel.email == test_email
        ).first()
        
        if not test_user:
            print(f"テストユーザーが見つかりません: {test_email}")
            return
        
        # テストユーザーを削除
        session.delete(test_user)
        session.commit()
        
        print(f"✅ テストユーザーを削除しました: {test_email}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ エラーが発生しました: {str(e)}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "delete":
        delete_test_user()
    else:
        create_test_user()
