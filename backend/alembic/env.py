
# ============================================================
# BMDA - ALEMBIC ENVIRONMENT
# Use the existing Backend database connection.
# ============================================================

from logging.config import fileConfig

from alembic import context

# Import the existing BMDA database engine.
from app.db.database import engine

# Import the shared SQLAlchemy Base.
from app.models.user import Base

# ============================================================
# SECTION 1: ALEMBIC CONFIGURATION
# ============================================================

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ============================================================
# SECTION 2: REGISTER MODEL METADATA
# Import all existing model modules so SQLAlchemy knows
# about their tables. No tables are created here.
# ============================================================

import importlib
import pkgutil
import app.models

for module_info in pkgutil.iter_modules(app.models.__path__):
    if not module_info.ispkg:
        importlib.import_module(
            f"app.models.{module_info.name}"
        )

target_metadata = Base.metadata


# ============================================================
# SECTION 3: OFFLINE MIGRATION
# Generate SQL without connecting to the database.
# ============================================================

def run_migrations_offline() -> None:

    context.configure(
        url=engine.url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# SECTION 4: ONLINE MIGRATION
# Reuse the existing BMDA SQLAlchemy engine.
# ============================================================

def run_migrations_online() -> None:

    with engine.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================
# SECTION 5: EXECUTION
# ============================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
