# for running async functions
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
# represents a connection to the database
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    # represents an async engine for sqlalchemy
    AsyncEngine,
    # for creating async engine and async db operations.
    create_async_engine
)
# provides access to alembic configuration and and context during migrations
from alembic import context
# BASE: The declarative base from SQLAlchemy where all 
# models inherit from, used to collect metadata.
from api.db.database import Base, DB_URL
from api.v1.models import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# sets the sqlalchemy.url option in the alembic configuration dynamically
# to the value or DB_URL
config.set_main_option(
    name='sqlalchemy.url',
    value=DB_URL
)
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
    # Configures logging according to the Alembic configuration file if it exists.
    # This is important for tracking and debugging migration processes.

# add your model's MetaData object here
# for 'autogenerate' support
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata
# Sets the target_metadata to the metadata of the SQLAlchemy base.
# This allows Alembic to auto-detect schema changes by inspecting the models.

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Retrieves the database URL from the Alembic configuration.
    url = config.get_main_option("sqlalchemy.url")
    # but would use the value set dynamically

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

# support for sync
def do_run_migrations(connection: Connection) -> None:
    """Runs the migrations using a given database connection.
    It's used for synchronous operations.

    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()

# support for async
async def run_async_migrations(engine: AsyncEngine):
    """Handles running migrations using an asynchronous engine.
    """
    # Asynchronously connects to the database.
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
        # Runs the synchronous migration function using the async connection.

    await engine.dispose()
    # Closes the engine and releases all resources.
    

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Checks if a connection is already available in the Alembic context.
    engine = config.attributes.get('connection', None)

    # Creates an asynchronous engine if one isn't provided.
    if not engine:
        engine = create_async_engine(
            url=DB_URL,
            future=True,
            poolclass=pool.NullPool
        )

    # run the asynchronous migrations if the engine is asynchronous
    if isinstance(engine, AsyncEngine):
        asyncio.run(run_async_migrations(engine))
    else:
        # runs the migrations synchronously.
        do_run_migrations(engine.connect())


# entry point
# Determines whether to run migrations in offline or online mode based on the Alembic context.
if context.is_offline_mode():
    # Checks if Alembic is running in offline mode.
    run_migrations_offline()
else:
    # or run_migrations_online() accordingly.
    run_migrations_online()
