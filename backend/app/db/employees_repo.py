"""
Employees Repository - Database operations for Employees
"""

from typing import Optional, Dict, Any
from app.db.connection import db


class EmployeesRepository:
    """Repository for Employee-related database operations"""

    @staticmethod
    def find_employee_by_phone(phone: str) -> Optional[Dict[str, Any]]:
        """
        Find employee by phone number
        Tries multiple phone formats to match

        Args:
            phone: Phone number to search for

        Returns:
            Employee dict if found, None otherwise
        """
        query = """
        SELECT
            EmployeeId,
            FullName,
            LoginName,
            Phone,
            Email,
            IsActive
        FROM Employees
        WHERE Phone = ? AND IsActive = 1
        """

        # Try exact match first
        employee = db.execute_query(query, (phone,), fetch_one=True)
        if employee:
            return employee

        # If phone starts with '91', try without country code
        if phone.startswith('91') and len(phone) == 12:
            phone_without_code = phone[2:]  # Remove '91'
            employee = db.execute_query(query, (phone_without_code,), fetch_one=True)
            if employee:
                return employee

        # If phone doesn't have country code, try with '91' prefix
        if not phone.startswith('91') and len(phone) == 10:
            phone_with_code = '91' + phone
            employee = db.execute_query(query, (phone_with_code,), fetch_one=True)
            if employee:
                return employee

        return None

    @staticmethod
    def get_employee_by_id(employee_id: int) -> Optional[Dict[str, Any]]:
        """Get employee by ID"""
        query = """
        SELECT
            EmployeeId,
            FullName,
            LoginName,
            Phone,
            Email,
            IsActive
        FROM Employees
        WHERE EmployeeId = ?
        """

        return db.execute_query(query, (employee_id,), fetch_one=True)


# Singleton instance
employees_repo = EmployeesRepository()
