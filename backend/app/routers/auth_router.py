"""
Authentication Router
Simple login without JWT or password hashing
"""

from fastapi import APIRouter, HTTPException, status
from app.models.dto import LoginRequest, LoginResponse
from app.db.connection import db


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Employee login endpoint - Simple authentication with plain text password (dev mode)
    """
    # Get employee by login name
    query = """
    SELECT EmployeeId, FullName, LoginName, PasswordHash, IsActive
    FROM Employees
    WHERE LoginName = ? AND IsActive = 1
    """

    employee = db.execute_query(query, (request.username,), fetch_one=True)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # For development: Store password in plain text in PasswordHash column
    # In production, you should use proper password hashing
    if employee["PasswordHash"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Return employee info without JWT token
    return LoginResponse(
        access_token="",  # No token needed
        employee_id=employee["EmployeeId"],
        full_name=employee["FullName"]
    )


@router.get("/me")
async def get_current_user():
    """Get current user info"""
    return {"message": "No authentication required"}
