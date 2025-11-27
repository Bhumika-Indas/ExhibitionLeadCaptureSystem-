"""
Employee Finder - Search employees by name with fuzzy matching
"""

from typing import Optional, Dict, Any, List
from app.db.employees_repo import employees_repo
from app.db.connection import db


class EmployeeFinder:
    """Find employees by name with flexible matching"""

    @staticmethod
    def find_by_name(name: str) -> Optional[Dict[str, Any]]:
        """
        Find employee by name (case-insensitive, partial match)

        Args:
            name: Employee name or partial name

        Returns:
            Employee dict or None
        """
        if not name:
            return None

        # Clean up name
        name = name.strip().lower()

        query = """
        SELECT EmployeeId, FullName, LoginName, Phone, Email, IsActive
        FROM Employees
        WHERE IsActive = 1
        AND (
            LOWER(FullName) LIKE ?
            OR LOWER(LoginName) LIKE ?
        )
        """

        # Try exact match first
        exact_match = db.execute_query(query, (name, name), fetch_one=True)
        if exact_match:
            return exact_match

        # Try partial match (starts with)
        partial_pattern = f"{name}%"
        partial_match = db.execute_query(query, (partial_pattern, partial_pattern), fetch_one=True)
        if partial_match:
            return partial_match

        # Try contains match
        contains_pattern = f"%{name}%"
        contains_match = db.execute_query(query, (contains_pattern, contains_pattern), fetch_one=True)
        if contains_match:
            return contains_match

        return None

    @staticmethod
    def get_all_active_employees() -> List[Dict[str, Any]]:
        """Get list of all active employees"""
        query = """
        SELECT EmployeeId, FullName, LoginName, Phone, Email
        FROM Employees
        WHERE IsActive = 1
        ORDER BY FullName
        """
        return db.execute_query(query) or []


# Singleton instance
employee_finder = EmployeeFinder()
