"""
Thin SQLite connection layer.

All dashboard and analysis code goes through these helpers so the DB path is
always resolved from config and connections are properly managed.
"""

import sqlite3
import logging
from typing import Optional

import pandas as pd

from src.config import DB_PATH

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row-factory set."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql: str, params: Optional[tuple] = None) -> pd.DataFrame:
    """
    Execute *sql* and return results as a DataFrame.

    Parameters
    ----------
    sql    : SQL query string (may contain ? placeholders)
    params : optional tuple of positional parameters
    """
    with get_connection() as conn:
        try:
            return pd.read_sql_query(sql, conn, params=params)
        except Exception as exc:
            logger.error("Query failed:\n%s\nError: %s", sql, exc)
            raise


def execute(sql: str, params: Optional[tuple] = None) -> None:
    """Execute a non-SELECT statement (DDL / DML)."""
    with get_connection() as conn:
        if params:
            conn.execute(sql, params)
        else:
            conn.execute(sql)
        conn.commit()


def table_exists(table_name: str) -> bool:
    """Return True if *table_name* exists in the database."""
    result = query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        params=(table_name,),
    )
    return not result.empty


def row_count(table_name: str = "loans") -> int:
    """Return the number of rows in *table_name*."""
    result = query(f"SELECT COUNT(*) AS n FROM {table_name}")  # noqa: S608
    return int(result["n"].iloc[0])
