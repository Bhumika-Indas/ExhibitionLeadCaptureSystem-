"""
WhatsApp Business Logic Service
Handles lead confirmations, inbound messages, and WhatsApp workflows
"""

import json
import re
import os
import base64
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.services.whatsapp_client import whatsapp_client
from app.db.leads_repo import leads_repo
from app.db.whatsapp_repo import whatsapp_repo
from app.db.messages_repo import messages_repo
from app.db.attachments_repo import attachments_repo
from app.db.employees_repo import employees_repo
from app.extraction.openai_normalizer import openai_normalizer
from app.extraction.card_extractor import card_extractor
from app.services.lead_segmentation_service import lead_segmentation_service
from app.utils.phone_normalizer import phone_normalizer
from app.config import settings


def sanitize_phone_number(phone: str) -> str:
    """
    Sanitize phone number by removing spaces, dashes, dots, and +91 prefix

    Args:
        phone: Raw phone number string

    Returns:
        Clean 10-digit phone number
    """
    if not phone:
        return ""

    # Remove all non-digit characters
    cleaned = re.sub(r"[^\d]", "", phone)

    # Remove +91 prefix if present
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]

    return cleaned


class WhatsAppService:
    """WhatsApp integration business logic"""

    async def send_lead_confirmation(self, lead_id: int) -> bool:
        """
        Send WhatsApp confirmation to lead after capture (WhatsApp self-service flow)
        Asks for YES/NO confirmation

        Args:
            lead_id: Lead ID

        Returns:
            Success status
        """
        # Get lead details
        lead = leads_repo.get_lead_by_id(lead_id)
        if not lead:
            print(f" Cannot send confirmation: Lead {lead_id} not found")
            return False

        # Sanitize and validate phone number
        phone = lead.get("PrimaryVisitorPhone")
        if phone:
            phone = sanitize_phone_number(phone)

        if not phone or len(phone) != 10 or phone[0] not in '6789':
            print(f" Cannot send confirmation: Lead {lead_id} has invalid phone number: {phone}")
            return False

        # Build confirmation message
        message = self._build_confirmation_message(lead)

        # Send via WhatsApp (use sanitized phone)
        result = await whatsapp_client.send_text(
            to=phone,
            text=message
        )

        # Log to database
        if result.get("success"):
            whatsapp_repo.create_message(
                lead_id=lead_id,
                direction="outbound",
                from_number=whatsapp_client.phone_number,
                to_number=phone,
                message_type="text",
                body=message,
                wa_message_id_external=result.get("message_id"),
                status="sent"
            )

            # Add system message to lead chat
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="system",
                message_text=" WhatsApp confirmation sent"
            )

            print(f" Confirmation sent to lead {lead_id}")
            return True
        else:
            print(f" Failed to send confirmation: {result.get('error')}")
            return False

    async def send_employee_greeting(self, lead_id: int) -> bool:
        """
        Send WhatsApp greeting to lead after employee verification (Employee scan flow)
        Simple greeting without YES/NO confirmation (details already verified by employee)

        Args:
            lead_id: Lead ID

        Returns:
            Success status
        """
        print(f"\n{'='*80}")
        print(f"📨 SEND EMPLOYEE GREETING - Lead ID: {lead_id}")
        print(f"{'='*80}")

        # Get lead details
        lead = leads_repo.get_lead_by_id(lead_id)
        if not lead:
            print(f"❌ Cannot send greeting: Lead {lead_id} not found")
            return False

        print(f"✓ Lead found: {lead.get('CompanyName')} - {lead.get('PrimaryVisitorName')}")

        # Sanitize and validate phone number
        phone = lead.get("PrimaryVisitorPhone")
        print(f"📞 Original phone: {phone}")

        if phone:
            phone = sanitize_phone_number(phone)
            print(f"📞 Sanitized phone: {phone}")

        if not phone or len(phone) != 10 or phone[0] not in '6789':
            print(f"❌ Cannot send greeting: Lead {lead_id} has invalid phone number: {phone}")
            return False

        print(f"✓ Phone validated: {phone}")

        # Build employee greeting message (simple, no confirmation needed)
        message = self._build_employee_greeting_message(lead)
        print(f"\n📝 Message to send:")
        print(f"{'-'*80}")
        print(message)
        print(f"{'-'*80}\n")

        # Send via WhatsApp (use sanitized phone)
        print(f"🚀 Calling WhatsApp API...")
        print(f"   Method: POST")
        print(f"   Endpoint: /api/send-message")
        print(f"   To: {phone}")

        result = await whatsapp_client.send_text(
            to=phone,
            text=message
        )

        print(f"\n📥 WhatsApp API Result:")
        print(f"   Success: {result.get('success')}")
        print(f"   Message ID: {result.get('message_id')}")
        print(f"   Status: {result.get('status')}")
        if not result.get('success'):
            print(f"   Error: {result.get('error')}")

        # Log to database
        if result.get("success"):
            whatsapp_repo.create_message(
                lead_id=lead_id,
                direction="outbound",
                from_number=whatsapp_client.phone_number,
                to_number=phone,
                message_type="text",
                body=message,
                wa_message_id_external=result.get("message_id"),
                status="sent"
            )

            # Add system message to lead chat
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="system",
                message_text="👋 WhatsApp greeting sent (employee-verified)"
            )

            print(f"👋 Employee greeting sent to lead {lead_id}")
            return True
        else:
            print(f" Failed to send greeting: {result.get('error')}")
            return False

    def _build_confirmation_message(self, lead: Dict[str, Any]) -> str:
        """Build confirmation message text (for WhatsApp self-service flow)"""
        company = lead.get("CompanyName") or "your company"
        name = lead.get("PrimaryVisitorName") or "there"
        exhibition = lead.get("ExhibitionName") or "the exhibition"

        message = f"""Hello {name}!

Thank you for visiting INDAS Analytics at {exhibition}.

We've captured your details:
Company: {company}
"""

        if lead.get("DiscussionSummary"):
            message += f"Discussion: {lead['DiscussionSummary']}\n"

        message += """
Please reply:
 YES - if details are correct
 NO - if corrections needed

Looking forward to connecting with you!

- Team INDAS Analytics"""

        return message

    def _build_employee_greeting_message(self, lead: Dict[str, Any]) -> str:
        """Build simple greeting message (for employee-scanned cards - no confirmation needed)"""
        company = lead.get("CompanyName") or "your company"
        name = lead.get("PrimaryVisitorName") or "there"
        exhibition = lead.get("ExhibitionName") or "the exhibition"

        message = f"""Hello {name} 👋

It was a pleasure meeting you today at **{exhibition}** — thank you for visiting the INDAS Analytics booth!

We have captured your details:
🏢 Company: {company}

Looking forward to staying connected and supporting you further.

Warm regards,
Team INDAS Analytics"""

        return message

    async def handle_inbound_message(self, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle inbound WhatsApp message from webhook

        Args:
            webhook_payload: Raw webhook data from WhatsApp provider

        Returns:
            Processing result
        """
        print(f"📥 Inbound WhatsApp message: {json.dumps(webhook_payload, indent=2)[:500]}...")

        # Parse webhook (format depends on provider)
        message_data = self._parse_webhook(webhook_payload)

        if not message_data:
            return {"status": "ignored", "reason": "Could not parse webhook"}

        # Save media file if present
        media_url = None
        if message_data.get("media_url"):
            print(f"📥 Media detected: {message_data.get('media_url')}")
            media_url = await self._save_media_file(message_data)
            if media_url:
                print(f"✅ Media saved locally: {media_url}")
            else:
                print(f"❌ Failed to save media locally")

        # Save raw message to database
        wa_msg_id = whatsapp_repo.create_message(
            lead_id=None,  # Will link later
            direction="inbound",
            from_number=message_data["from"],
            to_number=message_data["to"],
            message_type=message_data["type"],
            body=message_data.get("text"),
            media_url=media_url,
            wa_message_id_external=message_data.get("id"),
            raw_payload_json=json.dumps(webhook_payload),
            status="received"
        )

        # ============================================================
        # 3-STEP SENDER IDENTIFICATION
        # ============================================================
        sender_phone = message_data["from"]

        # Check if this is a LID (masked identifier) like "237309945499749@lid"
        if "@lid" in sender_phone:
            print(f"⚠️ WARNING: Received WhatsApp LID (masked phone): {sender_phone}")
            print(f"   This is NOT a real phone number. Cannot find existing lead by phone.")
            print(f"   Sender name: {message_data.get('sender_name')}")
            # For LID, we cannot reliably match to existing leads by phone
            is_employee = False
            employee = None
            lead = None
        else:
            # Step 1: Check if sender is an EMPLOYEE
            print(f"🔍 Checking if {sender_phone} is an employee...")
            employee = employees_repo.find_employee_by_phone(sender_phone)
            is_employee = employee is not None

            if is_employee:
                print(f"👤 EMPLOYEE detected: {employee.get('FullName')} (ID: {employee.get('EmployeeId')})")
                print(f"   Employees can scan multiple visiting cards")
                lead = None  # Don't link to existing lead for employees
            else:
                # Step 2: Check if sender is an EXISTING LEAD
                lead = leads_repo.find_lead_by_phone(sender_phone)

                if lead:
                    print(f"✅ EXISTING LEAD found: LeadId={lead.get('LeadId')}, Name={lead.get('PrimaryVisitorName')}")
                else:
                    # Step 2B: Fallback - try matching last 8 digits (for LID-like numbers)
                    print(f"🔍 No exact match. Trying fallback with last 8 digits...")
                    lead = leads_repo.find_lead_by_partial_phone(sender_phone)

                    if lead:
                        print(f"✅ LEAD found via partial match: LeadId={lead.get('LeadId')}, Name={lead.get('PrimaryVisitorName')}")
                    else:
                        # Step 3: Sender is a NEW VISITOR
                        print(f"🆕 NEW VISITOR: {sender_phone}")

        # Handle based on message type
        msg_type = message_data["type"]

        if msg_type == "text":
            if is_employee:
                # EMPLOYEE sending text: Check for their most recent lead
                # This allows employees to confirm/correct leads they just created
                from app.db.connection import db
                recent_lead_query = """
                SELECT TOP 1 LeadId, CompanyName, PrimaryVisitorName, PrimaryVisitorPhone, StatusCode
                FROM Leads
                WHERE AssignedEmployeeId = ?
                ORDER BY CreatedAt DESC
                """
                recent_lead = db.execute_query(recent_lead_query, (employee.get('EmployeeId'),), fetch_one=True)

                if recent_lead and recent_lead.get('StatusCode') in ['new', 'needs_correction']:
                    # Employee is responding to their most recent lead
                    print(f"📝 Employee responding to recent lead {recent_lead.get('LeadId')}")
                    return await self._handle_text_response(recent_lead, message_data["text"], wa_msg_id, sender_phone=sender_phone)
                else:
                    # Employee just saying hi or asking something - acknowledge
                    print(f"💬 Employee general message - acknowledging")
                    await whatsapp_client.send_text(
                        to=sender_phone,
                        text=f"Hello {employee.get('FullName')}! 👋\n\nSend a visiting card image to create a new lead.\n\n- Team INDAS Analytics"
                    )
                    return {"status": "employee_acknowledged", "employee_id": employee.get('EmployeeId')}

            elif lead:
                # Handle text response from existing lead (YES/NO/correction)
                return await self._handle_text_response(lead, message_data["text"], wa_msg_id, sender_phone=sender_phone)
            else:
                # Handle text from new visitor (Flow B - they might be explaining their need)
                return await self._handle_text_from_new_visitor(message_data, wa_msg_id)

        elif msg_type == "audio":
            # Handle voice note
            if is_employee:
                # EMPLOYEE sending voice note: Check for their most recent lead
                from app.db.connection import db
                recent_lead_query = """
                SELECT TOP 1 LeadId, CompanyName, PrimaryVisitorName, PrimaryVisitorPhone, StatusCode
                FROM Leads
                WHERE AssignedEmployeeId = ?
                ORDER BY CreatedAt DESC
                """
                recent_lead = db.execute_query(recent_lead_query, (employee.get('EmployeeId'),), fetch_one=True)

                if recent_lead:
                    print(f"🎤 Employee sending voice note for lead {recent_lead.get('LeadId')}")
                    return await self._handle_voice_note(recent_lead, message_data, wa_msg_id, media_url, sender_phone=sender_phone)
                else:
                    await whatsapp_client.send_text(
                        to=sender_phone,
                        text=f"Please send a visiting card first to create a lead, then you can add voice notes.\n\n- Team INDAS Analytics"
                    )
                    return {"status": "no_lead_for_audio", "employee_id": employee.get('EmployeeId')}

            elif lead:
                # Existing lead sending voice note
                return await self._handle_voice_note(lead, message_data, wa_msg_id, media_url, sender_phone=sender_phone)
            else:
                # New visitor sending audio - not supported
                await whatsapp_client.send_text(
                    to=sender_phone,
                    text="Please send your visiting card image first.\n\n- Team INDAS Analytics"
                )
                return {"status": "audio_without_lead"}

        elif msg_type == "image":
            # Handle image based on sender type

            if is_employee:
                # EMPLOYEE: Always create new lead from visiting card
                print(f"📸 Employee scanning visiting card - creating new lead")
                return await self._handle_qr_submission(
                    message_data,
                    wa_msg_id,
                    media_url,
                    employee_id=employee.get('EmployeeId')
                )

            elif lead:
                # EXISTING LEAD: Treat as additional media/update
                print(f"📸 Existing lead sending image - treating as media attachment")
                return await self._handle_media_from_lead(
                    lead,
                    message_data,
                    wa_msg_id,
                    media_url,
                    "image"
                )

            else:
                # NEW VISITOR: Create new lead from visiting card
                # Check for LID duplicates
                if "@lid" in sender_phone:
                    existing_wa_msg = whatsapp_repo.find_by_sender_lid(sender_phone)
                    if existing_wa_msg and existing_wa_msg.get("LeadId"):
                        lead_id = existing_wa_msg["LeadId"]
                        print(f"✅ Found existing lead {lead_id} with same LID {sender_phone}")
                        return await self._handle_media_from_lead(
                            leads_repo.get_lead_by_id(lead_id),
                            message_data,
                            wa_msg_id,
                            media_url,
                            "image"
                        )

                print(f"📸 New visitor sending visiting card - creating new lead")
                return await self._handle_qr_submission(message_data, wa_msg_id, media_url)

        elif msg_type in ["document", "video"] and lead:
            # Handle document/video from existing lead
            return await self._handle_media_from_lead(lead, message_data, wa_msg_id, media_url, msg_type)

        else:
            return {"status": "ignored", "reason": f"Unhandled message type: {msg_type} or no lead found"}

    async def _save_media_file(self, message_data: Dict[str, Any]) -> Optional[str]:
        """
        Download media from WhatsApp gateway URL and save to disk

        Returns:
            URL path to saved file
        """
        try:
            media_url = message_data.get("media_url")
            if not media_url:
                return None

            # Download file from gateway with auth headers
            import httpx
            headers = {
                "X-API-Key": settings.WHATSAPP_API_KEY,
                "Authorization": f"Bearer {settings.WHATSAPP_ACCOUNT_TOKEN}"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(media_url, headers=headers)

                if response.status_code != 200:
                    print(f"❌ Failed to download media: HTTP {response.status_code}")
                    return None

                file_bytes = response.content

            # Determine file extension from mimetype
            mimetype = message_data.get("media_mimetype", "application/octet-stream")
            ext_map = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
                "audio/ogg": ".ogg",
                "audio/mpeg": ".mp3",
                "audio/mp4": ".m4a",
                "video/mp4": ".mp4",
                "application/pdf": ".pdf",
                "application/msword": ".doc",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            }
            ext = ext_map.get(mimetype, ".bin")

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"whatsapp_{timestamp}_{unique_id}{ext}"

            # Create upload directory if not exists
            upload_dir = os.path.join(settings.UPLOAD_DIR, "whatsapp")
            os.makedirs(upload_dir, exist_ok=True)

            # Save file
            file_path = os.path.join(upload_dir, filename)
            with open(file_path, "wb") as f:
                f.write(file_bytes)

            file_url = f"/uploads/whatsapp/{filename}"
            print(f"✅ Downloaded and saved media: {file_url} ({len(file_bytes)} bytes)")
            return file_url

        except Exception as e:
            print(f"❌ Error downloading media file: {e}")
            return None

    async def _handle_voice_note(
        self,
        lead: Dict[str, Any],
        message_data: Dict[str, Any],
        wa_msg_id: int,
        media_url: Optional[str],
        sender_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle voice note from visitor or employee with transcription and classification"""
        lead_id = lead["LeadId"]
        reply_to_phone = sender_phone or lead.get("PrimaryVisitorPhone")

        # Link WhatsApp message to lead
        whatsapp_repo.update_message_lead(wa_msg_id, lead_id)

        # Save attachment to lead
        if media_url:
            attachments_repo.create_attachment(
                lead_id=lead_id,
                attachment_type="voice_note_inbound",
                file_url=media_url,
                mime_type=message_data.get("media_mimetype", "audio/ogg")
            )

        transcript = None
        intent = None

        # Try to transcribe and classify the voice note
        if media_url:
            try:
                from app.extraction.voice_transcriber import voice_transcriber
                from app.services.advanced_intent_classifier import advanced_intent_classifier

                # Download and transcribe
                audio_path = os.path.join(settings.UPLOAD_DIR, media_url.lstrip("/uploads/"))
                print(f"🔍 Checking audio file at: {audio_path}")
                print(f"🔍 File exists: {os.path.exists(audio_path)}")

                if os.path.exists(audio_path):
                    print(f"🎤 Transcribing voice note: {audio_path}")
                    result = voice_transcriber.transcribe_and_summarize(
                        audio_file_path=audio_path,
                        context=f"Lead discussion for {lead.get('CompanyName', 'visitor')}"
                    )
                    transcript = result.transcript
                    print(f"✅ Transcription: {transcript[:100]}...")

                    # Classify intent from transcript
                    intent_result = advanced_intent_classifier.classify_with_context(
                        message_text=transcript,
                        conversation_state=lead.get('ConversationState'),
                        sender_type="visitor",
                        lead_data=lead
                    )
                    intent = intent_result.get('intent')
                    print(f"🤖 Voice note intent: {intent}")

                    # Handle based on intent
                    if intent == "CORRECTION":
                        # Parse corrections from transcript
                        from app.utils.correction_parser import correction_parser
                        corrections = correction_parser.parse_correction(transcript)
                        if corrections:
                            correction_parser.apply_corrections_to_lead(lead_id, corrections)
                            print(f"✅ Applied corrections from voice note: {corrections}")

                    elif intent in ["DEMO_SCHEDULE", "MEETING_SCHEDULE"]:
                        # Extract datetime and create follow-up
                        from app.utils.datetime_parser import datetime_parser
                        parsed_dt = datetime_parser.parse_datetime_from_text(transcript)
                        if parsed_dt:
                            print(f"📅 Scheduling from voice note: {parsed_dt['formatted']}")
                            # Create follow-up (similar to text-based scheduling)
                else:
                    print(f"❌ Audio file not found at: {audio_path}")
                    print(f"❌ UPLOAD_DIR: {settings.UPLOAD_DIR}")
                    print(f"❌ media_url: {media_url}")

            except Exception as e:
                import traceback
                print(f"⚠️ Voice transcription/classification error: {e}")
                print(f"⚠️ Full traceback: {traceback.format_exc()}")

        # Add message to lead chat with transcript if available
        if transcript:
            message_text = f"🎤 Voice note: {transcript}"
        else:
            message_text = f"🎤 Voice note received from {message_data.get('sender_name', 'visitor')}"

        messages_repo.create_message(
            lead_id=lead_id,
            sender_type="visitor",
            message_text=message_text,
            whatsapp_message_id=str(wa_msg_id)
        )

        # Send acknowledgment
        if transcript and intent:
            ack_text = f"🎤 Voice note received and processed.\n\nDetected: {intent.replace('_', ' ').title()}\n\nOur team will follow up accordingly."
        else:
            ack_text = "Thank you for your voice message! Our team will listen and respond shortly."

        await whatsapp_client.send_text(
            to=reply_to_phone,
            text=ack_text
        )

        return {
            "status": "voice_note_processed",
            "lead_id": lead_id,
            "media_url": media_url,
            "transcript": transcript,
            "intent": intent
        }

    async def _handle_media_from_lead(
        self,
        lead: Dict[str, Any],
        message_data: Dict[str, Any],
        wa_msg_id: int,
        media_url: Optional[str],
        media_type: str
    ) -> Dict[str, Any]:
        """Handle media (image/document/video) from existing lead"""
        lead_id = lead["LeadId"]

        # Link WhatsApp message to lead
        whatsapp_repo.update_message_lead(wa_msg_id, lead_id)

        # Save attachment
        if media_url:
            attachment_type = f"{media_type}_inbound"
            attachments_repo.create_attachment(
                lead_id=lead_id,
                attachment_type=attachment_type,
                file_url=media_url,
                mime_type=message_data.get("media_mimetype")
            )

        # Add message to lead chat
        caption = message_data.get("text", "")
        msg_text = f"📎 {media_type.capitalize()} received"
        if caption:
            msg_text += f": {caption}"

        messages_repo.create_message(
            lead_id=lead_id,
            sender_type="visitor",
            message_text=msg_text,
            whatsapp_message_id=str(wa_msg_id)
        )

        return {
            "status": f"{media_type}_received",
            "lead_id": lead_id,
            "media_url": media_url
        }

    async def _handle_text_from_new_visitor(
        self,
        message_data: Dict[str, Any],
        wa_msg_id: int
    ) -> Dict[str, Any]:
        """
        Handle text message from unknown visitor (Flow B)

        When visitor scans QR and sends text, guide them to send visiting card.
        Reply in the same language they used (auto-detect Hindi/English/Hinglish).
        """
        sender_jid = message_data.get("from", "")  # WhatsApp JID like 919876543210@lid
        sender_name = message_data.get("sender_name", "")
        text = message_data.get("text", "")

        print(f"📨 _handle_text_from_new_visitor called")
        print(f"   From: {sender_jid}")
        print(f"   Name: {sender_name}")
        print(f"   Text: {text}")

        # CRITICAL: Check if this is a LID (masked phone)
        if "@lid" in sender_jid:
            print(f"⚠️  Cannot send reply to LID: {sender_jid}")
            print(f"   LID is a masked/garbage number. WhatsApp message will fail.")
            print(f"   Storing message but NOT sending auto-reply.")
            print(f"   ACTION REQUIRED: Contact WhatsApp API provider to send real phone numbers!")

            return {
                "status": "lid_detected",
                "message": f"Text received from new visitor with LID. Cannot send reply to masked number.",
                "visitor_text": text,
                "from": sender_jid,
                "sender_name": sender_name,
                "warning": "LID detected - no auto-reply sent"
            }

        # Detect language from user's message
        is_hindi = self._detect_hindi_script(text)

        # Build reply in appropriate language
        if is_hindi:
            # Pure Hindi/Devanagari detected
            reply = f"""नमस्ते{' ' + sender_name if sender_name else ''}! 🙏

कृपया अपना *Visiting Card की फोटो* भेजें ताकि हम आपकी details सेव कर सकें।

Card भेजने के बाद हम आपको confirm करेंगे। ✅"""
        else:
            # English or Hinglish
            reply = f"""Hello{' ' + sender_name if sender_name else ''}! 👋

Please send your *Visiting Card photo* so we can save your details.

We'll confirm once we process your card. ✅"""

        # Reply to sender
        print(f"📤 Sending greeting reply to: {sender_jid}")
        await whatsapp_client.send_text(to=sender_jid, text=reply)
        print(f"✅ Greeting reply sent successfully")

        return {
            "status": "instructed",
            "message": "Visitor asked to send visiting card",
            "visitor_text": text,
            "from": sender_jid
        }

    def _detect_hindi_script(self, text: str) -> bool:
        """Detect if text contains Devanagari (Hindi) characters"""
        if not text:
            return False
        # Check for Devanagari Unicode range (U+0900 to U+097F)
        devanagari_count = sum(1 for char in text if '\u0900' <= char <= '\u097F')
        return devanagari_count > len(text) * 0.3  # >30% Hindi characters

    async def _handle_text_response(
        self,
        lead: Dict[str, Any],
        text: str,
        wa_msg_id: int,
        sender_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle text response from visitor or employee

        Args:
            lead: Lead dict
            text: Message text
            wa_msg_id: WhatsApp message ID
            sender_phone: Phone number of the sender (for reply). If None, uses lead's phone.
        """
        lead_id = lead["LeadId"]
        # Use sender_phone for replies, fallback to lead's phone if not provided
        reply_to_phone = sender_phone or lead.get("PrimaryVisitorPhone")

        # Check if sender is an employee
        is_employee_sender = False
        if sender_phone:
            employee_check = employees_repo.find_employee_by_phone(sender_phone)
            is_employee_sender = employee_check is not None

        print(f"📨 _handle_text_response called for Lead {lead_id}")
        print(f"   Text: {text}")
        print(f"   Sender is employee: {is_employee_sender}")
        print(f"   Reply will be sent to: {reply_to_phone}")

        # Link WhatsApp message to lead
        whatsapp_repo.update_message_status(wa_msg_id, "processed")

        text_lower = text.lower().strip()

        # -------------------------------------------------------
        # 🚀 BUSINESS INTENTS (HIGHEST PRIORITY)
        # -------------------------------------------------------
        # Check for demo, meeting, problem, requirement requests FIRST
        # These should be processed BEFORE correction or AI logic

        if any(kw in text_lower for kw in ["demo", "schedule demo", "book demo", "demo schedule"]):
            print(f"🎯 DEMO REQUEST detected")
            return await self._process_demo_request(lead, text, wa_msg_id, reply_to_phone)

        if any(kw in text_lower for kw in ["meeting", "schedule meeting", "call", "schedule call"]):
            print(f"🎯 MEETING REQUEST detected")
            return await self._process_meeting_request(lead, text, wa_msg_id, reply_to_phone)

        if any(kw in text_lower for kw in ["problem", "issue", "not working", "error", "help"]):
            print(f"🎯 PROBLEM REPORT detected")
            return await self._process_problem_report(lead, text, wa_msg_id, reply_to_phone)

        if any(kw in text_lower for kw in ["requirement", "quotation", "quote", "pricing", "price"]):
            print(f"🎯 REQUIREMENT INQUIRY detected")
            return await self._process_requirement(lead, text, wa_msg_id, reply_to_phone)

        # -------------------------------------------------------
        # 🔍 RULE-BASED CORRECTION DETECTION (HIGH PRIORITY FIX)
        # -------------------------------------------------------
        # Detect pattern-based corrections BEFORE AI classification
        # Examples: "Designation-HR", "Name-Kiran", "Company-ABC Prints"

        patterns = [
            r"name[:\- ]",
            r"company[:\- ]",
            r"designation[:\- ]",
            r"phone[:\- ]",
            r"email[:\- ]",
            r"correct",
            r"change",
            r"गलत",
            r"सही",
            r"designation",
            r"role",
        ]

        import re
        if any(re.search(p, text_lower) for p in patterns):
            intent = "CORRECTION_TEXT"
            print(f"✅ Pattern-based correction detected: {intent}")
        else:
            # If no patterns matched → use AI intent
            print(f"🤖 Classifying intent with OpenAI...")
            intent_result = openai_normalizer.normalize_whatsapp_intent(text)
            intent = intent_result["intent"]
            print(f"✅ Intent classified as: {intent}")

        # Update lead based on intent
        if intent == "CONFIRM_YES":
            leads_repo.update_lead(
                lead_id=lead_id,
                status_code="confirmed",
                whatsapp_confirmed=True
            )

            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f" Confirmed: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            # Detect language from user's message
            is_hindi = self._detect_hindi_script(text)

            # Send thank you message in appropriate language
            if is_hindi:
                confirm_msg = "✅ धन्यवाद! आपकी जानकारी save हो गई है और हमारी team को भेज दी गई है। हम जल्द ही आपसे संपर्क करेंगे।\n\n- Team INDAS Analytics"
            else:
                confirm_msg = "✅ Thank you! Your information has been saved and sent to our team. We will contact you shortly.\n\n- Team INDAS Analytics"

            await whatsapp_client.send_text(
                to=reply_to_phone,
                text=confirm_msg
            )

            return {"status": "confirmed", "lead_id": lead_id}

        elif intent == "CONFIRM_NO":
            leads_repo.update_lead(
                lead_id=lead_id,
                status_code="needs_correction"
            )

            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f" Needs correction: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            # Detect language from user's message
            is_hindi = self._detect_hindi_script(text)

            # Send correction instructions in appropriate language
            if is_hindi:
                correction_instructions = """कोई बात नहीं! कृपया सही जानकारी इस format में भेजें:

Name: [आपका नाम]
Company: [कंपनी का नाम]
Designation: [आपका पद]
Phone: [आपका फोन नंबर]

या फिर बस वो detail भेजें जो गलत है।

- Team INDAS Analytics"""
            else:
                correction_instructions = """No problem! Please send the correct information in this format:

Name: [Your Name]
Company: [Company Name]
Designation: [Your Position]
Phone: [Your Phone Number]

Or just send the detail that is incorrect.

- Team INDAS Analytics"""

            await whatsapp_client.send_text(
                to=reply_to_phone,
                text=correction_instructions
            )

            return {"status": "needs_correction", "lead_id": lead_id}

        elif intent == "CORRECTION_TEXT":
            # Check if this is just the word "correction" or actual correction data
            text_lower = text.lower().strip()

            if text_lower in ['correction', 'corrections', 'गलत', 'wrong', 'correct']:
                # User just said "correction" without providing details
                # Ask them what to correct
                is_hindi = self._detect_hindi_script(text)

                if is_hindi:
                    correction_prompt = """कृपया बताएं क्या गलत है और सही जानकारी भेजें:

Name: [आपका नाम]
Company: [कंपनी का नाम]
Designation: [आपका पद]
Phone: [आपका फोन नंबर]

या फिर बस वो detail भेजें जो गलत है।

- Team INDAS Analytics"""
                else:
                    correction_prompt = """Please tell us what's incorrect and provide the correct information:

Name: [Your name]
Company: [Company name]
Designation: [Your designation]
Phone: [Your phone number]

Or just send the detail that is incorrect.

- Team INDAS Analytics"""

                await whatsapp_client.send_text(
                    to=reply_to_phone,
                    text=correction_prompt
                )

                return {"status": "correction_requested", "lead_id": lead_id}

            # User provided actual correction data
            # Step 1: Parse corrections
            from app.utils.correction_parser import correction_parser
            corrections = correction_parser.parse_correction(text)

            # Step 2: Save message
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f"✏️ Correction: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            # Step 3: Apply corrections if found
            if corrections:
                success = correction_parser.apply_corrections_to_lead(lead_id, corrections)
                if success:
                    # Build correction summary
                    correction_summary = "\n".join([f"• {k.title()}: {v}" for k, v in corrections.items()])

                    # Detect language
                    is_hindi = self._detect_hindi_script(text)

                    # Send success acknowledgment
                    if is_hindi:
                        correction_ack = f"✅ धन्यवाद! निम्नलिखित corrections apply हो गए हैं:\n\n{correction_summary}\n\n- Team INDAS Analytics"
                    else:
                        correction_ack = f"✅ Thank you! The following corrections have been applied:\n\n{correction_summary}\n\n- Team INDAS Analytics"

                    await whatsapp_client.send_text(
                        to=reply_to_phone,
                        text=correction_ack
                    )

                    return {"status": "correction_applied", "lead_id": lead_id, "corrections": corrections}

            # If no parseable corrections, just save and acknowledge
            leads_repo.update_lead(
                lead_id=lead_id,
                status_code="needs_correction"
            )

            is_hindi = self._detect_hindi_script(text)
            if is_hindi:
                correction_ack = "✅ धन्यवाद! आपका correction save हो गया है। हमारी team इसे update कर देगी।\n\n- Team INDAS Analytics"
            else:
                correction_ack = "✅ Thank you! Your correction has been saved. Our team will review it.\n\n- Team INDAS Analytics"

            await whatsapp_client.send_text(
                to=reply_to_phone,
                text=correction_ack
            )

            return {"status": "correction_logged", "lead_id": lead_id}

        # ---------------------------------------
        # HARD-CODED BUSINESS INTENT HANDLING (Keyword-based, NO OpenAI)
        # ---------------------------------------
        # Note: text_lower already defined above in pattern detection

        # ---------------------------
        # DEMO SCHEDULING WORKFLOW (Enhanced with NLP Date/Time Parsing)
        # ---------------------------
        if any(kw in text_lower for kw in ["demo", "product demo", "schedule demo", "book demo"]):

            # Step 1: Save message to Chat tab
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f"📅 Demo Request: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            # Step 2: Parse datetime using NLP
            from app.utils.datetime_parser import datetime_parser
            from app.utils.employee_finder import employee_finder

            parsed_dt = datetime_parser.parse_datetime_from_text(text)
            if parsed_dt:
                scheduled_at = parsed_dt['datetime']
                scheduled_display = parsed_dt['formatted']
                print(f"📅 Parsed datetime from text: {scheduled_display}")
            else:
                # Fallback: default next day 4PM
                scheduled_at = datetime.utcnow() + timedelta(days=1)
                scheduled_at = scheduled_at.replace(hour=16, minute=0, second=0)
                scheduled_display = scheduled_at.strftime("%d %B %Y at %I:%M %p")

            # Step 3: Create follow-up entry
            from app.db.connection import db
            db.execute_query(
                """
                INSERT INTO FollowUps (LeadId, ScheduledAt, ActionType, Notes, Status, CreatedAt)
                VALUES (?, ?, 'demo', ?, 'pending', SYSUTCDATETIME())
                """,
                (lead_id, scheduled_at, text)
            )
            print(f"✅ Demo follow-up created for Lead {lead_id} at {scheduled_display}")

            # Step 4: Send confirmation to visitor
            await whatsapp_client.send_text(
                to=reply_to_phone,
                text=f"✅ Demo scheduled for {scheduled_display}.\nOur team will contact you.\n\n- Team INDAS Analytics"
            )

            # Step 5: Check if specific employee mentioned (e.g., "schedule with Minesh")
            mentioned_emp_name = datetime_parser.extract_employee_name(text)
            target_employee = None

            if mentioned_emp_name:
                # Find employee by name
                target_employee = employee_finder.find_by_name(mentioned_emp_name)
                if target_employee:
                    print(f"👤 Employee mentioned in message: {target_employee.get('FullName')}")
                    # Reassign lead to mentioned employee
                    leads_repo.update_lead(
                        lead_id=lead_id,
                        assigned_employee_id=target_employee.get('EmployeeId')
                    )
                    print(f"✅ Lead reassigned to {target_employee.get('FullName')}")

            # Step 6: Determine who to notify
            if target_employee:
                # Notify the mentioned employee
                assigned_emp = target_employee
            else:
                # Notify currently assigned employee or admin
                assigned_emp_id = lead.get("AssignedEmployeeId")
                if assigned_emp_id:
                    assigned_emp = employees_repo.get_employee_by_id(assigned_emp_id)
                else:
                    assigned_emp = None

            if assigned_emp and assigned_emp.get("Phone"):
                emp_phone = assigned_emp["Phone"]
                emp_name = assigned_emp.get("FullName", "team member")
                # Add country code if missing
                if not emp_phone.startswith("91"):
                    emp_phone = "91" + emp_phone
            else:
                emp_phone = settings.EXHIBITION_ADMIN_PHONE
                emp_name = "Admin"

            # Step 7: Send notification to employee
            await whatsapp_client.send_text(
                to=emp_phone,
                text=f"""📅 *New Demo Request Received*

Lead: {lead.get('PrimaryVisitorName', 'Unknown')}
Company: {lead.get('CompanyName', 'Unknown')}
Requested Time: {scheduled_display}

Notes:
"{text}"

Please follow up.

- INDAS Lead Manager"""
            )
            print(f"📲 Demo notification sent to {emp_name}: {emp_phone}")

            return {"status": "demo_scheduled", "lead_id": lead_id, "assigned_to": emp_name}



        # ---------------------------
        # MEETING SCHEDULING WORKFLOW (Complete with Employee Notification)
        # ---------------------------
        if any(kw in text_lower for kw in ["meeting", "schedule meeting", "call", "book meeting"]):

            # Step 1: Save message to Chat tab
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f"📅 Meeting Request: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            # Step 2: Auto schedule time (default next day 12PM)
            scheduled_at = datetime.utcnow() + timedelta(days=1)
            scheduled_at = scheduled_at.replace(hour=12, minute=0, second=0)
            scheduled_display = scheduled_at.strftime("%d %B %Y at %I:%M %p")

            # Step 3: Create follow-up entry
            from app.db.connection import db
            db.execute_query(
                """
                INSERT INTO FollowUps (LeadId, ScheduledAt, ActionType, Notes, Status, CreatedAt)
                VALUES (?, ?, 'meeting', ?, 'pending', SYSUTCDATETIME())
                """,
                (lead_id, scheduled_at, text)
            )
            print(f"✅ Meeting follow-up created for Lead {lead_id} at {scheduled_display}")

            # Step 4: Send confirmation to visitor
            await whatsapp_client.send_text(
                to=reply_to_phone,
                text=f"📞 Meeting scheduled for {scheduled_display}.\nWe'll confirm shortly.\n\n- Team INDAS Analytics"
            )

            # Step 5: Notify assigned employee or admin
            assigned_emp_id = lead.get("AssignedEmployeeId")
            if assigned_emp_id:
                assigned_emp = employees_repo.get_employee_by_id(assigned_emp_id)
                if assigned_emp and assigned_emp.get("Phone"):
                    emp_phone = assigned_emp["Phone"]
                    # Add country code if missing
                    if not emp_phone.startswith("91"):
                        emp_phone = "91" + emp_phone
                else:
                    emp_phone = settings.EXHIBITION_ADMIN_PHONE
            else:
                emp_phone = settings.EXHIBITION_ADMIN_PHONE

            # Send notification to employee
            await whatsapp_client.send_text(
                to=emp_phone,
                text=f"""📞 *New Meeting Request Received*

Lead: {lead.get('PrimaryVisitorName', 'Unknown')}
Company: {lead.get('CompanyName', 'Unknown')}
Requested Time: {scheduled_display}

Notes:
"{text}"

Please follow up.

- INDAS Lead Manager"""
            )
            print(f"📲 Meeting notification sent to employee: {emp_phone}")

            return {"status": "meeting_scheduled", "lead_id": lead_id}



        # Problem or issue reporting
        if any(kw in text_lower for kw in ["issue", "problem", "not working", "error", "trouble"]):
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f"⚠️ Problem Reported: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            await whatsapp_client.send_text(
                to=reply_to_phone,
                text="⚠️ Thank you! We have recorded the issue. Our team will get back to you shortly.\n\n- Team INDAS Analytics"
            )
            return {"status": "problem_logged", "lead_id": lead_id}



        # Requirements or costing request
        if any(kw in text_lower for kw in ["need", "want", "requirement", "quotation", "costing", "price"]):
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f"📝 Requirement: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            await whatsapp_client.send_text(
                to=reply_to_phone,
                text="📝 Thank you! We have noted your requirement. Our team will respond soon.\n\n- Team INDAS Analytics"
            )
            return {"status": "requirement_logged", "lead_id": lead_id}



        # Follow-up
        if any(kw in text_lower for kw in ["follow up", "remind", "ping", "check tomorrow"]):
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f"⏳ Follow-up: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            await whatsapp_client.send_text(
                to=reply_to_phone,
                text="⏳ Sure! We will follow up accordingly.\n\n- Team INDAS Analytics"
            )
            return {"status": "followup_logged", "lead_id": lead_id}



        # Task assignment
        if any(kw in text_lower for kw in ["assign task", "assign", "give task", "task to"]):
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f"📌 Task Assigned: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            await whatsapp_client.send_text(
                to=reply_to_phone,
                text="📌 Task captured. Our team will take action accordingly.\n\n- Team INDAS Analytics"
            )
            return {"status": "task_logged", "lead_id": lead_id}

        # ---------------------------------------
        # NEW INTENT HANDLING FOR BUSINESS WORKFLOWS
        # ---------------------------------------

        elif intent in ["DEMO_REQUEST", "MEETING_SCHEDULE"]:
            # Store scheduling request
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f"📅 {intent.replace('_',' ').title()}: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            # Default scheduled time = tomorrow 11 AM
            scheduled_at = datetime.utcnow() + timedelta(days=1)
            scheduled_at = scheduled_at.replace(hour=11, minute=0, second=0, microsecond=0)

            # Save follow-up
            from app.db.connection import db
            db.execute_query(
                """
                INSERT INTO FollowUps (LeadId, ScheduledAt, ActionType, Notes, Status, CreatedAt)
                VALUES (?, ?, ?, ?, 'pending', SYSUTCDATETIME())
                """,
                (
                    lead_id,
                    scheduled_at,
                    "demo" if intent == "DEMO_REQUEST" else "meeting",
                    text
                )
            )

            # Reply
            msg = f"""✅ Your request has been noted.

📅 Scheduled:
{scheduled_at.strftime('%d %B %Y at %I:%M %p')}

Our team will confirm shortly.
- Team INDAS Analytics"""

            await whatsapp_client.send_text(to=reply_to_phone, text=msg)
            return {"status": "scheduled", "lead_id": lead_id}

        elif intent == "PROBLEM_STATEMENT":
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f"⚠️ Problem Reported: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            await whatsapp_client.send_text(
                to=reply_to_phone,
                text="⚠️ Thank you for reporting the issue. Our team will check and update you.\n\n- Team INDAS Analytics"
            )
            return {"status": "problem_logged", "lead_id": lead_id}

        elif intent == "REQUIREMENT_NOTE":
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f"📝 Requirement: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            await whatsapp_client.send_text(
                to=reply_to_phone,
                text="📝 Thank you! We have noted your requirement. Our team will respond soon.\n\n- Team INDAS Analytics"
            )
            return {"status": "requirement_logged", "lead_id": lead_id}

        elif intent == "FOLLOWUP_NOTE":
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f"⏳ Follow-up Note: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            await whatsapp_client.send_text(
                to=reply_to_phone,
                text="⏳ Got it! We will follow up accordingly.\n\n- Team INDAS Analytics"
            )
            return {"status": "followup_logged", "lead_id": lead_id}

        elif intent == "TASK_ASSIGN":
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=f"📌 Task Assigned: {text}",
                whatsapp_message_id=str(wa_msg_id)
            )

            await whatsapp_client.send_text(
                to=reply_to_phone,
                text="📌 Task noted. Team will take action accordingly.\n\n- Team INDAS Analytics"
            )
            return {"status": "task_logged", "lead_id": lead_id}

        else:
            # GENERAL_QUERY or unclassified message
            # Send acknowledgment to both employees and visitors

            if is_employee_sender:
                # Employee sending general message - log and acknowledge
                messages_repo.create_message(
                    lead_id=lead_id,
                    sender_type="employee",
                    message_text=f"💬 Note: {text}",
                    whatsapp_message_id=str(wa_msg_id)
                )

                # Send acknowledgment to employee
                await whatsapp_client.send_text(
                    to=reply_to_phone,
                    text="✅ Message received and noted.\n\n- Team INDAS Analytics"
                )
                print(f"📝 Employee message logged and acknowledged")
                return {"status": "employee_message_acknowledged", "lead_id": lead_id}

            # Visitor message - process normally
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="visitor",
                message_text=text,
                whatsapp_message_id=str(wa_msg_id)
            )

            # If message looks like they want to correct but didn't provide details
            text_lower = text.lower().strip()
            is_hindi = self._detect_hindi_script(text)

            if any(word in text_lower for word in ['correct', 'correction', 'गलत', 'change', 'wrong']):
                # Send correction instructions in appropriate language
                if is_hindi:
                    correction_msg = """कृपया सही जानकारी इस format में भेजें:

Name: [आपका नाम]
Company: [कंपनी का नाम]
Designation: [आपका पद]
Phone: [आपका फोन नंबर]

या फिर बस वो detail भेजें जो गलत है।

- Team INDAS Analytics"""
                else:
                    correction_msg = """Please send the correct information in this format:

Name: [Your name]
Company: [Company name]
Designation: [Your designation]
Phone: [Your phone number]

Or just send the detail that is incorrect.

- Team INDAS Analytics"""

                await whatsapp_client.send_text(
                    to=reply_to_phone,
                    text=correction_msg
                )
            # Check if it's a simple greeting
            elif any(greeting in text_lower for greeting in ['hi', 'hey', 'hello', 'hii', 'helo', 'namaste', 'नमस्ते', 'hiii', '👋']):
                # Send a friendly greeting response (once)
                if is_hindi:
                    greeting_msg = f"नमस्ते! 👋\n\nकैसे मदद कर सकते हैं?\n\n- Team INDAS Analytics"
                else:
                    greeting_msg = f"Hello! 👋\n\nHow can we help you?\n\n- Team INDAS Analytics"

                print(f"📤 Sending greeting response")
                await whatsapp_client.send_text(
                    to=reply_to_phone,
                    text=greeting_msg
                )
            else:
                # Send acknowledgment for actual queries
                if is_hindi:
                    ack_msg = "धन्यवाद! आपका message हमें मिल गया है। हमारी team जल्द ही आपसे संपर्क करेगी।\n\n- Team INDAS Analytics"
                else:
                    ack_msg = "Thank you! We received your message. Our team will contact you shortly.\n\n- Team INDAS Analytics"

                print(f"📤 Sending acknowledgment")
                await whatsapp_client.send_text(
                    to=reply_to_phone,
                    text=ack_msg
                )

            return {"status": "query_logged", "lead_id": lead_id}

    # ========================================================================
    # BUSINESS INTENT HANDLER FUNCTIONS
    # ========================================================================

    async def _process_demo_request(
        self,
        lead: Dict[str, Any],
        text: str,
        wa_msg_id: int,
        reply_to_phone: str
    ) -> Dict[str, Any]:
        """Handle demo scheduling request"""
        lead_id = lead["LeadId"]

        # Step 1: Save message
        messages_repo.create_message(
            lead_id=lead_id,
            sender_type="visitor",
            message_text=f"🎯 Demo Request: {text}",
            whatsapp_message_id=str(wa_msg_id)
        )

        # Step 2: Parse datetime using NLP
        from app.utils.datetime_parser import datetime_parser
        from app.utils.employee_finder import employee_finder

        parsed_dt = datetime_parser.parse_datetime_from_text(text)
        if parsed_dt:
            scheduled_at = parsed_dt['datetime']
            scheduled_display = parsed_dt['formatted']
        else:
            # Fallback: tomorrow 4PM
            scheduled_at = datetime.utcnow() + timedelta(days=1)
            scheduled_at = scheduled_at.replace(hour=16, minute=0, second=0)
            scheduled_display = scheduled_at.strftime("%d %B %Y at %I:%M %p")

        # Step 3: Create follow-up
        from app.db.connection import db
        db.execute_query(
            """
            INSERT INTO FollowUps (LeadId, ScheduledAt, ActionType, Notes, Status, CreatedAt)
            VALUES (?, ?, 'demo', ?, 'pending', SYSUTCDATETIME())
            """,
            (lead_id, scheduled_at, text)
        )

        # Step 4: Check for mentioned employee
        mentioned_emp_name = datetime_parser.extract_employee_name(text)
        if mentioned_emp_name:
            target_employee = employee_finder.find_by_name(mentioned_emp_name)
            if target_employee:
                leads_repo.update_lead(
                    lead_id=lead_id,
                    assigned_employee_id=target_employee.get('EmployeeId')
                )
                assigned_emp = target_employee
            else:
                assigned_emp_id = lead.get("AssignedEmployeeId")
                assigned_emp = employees_repo.get_employee_by_id(assigned_emp_id) if assigned_emp_id else None
        else:
            assigned_emp_id = lead.get("AssignedEmployeeId")
            assigned_emp = employees_repo.get_employee_by_id(assigned_emp_id) if assigned_emp_id else None

        # Step 5: Send confirmation to visitor
        await whatsapp_client.send_text(
            to=reply_to_phone,
            text=f"✅ Demo scheduled for {scheduled_display}.\nOur team will contact you.\n\n- Team INDAS Analytics"
        )

        # Step 6: Notify employee
        if assigned_emp and assigned_emp.get("Phone"):
            emp_phone = assigned_emp["Phone"]
            if not emp_phone.startswith("91"):
                emp_phone = "91" + emp_phone
        else:
            emp_phone = settings.EXHIBITION_ADMIN_PHONE

        await whatsapp_client.send_text(
            to=emp_phone,
            text=f"""📅 *New Demo Request*

Lead: {lead.get('PrimaryVisitorName', 'Unknown')}
Company: {lead.get('CompanyName', 'Unknown')}
Time: {scheduled_display}

Notes: "{text}"

Please follow up.
- INDAS Lead Manager"""
        )

        return {"status": "demo_scheduled", "lead_id": lead_id}

    async def _process_meeting_request(
        self,
        lead: Dict[str, Any],
        text: str,
        wa_msg_id: int,
        reply_to_phone: str
    ) -> Dict[str, Any]:
        """Handle meeting/call scheduling request"""
        lead_id = lead["LeadId"]

        # Step 1: Save message
        messages_repo.create_message(
            lead_id=lead_id,
            sender_type="visitor",
            message_text=f"📅 Meeting Request: {text}",
            whatsapp_message_id=str(wa_msg_id)
        )

        # Step 2: Parse datetime
        from app.utils.datetime_parser import datetime_parser

        parsed_dt = datetime_parser.parse_datetime_from_text(text)
        if parsed_dt:
            scheduled_at = parsed_dt['datetime']
            scheduled_display = parsed_dt['formatted']
        else:
            # Fallback: tomorrow 12PM
            scheduled_at = datetime.utcnow() + timedelta(days=1)
            scheduled_at = scheduled_at.replace(hour=12, minute=0, second=0)
            scheduled_display = scheduled_at.strftime("%d %B %Y at %I:%M %p")

        # Step 3: Create follow-up
        from app.db.connection import db
        db.execute_query(
            """
            INSERT INTO FollowUps (LeadId, ScheduledAt, ActionType, Notes, Status, CreatedAt)
            VALUES (?, ?, 'meeting', ?, 'pending', SYSUTCDATETIME())
            """,
            (lead_id, scheduled_at, text)
        )

        # Step 4: Send confirmation
        await whatsapp_client.send_text(
            to=reply_to_phone,
            text=f"✅ Meeting scheduled for {scheduled_display}.\nOur team will reach out.\n\n- Team INDAS Analytics"
        )

        # Step 5: Notify employee
        assigned_emp_id = lead.get("AssignedEmployeeId")
        if assigned_emp_id:
            assigned_emp = employees_repo.get_employee_by_id(assigned_emp_id)
            if assigned_emp and assigned_emp.get("Phone"):
                emp_phone = assigned_emp["Phone"]
                if not emp_phone.startswith("91"):
                    emp_phone = "91" + emp_phone
            else:
                emp_phone = settings.EXHIBITION_ADMIN_PHONE
        else:
            emp_phone = settings.EXHIBITION_ADMIN_PHONE

        await whatsapp_client.send_text(
            to=emp_phone,
            text=f"""📞 *New Meeting Request*

Lead: {lead.get('PrimaryVisitorName', 'Unknown')}
Company: {lead.get('CompanyName', 'Unknown')}
Time: {scheduled_display}

Notes: "{text}"

Please schedule the call.
- INDAS Lead Manager"""
        )

        return {"status": "meeting_scheduled", "lead_id": lead_id}

    async def _process_problem_report(
        self,
        lead: Dict[str, Any],
        text: str,
        wa_msg_id: int,
        reply_to_phone: str
    ) -> Dict[str, Any]:
        """Handle problem/issue report"""
        lead_id = lead["LeadId"]

        # Step 1: Save message
        messages_repo.create_message(
            lead_id=lead_id,
            sender_type="visitor",
            message_text=f"⚠️ Problem Report: {text}",
            whatsapp_message_id=str(wa_msg_id)
        )

        # Step 2: Update lead status
        leads_repo.update_lead(
            lead_id=lead_id,
            status_code="problem_reported"
        )

        # Step 3: Send acknowledgment
        await whatsapp_client.send_text(
            to=reply_to_phone,
            text="⚠️ Thank you for reporting. Our team will investigate and respond shortly.\n\n- Team INDAS Analytics"
        )

        # Step 4: Notify employee
        assigned_emp_id = lead.get("AssignedEmployeeId")
        if assigned_emp_id:
            assigned_emp = employees_repo.get_employee_by_id(assigned_emp_id)
            if assigned_emp and assigned_emp.get("Phone"):
                emp_phone = assigned_emp["Phone"]
                if not emp_phone.startswith("91"):
                    emp_phone = "91" + emp_phone
            else:
                emp_phone = settings.EXHIBITION_ADMIN_PHONE
        else:
            emp_phone = settings.EXHIBITION_ADMIN_PHONE

        await whatsapp_client.send_text(
            to=emp_phone,
            text=f"""⚠️ *Problem Report*

Lead: {lead.get('PrimaryVisitorName', 'Unknown')}
Company: {lead.get('CompanyName', 'Unknown')}

Issue: "{text}"

Please investigate urgently.
- INDAS Lead Manager"""
        )

        return {"status": "problem_reported", "lead_id": lead_id}

    async def _process_requirement(
        self,
        lead: Dict[str, Any],
        text: str,
        wa_msg_id: int,
        reply_to_phone: str
    ) -> Dict[str, Any]:
        """Handle requirement/quotation inquiry"""
        lead_id = lead["LeadId"]

        # Step 1: Save message
        messages_repo.create_message(
            lead_id=lead_id,
            sender_type="visitor",
            message_text=f"📝 Requirement: {text}",
            whatsapp_message_id=str(wa_msg_id)
        )

        # Step 2: Update lead status
        leads_repo.update_lead(
            lead_id=lead_id,
            status_code="requirement_received"
        )

        # Step 3: Send acknowledgment
        await whatsapp_client.send_text(
            to=reply_to_phone,
            text="📝 Thank you! We've noted your requirement. Our team will prepare a quotation and respond soon.\n\n- Team INDAS Analytics"
        )

        # Step 4: Notify employee
        assigned_emp_id = lead.get("AssignedEmployeeId")
        if assigned_emp_id:
            assigned_emp = employees_repo.get_employee_by_id(assigned_emp_id)
            if assigned_emp and assigned_emp.get("Phone"):
                emp_phone = assigned_emp["Phone"]
                if not emp_phone.startswith("91"):
                    emp_phone = "91" + emp_phone
            else:
                emp_phone = settings.EXHIBITION_ADMIN_PHONE
        else:
            emp_phone = settings.EXHIBITION_ADMIN_PHONE

        await whatsapp_client.send_text(
            to=emp_phone,
            text=f"""📝 *New Requirement*

Lead: {lead.get('PrimaryVisitorName', 'Unknown')}
Company: {lead.get('CompanyName', 'Unknown')}

Requirement: "{text}"

Please prepare quotation.
- INDAS Lead Manager"""
        )

        return {"status": "requirement_received", "lead_id": lead_id}

    async def _handle_qr_submission(
        self,
        message_data: Dict[str, Any],
        wa_msg_id: int,
        media_url: Optional[str] = None,
        employee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Handle new lead submission via QR + WhatsApp (visiting card image)

        Full workflow:
        1. Send immediate acknowledgment
        2. Extract card data from image using OCR/AI
        3. Create new lead with source_code = 'whatsapp_qr'
        4. Auto-segment and schedule drip sequence
        5. Send confirmation message with extracted details
        6. Link WhatsApp message to new lead
        """
        sender_phone = message_data.get("from", "")
        sender_name = message_data.get("sender_name", "Visitor")
        cleaned_phone = sanitize_phone_number(sender_phone)

        # Step 1: Send immediate acknowledgment
        await whatsapp_client.send_text(
            to=sender_phone,
            text=f"Thank you {sender_name}! We received your visiting card. Processing now... ⏳"
        )

        # Step 2: Check if media was saved
        if not media_url:
            await whatsapp_client.send_text(
                to=sender_phone,
                text="Sorry, we couldn't process your image. Please try sending your visiting card again."
            )
            return {
                "status": "error",
                "message": "No media file saved",
                "from": sender_phone
            }

        try:
            # Step 3: Get active exhibition (use the most recent one)
            # For WhatsApp submissions, we'll use a default exhibition or the latest active one
            from app.db.connection import db
            exhibitions = db.execute_query(
                "SELECT TOP 1 ExhibitionId FROM Exhibitions WHERE IsActive = 1 ORDER BY StartDate DESC",
                fetch_all=True
            )
            exhibition_id = exhibitions[0]["ExhibitionId"] if exhibitions else 1  # Fallback to 1

            # Step 4: Create draft lead
            lead_id = leads_repo.create_lead(
                exhibition_id=exhibition_id,
                source_code="qr_whatsapp",  # Use existing source code from database
                status_code="new",
                primary_visitor_phone=cleaned_phone,  # Use sender's phone
                assigned_employee_id=employee_id  # Assign to employee if provided
            )

            if employee_id:
                print(f"✅ Lead assigned to Employee ID: {employee_id}")

            # Step 5: Save the image as attachment
            attachments_repo.create_attachment(
                lead_id=lead_id,
                attachment_type="card_front",
                file_url=media_url,
                mime_type=message_data.get("media_mimetype", "image/jpeg")
            )

            # Step 6: Extract card data using OCR + AI
            abs_media_path = os.path.join(settings.UPLOAD_DIR, media_url.lstrip("/uploads/"))

            # Ensure the file exists before extraction
            if not os.path.exists(abs_media_path):
                # Try alternative path
                abs_media_path = "." + media_url
                if not os.path.exists(abs_media_path):
                    print(f"❌ ERROR: File not found at {abs_media_path}")
                    print(f"   Original media_url: {media_url}")
                    print(f"   Upload dir: {settings.UPLOAD_DIR}")
                    raise FileNotFoundError(f"Card image not found at {abs_media_path}")

            print(f"📄 Extracting card from: {abs_media_path}")
            extraction_result = card_extractor.extract(abs_media_path, None)
            print(f"✅ Extraction complete: Confidence={extraction_result.confidence:.0%}, Company={extraction_result.company_name}")

            # Step 7: Get primary person info
            primary_person = extraction_result.persons[0] if extraction_result.persons else None
            primary_phone = cleaned_phone  # Default to sender's phone
            primary_email = None
            primary_name = sender_name
            designation = None

            if primary_person:
                if primary_person.phones:
                    primary_phone = phone_normalizer.normalize(primary_person.phones[0]) or cleaned_phone
                if primary_person.emails:
                    primary_email = primary_person.emails[0]
                if primary_person.name:
                    primary_name = primary_person.name
                designation = primary_person.designation

            # Step 8: Auto-segment lead
            segment_info = lead_segmentation_service.segment_lead(designation)

            # Step 9: Update lead with extracted data
            # IMPORTANT: If sender used LID, use phone from visiting card instead
            final_phone = primary_phone
            if "@lid" in sender_phone:
                print(f"🔄 Sender used LID ({sender_phone}). Using phone from visiting card: {primary_phone}")
                # If card has no phone, fall back to cleaned_phone (which is LID without @lid)
                if not final_phone:
                    final_phone = cleaned_phone
                    print(f"⚠️  No phone on card. Storing LID as phone: {final_phone}")
            else:
                # Use sender's phone if no phone on card
                if not final_phone:
                    final_phone = cleaned_phone

            leads_repo.update_lead(
                lead_id=lead_id,
                company_name=extraction_result.company_name,
                primary_visitor_name=primary_name,
                primary_visitor_designation=designation,
                primary_visitor_phone=final_phone,
                primary_visitor_email=primary_email,
                raw_card_json=extraction_result.model_dump_json()
            )

            # Update segment
            lead_segmentation_service.update_lead_segment(
                lead_id=lead_id,
                segment=segment_info["segment"],
                priority=segment_info["priority"]
            )

            # Step 10: Store additional data (persons, phones, emails, etc.)
            for idx, person in enumerate(extraction_result.persons):
                # Skip persons with NULL name (database constraint)
                if not person.name or not person.name.strip():
                    print(f"⚠️ Skipping person with NULL/empty name")
                    continue

                leads_repo.add_person(
                    lead_id=lead_id,
                    name=person.name,
                    designation=person.designation,
                    phone=person.phones[0] if person.phones else None,
                    email=person.emails[0] if person.emails else None,
                    is_primary=(idx == 0)
                )

            for phone in extraction_result.phones:
                normalized = phone_normalizer.normalize(phone)
                if normalized:
                    try:
                        leads_repo.add_phone(lead_id, normalized)
                    except Exception:
                        pass

            for email in extraction_result.emails:
                if email and '@' in email:
                    try:
                        leads_repo.add_email(lead_id, email)
                    except Exception:
                        pass

            for address in extraction_result.addresses:
                leads_repo.add_address(
                    lead_id=lead_id,
                    address_text=address.address,
                    address_type=address.address_type,
                    city=address.city,
                    state=address.state,
                    country=address.country,
                    pin_code=address.pin_code
                )

            for website in extraction_result.websites:
                leads_repo.add_website(lead_id, website)

            # Step 11: Link WhatsApp message to lead
            whatsapp_repo.update_message_lead(wa_msg_id, lead_id)

            # Step 12: Add system message
            messages_repo.create_message(
                lead_id=lead_id,
                sender_type="system",
                message_text=f"📱 Lead created via WhatsApp QR submission. Confidence: {extraction_result.confidence:.0%} | Segment: {segment_info['segment']}"
            )

            # Step 13: Schedule smart drip sequence
            # Lazy import to avoid circular dependency
            from app.services.followup_service import followup_service
            await followup_service.schedule_smart_drip_sequence(
                lead_id=lead_id,
                drip_template_type=segment_info["drip_template"]
            )

            # Step 14: Save visitor's message/topic if provided
            visitor_text = message_data.get("text", "").strip()
            # Ignore default "[Media message]" text
            if visitor_text and visitor_text != "[Media message]":
                # Add visitor's message as a note
                messages_repo.create_message(
                    lead_id=lead_id,
                    sender_type="visitor",
                    message_text=f"📝 Visitor's message: {visitor_text}"
                )

            # Step 15: Send confirmation with extracted details
            company_display = extraction_result.company_name or "your company"
            confirmation_msg = f"""✅ आपका visiting card process हो गया है!

हमने ये details सेव की हैं:
👤 Name: {primary_name}
🏢 Company: {company_display}"""

            if designation:
                confirmation_msg += f"\n💼 Designation: {designation}"

            # Only show visitor message if it's real text (not "[Media message]")
            if visitor_text and visitor_text != "[Media message]":
                confirmation_msg += f"\n📝 आपका message: \"{visitor_text}\""

            confirmation_msg += f"""

📞 Phone: {primary_phone}

क्या ये सही है?
✅ YES लिखें confirm करने के लिए
या corrections भेजें

- Team INDAS Analytics"""

            await whatsapp_client.send_text(
                to=sender_phone,
                text=confirmation_msg
            )

            # Log outbound confirmation
            whatsapp_repo.create_message(
                lead_id=lead_id,
                direction="outbound",
                from_number=whatsapp_client.phone_number,
                to_number=sender_phone,
                message_type="text",
                body=confirmation_msg,
                status="sent"
            )

            print(f"✅ WhatsApp QR submission processed: Lead {lead_id} created from {sender_phone}")

            return {
                "status": "lead_created",
                "lead_id": lead_id,
                "extraction_confidence": extraction_result.confidence,
                "segment": segment_info["segment"],
                "company_name": extraction_result.company_name,
                "visitor_name": primary_name,
                "from": sender_phone,
                "media_url": media_url
            }

        except Exception as e:
            import traceback
            print(f"❌ WhatsApp QR submission error: {e}")
            print(f"   Traceback:\n{traceback.format_exc()}")

            # Send error message to user
            await whatsapp_client.send_text(
                to=sender_phone,
                text="Sorry, we had trouble processing your visiting card. Our team has been notified and will contact you shortly."
            )

            return {
                "status": "error",
                "message": str(e),
                "from": sender_phone,
                "media_url": media_url
            }

    def _parse_webhook(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse webhook payload from third-party WhatsApp API

        Expected format from third-party API:
        {
            "event": "message.received",
            "timestamp": "2025-01-15T10:30:00.000Z",
            "accountToken": "acc_...",
            "message": {
                "id": "3EB0ABC123456789",
                "from": "919876543210",
                "fromName": "John Doe",
                "body": "Hello!",
                "timestamp": "2025-01-15T10:30:00.000Z",
                "type": "text|image|audio|video|document",
                "hasMedia": false,
                "media": {
                    "mimetype": "image/jpeg",
                    "data": "base64_data...",
                    "filename": "photo.jpg"
                }
            }
        }

        Returns standardized format:
        {
            "id": "message_id",
            "from": "+919876543210",
            "to": "+917000090823",  # Our business number
            "type": "text | image | audio | document | video",
            "text": "message text",
            "media_data": "base64_encoded_data",
            "media_mimetype": "image/jpeg",
            "media_filename": "photo.jpg",
            "sender_name": "John Doe"
        }
        """
        try:
            # Check if this is the expected third-party API format
            if "event" not in payload or "message" not in payload:
                print(f"❌ Webhook payload missing required fields: {list(payload.keys())}")
                return None

            event = payload.get("event")
            if event != "message.received":
                print(f"ℹ️ Ignoring webhook event: {event}")
                return None

            msg = payload["message"]

            # Extract basic message info
            from_number = msg.get("from", "")

            # Clean phone number: Remove @lid/@s.whatsapp.net suffix
            # JID formats: 919876543210@lid, 919876543210@s.whatsapp.net, 919876543210@c.us
            original_from = msg.get("from", "")
            is_lid = "@lid" in original_from

            if "@" in from_number:
                from_number = from_number.split("@")[0]

            # Remove any non-digit characters except +
            from_number = ''.join(c for c in from_number if c.isdigit() or c == '+')

            print(f"🔍 Webhook from_number after cleaning: {from_number} (original: {original_from})")

            # CRITICAL WARNING: LID detected
            if is_lid:
                print(f"⚠️ ⚠️ ⚠️  CRITICAL: WhatsApp LID (Limited Identifier) detected! ⚠️ ⚠️ ⚠️")
                print(f"   Original: {original_from}")
                print(f"   Cleaned: {from_number}")
                print(f"   This is a MASKED/GARBAGE value, NOT a real phone number!")
                print(f"   Duplicate detection by phone will NOT work.")
                print(f"   Contact WhatsApp API provider to send real phone numbers.")
                print(f"   Using LID-based duplicate detection as fallback...")

            # Don't assume country code - keep number as received
            # The WhatsApp client will handle formatting

            result = {
                "id": msg.get("id"),
                "from": from_number,
                "to": "7000090823",  # Our business WhatsApp number (10 digits)
                "type": msg.get("type", "text"),
                "sender_name": msg.get("fromName"),
                "timestamp": msg.get("timestamp")
            }

            # Handle text messages
            if msg.get("type") == "text":
                result["text"] = msg.get("body", "")

            # Handle media messages (image, audio, video, document)
            elif "media" in msg:
                media = msg["media"]
                result["text"] = msg.get("body", "")  # Caption/message with media
                result["media_url"] = media.get("url")  # Download URL from gateway
                result["media_mimetype"] = media.get("mimetype")
                result["media_filename"] = media.get("filename", "file")

            print(f"✅ Parsed webhook message: Type={result['type']}, From={result['from']}, HasMedia={'media_url' in result}")
            return result

        except Exception as e:
            print(f"❌ Webhook parse error: {e}")
            print(f"   Payload keys: {list(payload.keys())}")
            return None


# Singleton instance
whatsapp_service = WhatsAppService()
