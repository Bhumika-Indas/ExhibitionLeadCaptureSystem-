"""
Drip Analytics Router
Provides analytics and insights for drip sequences
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.services.lead_segmentation_service import lead_segmentation_service
from app.db.connection import db

router = APIRouter(prefix="/api/drip-analytics", tags=["Drip Analytics"])


@router.get("/segment-stats")
async def get_segment_stats():
    """Get statistics for each lead segment"""
    try:
        stats = lead_segmentation_service.get_segment_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/high-priority-leads")
async def get_high_priority_leads(limit: int = 20):
    """Get high priority leads (Decision Makers & Technical)"""
    try:
        leads = lead_segmentation_service.get_high_priority_leads(limit)
        return {
            "success": True,
            "leads": leads,
            "count": len(leads)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drip-performance")
async def get_drip_performance():
    """Get drip sequence performance metrics"""
    try:
        query = """
        SELECT
            f.ActionType as DripType,
            COUNT(*) as TotalSent,
            SUM(CASE WHEN f.Status = 'completed' THEN 1 ELSE 0 END) as Completed,
            SUM(CASE WHEN f.Status = 'failed' THEN 1 ELSE 0 END) as Failed,
            SUM(CASE WHEN l.Status = 'confirmed' THEN 1 ELSE 0 END) as LeadsConverted,
            CAST(SUM(CASE WHEN l.Status = 'confirmed' THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(*), 0) * 100 as ConversionRate
        FROM FollowUps f
        LEFT JOIN Leads l ON f.LeadId = l.LeadId
        WHERE f.ActionType LIKE 'drip_%'
        GROUP BY f.ActionType
        ORDER BY f.ActionType
        """

        results = db.execute_query(query, fetch_all=True)

        return {
            "success": True,
            "performance": results or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drip-timeline/{lead_id}")
async def get_lead_drip_timeline(lead_id: int):
    """Get drip timeline for a specific lead"""
    try:
        query = """
        SELECT
            FollowUpId,
            ActionType,
            ScheduledAt,
            CompletedAt,
            Status,
            Notes,
            CreatedAt
        FROM FollowUps
        WHERE LeadId = ? AND ActionType LIKE 'drip_%'
        ORDER BY ScheduledAt ASC
        """

        results = db.execute_query(query, (lead_id,), fetch_all=True)

        return {
            "success": True,
            "timeline": results or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drip-engagement-stats")
async def get_drip_engagement_stats():
    """Get overall drip engagement statistics"""
    try:
        query = """
        SELECT
            COUNT(DISTINCT f.LeadId) as TotalLeadsInDrip,
            COUNT(*) as TotalDripsSent,
            SUM(CASE WHEN f.Status = 'completed' THEN 1 ELSE 0 END) as CompletedDrips,
            SUM(CASE WHEN f.Status = 'pending' THEN 1 ELSE 0 END) as PendingDrips,
            SUM(CASE WHEN f.Status = 'cancelled' THEN 1 ELSE 0 END) as CancelledDrips,
            SUM(CASE WHEN f.Status = 'failed' THEN 1 ELSE 0 END) as FailedDrips,
            SUM(CASE WHEN l.Status = 'confirmed' THEN 1 ELSE 0 END) as LeadsConfirmed,
            CAST(SUM(CASE WHEN l.Status = 'confirmed' THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(DISTINCT f.LeadId), 0) * 100 as OverallConversionRate
        FROM FollowUps f
        LEFT JOIN Leads l ON f.LeadId = l.LeadId
        WHERE f.ActionType LIKE 'drip_%'
        """

        result = db.execute_query(query, fetch_one=True)

        return {
            "success": True,
            "stats": result or {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/segment-drip-performance")
async def get_segment_drip_performance():
    """Get drip performance breakdown by segment"""
    try:
        query = """
        SELECT
            l.Segment,
            COUNT(DISTINCT l.LeadId) as TotalLeads,
            COUNT(f.FollowUpId) as DripsSent,
            SUM(CASE WHEN f.Status = 'completed' THEN 1 ELSE 0 END) as CompletedDrips,
            SUM(CASE WHEN l.Status = 'confirmed' THEN 1 ELSE 0 END) as LeadsConfirmed,
            CAST(SUM(CASE WHEN l.Status = 'confirmed' THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(DISTINCT l.LeadId), 0) * 100 as ConversionRate
        FROM Leads l
        LEFT JOIN FollowUps f ON l.LeadId = f.LeadId AND f.ActionType LIKE 'drip_%'
        WHERE l.Segment IS NOT NULL
        GROUP BY l.Segment
        ORDER BY ConversionRate DESC
        """

        results = db.execute_query(query, fetch_all=True)

        return {
            "success": True,
            "segment_performance": results or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel-drip/{lead_id}")
async def cancel_lead_drip(lead_id: int):
    """Cancel all pending drips for a lead"""
    try:
        query = """
        UPDATE FollowUps
        SET Status = 'cancelled', UpdatedAt = SYSUTCDATETIME()
        WHERE LeadId = ? AND Status = 'pending' AND ActionType LIKE 'drip_%'
        """

        db.execute_query(query, (lead_id,))

        return {
            "success": True,
            "message": f"All pending drips cancelled for lead {lead_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
