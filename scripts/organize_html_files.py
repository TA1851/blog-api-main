#!/usr/bin/env python3
"""
HTMLファイル自動整理スクリプト

このスクリプトは以下の処理を行います：
1. ルートディレクトリの新しいHTMLファイルを検出
2. ファイル名と内容に基づいて適切なディレクトリに移動
3. 古いHTMLレポートの自動アーカイブ
4. HTMLカバレッジディレクトリの整理
"""

import os
import shutil
import re
from datetime import datetime, timedelta
from pathlib import Path

class HTMLOrganizer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.reports_dir = self.project_root / "reports"
        self.test_results_dir = self.reports_dir / "test_results"
        self.bug_reports_dir = self.reports_dir / "bug_reports"
        self.coverage_current_dir = self.reports_dir / "coverage_html" / "current"
        self.coverage_archived_dir = self.reports_dir / "coverage_html" / "archived"
        
    def setup_directories(self):
        """必要なディレクトリを作成"""
        for directory in [
            self.test_results_dir, 
            self.bug_reports_dir, 
            self.coverage_current_dir, 
            self.coverage_archived_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def categorize_html_file(self, file_path: Path) -> str:
        """HTMLファイルをカテゴリ分けする"""
        filename = file_path.name.lower()
        
        # バグレポート
        if any(keyword in filename for keyword in ['bug_report', 'bug_tracking']):
            return 'bug_reports'
        
        # テスト結果
        if 'test_results' in filename:
            return 'test_results'
        
        # カバレッジレポート（単体ファイルの場合）
        if 'coverage' in filename and filename.endswith('.html'):
            return 'coverage_file'
        
        # その他のHTMLファイル
        return 'other'
    
    def organize_html_files(self):
        """ルートディレクトリの新しいHTMLファイルを整理"""
        html_files = list(self.project_root.glob("*.html"))
        
        if not html_files:
            print("整理するHTMLファイルが見つかりません。")
            return
        
        print(f"{len(html_files)}個のHTMLファイルを整理します...")
        
        for html_file in html_files:
            category = self.categorize_html_file(html_file)
            
            if category == 'bug_reports':
                destination = self.bug_reports_dir
            elif category == 'test_results':
                destination = self.test_results_dir
            elif category == 'coverage_file':
                destination = self.coverage_current_dir
            else:
                # その他はtest_resultsに分類
                destination = self.test_results_dir
            
            try:
                new_path = destination / html_file.name
                shutil.move(str(html_file), str(new_path))
                print(f"移動: {html_file.name} → {destination.relative_to(self.project_root)}/")
            except Exception as e:
                print(f"エラー: {html_file.name}の移動に失敗 - {e}")
    
    def organize_coverage_directories(self):
        """HTMLカバレッジディレクトリを整理"""
        # ルートディレクトリのhtmlcovディレクトリを探す
        htmlcov_dirs = list(self.project_root.glob("htmlcov*"))
        
        for htmlcov_dir in htmlcov_dirs:
            if htmlcov_dir.is_dir():
                # ディレクトリ名から適切な名前を生成
                if htmlcov_dir.name == "htmlcov":
                    new_name = "main_coverage"
                    destination = self.coverage_current_dir
                else:
                    # htmlcov_auth_final -> auth_final_coverage
                    new_name = htmlcov_dir.name.replace("htmlcov_", "") + "_coverage"
                    destination = self.coverage_current_dir
                
                try:
                    new_path = destination / new_name
                    if new_path.exists():
                        # 既存の場合はアーカイブに移動
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        archive_path = self.coverage_archived_dir / f"{new_name}_{timestamp}"
                        shutil.move(str(new_path), str(archive_path))
                        print(f"既存ディレクトリをアーカイブ: {archive_path.relative_to(self.project_root)}")
                    
                    shutil.move(str(htmlcov_dir), str(new_path))
                    print(f"移動: {htmlcov_dir.name} → {new_path.relative_to(self.project_root)}")
                except Exception as e:
                    print(f"エラー: {htmlcov_dir.name}の移動に失敗 - {e}")
        
        # testsディレクトリ内のhtmlcovディレクトリも確認
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            test_htmlcov_dirs = list(tests_dir.glob("htmlcov*"))
            
            for htmlcov_dir in test_htmlcov_dirs:
                if htmlcov_dir.is_dir():
                    if htmlcov_dir.name == "htmlcov":
                        new_name = "tests_coverage"
                        destination = self.coverage_archived_dir
                    else:
                        new_name = htmlcov_dir.name.replace("htmlcov_", "") + "_coverage"
                        # testsディレクトリのものは基本的にアーカイブ
                        destination = self.coverage_archived_dir
                    
                    try:
                        new_path = destination / new_name
                        if new_path.exists():
                            shutil.rmtree(new_path)
                        
                        shutil.move(str(htmlcov_dir), str(new_path))
                        print(f"移動: tests/{htmlcov_dir.name} → {new_path.relative_to(self.project_root)}")
                    except Exception as e:
                        print(f"エラー: tests/{htmlcov_dir.name}の移動に失敗 - {e}")
    
    def cleanup_old_reports(self, days_old: int = 30):
        """古いHTMLレポートを削除"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_count = 0
        
        # アーカイブディレクトリの古いファイルを削除
        for html_file in self.coverage_archived_dir.rglob("*.html"):
            try:
                file_time = datetime.fromtimestamp(html_file.stat().st_mtime)
                if file_time < cutoff_date:
                    # ディレクトリ全体を削除
                    parent_dir = html_file.parent
                    if parent_dir != self.coverage_archived_dir:
                        shutil.rmtree(parent_dir)
                        print(f"削除: {parent_dir.relative_to(self.project_root)}")
                        deleted_count += 1
                        break
            except Exception as e:
                print(f"エラー: {html_file.name}の削除に失敗 - {e}")
        
        if deleted_count > 0:
            print(f"{deleted_count}個の古いカバレッジディレクトリを削除しました。")
        else:
            print("削除対象の古いディレクトリはありませんでした。")
    
    def generate_index_html(self):
        """メインのインデックスHTMLページを生成"""
        index_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog API - レポートダッシュボード</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 0 20px rgba(0,0,0,0.1); 
        }
        h1 { 
            color: #333; 
            text-align: center; 
            border-bottom: 3px solid #007acc; 
            padding-bottom: 10px; 
        }
        .section { 
            margin: 30px 0; 
            padding: 20px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            background-color: #fafafa; 
        }
        .section h2 { 
            color: #007acc; 
            margin-top: 0; 
        }
        .file-list { 
            list-style: none; 
            padding: 0; 
        }
        .file-list li { 
            margin: 10px 0; 
            padding: 10px; 
            background: white; 
            border-radius: 3px; 
            border-left: 4px solid #007acc; 
        }
        .file-list a { 
            text-decoration: none; 
            color: #333; 
            font-weight: 500; 
        }
        .file-list a:hover { 
            color: #007acc; 
        }
        .stats { 
            display: flex; 
            justify-content: space-around; 
            margin: 20px 0; 
        }
        .stat { 
            text-align: center; 
            padding: 15px; 
            background: #007acc; 
            color: white; 
            border-radius: 5px; 
            min-width: 120px; 
        }
        .stat-number { 
            font-size: 2em; 
            font-weight: bold; 
        }
        .stat-label { 
            font-size: 0.9em; 
        }
        .timestamp { 
            text-align: center; 
            color: #666; 
            font-style: italic; 
            margin-top: 30px; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Blog API レポートダッシュボード</h1>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number" id="test-count">-</div>
                <div class="stat-label">テストレポート</div>
            </div>
            <div class="stat">
                <div class="stat-number" id="bug-count">-</div>
                <div class="stat-label">バグレポート</div>
            </div>
            <div class="stat">
                <div class="stat-number" id="coverage-count">-</div>
                <div class="stat-label">カバレッジレポート</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 テスト結果レポート</h2>
            <ul class="file-list" id="test-results">
                <li>読み込み中...</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>🐛 バグトラッキングレポート</h2>
            <ul class="file-list" id="bug-reports">
                <li>読み込み中...</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>📈 カバレッジレポート (最新)</h2>
            <ul class="file-list" id="coverage-current">
                <li>読み込み中...</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>📦 カバレッジレポート (アーカイブ)</h2>
            <ul class="file-list" id="coverage-archived">
                <li>読み込み中...</li>
            </ul>
        </div>
        
        <div class="timestamp">
            最終更新: <span id="timestamp"></span>
        </div>
    </div>
    
    <script>
        // タイムスタンプを設定
        document.getElementById('timestamp').textContent = new Date().toLocaleString('ja-JP');
        
        // 統計を更新（実際の実装では動的に取得）
        document.getElementById('test-count').textContent = '4';
        document.getElementById('bug-count').textContent = '4';
        document.getElementById('coverage-count').textContent = '6';
        
        // ファイルリストを更新（実際の実装では動的に取得）
        function updateFileList(elementId, files) {
            const element = document.getElementById(elementId);
            if (files.length === 0) {
                element.innerHTML = '<li>ファイルがありません</li>';
                return;
            }
            
            element.innerHTML = files.map(file => 
                `<li><a href="${file.path}" target="_blank">${file.name}</a></li>`
            ).join('');
        }
        
        // サンプルデータ（実際の実装では動的に取得）
        setTimeout(() => {
            updateFileList('test-results', [
                {name: 'メインテスト結果', path: 'test_results/test_results_main.html'},
                {name: '認証ルーターテスト', path: 'test_results/test_results_auth_router_final.html'},
                {name: '記事ルーターテスト', path: 'test_results/test_results_with_article_router.html'}
            ]);
            
            updateFileList('bug-reports', [
                {name: '包括的バグトラッキング', path: 'bug_reports/comprehensive_bug_tracking_report.html'},
                {name: '最新バグレポート', path: 'bug_reports/bug_report_latest.html'}
            ]);
            
            updateFileList('coverage-current', [
                {name: 'メインカバレッジ', path: 'coverage_html/current/main_coverage/index.html'},
                {name: '完全カバレッジ', path: 'coverage_html/current/full_coverage/index.html'}
            ]);
            
            updateFileList('coverage-archived', [
                {name: 'ユーザールーターカバレッジ', path: 'coverage_html/archived/user_router_coverage/index.html'}
            ]);
        }, 500);
    </script>
</body>
</html>"""
        
        index_path = self.reports_dir / "index.html"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"ダッシュボードを作成: {index_path.relative_to(self.project_root)}")
    
    def generate_summary_report(self):
        """現在の状況サマリーを生成"""
        print("\n=== HTMLファイル整理サマリー ===")
        
        categories = {
            "テスト結果": self.test_results_dir,
            "バグレポート": self.bug_reports_dir,
            "カバレッジ(最新)": self.coverage_current_dir,
            "カバレッジ(アーカイブ)": self.coverage_archived_dir
        }
        
        total_files = 0
        for category_name, directory in categories.items():
            if directory.exists():
                html_count = len(list(directory.rglob("*.html")))
                dir_count = len([d for d in directory.iterdir() if d.is_dir()])
                print(f"{category_name}: {html_count}ファイル, {dir_count}ディレクトリ")
                total_files += html_count
            else:
                print(f"{category_name}: ディレクトリなし")
        
        # ルートディレクトリの確認
        root_html_count = len(list(self.project_root.glob("*.html")))
        print(f"ルートディレクトリ: {root_html_count}ファイル")
        
        print(f"\n総HTML管理ファイル数: {total_files}ファイル")

def main():
    """メイン実行関数"""
    import sys
    
    # プロジェクトルートを取得
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        # スクリプトの親ディレクトリをプロジェクトルートとして使用
        project_root = Path(__file__).parent.parent
    
    organizer = HTMLOrganizer(project_root)
    organizer.setup_directories()
    
    print("HTMLファイル自動整理を開始します...")
    organizer.organize_html_files()
    organizer.organize_coverage_directories()
    
    # インデックスページの生成
    organizer.generate_index_html()
    
    # 古いファイルの削除（オプション）
    cleanup = input("30日以上古いアーカイブレポートを削除しますか？ (y/N): ")
    if cleanup.lower() == 'y':
        organizer.cleanup_old_reports(30)
    
    organizer.generate_summary_report()
    print("整理が完了しました！")
    print(f"ダッシュボード: reports/index.html")

if __name__ == "__main__":
    main()
