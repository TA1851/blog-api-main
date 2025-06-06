#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
単体テスト実行・履歴管理システム
バグ履歴とカバレッジ履歴を記録し、詳細なレポートを生成します。
"""

import subprocess
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET


class TestHistoryManager:
    """テスト履歴管理クラス"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.bug_history_file = self.base_dir / "bug_history.json"
        self.coverage_history_file = self.base_dir / "coverage_history.json"
        self.reports_dir = self.base_dir / "test_reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # 履歴データを初期化
        self.bug_history = self._load_json(self.bug_history_file, [])
        self.coverage_history = self._load_json(self.coverage_history_file, [])
    
    def _load_json(self, file_path: Path, default: Any) -> Any:
        """JSONファイルを安全に読み込み"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"警告: {file_path}の読み込みに失敗: {e}")
        return default
    
    def _save_json(self, data: Any, file_path: Path) -> None:
        """JSONファイルに安全に保存"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"エラー: {file_path}への保存に失敗: {e}")
    
    def run_command(self, command: str, description: str) -> Optional[subprocess.CompletedProcess]:
        """コマンドを実行して結果を返す"""
        print(f"\n🔄 {description}")
        print(f"実行コマンド: {command}")
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=self.base_dir
            )
            
            if result.returncode == 0:
                print(f"✅ {description} - 成功")
            else:
                print(f"❌ {description} - 失敗 (終了コード: {result.returncode})")
                if result.stderr:
                    print(f"エラー:\n{result.stderr}")
            
            return result
        except Exception as e:
            print(f"❌ {description} - 例外発生: {e}")
            return None
    
    def parse_junit_xml(self, xml_file: str) -> Dict[str, Any]:
        """JUnit XMLファイルを解析してテスト結果を取得"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # テストスイート情報を取得
            testsuite = root.find('testsuite') if root.tag != 'testsuite' else root
            if testsuite is None:
                testsuite = root
            
            total_tests = int(testsuite.get('tests', 0))
            failures = int(testsuite.get('failures', 0))
            errors = int(testsuite.get('errors', 0))
            skipped = int(testsuite.get('skipped', 0))
            time_taken = float(testsuite.get('time', 0))
            
            # 個別のテストケース情報を収集
            test_cases = []
            for testcase in testsuite.findall('.//testcase'):
                case_info = {
                    'name': testcase.get('name', ''),
                    'classname': testcase.get('classname', ''),
                    'time': float(testcase.get('time', 0)),
                    'status': 'passed'
                }
                
                # 失敗やエラーの詳細を取得
                failure = testcase.find('failure')
                error = testcase.find('error')
                skipped_elem = testcase.find('skipped')
                
                if failure is not None:
                    case_info['status'] = 'failed'
                    case_info['failure_message'] = failure.get('message', '')
                    case_info['failure_text'] = failure.text or ''
                elif error is not None:
                    case_info['status'] = 'error'
                    case_info['error_message'] = error.get('message', '')
                    case_info['error_text'] = error.text or ''
                elif skipped_elem is not None:
                    case_info['status'] = 'skipped'
                    case_info['skip_reason'] = skipped_elem.get('message', '')
                
                test_cases.append(case_info)
            
            return {
                'total_tests': total_tests,
                'passed': total_tests - failures - errors - skipped,
                'failed': failures,
                'errors': errors,
                'skipped': skipped,
                'success_rate': ((total_tests - failures - errors) / total_tests * 100) if total_tests > 0 else 0,
                'execution_time': time_taken,
                'test_cases': test_cases
            }
        
        except Exception as e:
            print(f"XMLファイル解析エラー: {e}")
            return {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'skipped': 0,
                'success_rate': 0,
                'execution_time': 0,
                'test_cases': []
            }
    
    def parse_coverage_report(self, coverage_json_file: str) -> Dict[str, Any]:
        """カバレッジJSONレポートを解析"""
        try:
            with open(coverage_json_file, 'r', encoding='utf-8') as f:
                coverage_data = json.load(f)
            
            totals = coverage_data.get('totals', {})
            files_coverage = {}
            
            # ファイル別カバレッジ情報を取得
            for file_path, file_data in coverage_data.get('files', {}).items():
                summary = file_data.get('summary', {})
                files_coverage[file_path] = {
                    'covered_lines': summary.get('covered_lines', 0),
                    'num_statements': summary.get('num_statements', 0),
                    'percent_covered': summary.get('percent_covered', 0),
                    'missing_lines': summary.get('missing_lines', 0),
                    'excluded_lines': summary.get('excluded_lines', 0)
                }
            
            return {
                'overall_coverage': totals.get('percent_covered', 0),
                'total_statements': totals.get('num_statements', 0),
                'covered_statements': totals.get('covered_lines', 0),
                'missing_statements': totals.get('missing_lines', 0),
                'excluded_statements': totals.get('excluded_lines', 0),
                'files_coverage': files_coverage
            }
        
        except Exception as e:
            print(f"カバレッジレポート解析エラー: {e}")
            return {
                'overall_coverage': 0,
                'total_statements': 0,
                'covered_statements': 0,
                'missing_statements': 0,
                'excluded_statements': 0,
                'files_coverage': {}
            }
    
    def run_tests_with_coverage(self, test_module: str = None) -> Dict[str, Any]:
        """テストをカバレッジ付きで実行"""
        timestamp = datetime.now()
        test_id = timestamp.strftime('%Y%m%d_%H%M%S')
        
        # テスト対象を決定
        if test_module:
            test_target = f"tests/test_{test_module}.py"
            test_name = f"test_{test_module}"
        else:
            test_target = "tests/"
            test_name = "all_tests"
        
        # ファイル名を設定
        xml_file = f"test_results_{test_id}.xml"
        coverage_file = f"coverage_{test_id}.json"
        html_dir = f"htmlcov_{test_id}"
        
        print(f"\n{'='*60}")
        print(f"🧪 テスト実行開始: {test_name}")
        print(f"タイムスタンプ: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # 1. テストを実行（カバレッジ付き）
        test_command = f"python -m pytest {test_target} --junit-xml={xml_file} --cov=. --cov-report=json:{coverage_file} --cov-report=html:{html_dir} -v"
        test_result = self.run_command(test_command, f"{test_name}の実行")
        
        # 2. テスト結果を解析
        test_data = self.parse_junit_xml(xml_file) if Path(xml_file).exists() else {}
        
        # 3. カバレッジ結果を解析
        coverage_data = self.parse_coverage_report(coverage_file) if Path(coverage_file).exists() else {}
        
        # 4. 統合結果を作成
        result = {
            'timestamp': timestamp.isoformat(),
            'test_id': test_id,
            'test_name': test_name,
            'test_target': test_target,
            'test_results': test_data,
            'coverage_results': coverage_data,
            'files': {
                'xml_report': xml_file,
                'coverage_json': coverage_file,
                'html_coverage': html_dir
            }
        }
        
        # 5. 履歴に追加
        self.add_to_history(result)
        
        # 6. レポート生成
        self.generate_report(result)
        
        return result
    
    def add_to_history(self, result: Dict[str, Any]) -> None:
        """結果を履歴に追加"""
        # バグ履歴に追加
        bug_entry = {
            'timestamp': result['timestamp'],
            'test_id': result['test_id'],
            'test_name': result['test_name'],
            'total_tests': result['test_results'].get('total_tests', 0),
            'passed': result['test_results'].get('passed', 0),
            'failed': result['test_results'].get('failed', 0),
            'errors': result['test_results'].get('errors', 0),
            'skipped': result['test_results'].get('skipped', 0),
            'success_rate': result['test_results'].get('success_rate', 0),
            'execution_time': result['test_results'].get('execution_time', 0),
            'failed_tests': [
                tc for tc in result['test_results'].get('test_cases', [])
                if tc['status'] in ['failed', 'error']
            ]
        }
        self.bug_history.append(bug_entry)
        
        # カバレッジ履歴に追加
        coverage_entry = {
            'timestamp': result['timestamp'],
            'test_id': result['test_id'],
            'test_name': result['test_name'],
            'overall_coverage': result['coverage_results'].get('overall_coverage', 0),
            'total_statements': result['coverage_results'].get('total_statements', 0),
            'covered_statements': result['coverage_results'].get('covered_statements', 0),
            'missing_statements': result['coverage_results'].get('missing_statements', 0),
            'files_coverage': result['coverage_results'].get('files_coverage', {})
        }
        self.coverage_history.append(coverage_entry)
        
        # ファイルに保存
        self._save_json(self.bug_history, self.bug_history_file)
        self._save_json(self.coverage_history, self.coverage_history_file)
        
        print(f"✅ 履歴に追加しました（バグ履歴: {len(self.bug_history)}件、カバレッジ履歴: {len(self.coverage_history)}件）")
    
    def generate_report(self, result: Dict[str, Any]) -> None:
        """詳細レポートを生成"""
        test_id = result['test_id']
        
        # Markdownレポートを生成
        md_report_path = self.reports_dir / f"test_report_{test_id}.md"
        self._generate_markdown_report(result, md_report_path)
        
        # HTMLレポートを生成
        html_report_path = self.reports_dir / f"test_report_{test_id}.html"
        self._generate_html_report(result, html_report_path)
        
        print(f"📄 レポート生成完了:")
        print(f"   - Markdown: {md_report_path}")
        print(f"   - HTML: {html_report_path}")
    
    def _generate_markdown_report(self, result: Dict[str, Any], output_path: Path) -> None:
        """Markdownレポートを生成"""
        test_results = result['test_results']
        coverage_results = result['coverage_results']
        
        content = f"""# テスト実行レポート

## 📊 基本情報
- **実行日時**: {result['timestamp']}
- **テストID**: {result['test_id']}
- **テスト対象**: {result['test_name']}
- **テストファイル**: {result['test_target']}

## 🧪 テスト結果サマリー

| 項目 | 値 |
|------|-----|
| 総テスト数 | {test_results.get('total_tests', 0)} |
| 成功 | {test_results.get('passed', 0)} |
| 失敗 | {test_results.get('failed', 0)} |
| エラー | {test_results.get('errors', 0)} |
| スキップ | {test_results.get('skipped', 0)} |
| 成功率 | {test_results.get('success_rate', 0):.2f}% |
| 実行時間 | {test_results.get('execution_time', 0):.3f}秒 |

## 📈 カバレッジ結果

| 項目 | 値 |
|------|-----|
| 全体カバレッジ | {coverage_results.get('overall_coverage', 0):.2f}% |
| 総ステートメント数 | {coverage_results.get('total_statements', 0)} |
| カバー済みステートメント | {coverage_results.get('covered_statements', 0)} |
| 未カバーステートメント | {coverage_results.get('missing_statements', 0)} |
| 除外ステートメント | {coverage_results.get('excluded_statements', 0)} |

"""
        
        # 失敗したテストの詳細
        failed_tests = [tc for tc in test_results.get('test_cases', []) if tc['status'] in ['failed', 'error']]
        if failed_tests:
            content += "\n## ❌ 失敗したテスト\n\n"
            for i, test in enumerate(failed_tests, 1):
                content += f"### {i}. {test['name']}\n"
                content += f"- **クラス**: {test['classname']}\n"
                content += f"- **ステータス**: {test['status']}\n"
                content += f"- **実行時間**: {test['time']:.3f}秒\n"
                
                if test['status'] == 'failed' and 'failure_message' in test:
                    content += f"- **失敗メッセージ**: {test['failure_message']}\n"
                    if 'failure_text' in test and test['failure_text']:
                        content += f"```\n{test['failure_text']}\n```\n"
                elif test['status'] == 'error' and 'error_message' in test:
                    content += f"- **エラーメッセージ**: {test['error_message']}\n"
                    if 'error_text' in test and test['error_text']:
                        content += f"```\n{test['error_text']}\n```\n"
                content += "\n"
        
        # ファイル別カバレッジ詳細
        files_coverage = coverage_results.get('files_coverage', {})
        if files_coverage:
            content += "\n## 📁 ファイル別カバレッジ\n\n"
            content += "| ファイル | カバレッジ | ステートメント | カバー済み | 未カバー |\n"
            content += "|----------|------------|----------------|-----------|----------|\n"
            
            for file_path, file_cov in sorted(files_coverage.items()):
                coverage_pct = file_cov.get('percent_covered', 0)
                total_stmts = file_cov.get('num_statements', 0)
                covered_stmts = file_cov.get('covered_lines', 0)
                missing_stmts = file_cov.get('missing_lines', 0)
                
                content += f"| {file_path} | {coverage_pct:.1f}% | {total_stmts} | {covered_stmts} | {missing_stmts} |\n"
        
        content += f"\n## 📎 生成ファイル\n"
        content += f"- **JUnit XML**: {result['files']['xml_report']}\n"
        content += f"- **カバレッジJSON**: {result['files']['coverage_json']}\n"
        content += f"- **HTMLカバレッジ**: {result['files']['html_coverage']}/\n"
        
        # ファイルに書き込み
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_html_report(self, result: Dict[str, Any], output_path: Path) -> None:
        """HTMLレポートを生成"""
        # 簡単なHTMLレポートを生成
        test_results = result['test_results']
        coverage_results = result['coverage_results']
        
        html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>テスト実行レポート - {result['test_id']}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2 {{ color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #007acc; color: white; }}
        .success {{ color: #28a745; font-weight: bold; }}
        .failure {{ color: #dc3545; font-weight: bold; }}
        .warning {{ color: #ffc107; font-weight: bold; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; color: white; font-size: 0.9em; }}
        .badge-success {{ background-color: #28a745; }}
        .badge-danger {{ background-color: #dc3545; }}
        .badge-warning {{ background-color: #ffc107; }}
        .progress-bar {{ width: 100%; background-color: #e9ecef; border-radius: 4px; height: 20px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background-color: #28a745; transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 テスト実行レポート</h1>
        
        <h2>📊 基本情報</h2>
        <table>
            <tr><th>実行日時</th><td>{result['timestamp']}</td></tr>
            <tr><th>テストID</th><td>{result['test_id']}</td></tr>
            <tr><th>テスト対象</th><td>{result['test_name']}</td></tr>
            <tr><th>テストファイル</th><td>{result['test_target']}</td></tr>
        </table>
        
        <h2>🧪 テスト結果</h2>
        <table>
            <tr><th>項目</th><th>値</th><th>ステータス</th></tr>
            <tr>
                <td>総テスト数</td>
                <td>{test_results.get('total_tests', 0)}</td>
                <td><span class="badge badge-{'success' if test_results.get('total_tests', 0) > 0 else 'warning'}">{test_results.get('total_tests', 0)} テスト</span></td>
            </tr>
            <tr>
                <td>成功</td>
                <td>{test_results.get('passed', 0)}</td>
                <td><span class="badge badge-success">{test_results.get('passed', 0)} 成功</span></td>
            </tr>
            <tr>
                <td>失敗</td>
                <td>{test_results.get('failed', 0)}</td>
                <td><span class="badge badge-{'danger' if test_results.get('failed', 0) > 0 else 'success'}">{test_results.get('failed', 0)} 失敗</span></td>
            </tr>
            <tr>
                <td>成功率</td>
                <td>{test_results.get('success_rate', 0):.2f}%</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {test_results.get('success_rate', 0)}%;"></div>
                    </div>
                </td>
            </tr>
        </table>
        
        <h2>📈 カバレッジ結果</h2>
        <table>
            <tr><th>項目</th><th>値</th><th>グラフ</th></tr>
            <tr>
                <td>全体カバレッジ</td>
                <td>{coverage_results.get('overall_coverage', 0):.2f}%</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {coverage_results.get('overall_coverage', 0)}%;"></div>
                    </div>
                </td>
            </tr>
            <tr><td>総ステートメント数</td><td>{coverage_results.get('total_statements', 0)}</td><td>-</td></tr>
            <tr><td>カバー済み</td><td>{coverage_results.get('covered_statements', 0)}</td><td>-</td></tr>
            <tr><td>未カバー</td><td>{coverage_results.get('missing_statements', 0)}</td><td>-</td></tr>
        </table>
        
        <p><em>生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
    </div>
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def show_history_summary(self, limit: int = 10) -> None:
        """履歴のサマリーを表示"""
        print(f"\n{'='*60}")
        print("📊 テスト履歴サマリー")
        print(f"{'='*60}")
        
        if not self.bug_history:
            print("履歴が見つかりません。")
            return
        
        print(f"\n🐛 バグ履歴（最新{min(limit, len(self.bug_history))}件）:")
        for entry in self.bug_history[-limit:]:
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
            status = "✅" if entry['failed'] == 0 and entry['errors'] == 0 else "❌"
            print(f"  {status} {timestamp} | {entry['test_name']} | "
                  f"成功率: {entry['success_rate']:.1f}% | "
                  f"失敗: {entry['failed']} | エラー: {entry['errors']}")
        
        print(f"\n📈 カバレッジ履歴（最新{min(limit, len(self.coverage_history))}件）:")
        for entry in self.coverage_history[-limit:]:
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
            coverage = entry['overall_coverage']
            status = "🟢" if coverage >= 90 else "🟡" if coverage >= 70 else "🔴"
            print(f"  {status} {timestamp} | {entry['test_name']} | "
                  f"カバレッジ: {coverage:.1f}% | "
                  f"ステートメント: {entry['covered_statements']}/{entry['total_statements']}")


def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='単体テスト実行・履歴管理システム')
    parser.add_argument('--module', '-m', type=str, help='特定のテストモジュールを実行（例: database, models）')
    parser.add_argument('--history', '-H', action='store_true', help='履歴サマリーを表示')
    parser.add_argument('--limit', '-l', type=int, default=10, help='履歴表示件数（デフォルト: 10）')
    
    args = parser.parse_args()
    
    # テスト履歴管理システムを初期化
    manager = TestHistoryManager()
    
    if args.history:
        # 履歴表示のみ
        manager.show_history_summary(args.limit)
    else:
        # テスト実行
        result = manager.run_tests_with_coverage(args.module)
        
        # 結果サマリーを表示
        print(f"\n{'='*60}")
        print("🎉 テスト実行完了")
        print(f"{'='*60}")
        
        test_results = result['test_results']
        coverage_results = result['coverage_results']
        
        print(f"📊 テスト結果:")
        print(f"   総テスト数: {test_results.get('total_tests', 0)}")
        print(f"   成功: {test_results.get('passed', 0)}")
        print(f"   失敗: {test_results.get('failed', 0)}")
        print(f"   成功率: {test_results.get('success_rate', 0):.2f}%")
        
        print(f"\n📈 カバレッジ結果:")
        print(f"   全体カバレッジ: {coverage_results.get('overall_coverage', 0):.2f}%")
        print(f"   カバー済み: {coverage_results.get('covered_statements', 0)}/{coverage_results.get('total_statements', 0)}")
        
        # 最新の履歴も表示
        print(f"\n最新の履歴サマリー:")
        manager.show_history_summary(5)


if __name__ == "__main__":
    main()
