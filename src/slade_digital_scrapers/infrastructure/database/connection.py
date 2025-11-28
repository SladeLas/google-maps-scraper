"""Create a cached PostgreSQL connection pool."""

import contextlib
from functools import lru_cache
from psycopg2.pool import SimpleConnectionPool
from slade_digital_scrapers.core.config import (
    DB_URI,
    DB_HOST,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_PORT,
)


def _build_dsn() -> str:
    """Build a DSN connection string from individual parameters or use DB_URI."""
    # Use DB_URI if it's set and not empty
    if DB_URI and DB_URI.strip():
        return DB_URI

    # Build PostgreSQL URI from individual parameters
    # Format: postgresql://user:password@host:port/dbname
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


@lru_cache(maxsize=1)
def get_pool(dsn: str | None = None, maxconn: int | None = None) -> SimpleConnectionPool:
    """Create (once) and return a psycopg2 connection pool."""
    dsn = dsn or _build_dsn()
    maxconn = maxconn or 15
    return SimpleConnectionPool(minconn=2, maxconn=maxconn, dsn=dsn)

def close_pool() -> None:
    """Close and reset the cached pool (use in tests/shutdown)."""
    try:
        get_pool().closeall()
    finally:
        get_pool.cache_clear()

@contextlib.contextmanager
def db_connection():
    """Context manager to get a connection from the pool."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)