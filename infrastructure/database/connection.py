"""Create a cached PostgreSQL connection pool."""

import contextlib
from functools import lru_cache
from psycopg2.pool import SimpleConnectionPool
from dustly.core.config import DB_URI

@lru_cache(maxsize=1)
def get_pool(dsn: str | None = None, maxconn: int | None = None) -> SimpleConnectionPool:
    """Create (once) and return a psycopg2 connection pool."""
    dsn = dsn or DB_URI
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