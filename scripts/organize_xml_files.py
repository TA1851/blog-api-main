#!/usr/bin/env python3
"""
XMLファイル自動整理スクリプト

このスクリプトは以下の処理を行います：
1. ルートディレクトリの新しいXMLファイルを検出
2. ファイル名と内容に基づいて適切なディレクトリに移動
3. 古いアーカイブファイルの自動削除（30日以上）
"""

import os
import shutil
import re
from datetime import datetime, timedelta
from pathlib import Path

class XMLOrganizer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.test_results_dir = self.project_root / "test_results"
        self.test_archives_dir = self.project_root / "test_archives" / "xml_archive"
        self.current_dir = self.test_results_dir / "current"
        self.coverage_dir = self.test_results_dir / "coverage"
        self.component_dir = self.test_archives_dir / "component_tests"
        
    def setup_directories(self):
        """必要なディレクトリを作成"""
        for directory in [self.current_dir, self.coverage_dir, self.component_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def categorize_xml_file(self, file_path: Path) -> str:
        """XMLファイルをカテゴリ分けする"""
        filename = file_path.name.lower()
        
        # カバレッジレポート
        if 'coverage' in filename:
            return 'coverage'
        
        # 最新テスト結果（main, comprehensive, latest等のキーワード）
        if any(keyword in filename for keyword in ['main', 'comprehensive', 'latest', 'current']):
            return 'current'
        
        # コンポーネントテスト
        if any(keyword in filename for keyword in ['email', 'validator', 'sender', 'component']):
            return 'component'
        
        # その他はアーカイブ
        return 'archive'
    
    def organize_new_xml_files(self):
        """ルートディレクトリの新しいXMLファイルを整理"""
        xml_files = list(self.project_root.glob("*.xml"))
        
        if not xml_files:
            print("整理するXMLファイルが見つかりません。")
            return
        
        print(f"{len(xml_files)}個のXMLファイルを整理します...")
        
        for xml_file in xml_files:
            category = self.categorize_xml_file(xml_file)
            
            if category == 'coverage':
                destination = self.coverage_dir
            elif category == 'current':
                destination = self.current_dir
            elif category == 'component':
                destination = self.component_dir
            else:
                destination = self.test_archives_dir
            
            try:
                new_path = destination / xml_file.name
                shutil.move(str(xml_file), str(new_path))
                print(f"移動: {xml_file.name} → {destination.relative_to(self.project_root)}/")
            except Exception as e:
                print(f"エラー: {xml_file.name}の移動に失敗 - {e}")
    
    def cleanup_old_archives(self, days_old: int = 30):
        """古いアーカイブファイルを削除"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_count = 0
        
        for xml_file in self.test_archives_dir.rglob("*.xml"):
            try:
                file_time = datetime.fromtimestamp(xml_file.stat().st_mtime)
                if file_time < cutoff_date:
                    xml_file.unlink()
                    print(f"削除: {xml_file.relative_to(self.project_root)}")
                    deleted_count += 1
            except Exception as e:
                print(f"エラー: {xml_file.name}の削除に失敗 - {e}")
        
        if deleted_count > 0:
            print(f"{deleted_count}個の古いファイルを削除しました。")
        else:
            print("削除対象の古いファイルはありませんでした。")
    
    def generate_summary_report(self):
        """現在の状況サマリーを生成"""
        print("\n=== XMLファイル整理サマリー ===")
        
        categories = {
            "現在のテスト結果": self.current_dir,
            "カバレッジレポート": self.coverage_dir,
            "コンポーネントテスト": self.component_dir,
            "アーカイブ": self.test_archives_dir
        }
        
        for category_name, directory in categories.items():
            if directory.exists():
                xml_count = len(list(directory.glob("*.xml")))
                print(f"{category_name}: {xml_count}ファイル")
            else:
                print(f"{category_name}: ディレクトリなし")
        
        # ルートディレクトリの確認
        root_xml_count = len(list(self.project_root.glob("*.xml")))
        print(f"ルートディレクトリ: {root_xml_count}ファイル")

def main():
    """メイン実行関数"""
    import sys
    
    # プロジェクトルートを取得
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        # スクリプトの親ディレクトリをプロジェクトルートとして使用
        project_root = Path(__file__).parent.parent
    
    organizer = XMLOrganizer(project_root)
    organizer.setup_directories()
    
    print("XMLファイル自動整理を開始します...")
    organizer.organize_new_xml_files()
    
    # 古いファイルの削除（オプション）
    cleanup = input("30日以上古いアーカイブファイルを削除しますか？ (y/N): ")
    if cleanup.lower() == 'y':
        organizer.cleanup_old_archives(30)
    
    organizer.generate_summary_report()
    print("整理が完了しました！")

if __name__ == "__main__":
    main()
