#!/bin/bash
# 🚀 テストレポート更新クイックスクリプト
# 使用方法: ./quick_test_update.sh [オプション]

set -e

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# プロジェクトディレクトリ確認と移動
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# エラーハンドリング関数
handle_error() {
    echo -e "${RED}❌ エラーが発生しました: $1${NC}"
    echo -e "${YELLOW}💡 解決方法:${NC}"
    echo "  1. 仮想環境が有効化されているか確認"
    echo "  2. 依存関係がインストールされているか確認: pip list | grep pytest"
    echo "  3. テストファイルが存在するか確認: ls tests/"
    exit 1
}

echo -e "${BLUE}🧪 Blog API テストレポート更新ツール${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "${CYAN}📍 作業ディレクトリ: $(pwd)${NC}"
echo ""

# 基本的な環境チェック
if [ ! -f "test_runner_with_history.py" ]; then
    handle_error "test_runner_with_history.py が見つかりません"
fi

if [ ! -d "tests" ]; then
    handle_error "tests ディレクトリが見つかりません"
fi

# 引数チェック
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}📋 使用可能なオプション:${NC}"
    echo -e "  ${GREEN}all${NC}         - 全テスト実行 + 履歴更新 ⭐最重要"
    echo -e "  ${GREEN}core${NC}        - コア機能カバレッジのみ ⚡高速"
    echo -e "  ${GREEN}user${NC}        - ユーザー機能テスト 👤"
    echo -e "  ${GREEN}article${NC}     - 記事機能テスト 📝"
    echo -e "  ${GREEN}auth${NC}        - 認証機能テスト 🔐"
    echo -e "  ${GREEN}integration${NC} - 統合テスト 🔗"
    echo -e "  ${GREEN}coverage${NC}    - カバレッジレポートのみ 📊"
    echo -e "  ${GREEN}history${NC}     - 履歴サマリー表示 📈"
    echo ""
    echo -e "${BLUE}💡 使用例:${NC}"
    echo -e "  ${PURPLE}./quick_test_update.sh all${NC}      # 推奨：全テスト実行"
    echo -e "  ${PURPLE}./quick_test_update.sh core${NC}     # 高速：コア機能のみ"
    echo -e "  ${PURPLE}./quick_test_update.sh history${NC}  # 確認：履歴表示"
    echo ""
    echo -e "${YELLOW}🚀 最頻用コマンド: ${PURPLE}python test_runner_with_history.py${NC}"
    exit 1
fi

case "$1" in
    "all")
        echo -e "${GREEN}🚀 全テスト実行 + 履歴更新を開始...${NC}"
        python test_runner_with_history.py || handle_error "全テスト実行に失敗しました"
        ;;
    
    "core")
        echo -e "${GREEN}🎯 コア機能カバレッジ測定を開始...${NC}"
        if [ ! -f ".coveragerc_core" ]; then
            handle_error ".coveragerc_core ファイルが見つかりません"
        fi
        python -m pytest tests/ --cov=. --cov-config=.coveragerc_core --cov-report=term-missing --cov-report=html:htmlcov_core_only -v || handle_error "コア機能カバレッジ測定に失敗しました"
        echo -e "${BLUE}📊 カバレッジレポート: ${CYAN}htmlcov_core_only/index.html${NC}"
        ;;
    
    "user")
        echo -e "${GREEN}👤 ユーザー機能テスト実行...${NC}"
        python test_runner_with_history.py test_user_router test_user_deletion_integration || handle_error "ユーザー機能テストに失敗しました"
        ;;
    
    "article")
        echo -e "${GREEN}📝 記事機能テスト実行...${NC}"
        python test_runner_with_history.py test_article_router || handle_error "記事機能テストに失敗しました"
        ;;
    
    "auth")
        echo -e "${GREEN}🔐 認証機能テスト実行...${NC}"
        python test_runner_with_history.py test_auth_router test_oauth2 test_custom_token || handle_error "認証機能テストに失敗しました"
        ;;
    
    "integration")
        echo -e "${GREEN}🔗 統合テスト実行...${NC}"
        python test_runner_with_history.py test_integration test_user_deletion_integration || handle_error "統合テストに失敗しました"
        ;;
    
    "coverage")
        echo -e "${GREEN}📊 カバレッジレポート生成...${NC}"
        python -m pytest tests/ --cov=. --cov-report=term-missing --cov-report=html || handle_error "カバレッジレポート生成に失敗しました"
        echo -e "${BLUE}📊 フルカバレッジ: ${CYAN}htmlcov/index.html${NC}"
        echo -e "${BLUE}📊 コアカバレッジ: ${CYAN}htmlcov_core_only/index.html${NC}"
        ;;
    
    "history")
        echo -e "${GREEN}📈 履歴サマリー表示...${NC}"
        echo -e "${YELLOW}🐛 最新バグ履歴 (最新5件):${NC}"
        python -c "
import json
try:
    with open('bug_history.json', 'r', encoding='utf-8') as f:
        history = json.load(f)
        print(f'  総実行回数: {len(history)}回')
        for entry in history[-5:]:
            status = '✅' if entry['success_rate'] == 100.0 else '❌'
            print(f'  {status} {entry[\"timestamp\"]} | {entry[\"test_name\"]} | 成功率: {entry[\"success_rate\"]}%')
except FileNotFoundError:
    print('  履歴ファイルが見つかりません')
except Exception as e:
    print(f'  エラー: {e}')
"
        echo ""
        echo -e "${YELLOW}📊 最新カバレッジ履歴 (最新5件):${NC}"
        python -c "
import json
try:
    with open('coverage_history.json', 'r', encoding='utf-8') as f:
        history = json.load(f)
        print(f'  総測定回数: {len(history)}回')
        for entry in history[-5:]:
            coverage = entry.get('overall_coverage', entry.get('coverage_percent', 0))
            coverage_icon = '🟢' if coverage >= 80 else '🟡' if coverage >= 60 else '🔴'
            print(f'  {coverage_icon} {entry[\"timestamp\"]} | {entry[\"test_name\"]} | カバレッジ: {coverage:.1f}%')
except FileNotFoundError:
    print('  履歴ファイルが見つかりません')
except Exception as e:
    print(f'  エラー: {e}')
"
        ;;
    
    *)
        echo -e "${RED}❌ 不明なオプション: $1${NC}"
        echo -e "${YELLOW}💡 利用可能なオプション:${NC}"
        echo "   all, core, user, article, auth, integration, coverage, history"
        echo ""
        echo -e "${BLUE}ヘルプ表示: ${PURPLE}./quick_test_update.sh${NC}"
        exit 1
        ;;
esac

# 成功メッセージ（historyオプション以外）
if [ "$1" != "history" ]; then
    echo ""
    echo -e "${GREEN}✅ 処理完了！${NC}"
    echo -e "${BLUE}📋 生成されたレポート:${NC}"
    echo -e "  📄 Markdownレポート: ${CYAN}test_reports/${NC}"
    echo -e "  🌐 HTMLレポート: ${CYAN}test_reports/${NC}"
    echo -e "  📊 カバレッジレポート: ${CYAN}htmlcov/ または htmlcov_core_only/${NC}"
    echo ""
    echo -e "${YELLOW}💡 次のステップ:${NC}"
    echo -e "  📈 履歴確認: ${PURPLE}./quick_test_update.sh history${NC}"
    if [ "$1" = "core" ]; then
        echo -e "  🌐 カバレッジ表示: ${PURPLE}open htmlcov_core_only/index.html${NC}"
    elif [ "$1" = "coverage" ]; then
        echo -e "  🌐 カバレッジ表示: ${PURPLE}open htmlcov/index.html${NC}"
    fi
fi
