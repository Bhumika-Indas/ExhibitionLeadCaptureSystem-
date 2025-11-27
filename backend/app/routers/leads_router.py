"""
Leads Router
CRUD operations for leads
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.models.dto import LeadCreateRequest, LeadUpdateRequest, LeadResponse
from app.db.leads_repo import leads_repo
from app.db.messages_repo import messages_repo
from app.db.attachments_repo import attachments_repo


router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post("/", status_code=201)
async def create_lead(request: LeadCreateRequest):
    """Create new lead"""
    try:
        lead_id = leads_repo.create_lead(
            exhibition_id=request.exhibition_id,
            source_code=request.source_code,
            company_name=request.company_name,
            primary_visitor_name=request.primary_visitor_name,
            primary_visitor_designation=request.primary_visitor_designation,
            primary_visitor_phone=request.primary_visitor_phone,
            primary_visitor_email=request.primary_visitor_email,
            discussion_summary=request.discussion_summary,
            next_step=request.next_step
        )

        # Note: WhatsApp greeting sent after employee verification
        # Use POST /api/leads/{lead_id}/send-greeting endpoint

        return {"success": True, "lead_id": lead_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_leads(
    exhibition_id: Optional[int] = Query(None),
    source_code: Optional[str] = Query(None),
    status_code: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """Get leads with filters"""
    try:
        leads = leads_repo.get_leads(
            exhibition_id=exhibition_id,
            source_code=source_code,
            status_code=status_code,
            limit=limit,
            offset=offset
        )

        return {"success": True, "leads": leads, "count": len(leads)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}")
async def get_lead(lead_id: int):
    """Get lead by ID with all details"""
    try:
        lead = leads_repo.get_lead_by_id(lead_id)

        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Get related data
        persons = leads_repo.get_lead_persons(lead_id)
        addresses = leads_repo.get_lead_addresses(lead_id)
        websites = leads_repo.get_lead_websites(lead_id)
        services = leads_repo.get_lead_services(lead_id)
        topics = leads_repo.get_lead_topics(lead_id)
        messages = messages_repo.get_messages_by_lead(lead_id)
        attachments = attachments_repo.get_attachments_by_lead(lead_id)

        # Get new multi-contact fields (with fallback for missing tables)
        try:
            brands = leads_repo.get_lead_brands(lead_id)
        except Exception:
            brands = []

        try:
            phones = leads_repo.get_lead_phones(lead_id)
        except Exception:
            phones = []

        try:
            emails = leads_repo.get_lead_emails(lead_id)
        except Exception:
            emails = []

        return {
            "success": True,
            "lead": lead,
            "persons": persons,
            "addresses": addresses,
            "websites": websites,
            "services": services,
            "topics": topics,
            "messages": messages,
            "attachments": attachments,
            "brands": brands,
            "phones": phones,
            "emails": emails
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{lead_id}")
async def update_lead(lead_id: int, request: LeadUpdateRequest):
    """Update lead"""
    try:
        success = leads_repo.update_lead(
            lead_id=lead_id,
            company_name=request.company_name,
            primary_visitor_name=request.primary_visitor_name,
            primary_visitor_designation=request.primary_visitor_designation,
            primary_visitor_phone=request.primary_visitor_phone,
            primary_visitor_email=request.primary_visitor_email,
            discussion_summary=request.discussion_summary,
            next_step=request.next_step,
            status_code=request.status_code
        )

        if not success:
            raise HTTPException(status_code=404, detail="Lead not found or no changes made")

        return {"success": True, "message": "Lead updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{lead_id}")
async def delete_lead(lead_id: int, hard_delete: bool = False):
    """
    Delete lead (soft delete by default - marks IsActive=0, keeps all data)
    WARNING: hard_delete=True permanently removes from database (admin only)
    """
    try:
        if hard_delete:
            success = leads_repo.hard_delete_lead(lead_id)
            message = "Lead permanently deleted from database"
        else:
            success = leads_repo.delete_lead(lead_id)
            message = "Lead marked as inactive (soft delete - data preserved)"

        if not success:
            raise HTTPException(status_code=404, detail="Lead not found or deletion failed")

        return {"success": True, "message": message}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lead_id}/restore")
async def restore_lead(lead_id: int):
    """
    Restore a soft-deleted lead by marking IsActive=1
    """
    try:
        success = leads_repo.restore_lead(lead_id)

        if not success:
            raise HTTPException(status_code=404, detail="Lead not found or restore failed")

        return {"success": True, "message": "Lead restored successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lead_id}/send-greeting")
async def send_greeting_after_verification(lead_id: int):
    """
    Send WhatsApp greeting to visitor AFTER employee verifies lead details
    This should be called when employee confirms extracted data is correct
    Uses simple greeting message (no YES/NO confirmation needed)
    """
    try:
        from app.services.whatsapp_service import whatsapp_service

        # Verify lead exists
        lead = leads_repo.get_lead_by_id(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Check if lead has valid phone number
        phone = lead.get("PrimaryVisitorPhone")
        if not phone:
            raise HTTPException(status_code=400, detail="Lead has no phone number")

        # Send employee greeting (simple message, no confirmation needed)
        success = await whatsapp_service.send_employee_greeting(lead_id)

        if success:
            # Update lead status to confirmed (details verified by employee)
            leads_repo.update_lead(
                lead_id=lead_id,
                status_code="confirmed"
            )

            return {
                "success": True,
                "message": "WhatsApp greeting sent successfully. Lead marked as confirmed."
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send WhatsApp greeting. Check phone number validity."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}/messages")
async def get_messages(lead_id: int):
    """Get all messages for a lead"""
    try:
        messages = messages_repo.get_messages_by_lead(lead_id)
        return {"success": True, "messages": messages or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lead_id}/messages")
async def add_message(lead_id: int, sender_type: str, message_text: str, sender_employee_id: Optional[int] = None):
    """Add message to lead chat"""
    try:
        message_id = messages_repo.create_message(
            lead_id=lead_id,
            sender_type=sender_type,
            message_text=message_text,
            sender_employee_id=sender_employee_id
        )

        return {"success": True, "message_id": message_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}/journey")
async def get_lead_journey(lead_id: int):
    """
    Get complete timeline/journey of a lead
    Includes: creation, status changes, WhatsApp messages, follow-ups, drip sequences, demos, etc.
    """
    try:
        from app.db.database import get_connection

        # Verify lead exists
        lead = leads_repo.get_lead_by_id(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        timeline_events = []

        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. Lead Creation Event
            timeline_events.append({
                "id": f"lead_created_{lead['LeadId']}",
                "type": "lead_created",
                "title": "Lead Captured",
                "description": f"Lead created from {lead.get('SourceName', 'Unknown')} by {lead.get('CreatedByEmployee', 'System')}",
                "timestamp": lead['CreatedAt'].isoformat() if lead.get('CreatedAt') else None,
                "icon": "user_plus",
                "color": "blue",
                "metadata": {
                    "source": lead.get('SourceName'),
                    "exhibition": lead.get('ExhibitionName')
                }
            })

            # 2. Status Change Events (from Leads UpdatedAt and StatusCode)
            if lead.get('StatusCode') and lead['StatusCode'] != 'new':
                timeline_events.append({
                    "id": f"status_{lead['LeadId']}_{lead['StatusCode']}",
                    "type": "status_change",
                    "title": f"Status: {lead.get('StatusName', lead['StatusCode'])}",
                    "description": f"Lead status updated to {lead.get('StatusName', lead['StatusCode'])}",
                    "timestamp": lead['UpdatedAt'].isoformat() if lead.get('UpdatedAt') else lead['CreatedAt'].isoformat(),
                    "icon": "status",
                    "color": "purple",
                    "metadata": {
                        "status": lead.get('StatusName')
                    }
                })

            # 3. WhatsApp Greeting Confirmation
            if lead.get('WhatsAppConfirmed') and lead.get('ConfirmedAt'):
                timeline_events.append({
                    "id": f"whatsapp_confirmed_{lead['LeadId']}",
                    "type": "whatsapp_greeting",
                    "title": "WhatsApp Greeting Sent",
                    "description": "Initial greeting message sent via WhatsApp",
                    "timestamp": lead['ConfirmedAt'].isoformat(),
                    "icon": "whatsapp",
                    "color": "green",
                    "metadata": {
                        "phone": lead.get('PrimaryVisitorPhone')
                    }
                })

            # 4. Follow-ups and Drip Sequences
            cursor.execute("""
                SELECT
                    f.FollowUpId,
                    f.ActionType,
                    f.ScheduledAt,
                    f.CompletedAt,
                    f.Status,
                    f.Notes,
                    f.CreatedAt,
                    dat.Name as ActionName,
                    dat.Description as ActionDescription,
                    dat.IsAutomated,
                    e.FullName as CompletedBy
                FROM FollowUps f
                LEFT JOIN DripActionTypes dat ON f.ActionType = dat.ActionType
                LEFT JOIN Employees e ON f.CompletedByEmployeeId = e.EmployeeId
                WHERE f.LeadId = ?
                ORDER BY f.ScheduledAt ASC
            """, lead_id)

            followups = cursor.fetchall()
            for row in followups:
                fu_dict = dict(zip([column[0] for column in cursor.description], row))

                # Determine event type and icon
                action_type = fu_dict['ActionType']
                is_completed = fu_dict['Status'] == 'completed'
                is_automated = fu_dict.get('IsAutomated', False)

                icon = "calendar"
                color = "orange"
                title_prefix = "Scheduled"

                if is_automated:
                    icon = "auto_message"
                    color = "indigo"
                    title_prefix = "Drip Sequence"
                elif action_type == "demo":
                    icon = "presentation"
                    color = "teal"
                    title_prefix = "Demo"
                elif action_type == "callback":
                    icon = "phone"
                    color = "blue"
                    title_prefix = "Callback"
                elif action_type == "proposal":
                    icon = "document"
                    color = "purple"
                    title_prefix = "Proposal"

                if is_completed:
                    timeline_events.append({
                        "id": f"followup_{fu_dict['FollowUpId']}",
                        "type": "followup_completed",
                        "title": f"{title_prefix}: {fu_dict.get('ActionName', action_type)}",
                        "description": fu_dict.get('Notes') or fu_dict.get('ActionDescription') or f"{title_prefix} completed",
                        "timestamp": fu_dict['CompletedAt'].isoformat() if fu_dict['CompletedAt'] else fu_dict['ScheduledAt'].isoformat(),
                        "icon": icon,
                        "color": color,
                        "metadata": {
                            "action_type": action_type,
                            "completed_by": fu_dict.get('CompletedBy'),
                            "scheduled_at": fu_dict['ScheduledAt'].isoformat() if fu_dict['ScheduledAt'] else None
                        }
                    })
                elif fu_dict['Status'] == 'pending':
                    timeline_events.append({
                        "id": f"followup_{fu_dict['FollowUpId']}",
                        "type": "followup_scheduled",
                        "title": f"Upcoming: {fu_dict.get('ActionName', action_type)}",
                        "description": f"Scheduled for follow-up",
                        "timestamp": fu_dict['ScheduledAt'].isoformat(),
                        "icon": icon,
                        "color": "gray",
                        "metadata": {
                            "action_type": action_type,
                            "status": "pending"
                        }
                    })

            # 5. WhatsApp Messages (Communication History)
            cursor.execute("""
                SELECT
                    WaMessageId,
                    Direction,
                    MessageType,
                    Body,
                    Status,
                    CreatedAt
                FROM WhatsAppMessages
                WHERE LeadId = ?
                ORDER BY CreatedAt ASC
            """, lead_id)

            wa_messages = cursor.fetchall()
            for row in wa_messages:
                msg = dict(zip([column[0] for column in cursor.description], row))

                is_outbound = msg['Direction'] == 'outbound'
                timeline_events.append({
                    "id": f"whatsapp_{msg['WaMessageId']}",
                    "type": "whatsapp_message",
                    "title": f"WhatsApp {'Sent' if is_outbound else 'Received'}",
                    "description": msg['Body'][:100] + '...' if msg.get('Body') and len(msg['Body']) > 100 else msg.get('Body', f"{msg['MessageType']} message"),
                    "timestamp": msg['CreatedAt'].isoformat() if msg['CreatedAt'] else None,
                    "icon": "whatsapp",
                    "color": "green" if is_outbound else "blue",
                    "metadata": {
                        "direction": msg['Direction'],
                        "message_type": msg['MessageType'],
                        "status": msg.get('Status')
                    }
                })

            # 6. Internal Notes/Messages (LeadMessages)
            cursor.execute("""
                SELECT
                    lm.MessageId,
                    lm.SenderType,
                    lm.MessageText,
                    lm.CreatedAt,
                    e.FullName as EmployeeName
                FROM LeadMessages lm
                LEFT JOIN Employees e ON lm.SenderEmployeeId = e.EmployeeId
                WHERE lm.LeadId = ?
                ORDER BY lm.CreatedAt ASC
            """, lead_id)

            internal_messages = cursor.fetchall()
            for row in internal_messages:
                msg = dict(zip([column[0] for column in cursor.description], row))

                timeline_events.append({
                    "id": f"note_{msg['MessageId']}",
                    "type": "internal_note",
                    "title": f"Internal Note by {msg.get('EmployeeName', 'Employee')}",
                    "description": msg['MessageText'][:150] + '...' if len(msg['MessageText']) > 150 else msg['MessageText'],
                    "timestamp": msg['CreatedAt'].isoformat() if msg['CreatedAt'] else None,
                    "icon": "note",
                    "color": "yellow",
                    "metadata": {
                        "sender": msg.get('EmployeeName'),
                        "sender_type": msg['SenderType']
                    }
                })

        # Sort all events by timestamp
        timeline_events.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '', reverse=True)

        return {
            "success": True,
            "lead_id": lead_id,
            "lead_name": lead.get('PrimaryVisitorName'),
            "company_name": lead.get('CompanyName'),
            "current_status": lead.get('StatusName'),
            "timeline": timeline_events,
            "total_events": len(timeline_events)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching lead journey: {e}")
        raise HTTPException(status_code=500, detail=str(e))
