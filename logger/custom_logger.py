"""カスタムロガーパッケージ"""

from logging import getLogger, FileHandler, Formatter, INFO, ERROR
from pathlib import Path


"""ロガーの設定

:param log_dir: ログファイルの保存先ディレクトリ
:type log_dir: str
:param log_file: ログファイル名
:type log_file: str
:param log_level: ログレベル
"""


# ロガーの設定
log_dir = Path(__file__).parent.parent / 'log'
log_dir.mkdir(parents=True, exist_ok=True)  # ディレクトリが存在しない場合は作成

# INFOレベルのロガーを作成
logger = getLogger("app_logger")
logger.setLevel(INFO)

# フォーマットの設定
formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')

# INFOログのハンドラー
info_handler = FileHandler(log_dir / 'app.log')
info_handler.setLevel(INFO)
info_handler.setFormatter(formatter)

# ERRORログのハンドラー
error_handler = FileHandler(log_dir / 'error.log')
error_handler.setLevel(ERROR)
error_handler.setFormatter(formatter)

# ハンドラーをロガーに追加（重複追加を防ぐ）
if not logger.handlers:
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)

# INFOレベルを呼び出し先でに記録する
def create_logger(info_msg: str):
    """INFOレベルのログを記録する関数

    :param info_msg: ログに記録するメッセージ
    :type info_msg: str
    """
    logger.info(info_msg)

# ERRORレベルを呼び出し先でに記録する
def create_error_logger(error_msg: str):
    """ERRORレベルのログを記録する関数

    :param error_msg: ログに記録するメッセージ
    :type error_msg: str
    """
    logger.error(error_msg)