#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
継続的バグトラッキングシステム
pytestの結果を解析して、バグの履歴を管理し、レポートを生成します。
"""

import xml.etree.ElementTree as ET
import json
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import hashlib


class BugTracker:
    def __init__(self, history_file='bug_history.json'):
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self):
        """履歴データを読み込み"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                print(f"警告: {self.history_file}の読み込みに失敗しました。新しい履歴を開始します。")
        return []
    
    def _save_history(self):
        """履歴データを保存"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def _generate_test_id(self, test_name, test_class):
        """テストの一意IDを生成"""
        return hashlib.md5(f"{test_class}::{test_name}".encode()).hexdigest()[:8]
    
    def parse_junit_xml(self, xml_file):
        """JUnit XMLファイルを解析してテスト結果を抽出"""
        if not os.path.exists(xml_file):
            raise FileNotFoundError(f"XMLファイルが見つかりません: {xml_file}")
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # testsuiteエレメントから統計を取得
        testsuite = root.find('testsuite')
        if testsuite is not None:
            stats_element = testsuite
        else:
            stats_element = root
        
        # 基本統計
        total_tests = int(stats_element.get('tests', 0))
        failures = int(stats_element.get('failures', 0))
        errors = int(stats_element.get('errors', 0))
        skipped = int(stats_element.get('skipped', 0))
        passed = total_tests - failures - errors - skipped
        execution_time = float(stats_element.get('time', 0))
        
        # 個別テスト結果
        test_results = []
        for testcase in root.findall('.//testcase'):
            test_name = testcase.get('name')
            test_class = testcase.get('classname', '')
            test_time = float(testcase.get('time', 0))
            
            # テストの状態を判定
            failure = testcase.find('failure')
            error = testcase.find('error')
            skipped_elem = testcase.find('skipped')
            
            if failure is not None:
                status = 'failed'
                message = failure.get('message', '')
                detail = failure.text or ''
            elif error is not None:
                status = 'error'
                message = error.get('message', '')
                detail = error.text or ''
            elif skipped_elem is not None:
                status = 'skipped'
                message = skipped_elem.get('message', '')
                detail = skipped_elem.text or ''
            else:
                status = 'passed'
                message = ''
                detail = ''
            
            test_results.append({
                'id': self._generate_test_id(test_name, test_class),
                'name': test_name,
                'class': test_class,
                'status': status,
                'time': test_time,
                'message': message,
                'detail': detail
            })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': total_tests,
                'passed': passed,
                'failed': failures,
                'errors': errors,
                'skipped': skipped,
                'execution_time': execution_time,
                'success_rate': (passed / total_tests * 100) if total_tests > 0 else 0
            },
            'tests': test_results
        }
    
    def add_test_result(self, xml_file, version=None, notes=""):
        """新しいテスト結果を履歴に追加"""
        result = self.parse_junit_xml(xml_file)
        result['version'] = version or f"v{len(self.history) + 1}"
        result['notes'] = notes
        
        self.history.append(result)
        self._save_history()
        print(f"テスト結果を追加しました: {result['version']} ({result['timestamp']})")
        return result
    
    def get_bug_trends(self, days=30):
        """指定期間内のバグトレンドを分析"""
        if len(self.history) < 2:
            return {"error": "履歴データが不足しています（最低2回の実行結果が必要）"}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_history = [
            h for h in self.history 
            if datetime.fromisoformat(h['timestamp']) > cutoff_date
        ]
        
        if len(recent_history) < 2:
            recent_history = self.history[-2:]  # 最低でも最新2件は含める
        
        current = recent_history[-1]
        previous = recent_history[-2]
        
        # バグの変化を分析
        current_failed_tests = {
            t['id']: t for t in current['tests'] 
            if t['status'] in ['failed', 'error']
        }
        previous_failed_tests = {
            t['id']: t for t in previous['tests'] 
            if t['status'] in ['failed', 'error']
        }
        
        # 新規バグ、修正されたバグ、継続中のバグを特定
        new_bugs = set(current_failed_tests.keys()) - set(previous_failed_tests.keys())
        fixed_bugs = set(previous_failed_tests.keys()) - set(current_failed_tests.keys())
        ongoing_bugs = set(current_failed_tests.keys()) & set(previous_failed_tests.keys())
        
        return {
            'period_days': days,
            'comparison': {
                'current_version': current['version'],
                'previous_version': previous['version'],
                'current_timestamp': current['timestamp'],
                'previous_timestamp': previous['timestamp']
            },
            'summary': {
                'new_bugs': len(new_bugs),
                'fixed_bugs': len(fixed_bugs),
                'ongoing_bugs': len(ongoing_bugs),
                'total_current_bugs': len(current_failed_tests),
                'success_rate_change': current['summary']['success_rate'] - previous['summary']['success_rate']
            },
            'details': {
                'new_bugs': [
                    {
                        'id': bug_id,
                        'name': current_failed_tests[bug_id]['name'],
                        'class': current_failed_tests[bug_id]['class'],
                        'message': current_failed_tests[bug_id]['message']
                    }
                    for bug_id in new_bugs
                ],
                'fixed_bugs': [
                    {
                        'id': bug_id,
                        'name': previous_failed_tests[bug_id]['name'],
                        'class': previous_failed_tests[bug_id]['class']
                    }
                    for bug_id in fixed_bugs
                ],
                'ongoing_bugs': [
                    {
                        'id': bug_id,
                        'name': current_failed_tests[bug_id]['name'],
                        'class': current_failed_tests[bug_id]['class'],
                        'message': current_failed_tests[bug_id]['message']
                    }
                    for bug_id in ongoing_bugs
                ]
            }
        }
    
    def generate_report(self, output_format='console', output_file=None):
        """レポートを生成"""
        if not self.history:
            return "テスト履歴がありません。"
        
        trends = self.get_bug_trends()
        if 'error' in trends:
            return trends['error']
        
        latest = self.history[-1]
        
        if output_format == 'console':
            return self._generate_console_report(trends, latest)
        elif output_format == 'html':
            html_content = self._generate_html_report(trends, latest)
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                return f"HTMLレポートを生成しました: {output_file}"
            return html_content
        elif output_format == 'json':
            json_content = json.dumps({
                'trends': trends,
                'latest_result': latest
            }, indent=2, ensure_ascii=False)
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(json_content)
                return f"JSONレポートを生成しました: {output_file}"
            return json_content
    
    def _generate_console_report(self, trends, latest):
        """コンソール用レポート生成"""
        report = []
        report.append("=" * 60)
        report.append("🐛 継続的バグトラッキングレポート")
        report.append("=" * 60)
        report.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"総実行回数: {len(self.history)}回")
        report.append("")
        
        # 最新の状況
        report.append("📊 最新のテスト結果")
        report.append("-" * 30)
        report.append(f"バージョン: {latest['version']}")
        report.append(f"実行日時: {latest['timestamp']}")
        report.append(f"総テスト数: {latest['summary']['total']}")
        report.append(f"成功: {latest['summary']['passed']} ({latest['summary']['success_rate']:.1f}%)")
        report.append(f"失敗: {latest['summary']['failed']}")
        report.append(f"エラー: {latest['summary']['errors']}")
        report.append(f"スキップ: {latest['summary']['skipped']}")
        report.append(f"実行時間: {latest['summary']['execution_time']:.2f}秒")
        report.append("")
        
        # トレンド分析
        report.append("📈 バグトレンド分析")
        report.append("-" * 30)
        report.append(f"比較期間: {trends['comparison']['previous_version']} → {trends['comparison']['current_version']}")
        report.append(f"🆕 新規バグ: {trends['summary']['new_bugs']}件")
        report.append(f"✅ 修正されたバグ: {trends['summary']['fixed_bugs']}件")
        report.append(f"🔄 継続中のバグ: {trends['summary']['ongoing_bugs']}件")
        report.append(f"📊 成功率の変化: {trends['summary']['success_rate_change']:+.1f}%")
        report.append("")
        
        # 新規バグの詳細
        if trends['details']['new_bugs']:
            report.append("🚨 新規バグの詳細")
            report.append("-" * 30)
            for bug in trends['details']['new_bugs']:
                report.append(f"• {bug['class']}::{bug['name']}")
                if bug['message']:
                    report.append(f"  エラー: {bug['message'][:100]}...")
            report.append("")
        
        # 修正されたバグ
        if trends['details']['fixed_bugs']:
            report.append("✨ 修正されたバグ")
            report.append("-" * 30)
            for bug in trends['details']['fixed_bugs']:
                report.append(f"• {bug['class']}::{bug['name']}")
            report.append("")
        
        return "\n".join(report)
    
    def _generate_html_report(self, trends, latest):
        """HTML用レポート生成"""
        return f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>バグトラッキングレポート</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 8px; text-align: center; }}
        .trend-up {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .trend-down {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
        .bug-list {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        .bug-item {{ background: white; margin: 5px 0; padding: 10px; border-left: 4px solid #dc3545; border-radius: 4px; }}
        .fixed-bug {{ border-left-color: #28a745; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐛 継続的バグトラッキングレポート</h1>
            <p>生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <h3>{latest['summary']['total']}</h3>
                <p>総テスト数</p>
            </div>
            <div class="metric-card trend-{'down' if trends['summary']['success_rate_change'] >= 0 else 'up'}">
                <h3>{latest['summary']['success_rate']:.1f}%</h3>
                <p>成功率 ({trends['summary']['success_rate_change']:+.1f}%)</p>
            </div>
            <div class="metric-card trend-up">
                <h3>{trends['summary']['new_bugs']}</h3>
                <p>新規バグ</p>
            </div>
            <div class="metric-card trend-down">
                <h3>{trends['summary']['fixed_bugs']}</h3>
                <p>修正されたバグ</p>
            </div>
        </div>
        
        <h2>📈 バグトレンド分析</h2>
        <table>
            <tr><th>項目</th><th>値</th></tr>
            <tr><td>比較バージョン</td><td>{trends['comparison']['previous_version']} → {trends['comparison']['current_version']}</td></tr>
            <tr><td>新規バグ</td><td>{trends['summary']['new_bugs']}件</td></tr>
            <tr><td>修正されたバグ</td><td>{trends['summary']['fixed_bugs']}件</td></tr>
            <tr><td>継続中のバグ</td><td>{trends['summary']['ongoing_bugs']}件</td></tr>
        </table>
        
        {"<h2>🚨 新規バグ</h2><div class='bug-list'>" + "".join([f"<div class='bug-item'><strong>{bug['class']}::{bug['name']}</strong><br><small>{bug['message'][:100]}...</small></div>" for bug in trends['details']['new_bugs']]) + "</div>" if trends['details']['new_bugs'] else ""}
        
        {"<h2>✅ 修正されたバグ</h2><div class='bug-list'>" + "".join([f"<div class='bug-item fixed-bug'><strong>{bug['class']}::{bug['name']}</strong></div>" for bug in trends['details']['fixed_bugs']]) + "</div>" if trends['details']['fixed_bugs'] else ""}
    </div>
</body>
</html>
"""

def main():
    parser = argparse.ArgumentParser(description='継続的バグトラッキングシステム')
    parser.add_argument('command', choices=['add', 'report', 'history'], help='実行するコマンド')
    parser.add_argument('--xml', '-x', help='JUnit XMLファイルパス (addコマンド用)')
    parser.add_argument('--version', '-v', help='バージョン名 (addコマンド用)')
    parser.add_argument('--notes', '-n', default='', help='メモ (addコマンド用)')
    parser.add_argument('--format', '-f', choices=['console', 'html', 'json'], default='console', help='レポート形式')
    parser.add_argument('--output', '-o', help='出力ファイル名')
    parser.add_argument('--history-file', default='bug_history.json', help='履歴ファイル名')
    parser.add_argument('--days', '-d', type=int, default=30, help='トレンド分析の日数')
    
    args = parser.parse_args()
    
    tracker = BugTracker(args.history_file)
    
    if args.command == 'add':
        if not args.xml:
            print("エラー: --xml オプションでJUnit XMLファイルを指定してください")
            return
        
        try:
            result = tracker.add_test_result(args.xml, args.version, args.notes)
            print(f"✅ テスト結果を追加しました")
            print(f"   バージョン: {result['version']}")
            print(f"   総テスト数: {result['summary']['total']}")
            print(f"   成功率: {result['summary']['success_rate']:.1f}%")
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    elif args.command == 'report':
        try:
            report = tracker.generate_report(args.format, args.output)
            if args.output and args.format != 'console':
                print(report)
            else:
                print(report)
        except Exception as e:
            print(f"❌ レポート生成エラー: {e}")
    
    elif args.command == 'history':
        if not tracker.history:
            print("履歴がありません。")
            return
        
        print("📚 テスト実行履歴")
        print("-" * 50)
        for i, entry in enumerate(tracker.history, 1):
            print(f"{i:2d}. {entry['version']} ({entry['timestamp'][:19]})")
            print(f"    成功率: {entry['summary']['success_rate']:.1f}% "
                  f"({entry['summary']['passed']}/{entry['summary']['total']})")
            if entry.get('notes'):
                print(f"    メモ: {entry['notes']}")
            print()

if __name__ == '__main__':
    main()