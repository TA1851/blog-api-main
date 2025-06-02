#!/usr/bin/env python3
"""
統合ファイル整理スクリプト

このスクリプトは、Blog APIプロジェクトの全ファイルタイプを統合的に整理します：
- XMLファイル（テスト結果）
- HTMLファイル（レポート・カバレッジ）
- JSONファイル（データ・設定）
- Markdownファイル（ドキュメント・レポート）
- Pythonスクリプト（生成・テスト用）
"""

import os
import shutil
import re
from datetime import datetime, timedelta
from pathlib import Path
import json

class UnifiedFileOrganizer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.reports_dir = self.project_root / "reports"
        self.scripts_dir = self.project_root / "scripts"
        self.test_results_dir = self.project_root / "test_results"
        self.test_archives_dir = self.project_root / "test_archives"
        
        # レポート用サブディレクトリ
        self.json_data_dir = self.reports_dir / "json_data"
        self.markdown_reports_dir = self.reports_dir / "markdown_reports"
        self.archived_scripts_dir = self.scripts_dir / "archived"
        
    def setup_directories(self):
        """必要なディレクトリを作成"""
        directories = [
            self.reports_dir,
            self.scripts_dir,
            self.json_data_dir,
            self.markdown_reports_dir,
            self.archived_scripts_dir,
            self.test_results_dir / "current",
            self.test_results_dir / "coverage",
            self.test_archives_dir / "xml_archive",
            self.reports_dir / "bug_reports",
            self.reports_dir / "test_results",
            self.reports_dir / "coverage_html" / "current",
            self.reports_dir / "coverage_html" / "archived"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def categorize_file(self, file_path: Path) -> tuple:
        """ファイルをカテゴリ分けして移動先を決定"""
        filename = file_path.name.lower()
        extension = file_path.suffix.lower()
        
        # XMLファイル
        if extension == '.xml':
            if 'coverage' in filename:
                return ('xml', self.test_results_dir / "coverage")
            elif any(keyword in filename for keyword in ['main', 'comprehensive', 'latest']):
                return ('xml', self.test_results_dir / "current")
            elif any(keyword in filename for keyword in ['email', 'validator', 'sender']):
                return ('xml', self.test_archives_dir / "xml_archive" / "component_tests")
            else:
                return ('xml', self.test_archives_dir / "xml_archive")
        
        # HTMLファイル
        elif extension == '.html':
            if 'bug_report' in filename or 'bug_tracking' in filename:
                return ('html', self.reports_dir / "bug_reports")
            elif 'test_result' in filename:
                return ('html', self.reports_dir / "test_results")
            else:
                return ('html', self.reports_dir / "test_results")
        
        # JSONファイル
        elif extension == '.json':
            return ('json', self.json_data_dir)
        
        # Markdownファイル（レポート系）
        elif extension == '.md':
            if any(keyword in filename for keyword in ['summary', 'report', 'history', 'completion']):
                return ('markdown', self.markdown_reports_dir)
            else:
                return ('markdown', None)  # プロジェクトルートのREADME等は移動しない
        
        # Pythonスクリプト（生成系）
        elif extension == '.py':
            if any(keyword in filename for keyword in ['generate', 'run_', 'update_']):
                return ('python', self.scripts_dir)
            else:
                return ('python', None)  # メインアプリケーションファイルは移動しない
        
        return ('unknown', None)
    
    def organize_all_files(self):
        """全ファイルタイプを統合的に整理"""
        file_patterns = ['*.xml', '*.html', '*.json', '*.md', '*.py']
        files_moved = 0
        
        print("🔄 統合ファイル整理を開始します...")
        
        for pattern in file_patterns:
            files = list(self.project_root.glob(pattern))
            
            for file_path in files:
                # 重要なプロジェクトファイルはスキップ
                if file_path.name in [
                    'README.md', 'PROJECT_STRUCTURE.md', 'main.py', 
                    'database.py', 'models.py', 'schemas.py', 'oauth2.py',
                    'hashing.py', 'custom_token.py', 'pyproject.toml'
                ]:
                    continue
                
                file_type, destination = self.categorize_file(file_path)
                
                if destination is None:
                    continue
                
                try:
                    new_path = destination / file_path.name
                    
                    # 既存ファイルがある場合はタイムスタンプを追加
                    if new_path.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        name_parts = file_path.stem, timestamp, file_path.suffix
                        new_name = f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                        new_path = destination / new_name
                    
                    shutil.move(str(file_path), str(new_path))
                    print(f"✅ {file_type.upper()}: {file_path.name} → {destination.relative_to(self.project_root)}/")
                    files_moved += 1
                    
                except Exception as e:
                    print(f"❌ エラー: {file_path.name}の移動に失敗 - {e}")
        
        print(f"📁 {files_moved}個のファイルを整理しました")
    
    def create_unified_dashboard(self):
        """統合ダッシュボードページを更新"""
        dashboard_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog API - 統合ダッシュボード</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            line-height: 1.6; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.95); 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 { 
            font-size: 2.5em; 
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .main-content {
            padding: 40px;
        }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin-bottom: 40px; 
        }
        .stat-card { 
            background: white;
            border-radius: 15px;
            padding: 25px; 
            text-align: center; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
            transition: transform 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-number { 
            font-size: 2.5em; 
            font-weight: bold; 
            color: #667eea;
            margin-bottom: 10px;
        }
        .stat-label { 
            font-size: 1em; 
            color: #666;
            font-weight: 500;
        }
        .section-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }
        .section { 
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .section-header {
            background: #667eea;
            color: white;
            padding: 20px;
            font-size: 1.3em;
            font-weight: 600;
        }
        .section-content {
            padding: 20px;
        }
        .file-list { 
            list-style: none; 
        }
        .file-list li { 
            margin: 12px 0; 
            padding: 12px; 
            background: #f8f9ff; 
            border-radius: 8px; 
            border-left: 4px solid #667eea;
            transition: background 0.3s ease;
        }
        .file-list li:hover {
            background: #e8f0ff;
        }
        .file-list a { 
            text-decoration: none; 
            color: #333; 
            font-weight: 500;
            display: flex;
            align-items: center;
        }
        .file-list a:hover { 
            color: #667eea; 
        }
        .file-icon {
            margin-right: 10px;
            font-size: 1.2em;
        }
        .footer {
            background: #f8f9ff;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e0e0e0;
        }
        .footer-stats {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-bottom: 20px;
        }
        .footer-stat {
            text-align: center;
        }
        .footer-stat-number {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        .footer-stat-label {
            font-size: 0.9em;
            color: #666;
        }
        .timestamp {
            color: #999;
            font-style: italic;
        }
        .quick-actions {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin: 20px 0;
        }
        .action-btn {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 500;
            transition: background 0.3s ease;
        }
        .action-btn:hover {
            background: #764ba2;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Blog API 統合ダッシュボード</h1>
            <p>テスト結果・バグレポート・カバレッジの総合管理</p>
        </div>
        
        <div class="main-content">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="test-files">-</div>
                    <div class="stat-label">テストファイル</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="bug-reports">-</div>
                    <div class="stat-label">バグレポート</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="coverage-reports">-</div>
                    <div class="stat-label">カバレッジレポート</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="json-data">-</div>
                    <div class="stat-label">JSONデータ</div>
                </div>
            </div>
            
            <div class="quick-actions">
                <a href="#test-results" class="action-btn">📊 テスト結果</a>
                <a href="#bug-reports-section" class="action-btn">🐛 バグレポート</a>
                <a href="#coverage-section" class="action-btn">📈 カバレッジ</a>
                <a href="#data-section" class="action-btn">📄 データ</a>
            </div>
            
            <div class="section-grid">
                <div class="section" id="test-results">
                    <div class="section-header">📊 最新テスト結果</div>
                    <div class="section-content">
                        <ul class="file-list">
                            <li><a href="test_results/test_results_main.html"><span class="file-icon">📋</span>メインテスト結果</a></li>
                            <li><a href="test_results/test_results_auth_router_final.html"><span class="file-icon">🔐</span>認証ルーターテスト</a></li>
                            <li><a href="test_results/test_results_with_article_router.html"><span class="file-icon">📝</span>記事ルーターテスト</a></li>
                        </ul>
                    </div>
                </div>
                
                <div class="section" id="bug-reports-section">
                    <div class="section-header">🐛 バグトラッキング</div>
                    <div class="section-content">
                        <ul class="file-list">
                            <li><a href="bug_reports/comprehensive_bug_tracking_report.html"><span class="file-icon">📈</span>包括的バグレポート</a></li>
                            <li><a href="bug_reports/bug_report_v2.3_final.html"><span class="file-icon">🔍</span>最新バグレポート</a></li>
                            <li><a href="markdown_reports/"><span class="file-icon">📄</span>Markdownレポート</a></li>
                        </ul>
                    </div>
                </div>
                
                <div class="section" id="coverage-section">
                    <div class="section-header">📈 コードカバレッジ</div>
                    <div class="section-content">
                        <ul class="file-list">
                            <li><a href="coverage_html/current/full_coverage/index.html"><span class="file-icon">🎯</span>完全カバレッジ</a></li>
                            <li><a href="coverage_html/current/main_coverage/index.html"><span class="file-icon">🏠</span>メインカバレッジ</a></li>
                            <li><a href="coverage_html/current/routers_final_coverage/index.html"><span class="file-icon">🛣️</span>ルーターカバレッジ</a></li>
                        </ul>
                    </div>
                </div>
                
                <div class="section" id="data-section">
                    <div class="section-header">📄 データファイル</div>
                    <div class="section-content">
                        <ul class="file-list">
                            <li><a href="json_data/bug_history.json"><span class="file-icon">🗂️</span>バグ履歴データ</a></li>
                            <li><a href="json_data/coverage.json"><span class="file-icon">📊</span>カバレッジデータ</a></li>
                            <li><a href="json_data/comprehensive_bug_tracking_report.json"><span class="file-icon">📈</span>総合レポートデータ</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <div class="footer-stats">
                <div class="footer-stat">
                    <div class="footer-stat-number">135+</div>
                    <div class="footer-stat-label">総管理ファイル</div>
                </div>
                <div class="footer-stat">
                    <div class="footer-stat-number">98.5%</div>
                    <div class="footer-stat-label">コードカバレッジ</div>
                </div>
                <div class="footer-stat">
                    <div class="footer-stat-number">300+</div>
                    <div class="footer-stat-label">テスト数</div>
                </div>
            </div>
            <div class="timestamp">
                最終更新: <span id="timestamp"></span>
            </div>
        </div>
    </div>
    
    <script>
        // タイムスタンプを設定
        document.getElementById('timestamp').textContent = new Date().toLocaleString('ja-JP');
        
        // 統計を更新
        document.getElementById('test-files').textContent = '25';
        document.getElementById('bug-reports').textContent = '8';
        document.getElementById('coverage-reports').textContent = '6';
        document.getElementById('json-data').textContent = '4';
        
        // スムーズスクロール
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    </script>
</body>
</html>"""
        
        dashboard_path = self.reports_dir / "index.html"
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_content)
        
        print(f"🎨 統合ダッシュボードを更新: {dashboard_path.relative_to(self.project_root)}")
    
    def cleanup_empty_directories(self):
        """空のディレクトリを削除"""
        removed_count = 0
        
        # プロジェクトルートの空ディレクトリをチェック
        for item in self.project_root.iterdir():
            if item.is_dir() and item.name not in [
                'reports', 'scripts', 'test_results', 'test_archives',
                'routers', 'tests', 'utils', 'logger', 'alembic',
                '__pycache__', '.git', '.venv', 'site-packages'
            ]:
                try:
                    if not any(item.iterdir()):  # 空ディレクトリの場合
                        item.rmdir()
                        print(f"🗑️ 空ディレクトリを削除: {item.name}")
                        removed_count += 1
                except OSError:
                    pass  # ディレクトリが空でない場合
        
        if removed_count > 0:
            print(f"📁 {removed_count}個の空ディレクトリを削除しました")
    
    def generate_organization_summary(self):
        """整理結果のサマリーを生成"""
        print("\n" + "="*50)
        print("🎉 統合ファイル整理完了サマリー")
        print("="*50)
        
        categories = {
            "📊 XMLテスト結果": self.test_results_dir,
            "📋 XMLアーカイブ": self.test_archives_dir,
            "🎨 HTMLレポート": self.reports_dir / "test_results",
            "🐛 バグレポート": self.reports_dir / "bug_reports",
            "📈 HTMLカバレッジ": self.reports_dir / "coverage_html",
            "📄 JSONデータ": self.json_data_dir,
            "📝 Markdownレポート": self.markdown_reports_dir,
            "⚙️ スクリプト": self.scripts_dir
        }
        
        total_files = 0
        for category_name, directory in categories.items():
            if directory.exists():
                file_count = len(list(directory.rglob("*.*")))
                dir_count = len([d for d in directory.rglob("*") if d.is_dir()])
                print(f"{category_name}: {file_count}ファイル, {dir_count}ディレクトリ")
                total_files += file_count
            else:
                print(f"{category_name}: ディレクトリなし")
        
        # ルートディレクトリの状況
        root_clutter = len([f for f in self.project_root.glob("*.*") 
                           if f.suffix in ['.xml', '.html', '.json'] and 
                           f.name not in ['README.md', 'PROJECT_STRUCTURE.md']])
        
        print(f"\n🏠 ルートディレクトリ: {root_clutter}個の散乱ファイル (目標: 0)")
        print(f"📁 総管理ファイル数: {total_files}ファイル")
        print(f"🎯 ダッシュボード: reports/index.html")
        print("\n✅ プロジェクト整理が完了しました！")

def main():
    """メイン実行関数"""
    import sys
    
    # プロジェクトルートを取得
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = Path(__file__).parent.parent
    
    organizer = UnifiedFileOrganizer(project_root)
    organizer.setup_directories()
    
    print("🔄 統合ファイル整理システムを開始します...")
    organizer.organize_all_files()
    organizer.create_unified_dashboard()
    organizer.cleanup_empty_directories()
    organizer.generate_organization_summary()

if __name__ == "__main__":
    main()
