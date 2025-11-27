"""
Analytics Router
Dashboard metrics and reports
"""

from fastapi import APIRouter, Query
from typing import Optional
from app.db.connection import db


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
async def get_summary(exhibition_id: Optional[int] = Query(None)):
    """
    Get analytics summary

    Metrics:
    - Total leads
    - Confirmed leads
    - Pending leads
    - Source breakdown
    - Confirmation rate
    """
    try:
        # Build filter
        where_clause = f"WHERE ExhibitionId = {exhibition_id}" if exhibition_id else ""

        # Total leads
        total_query = f"SELECT COUNT(*) FROM Leads {where_clause}"
        total_leads = db.execute_scalar(total_query)

        # Confirmed leads
        confirmed_query = f"""
        SELECT COUNT(*) FROM Leads
        {where_clause}
        {' AND ' if where_clause else 'WHERE '} WhatsAppConfirmed = 1
        """
        confirmed_leads = db.execute_scalar(confirmed_query)

        # Pending leads
        pending_query = f"""
        SELECT COUNT(*) FROM Leads
        {where_clause}
        {' AND ' if where_clause else 'WHERE '} StatusCode = 'new'
        """
        pending_leads = db.execute_scalar(pending_query)

        # Employee scan count
        employee_query = f"""
        SELECT COUNT(*) FROM Leads
        {where_clause}
        {' AND ' if where_clause else 'WHERE '} SourceCode = 'employee_scan'
        """
        employee_scan_count = db.execute_scalar(employee_query)

        # QR WhatsApp count
        qr_query = f"""
        SELECT COUNT(*) FROM Leads
        {where_clause}
        {' AND ' if where_clause else 'WHERE '} SourceCode = 'qr_whatsapp'
        """
        qr_whatsapp_count = db.execute_scalar(qr_query)

        # Confirmation rate
        confirmation_rate = (confirmed_leads / total_leads * 100) if total_leads > 0 else 0

        return {
            "total_leads": total_leads or 0,
            "confirmed_leads": confirmed_leads or 0,
            "pending_leads": pending_leads or 0,
            "employee_scan_count": employee_scan_count or 0,
            "qr_whatsapp_count": qr_whatsapp_count or 0,
            "confirmation_rate": round(confirmation_rate, 2)
        }

    except Exception as e:
        print(f" Analytics error: {e}")
        return {
            "total_leads": 0,
            "confirmed_leads": 0,
            "pending_leads": 0,
            "employee_scan_count": 0,
            "qr_whatsapp_count": 0,
            "confirmation_rate": 0.0
        }


@router.get("/employee-performance")
async def get_employee_performance(exhibition_id: Optional[int] = Query(None)):
    """Get lead counts by employee"""
    try:
        where_clause = f"WHERE l.ExhibitionId = {exhibition_id}" if exhibition_id else ""

        query = f"""
        SELECT
            e.EmployeeId,
            e.FullName,
            COUNT(l.LeadId) AS TotalLeads,
            SUM(CASE WHEN l.WhatsAppConfirmed = 1 THEN 1 ELSE 0 END) AS ConfirmedLeads
        FROM Employees e
        LEFT JOIN Leads l ON e.EmployeeId = l.AssignedEmployeeId
        {where_clause}
        GROUP BY e.EmployeeId, e.FullName
        ORDER BY TotalLeads DESC
        """

        results = db.execute_query(query, fetch_all=True)

        return {"success": True, "data": results}

    except Exception as e:
        print(f" Employee performance error: {e}")
        return {"success": False, "data": []}
