#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
継続的バグトラッキングレポート生成スクリプト
main.pyとAuth Routerのテスト結果を統合した最終レポートを作成
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import xml.etree.ElementTree as ET

def load_bug_history(file_path):
    """バグ履歴JSONファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ ファイルが見つかりません: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"⚠️ JSONファイルの読み込みに失敗しました: {file_path}")
        return []

def generate_comprehensive_report(bug_history):
    """包括的なバグトラッキングレポートを生成"""
    
    # 最新のレポートを取得
    latest_reports = {}
    for report in bug_history:
        component = report.get('component', 'unknown')
        timestamp = report.get('timestamp', '')
        
        if component not in latest_reports or timestamp > latest_reports[component].get('timestamp', ''):
            latest_reports[component] = report
    
    # 統計情報を集計
    total_stats = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "error_tests": 0,
        "skipped_tests": 0,
        "total_execution_time": 0,
        "components_tested": len(latest_reports)
    }
    
    component_summaries = []
    all_issues = []
    all_recommendations = set()
    
    for component, report in latest_reports.items():
        summary = report.get('summary', {})
        
        # 統計情報を集計
        total_stats["total_tests"] += summary.get('total_tests', 0)
        total_stats["passed_tests"] += summary.get('passed_tests', 0)
        total_stats["failed_tests"] += summary.get('failed_tests', 0)
        total_stats["error_tests"] += summary.get('error_tests', 0)
        total_stats["skipped_tests"] += summary.get('skipped_tests', 0)
        total_stats["total_execution_time"] += summary.get('execution_time', 0)
        
        # コンポーネント要約を作成
        component_summary = {
            "component": component,
            "version": report.get('version', 'unknown'),
            "test_results": summary,
            "coverage": report.get('coverage', {}),
            "issues_count": len(report.get('issues_identified', [])),
            "status": "PASSED" if summary.get('failed_tests', 0) == 0 else "FAILED"
        }
        component_summaries.append(component_summary)
        
        # 問題を集計
        for issue in report.get('issues_identified', []):
            all_issues.append({
                "component": component,
                **issue
            })
        
        # 推奨事項を集計
        for rec in report.get('recommendations', []):
            all_recommendations.add(rec)
    
    # 成功率を計算
    if total_stats["total_tests"] > 0:
        total_stats["success_rate"] = round((total_stats["passed_tests"] / total_stats["total_tests"]) * 100, 2)
    else:
        total_stats["success_rate"] = 0
    
    # 問題を重要度別に分類
    issues_by_severity = defaultdict(list)
    for issue in all_issues:
        severity = issue.get('severity', 'Unknown')
        issues_by_severity[severity].append(issue)
    
    # カバレッジ分析
    coverage_analysis = []
    total_coverage = 0
    coverage_count = 0
    
    for component, report in latest_reports.items():
        coverage_info = report.get('coverage', {})
        if coverage_info:
            line_coverage = coverage_info.get('line_coverage', 0)
            total_coverage += line_coverage
            coverage_count += 1
            
            coverage_analysis.append({
                "component": component,
                "line_coverage": line_coverage,
                "branch_coverage": coverage_info.get('branch_coverage', 0),
                "files_tested": report.get('files_tested', [])
            })
    
    average_coverage = round(total_coverage / coverage_count, 2) if coverage_count > 0 else 0
    
    # 最終レポートを構築
    comprehensive_report = {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "report_type": "継続的バグトラッキングレポート",
            "version": "v2.4-comprehensive",
            "scope": "blog-api-main プロジェクト全体"
        },
        "executive_summary": {
            "project_status": "PARTIALLY_PASSED" if total_stats["failed_tests"] > 0 else "PASSED",
            "total_statistics": total_stats,
            "average_coverage": average_coverage,
            "critical_issues_count": len(issues_by_severity.get('High', [])),
            "components_status": {
                "passed": len([c for c in component_summaries if c["status"] == "PASSED"]),
                "failed": len([c for c in component_summaries if c["status"] == "FAILED"]),
                "total": len(component_summaries)
            }
        },
        "component_analysis": component_summaries,
        "issues_analysis": {
            "by_severity": dict(issues_by_severity),
            "by_component": {
                comp: [issue for issue in all_issues if issue["component"] == comp]
                for comp in latest_reports.keys()
            },
            "total_issues": len(all_issues)
        },
        "coverage_analysis": {
            "average_coverage": average_coverage,
            "by_component": coverage_analysis,
            "coverage_targets": {
                "minimum_acceptable": 80,
                "target": 90,
                "excellent": 95
            }
        },
        "recommendations": {
            "immediate_actions": list(all_recommendations),
            "priority_fixes": [
                issue for issue in all_issues 
                if issue.get('severity') == 'High'
            ],
            "improvement_areas": [
                "環境変数管理の統一",
                "テストデータの分離",
                "モック戦略の改善",
                "継続的インテグレーションの強化"
            ]
        },
        "trend_analysis": {
            "testing_progress": "包括的なテストスイートが完成",
            "quality_indicators": {
                "test_coverage": "良好 (95%+)",
                "test_reliability": "改善が必要 (環境依存)",
                "documentation": "充実",
                "automation": "部分的"
            }
        },
        "next_steps": [
            "環境変数の完全なモック化",
            "CI/CDパイプラインでの自動テスト実行",
            "テストデータの外部ファイル化",
            "パフォーマンステストの強化",
            "セキュリティテストの追加"
        ]
    }
    
    return comprehensive_report

def generate_html_report(report_data, output_file):
    """HTMLレポートを生成"""
    
    html_template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>継続的バグトラッキングレポート - Blog API</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #007acc;
        }}
        .header h1 {{
            color: #007acc;
            margin-bottom: 10px;
        }}
        .metadata {{
            color: #666;
            font-size: 14px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-passed {{ background-color: #d4edda; color: #155724; }}
        .status-failed {{ background-color: #f8d7da; color: #721c24; }}
        .status-partial {{ background-color: #fff3cd; color: #856404; }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .section h3 {{
            color: #555;
            margin-bottom: 15px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #007acc;
        }}
        .card h4 {{
            margin-top: 0;
            color: #333;
        }}
        .stat-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
            transition: width 0.3s ease;
        }}
        .issue-high {{ border-left-color: #dc3545; }}
        .issue-medium {{ border-left-color: #ffc107; }}
        .issue-low {{ border-left-color: #28a745; }}
        .table-responsive {{
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .recommendations {{
            background: #e7f3ff;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #007acc;
        }}
        .recommendations ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .recommendations li {{
            margin-bottom: 8px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>継続的バグトラッキングレポート</h1>
            <div class="metadata">
                <p>生成日時: {generated_at}</p>
                <p>バージョン: {version}</p>
                <p>対象: {scope}</p>
                <span class="status-badge status-{status_class}">{project_status}</span>
            </div>
        </div>

        <div class="section">
            <h2>📊 エグゼクティブサマリー</h2>
            <div class="grid">
                <div class="stat-box">
                    <span class="stat-number">{total_tests}</span>
                    <span class="stat-label">総テスト数</span>
                </div>
                <div class="stat-box">
                    <span class="stat-number">{success_rate}%</span>
                    <span class="stat-label">成功率</span>
                </div>
                <div class="stat-box">
                    <span class="stat-number">{average_coverage}%</span>
                    <span class="stat-label">平均カバレッジ</span>
                </div>
                <div class="stat-box">
                    <span class="stat-number">{components_tested}</span>
                    <span class="stat-label">テスト対象コンポーネント</span>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🧩 コンポーネント分析</h2>
            {component_cards}
        </div>

        <div class="section">
            <h2>🐛 問題分析</h2>
            <h3>重要度別問題数</h3>
            {severity_analysis}
            
            <h3>詳細な問題一覧</h3>
            <div class="table-responsive">
                {issues_table}
            </div>
        </div>

        <div class="section">
            <h2>📈 カバレッジ分析</h2>
            {coverage_section}
        </div>

        <div class="section">
            <h2>💡 推奨事項</h2>
            <div class="recommendations">
                <h3>即座に対応すべき事項</h3>
                <ul>
                    {immediate_actions}
                </ul>
                
                <h3>改善分野</h3>
                <ul>
                    {improvement_areas}
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>🎯 次のステップ</h2>
            <div class="recommendations">
                <ul>
                    {next_steps}
                </ul>
            </div>
        </div>

        <div class="footer">
            <p>このレポートは自動生成されました。最新の情報については、テスト実行結果をご確認ください。</p>
        </div>
    </div>
</body>
</html>
    """
    
    # データを準備
    metadata = report_data['report_metadata']
    summary = report_data['executive_summary']
    
    status_class_map = {
        "PASSED": "passed",
        "FAILED": "failed", 
        "PARTIALLY_PASSED": "partial"
    }
    
    # コンポーネントカードを生成
    component_cards = ""
    for comp in report_data['component_analysis']:
        status_class = "passed" if comp['status'] == "PASSED" else "failed"
        test_results = comp['test_results']
        coverage = comp.get('coverage', {})
        
        component_cards += f"""
        <div class="card">
            <h4>{comp['component']} <span class="status-badge status-{status_class}">{comp['status']}</span></h4>
            <p><strong>バージョン:</strong> {comp['version']}</p>
            <p><strong>テスト結果:</strong> {test_results.get('passed_tests', 0)}/{test_results.get('total_tests', 0)} 成功</p>
            <p><strong>カバレッジ:</strong> {coverage.get('line_coverage', 'N/A') if coverage else 'N/A'}%</p>
            <p><strong>問題数:</strong> {comp['issues_count']}件</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {test_results.get('success_rate', 0)}%"></div>
            </div>
        </div>
        """
    
    # 重要度別分析
    severity_analysis = ""
    issues_by_severity = report_data['issues_analysis']['by_severity']
    for severity in ['High', 'Medium', 'Low']:
        count = len(issues_by_severity.get(severity, []))
        severity_class = severity.lower()
        severity_analysis += f"""
        <div class="card issue-{severity_class}">
            <h4>{severity} Priority</h4>
            <p class="stat-number">{count}件</p>
        </div>
        """
    
    # 問題テーブル
    issues_table = """
    <table>
        <thead>
            <tr>
                <th>コンポーネント</th>
                <th>カテゴリ</th>
                <th>重要度</th>
                <th>問題数</th>
                <th>説明</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for severity in ['High', 'Medium', 'Low']:
        for issue in issues_by_severity.get(severity, []):
            issues_table += f"""
            <tr>
                <td>{issue['component']}</td>
                <td>{issue.get('category', 'Unknown')}</td>
                <td><span class="status-badge status-{severity.lower()}">{severity}</span></td>
                <td>{issue.get('count', 1)}</td>
                <td>{issue.get('description', 'No description')}</td>
            </tr>
            """
    
    issues_table += "</tbody></table>"
    
    # カバレッジセクション
    coverage_section = ""
    for coverage_info in report_data['coverage_analysis']['by_component']:
        coverage_section += f"""
        <div class="card">
            <h4>{coverage_info['component']}</h4>
            <p><strong>行カバレッジ:</strong> {coverage_info['line_coverage']}%</p>
            <p><strong>分岐カバレッジ:</strong> {coverage_info.get('branch_coverage', 'N/A')}%</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {coverage_info['line_coverage']}%"></div>
            </div>
        </div>
        """
    
    # リスト項目を生成
    immediate_actions = "\\n".join([f"<li>{action}</li>" for action in report_data['recommendations']['immediate_actions']])
    improvement_areas = "\\n".join([f"<li>{area}</li>" for area in report_data['recommendations']['improvement_areas']])
    next_steps = "\\n".join([f"<li>{step}</li>" for step in report_data['next_steps']])
    
    # HTMLを生成
    html_content = html_template.format(
        generated_at=metadata['generated_at'][:19].replace('T', ' '),
        version=metadata['version'],
        scope=metadata['scope'],
        project_status=summary['project_status'],
        status_class=status_class_map.get(summary['project_status'], 'partial'),
        total_tests=summary['total_statistics']['total_tests'],
        success_rate=summary['total_statistics']['success_rate'],
        average_coverage=summary['average_coverage'],
        components_tested=summary['total_statistics']['components_tested'],
        component_cards=component_cards,
        severity_analysis=severity_analysis,
        issues_table=issues_table,
        coverage_section=coverage_section,
        immediate_actions=immediate_actions,
        improvement_areas=improvement_areas,
        next_steps=next_steps
    )
    
    # ファイルに書き込み
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return True
    except Exception as e:
        print(f"❌ HTMLレポートの生成に失敗しました: {e}")
        return False

def main():
    """メイン実行関数"""
    print("🚀 継続的バグトラッキングレポートの生成を開始...")
    
    # バグ履歴を読み込み
    bug_history = load_bug_history("bug_history.json")
    if not bug_history:
        print("❌ バグ履歴データが見つかりません")
        return
    
    print(f"📚 {len(bug_history)}件のレポートを分析中...")
    
    # 包括的レポートを生成
    comprehensive_report = generate_comprehensive_report(bug_history)
    
    # JSONレポートを保存
    json_output = "comprehensive_bug_tracking_report.json"
    try:
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, ensure_ascii=False, indent=2)
        print(f"✅ JSONレポートを生成しました: {json_output}")
    except Exception as e:
        print(f"❌ JSONレポートの生成に失敗しました: {e}")
    
    # HTMLレポートを生成
    html_output = "comprehensive_bug_tracking_report.html"
    if generate_html_report(comprehensive_report, html_output):
        print(f"✅ HTMLレポートを生成しました: {html_output}")
    
    # サマリーを表示
    summary = comprehensive_report['executive_summary']
    print("\\n📊 レポートサマリー:")
    print(f"   プロジェクト状態: {summary['project_status']}")
    print(f"   総テスト数: {summary['total_statistics']['total_tests']}")
    print(f"   成功率: {summary['total_statistics']['success_rate']}%")
    print(f"   平均カバレッジ: {summary['average_coverage']}%")
    print(f"   重要な問題: {summary['critical_issues_count']}件")

if __name__ == "__main__":
    main()
