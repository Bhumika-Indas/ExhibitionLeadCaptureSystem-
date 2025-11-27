"""
Drip System Router
Message Master, Drip Configuration, and Drip Assignment endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import json

from app.db.drip_repo import drip_repo
from app.services.file_storage_service import file_storage_service


router = APIRouter(prefix="/drip", tags=["Drip System"])


# ==================== DTOs ====================

class MessageCreateRequest(BaseModel):
    title: str
    message_type: str  # text, image, document, video
    body: Optional[str] = None
    variables: Optional[List[str]] = None


class MessageUpdateRequest(BaseModel):
    title: Optional[str] = None
    message_type: Optional[str] = None
    body: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class DripCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class DripUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DripMessageAddRequest(BaseModel):
    message_id: int
    day_number: int = 0
    send_time: str = "10:00"
    sort_order: int = 0


class DripMessageUpdateRequest(BaseModel):
    day_number: Optional[int] = None
    send_time: Optional[str] = None
    sort_order: Optional[int] = None


class ApplyDripRequest(BaseModel):
    lead_id: int
    drip_id: int


# ==================== MESSAGE MASTER ENDPOINTS ====================

@router.get("/messages")
async def get_all_messages(active_only: bool = True):
    """Get all message templates"""
    messages = drip_repo.get_all_messages(active_only=active_only)
    return {"success": True, "messages": messages, "count": len(messages)}


@router.get("/messages/{message_id}")
async def get_message(message_id: int):
    """Get single message template"""
    message = drip_repo.get_message_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"success": True, "message": message}


@router.post("/messages")
async def create_message(request: MessageCreateRequest):
    """Create a new message template"""
    variables_json = json.dumps(request.variables) if request.variables else None

    message_id = drip_repo.create_message(
        title=request.title,
        message_type=request.message_type,
        body=request.body,
        variables=variables_json
    )

    return {"success": True, "message_id": message_id}


@router.post("/messages/upload")
async def create_message_with_media(
    title: str = Form(...),
    message_type: str = Form(...),
    body: Optional[str] = Form(None),
    variables: Optional[str] = Form(None),  # JSON array string
    file: UploadFile = File(None)
):
    """Create message template with media file upload"""
    file_url = None
    file_name = None
    file_mime_type = None

    if file and message_type in ['image', 'document', 'video']:
        # Save the file
        file_path, file_size, mime_type = await file_storage_service.save_document(file, 0)
        file_url = file_path
        file_name = file.filename
        file_mime_type = mime_type

    message_id = drip_repo.create_message(
        title=title,
        message_type=message_type,
        body=body,
        file_url=file_url,
        file_name=file_name,
        file_mime_type=file_mime_type,
        variables=variables
    )

    return {"success": True, "message_id": message_id, "file_url": file_url}


@router.put("/messages/{message_id}")
async def update_message(message_id: int, request: MessageUpdateRequest):
    """Update a message template"""
    updates = {}
    if request.title:
        updates['message_title'] = request.title
    if request.message_type:
        updates['message_type'] = request.message_type
    if request.body is not None:
        updates['message_body'] = request.body
    if request.variables is not None:
        updates['variables'] = json.dumps(request.variables)
    if request.is_active is not None:
        updates['is_active'] = request.is_active

    success = drip_repo.update_message(message_id, **updates)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found or no updates")

    return {"success": True}


@router.delete("/messages/{message_id}")
async def delete_message(message_id: int):
    """Delete (deactivate) a message template"""
    success = drip_repo.delete_message(message_id)
    return {"success": success}


# ==================== DRIP MASTER ENDPOINTS ====================

@router.get("/drips")
async def get_all_drips(active_only: bool = True):
    """Get all drip sequences"""
    drips = drip_repo.get_all_drips(active_only=active_only)
    return {"success": True, "drips": drips, "count": len(drips)}


@router.get("/drips/{drip_id}")
async def get_drip(drip_id: int):
    """Get drip with all messages"""
    drip = drip_repo.get_drip_by_id(drip_id)
    if not drip:
        raise HTTPException(status_code=404, detail="Drip not found")
    return {"success": True, "drip": drip}


@router.post("/drips")
async def create_drip(request: DripCreateRequest):
    """Create a new drip sequence"""
    drip_id = drip_repo.create_drip(
        name=request.name,
        description=request.description
    )
    return {"success": True, "drip_id": drip_id}


@router.put("/drips/{drip_id}")
async def update_drip(drip_id: int, request: DripUpdateRequest):
    """Update a drip sequence"""
    updates = {}
    if request.name:
        updates['drip_name'] = request.name
    if request.description is not None:
        updates['drip_description'] = request.description
    if request.is_active is not None:
        updates['is_active'] = request.is_active

    success = drip_repo.update_drip(drip_id, **updates)
    if not success:
        raise HTTPException(status_code=404, detail="Drip not found or no updates")

    return {"success": True}


@router.delete("/drips/{drip_id}")
async def delete_drip(drip_id: int):
    """Delete (deactivate) a drip sequence"""
    success = drip_repo.delete_drip(drip_id)
    return {"success": success}


# ==================== DRIP MESSAGE ENDPOINTS ====================

@router.post("/drips/{drip_id}/messages")
async def add_message_to_drip(drip_id: int, request: DripMessageAddRequest):
    """Add a message to a drip sequence"""
    drip_message_id = drip_repo.add_message_to_drip(
        drip_id=drip_id,
        message_id=request.message_id,
        day_number=request.day_number,
        send_time=request.send_time,
        sort_order=request.sort_order
    )
    return {"success": True, "drip_message_id": drip_message_id}


@router.put("/drips/messages/{drip_message_id}")
async def update_drip_message(drip_message_id: int, request: DripMessageUpdateRequest):
    """Update a drip message (day, time, order)"""
    updates = {}
    if request.day_number is not None:
        updates['day_number'] = request.day_number
    if request.send_time is not None:
        updates['send_time'] = request.send_time
    if request.sort_order is not None:
        updates['sort_order'] = request.sort_order

    success = drip_repo.update_drip_message(drip_message_id, **updates)
    return {"success": success}


@router.delete("/drips/messages/{drip_message_id}")
async def remove_message_from_drip(drip_message_id: int):
    """Remove a message from a drip"""
    success = drip_repo.remove_message_from_drip(drip_message_id)
    return {"success": success}


# ==================== DRIP ASSIGNMENT ENDPOINTS ====================

@router.post("/apply")
async def apply_drip_to_lead(request: ApplyDripRequest):
    """Apply a drip sequence to a lead (schedules all messages)"""
    try:
        assignment_id = drip_repo.apply_drip_to_lead(
            lead_id=request.lead_id,
            drip_id=request.drip_id
        )
        return {
            "success": True,
            "assignment_id": assignment_id,
            "message": "Drip applied successfully. Day 0 messages will be sent shortly."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lead/{lead_id}/stop")
async def stop_drip(lead_id: int, assignment_id: Optional[int] = None):
    """Stop drip sequence for a lead"""
    success = drip_repo.stop_drip_for_lead(lead_id, assignment_id)
    return {"success": success, "message": "Drip stopped and pending messages cancelled"}


@router.post("/lead/{lead_id}/pause")
async def pause_drip(lead_id: int, assignment_id: Optional[int] = None):
    """Pause drip sequence for a lead (can resume later)"""
    success = drip_repo.pause_drip_for_lead(lead_id, assignment_id)
    return {"success": success, "message": "Drip paused"}


@router.post("/lead/{lead_id}/resume")
async def resume_drip(lead_id: int, assignment_id: Optional[int] = None):
    """Resume a paused drip sequence"""
    success = drip_repo.resume_drip_for_lead(lead_id, assignment_id)
    return {"success": success, "message": "Drip resumed"}


@router.get("/lead/{lead_id}/status")
async def get_lead_drip_status(lead_id: int):
    """Get current drip status for a lead"""
    status = drip_repo.get_lead_drip_status(lead_id)
    scheduled = drip_repo.get_scheduled_messages_for_lead(lead_id)
    return {
        "success": True,
        "assignment": status,
        "scheduled_messages": scheduled
    }


@router.post("/messages/{scheduled_id}/skip")
async def skip_scheduled_message(scheduled_id: int):
    """Skip a specific scheduled message"""
    success = drip_repo.skip_message(scheduled_id)
    return {"success": success}


@router.get("/assignments")
async def get_all_assignments(status: Optional[str] = None, limit: int = 100):
    """Get all drip assignments"""
    assignments = drip_repo.get_all_assignments(status=status, limit=limit)
    return {"success": True, "assignments": assignments, "count": len(assignments)}


@router.get("/pending")
async def get_pending_messages():
    """Get all pending messages ready to send"""
    messages = drip_repo.get_pending_messages_to_send()
    return {"success": True, "messages": messages, "count": len(messages)}


@router.post("/process")
async def process_pending_messages():
    """Process and send all pending drip messages"""
    from app.services.whatsapp_client import whatsapp_client
    import re

    pending = drip_repo.get_pending_messages_to_send()
    processed = 0
    failed = 0

    for msg in pending:
        try:
            # Skip if assignment is not active
            if msg.get('AssignmentStatus') != 'active':
                continue

            # Get phone number
            phone = msg.get('PrimaryVisitorPhone')
            if not phone:
                drip_repo.mark_message_failed(msg['ScheduledId'], "No phone number")
                failed += 1
                continue

            # Clean phone
            phone = re.sub(r"[^\d]", "", phone)
            if len(phone) == 12 and phone.startswith("91"):
                phone = phone[2:]

            if len(phone) != 10 or phone[0] not in '6789':
                drip_repo.mark_message_failed(msg['ScheduledId'], f"Invalid phone: {phone}")
                failed += 1
                continue

            # Replace variables in message body
            body = msg.get('MessageBody', '')
            if body:
                body = body.replace('{{name}}', msg.get('PrimaryVisitorName', 'there'))
                body = body.replace('{{company}}', msg.get('CompanyName', 'your company'))

            # Send message
            if msg['MessageType'] == 'text':
                result = await whatsapp_client.send_text(to=phone, text=body)
            else:
                # For media, send text with file URL for now
                result = await whatsapp_client.send_text(to=phone, text=body or msg.get('MessageTitle', ''))

            if result.get('success'):
                drip_repo.mark_message_sent(msg['ScheduledId'], result.get('message_id'))
                processed += 1
            else:
                drip_repo.mark_message_failed(msg['ScheduledId'], result.get('error', 'Unknown error'))
                failed += 1

        except Exception as e:
            drip_repo.mark_message_failed(msg['ScheduledId'], str(e))
            failed += 1

    return {
        "success": True,
        "processed": processed,
        "failed": failed,
        "total": len(pending)
    }
