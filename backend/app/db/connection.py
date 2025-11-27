"""
Database Connection Management using pyodbc
Manual SQL queries - No ORM
"""

import pyodbc
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from app.config import settings


class DatabaseConnection:
    """Database connection manager with context support"""

    def __init__(self):
        self.conn_string = settings.MSSQL_CONN_STRING
        self._connection: Optional[pyodbc.Connection] = None

    def connect(self) -> pyodbc.Connection:
        """Establish database connection"""
        if self._connection is None or self._connection.closed:
            self._connection = pyodbc.connect(
                self.conn_string,
                timeout=settings.DB_TIMEOUT,
                autocommit=False
            )
        return self._connection

    def disconnect(self):
        """Close database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        connection = self.connect()
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Any:
        """
        Execute a SQL query with optional parameters

        Args:
            query: SQL query string
            params: Query parameters tuple
            fetch_one: Return single row
            fetch_all: Return all rows

        Returns:
            Query results or None
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())

            if fetch_one:
                row = cursor.fetchone()
                return self._row_to_dict(cursor, row) if row else None

            if fetch_all:
                rows = cursor.fetchall()
                return [self._row_to_dict(cursor, row) for row in rows]

            # For INSERT/UPDATE/DELETE, return affected rows
            return cursor.rowcount

    def execute_scalar(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute query and return single value"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            row = cursor.fetchone()
            return row[0] if row else None

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute batch insert/update"""
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount

    @staticmethod
    def _row_to_dict(cursor: pyodbc.Cursor, row: pyodbc.Row) -> Dict[str, Any]:
        """Convert pyodbc Row to dictionary"""
        if row is None:
            return {}
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))


# Global database instance
db = DatabaseConnection()


@contextmanager
def get_db_cursor():
    """Dependency for FastAPI routes"""
    with db.get_cursor() as cursor:
        yield cursor


def test_connection() -> bool:
    """Test database connectivity"""
    try:
        result = db.execute_scalar("SELECT 1 AS test")
        return result == 1
    except Exception as e:
        print(f" Database connection failed: {e}")
        return False
