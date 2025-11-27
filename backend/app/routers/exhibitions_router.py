"""
Exhibitions Router
CRUD operations for exhibitions
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from app.db.connection import db


router = APIRouter(prefix="/exhibitions", tags=["Exhibitions"])


class ExhibitionCreateRequest(BaseModel):
    name: str
    location: Optional[str] = None
    start_date: date
    end_date: date
    description: Optional[str] = None


class ExhibitionUpdateRequest(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


@router.get("/")
async def get_exhibitions():
    """Get all active exhibitions"""
    try:
        query = """
        SELECT
            ExhibitionId,
            Name,
            Location,
            StartDate,
            EndDate,
            Description,
            IsActive,
            CreatedAt
        FROM Exhibitions
        WHERE IsActive = 1
        ORDER BY StartDate DESC
        """
        exhibitions = db.execute_query(query, fetch_all=True)

        return {"success": True, "exhibitions": exhibitions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{exhibition_id}")
async def get_exhibition(exhibition_id: int):
    """Get single exhibition by ID"""
    try:
        query = """
        SELECT *
        FROM Exhibitions
        WHERE ExhibitionId = ?
        """
        exhibition = db.execute_query(query, (exhibition_id,), fetch_one=True)

        if not exhibition:
            raise HTTPException(status_code=404, detail="Exhibition not found")

        return {"success": True, "exhibition": exhibition}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=201)
async def create_exhibition(request: ExhibitionCreateRequest):
    """Create new exhibition"""
    try:
        # Validate dates
        if request.end_date < request.start_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")

        query = """
        INSERT INTO Exhibitions (Name, Location, StartDate, EndDate, Description, IsActive)
        OUTPUT INSERTED.ExhibitionId
        VALUES (?, ?, ?, ?, ?, 1)
        """
        result = db.execute_query(
            query,
            (request.name, request.location, request.start_date, request.end_date, request.description),
            fetch_one=True
        )

        exhibition_id = result["ExhibitionId"] if result else None

        return {
            "success": True,
            "exhibition_id": exhibition_id,
            "message": f"Exhibition '{request.name}' created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{exhibition_id}")
async def update_exhibition(exhibition_id: int, request: ExhibitionUpdateRequest):
    """Update exhibition details"""
    try:
        # Check if exhibition exists
        check_query = "SELECT ExhibitionId FROM Exhibitions WHERE ExhibitionId = ?"
        existing = db.execute_query(check_query, (exhibition_id,), fetch_one=True)
        if not existing:
            raise HTTPException(status_code=404, detail="Exhibition not found")

        # Build dynamic update query
        updates = []
        params = []

        if request.name is not None:
            updates.append("Name = ?")
            params.append(request.name)
        if request.location is not None:
            updates.append("Location = ?")
            params.append(request.location)
        if request.start_date is not None:
            updates.append("StartDate = ?")
            params.append(request.start_date)
        if request.end_date is not None:
            updates.append("EndDate = ?")
            params.append(request.end_date)
        if request.description is not None:
            updates.append("Description = ?")
            params.append(request.description)

        if not updates:
            return {"success": True, "message": "No updates provided"}

        updates.append("UpdatedAt = GETDATE()")
        params.append(exhibition_id)

        query = f"""
        UPDATE Exhibitions
        SET {', '.join(updates)}
        WHERE ExhibitionId = ?
        """
        db.execute_query(query, tuple(params))

        return {"success": True, "message": "Exhibition updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{exhibition_id}")
async def delete_exhibition(exhibition_id: int):
    """Delete exhibition (soft delete)"""
    try:
        query = """
        UPDATE Exhibitions
        SET IsActive = 0, UpdatedAt = GETDATE()
        WHERE ExhibitionId = ?
        """
        db.execute_query(query, (exhibition_id,))

        return {"success": True, "message": "Exhibition deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
