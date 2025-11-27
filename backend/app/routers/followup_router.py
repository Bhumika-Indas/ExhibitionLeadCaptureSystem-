"""
Follow-up and Drip Sequence API Router
Handles follow-up management endpoints
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime
from app.services.followup_service import followup_service
from app.db.connection import db
from pydantic import BaseModel

router = APIRouter(prefix="/api/followups", tags=["Follow-ups"])


# Request/Response Models
class FollowUpResponse(BaseModel):
    FollowUpId: int
    LeadId: int
    ActionType: str
    ScheduledAt: datetime
    Status: str
    CompletedAt: Optional[datetime] = None
    Notes: Optional[str] = None
    CreatedAt: datetime
    UpdatedAt: Optional[datetime] = None

    # Lead details (from join)
    LeadName: Optional[str] = None
    CompanyName: Optional[str] = None
    Phone: Optional[str] = None


class FollowUpCreateRequest(BaseModel):
    lead_id: int
    action_type: str
    scheduled_at: datetime
    notes: Optional[str] = None


class FollowUpUpdateRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None


class DripSequenceStatsResponse(BaseModel):
    total: int
    pending: int
    completed: int
    cancelled: int
    failed: int


@router.get("/stats", response_model=DripSequenceStatsResponse)
async def get_followup_stats():
    """Get follow-up statistics"""

    query = """
    SELECT
        COUNT(*) as Total,
        SUM(CASE WHEN Status = 'pending' THEN 1 ELSE 0 END) as Pending,
        SUM(CASE WHEN Status = 'completed' THEN 1 ELSE 0 END) as Completed,
        SUM(CASE WHEN Status = 'cancelled' THEN 1 ELSE 0 END) as Cancelled,
        SUM(CASE WHEN Status = 'failed' THEN 1 ELSE 0 END) as Failed
    FROM FollowUps
    """

    result = db.execute_query(query, fetch_one=True)

    return DripSequenceStatsResponse(
        total=result['Total'] or 0,
        pending=result['Pending'] or 0,
        completed=result['Completed'] or 0,
        cancelled=result['Cancelled'] or 0,
        failed=result['Failed'] or 0
    )


@router.get("/", response_model=List[FollowUpResponse])
async def get_followups(
    status: Optional[str] = None,
    lead_id: Optional[int] = None,
    limit: int = 100
):
    """
    Get all follow-ups with optional filters

    - **status**: Filter by status (pending, completed, cancelled, failed)
    - **lead_id**: Filter by specific lead
    - **limit**: Maximum number of results
    """

    query = """
    SELECT
        f.FollowUpId, f.LeadId, f.ActionType, f.ScheduledAt,
        f.Status, f.CompletedAt, f.Notes, f.CreatedAt, f.UpdatedAt,
        l.PrimaryVisitorName as LeadName,
        l.CompanyName,
        l.PrimaryVisitorPhone as Phone
    FROM FollowUps f
    LEFT JOIN Leads l ON f.LeadId = l.LeadId
    WHERE 1=1
    """
    params = []

    if status:
        query += " AND f.Status = ?"
        params.append(status)

    if lead_id:
        query += " AND f.LeadId = ?"
        params.append(lead_id)

    query += " ORDER BY f.ScheduledAt DESC"
    query += f" OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"

    results = db.execute_query(query, tuple(params) if params else None, fetch_all=True)

    return [FollowUpResponse(**row) for row in (results or [])]


@router.get("/{followup_id}", response_model=FollowUpResponse)
async def get_followup(
    followup_id: int
):
    """Get specific follow-up by ID"""

    query = """
    SELECT
        f.FollowUpId, f.LeadId, f.ActionType, f.ScheduledAt,
        f.Status, f.CompletedAt, f.Notes, f.CreatedAt, f.UpdatedAt,
        l.PrimaryVisitorName as LeadName,
        l.CompanyName,
        l.PrimaryVisitorPhone as Phone
    FROM FollowUps f
    LEFT JOIN Leads l ON f.LeadId = l.LeadId
    WHERE f.FollowUpId = ?
    """

    result = db.execute_query(query, (followup_id,), fetch_one=True)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Follow-up {followup_id} not found"
        )

    return FollowUpResponse(**result)


@router.post("/", response_model=FollowUpResponse)
async def create_followup(
    request: FollowUpCreateRequest
):
    """Create a new manual follow-up task"""

    followup_id = await followup_service.create_manual_followup(
        lead_id=request.lead_id,
        action_type=request.action_type,
        scheduled_at=request.scheduled_at,
        notes=request.notes
    )

    if not followup_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create follow-up"
        )

    # Fetch and return the created follow-up
    return await get_followup(followup_id)


@router.put("/{followup_id}", response_model=FollowUpResponse)
async def update_followup(
    followup_id: int,
    request: FollowUpUpdateRequest
):
    """Update a follow-up task"""

    # Check if followup exists
    existing = db.execute_query(
        "SELECT FollowUpId FROM FollowUps WHERE FollowUpId = ?",
        (followup_id,),
        fetch_one=True
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Follow-up {followup_id} not found"
        )

    # Build update query
    updates = []
    params = []

    if request.status:
        updates.append("Status = ?")
        params.append(request.status)

    if request.notes is not None:
        updates.append("Notes = ?")
        params.append(request.notes)

    if request.completed_at:
        updates.append("CompletedAt = ?")
        params.append(request.completed_at)

    if updates:
        updates.append("UpdatedAt = SYSUTCDATETIME()")
        query = f"UPDATE FollowUps SET {', '.join(updates)} WHERE FollowUpId = ?"
        params.append(followup_id)

        db.execute_query(query, tuple(params))

    # Return updated follow-up
    return await get_followup(followup_id)


@router.delete("/{followup_id}")
async def delete_followup(
    followup_id: int
):
    """Cancel a follow-up (soft delete by setting status to cancelled)"""

    query = """
    UPDATE FollowUps
    SET Status = 'cancelled', UpdatedAt = SYSUTCDATETIME()
    WHERE FollowUpId = ?
    """

    db.execute_query(query, (followup_id,))

    return {"message": f"Follow-up {followup_id} cancelled successfully"}


@router.post("/lead/{lead_id}/schedule-drip")
async def schedule_drip_sequence(
    lead_id: int
):
    """Manually schedule drip sequence for a lead"""

    # Check if lead exists
    lead = db.execute_query(
        "SELECT LeadId FROM Leads WHERE LeadId = ?",
        (lead_id,),
        fetch_one=True
    )

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} not found"
        )

    await followup_service.schedule_drip_sequence(lead_id)

    return {"message": f"Drip sequence scheduled for lead {lead_id}"}


@router.post("/lead/{lead_id}/cancel-drip")
async def cancel_drip_sequence(
    lead_id: int
):
    """Cancel all pending drips for a lead"""

    await followup_service.cancel_drip_sequence(lead_id)

    return {"message": f"All pending drips cancelled for lead {lead_id}"}


@router.post("/process-pending")
async def process_pending_followups():
    """
    Manually trigger processing of pending follow-ups
    (Normally called by scheduler, but can be triggered manually)
    """

    processed = await followup_service.process_pending_followups()

    return {
        "message": f"Processed {processed} pending follow-ups",
        "processed_count": processed
    }
