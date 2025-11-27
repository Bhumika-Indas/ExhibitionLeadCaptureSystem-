"""
Duplicates Router
Endpoints for duplicate detection and management
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from pydantic import BaseModel

from app.services.duplicate_detection_service import duplicate_detection_service
from app.db.leads_repo import leads_repo


router = APIRouter(prefix="/duplicates", tags=["Duplicates"])


class CheckDuplicateRequest(BaseModel):
    company_name: str | None = None
    phone: str | None = None
    email: str | None = None
    visitor_name: str | None = None
    exhibition_id: int | None = None


class MergeDuplicatesRequest(BaseModel):
    primary_lead_id: int
    duplicate_lead_ids: List[int]


@router.post("/check")
async def check_duplicate(request: CheckDuplicateRequest):
    """
    Check if provided lead data matches existing leads
    """
    try:
        result = duplicate_detection_service.check_duplicate_before_save(
            company_name=request.company_name,
            phone=request.phone,
            email=request.email,
            visitor_name=request.visitor_name,
            exhibition_id=request.exhibition_id
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lead/{lead_id}")
async def find_duplicates_for_lead(lead_id: int):
    """
    Find potential duplicates for a specific lead
    """
    try:
        duplicates = duplicate_detection_service.find_duplicates_for_lead(lead_id)

        return {
            "success": True,
            "lead_id": lead_id,
            "duplicate_count": len(duplicates),
            "duplicates": duplicates
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge")
async def merge_duplicates(request: MergeDuplicatesRequest):
    """
    Merge duplicate leads into primary lead
    """
    try:
        result = duplicate_detection_service.merge_leads(
            primary_lead_id=request.primary_lead_id,
            duplicate_lead_ids=request.duplicate_lead_ids
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Merge failed'))

        return {
            "success": True,
            **result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_duplicates(
    exhibition_id: int | None = Query(None),
    min_similarity: float = Query(70.0, ge=0, le=100)
):
    """
    Find all duplicate lead groups in the system
    """
    try:
        # Get all leads
        filters = {}
        if exhibition_id:
            filters['exhibition_id'] = exhibition_id

        all_leads = leads_repo.get_leads(**filters)

        # Track which leads have been checked
        checked_leads = set()
        duplicate_groups = []

        for lead in all_leads:
            lead_id = lead['LeadId']

            # Skip if already in a duplicate group
            if lead_id in checked_leads:
                continue

            # Find duplicates for this lead
            duplicates = duplicate_detection_service.find_duplicates_for_lead(lead_id)

            # Filter by minimum similarity
            filtered_duplicates = [d for d in duplicates if d['similarity_score'] >= min_similarity]

            if filtered_duplicates:
                # Add this group
                duplicate_groups.append({
                    'primary_lead': {
                        'lead_id': lead_id,
                        'company_name': lead.get('CompanyName'),
                        'visitor_name': lead.get('PrimaryVisitorName'),
                        'phone': lead.get('PrimaryVisitorPhone'),
                        'email': lead.get('PrimaryVisitorEmail'),
                        'created_at': lead.get('CreatedAt')
                    },
                    'duplicates': filtered_duplicates,
                    'count': len(filtered_duplicates)
                })

                # Mark all leads in this group as checked
                checked_leads.add(lead_id)
                for dup in filtered_duplicates:
                    checked_leads.add(dup['lead_id'])

        # Sort by number of duplicates descending
        duplicate_groups.sort(key=lambda x: x['count'], reverse=True)

        return {
            "success": True,
            "total_groups": len(duplicate_groups),
            "duplicate_groups": duplicate_groups
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
