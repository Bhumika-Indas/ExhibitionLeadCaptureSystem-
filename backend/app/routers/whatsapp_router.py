"""
WhatsApp Router
Inbound webhook and outbound message management
"""

from fastapi import APIRouter, HTTPException, Request
from app.models.dto import WhatsAppWebhookRequest, WhatsAppSendRequest
from app.services.whatsapp_service import whatsapp_service


router = APIRouter(tags=["WhatsApp"])


@router.post("/inbound")
async def inbound_webhook(request: Request):
    """
    WhatsApp inbound message webhook

    Handles incoming messages from visitors
    """
    try:
        # Parse raw request body
        body = await request.json()

        # Process message
        result = await whatsapp_service.handle_inbound_message(body)

        return {"success": True, "result": result}

    except Exception as e:
        print(f" Webhook error: {e}")
        # Return 200 even on error to avoid webhook retries
        return {"success": False, "error": str(e)}


@router.get("/webhook")
async def webhook_verification(request: Request):
    """
    WhatsApp webhook verification (for initial setup)

    WhatsApp Cloud API sends GET request with challenge parameter
    """
    query_params = dict(request.query_params)

    # Facebook/WhatsApp verification
    mode = query_params.get("hub.mode")
    token = query_params.get("hub.verify_token")
    challenge = query_params.get("hub.challenge")

    if mode == "subscribe" and token == "INDAS_VERIFY_TOKEN":  # Configure this token
        return int(challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def webhook_inbound(request: Request):
    """
    WhatsApp inbound message webhook (POST)

    Handles incoming messages from WhatsApp Cloud API
    """
    try:
        # Parse raw request body
        body = await request.json()
        print(f"📥 [WEBHOOK] Received WhatsApp webhook: {body}")

        # Process message
        result = await whatsapp_service.handle_inbound_message(body)

        return {"success": True, "result": result}

    except Exception as e:
        print(f"❌ [WEBHOOK] Error: {e}")
        # Return 200 even on error to avoid webhook retries
        return {"success": False, "error": str(e)}


@router.post("/send-confirmation/{lead_id}")
async def send_confirmation(lead_id: int):
    """Manually trigger WhatsApp confirmation for a lead"""
    from app.db.leads_repo import leads_repo
    import re

    try:
        # Validate lead exists and has phone number
        lead = leads_repo.get_lead_by_id(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

        phone = lead.get("PrimaryVisitorPhone")
        if phone:
            # Sanitize phone number
            phone = re.sub(r"[^\d]", "", phone)
            if phone.startswith("91") and len(phone) == 12:
                phone = phone[2:]

        if not phone or len(phone) != 10 or phone[0] not in '6789':
            raise HTTPException(
                status_code=400,
                detail=f"Lead {lead_id} has invalid or missing phone number. Cannot send WhatsApp."
            )

        # Send confirmation
        success = await whatsapp_service.send_lead_confirmation(lead_id)

        if success:
            return {"success": True, "message": "Confirmation sent"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send confirmation")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_message(request: WhatsAppSendRequest):
    """Send ad-hoc WhatsApp message"""
    from app.services.whatsapp_client import whatsapp_client

    try:
        result = await whatsapp_client.send_text(
            to=request.to,
            text=request.message
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
