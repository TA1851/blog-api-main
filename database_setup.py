#!/usr/bin/env python3
"""
データベース初期化・マイグレーションスクリプト

このスクリプトは以下の処理を行います：
1. 環境に応じたデータベース接続
2. テーブルの作成
3. 初期データの投入（オプション）

使用方法:
  python database_setup.py [--environment development|production] [--init-data]
"""

import argparse
import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database import Base, engine, db_env
from models import Article, User
from sqlalchemy.orm import sessionmaker
from logger.custom_logger import create_logger, create_error_logger


def create_tables():
    """全テーブルを作成"""
    try:
        Base.metadata.create_all(bind=engine)
        create_logger("テーブルの作成が完了しました")
        print("✅ テーブルの作成が完了しました")
        return True
    except Exception as e:
        create_error_logger(f"テーブル作成に失敗しました: {str(e)}")
        print(f"❌ テーブル作成に失敗しました: {str(e)}")
        return False


def insert_sample_data():
    """サンプルデータを挿入"""
    try:
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # 既存データをチェック
        existing_articles = db.query(Article).count()
        if existing_articles > 0:
            print(f"⚠️  既に {existing_articles} 件の記事が存在します。サンプルデータの挿入をスキップします。")
            return True
        
        # サンプル記事データ
        sample_articles = [
            {
                "title": "FastAPI入門",
                "body": "# FastAPI入門\n\nFastAPIは高速でモダンなWebフレームワークです。\n\n## 特徴\n- 高速な実行速度\n- 自動ドキュメント生成\n- 型ヒントサポート\n\n始めてみましょう！",
                "user_id": 1
            },
            {
                "title": "PostgreSQL vs SQLite",
                "body": "# データベース比較\n\n## SQLite\n- 軽量\n- ファイルベース\n- 開発環境に最適\n\n## PostgreSQL\n- 高機能\n- スケーラブル\n- 本番環境に最適\n\n用途に応じて選択しましょう。",
                "user_id": 1
            },
            {
                "title": "Renderでのデプロイ",
                "body": "# Renderデプロイガイド\n\nRenderを使ったアプリケーションのデプロイ方法を説明します。\n\n## 手順\n1. Gitリポジトリの準備\n2. Renderアカウント作成\n3. サービスの設定\n4. 環境変数の設定\n\n簡単にデプロイできます！",
                "user_id": 1
            }
        ]
        
        # 記事を挿入
        for article_data in sample_articles:
            article = Article(**article_data)
            db.add(article)
        
        db.commit()
        create_logger(f"サンプルデータ（{len(sample_articles)}件）を挿入しました")
        print(f"✅ サンプルデータ（{len(sample_articles)}件）を挿入しました")
        
        db.close()
        return True
        
    except Exception as e:
        create_error_logger(f"サンプルデータ挿入に失敗しました: {str(e)}")
        print(f"❌ サンプルデータ挿入に失敗しました: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="データベース初期化スクリプト")
    parser.add_argument(
        "--environment", 
        choices=["development", "production"], 
        default="development",
        help="実行環境を指定（デフォルト: development）"
    )
    parser.add_argument(
        "--init-data", 
        action="store_true", 
        help="サンプルデータを挿入"
    )
    
    args = parser.parse_args()
    
    # 環境情報を表示
    current_env = db_env.get("environment", "development")
    print(f"🌟 データベース初期化を開始します")
    print(f"📊 現在の環境: {current_env}")
    print(f"🔗 データベースURL: {db_env.get('database_url', '未設定')}")
    print("-" * 50)
    
    # テーブル作成
    print("1️⃣ テーブルを作成中...")
    if not create_tables():
        sys.exit(1)
    
    # サンプルデータ挿入（オプション）
    if args.init_data:
        print("2️⃣ サンプルデータを挿入中...")
        if not insert_sample_data():
            sys.exit(1)
    
    print("-" * 50)
    print("🎉 データベース初期化が完了しました！")
    
    if current_env == "development":
        print("\n🚀 開発サーバーを起動するには:")
        print("   uvicorn main:app --reload --port 8000")
    else:
        print("\n🌐 本番環境での実行準備が完了しました")


if __name__ == "__main__":
    main()
