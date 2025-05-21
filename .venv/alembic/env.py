alembic/env.py
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from blog.model import Base

# alembic.ini からの設定を読む
config = context.config

# logging設定を読み込む（存在する場合）
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy のメタデータを設定:モデル定義からメタデータを取得
target_metadata = Base.metadata

# データベースのURLを環境変数から取得する関数
def get_url():
    return os.getenv("DATABASE_URL", "sqlite:///./blog.db")

def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        render_as_batch=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()