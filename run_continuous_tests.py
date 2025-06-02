#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
継続的テスト実行・バグトラッキング自動化スクリプト
プロジェクト固有のテストのみを実行し、結果をバグトラッカーに記録
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path


def run_command(command, description):
    """コマンドを実行して結果を返す"""
    print(f"\n🔄 {description}")
    print(f"実行コマンド: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - 成功")
            if result.stdout:
                print(f"出力:\n{result.stdout}")
        else:
            print(f"❌ {description} - 失敗 (終了コード: {result.returncode})")
            if result.stderr:
                print(f"エラー:\n{result.stderr}")
        
        return result
    except Exception as e:
        print(f"❌ {description} - 例外発生: {e}")
        return None


def main():
    """メイン実行関数"""
    print("=" * 60)
    print("🚀 継続的テスト実行・バグトラッキング自動化")
    print("=" * 60)
    print(f"実行開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 現在のディレクトリ確認
    current_dir = Path.cwd()
    print(f"作業ディレクトリ: {current_dir}")
    
    # 1. プロジェクト固有のテストのみを実行
    test_result = run_command(
        "python -m pytest tests/ --junit-xml=test_results_continuous.xml",
        "プロジェクト固有テストの実行"
    )
    
    if test_result is None or test_result.returncode != 0:
        print("⚠️  テスト実行に問題がありましたが、処理を続行します")
    
    # 2. XMLファイルの存在確認
    xml_file = Path("test_results_continuous.xml")
    if not xml_file.exists():
        print("❌ JUnit XMLファイルが見つかりません")
        return 1
    
    # 3. バグトラッカーへの結果追加
    version = f"continuous-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    notes = f"継続的テスト実行 - {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"
    
    tracker_result = run_command(
        f'python tests/bug_tracker.py add --xml test_results_continuous.xml --version "{version}" --notes "{notes}"',
        "バグトラッカーへの結果追加"
    )
    
    # 4. コンソールレポート生成
    run_command(
        "python tests/bug_tracker.py report --format console",
        "コンソールレポート生成"
    )
    
    # 5. HTMLレポート生成
    run_command(
        "python tests/bug_tracker.py report --format html --output bug_report_latest.html",
        "HTMLレポート生成"
    )
    
    # 6. 最新履歴表示
    run_command(
        "python tests/bug_tracker.py history",
        "テスト実行履歴表示"
    )
    
    print("\n" + "=" * 60)
    print("🎉 継続的テスト実行・バグトラッキング完了")
    print("=" * 60)
    print(f"実行終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # テスト結果に基づく終了コード
    if test_result and test_result.returncode == 0:
        print("✅ すべてのテストが成功しました")
        return 0
    else:
        print("❌ 一部のテストで問題が発生しました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
