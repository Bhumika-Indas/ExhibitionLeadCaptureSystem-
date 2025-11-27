"""
Extraction Router
Card OCR and Voice transcription endpoints
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import json

from app.extraction.card_extractor import card_extractor
from app.extraction.voice_transcriber import voice_transcriber
from app.services.file_storage_service import file_storage_service
from app.services.lead_segmentation_service import lead_segmentation_service
from app.services.followup_service import followup_service
from app.services.duplicate_detection_service import duplicate_detection_service
from app.db.leads_repo import leads_repo
from app.db.attachments_repo import attachments_repo
from app.db.messages_repo import messages_repo
from app.utils.phone_normalizer import phone_normalizer


router = APIRouter(prefix="/extraction", tags=["Extraction"])


@router.post("/card")
async def extract_card(
    front_image: UploadFile = File(...),
    back_image: Optional[UploadFile] = File(None),
    exhibition_id: int = Form(...),
    employee_id: int = Form(...)
):
    """
    Extract visiting card data and create lead

    Flow:
    1. Save images to storage
    2. Extract data using OCR + OpenAI
    3. Create lead record
    4. Link attachments
    5. Return structured result
    """
    try:
        # Step 1: Create draft lead to get ID
        lead_id = leads_repo.create_lead(
            exhibition_id=exhibition_id,
            source_code="employee_scan",
            assigned_employee_id=employee_id,
            status_code="new"
        )

        # Step 2: Save front image
        front_path, front_size, front_mime = await file_storage_service.save_card_image(
            front_image, lead_id, "front"
        )

        front_attachment_id = attachments_repo.create_attachment(
            lead_id=lead_id,
            attachment_type="card_front",
            file_url=front_path,
            file_size_bytes=front_size,
            mime_type=front_mime
        )

        # Step 3: Save back image if provided
        back_path = None
        if back_image:
            back_path, back_size, back_mime = await file_storage_service.save_card_image(
                back_image, lead_id, "back"
            )

            attachments_repo.create_attachment(
                lead_id=lead_id,
                attachment_type="card_back",
                file_url=back_path,
                file_size_bytes=back_size,
                mime_type=back_mime
            )

        # Step 4: Extract card data
        front_abs_path = file_storage_service.get_absolute_path(front_path)
        back_abs_path = file_storage_service.get_absolute_path(back_path) if back_path else None

        extraction_result = card_extractor.extract(front_abs_path, back_abs_path)

        # Step 5: Check for duplicates BEFORE saving all data
        primary_person = extraction_result.persons[0] if extraction_result.persons else None
        primary_phone = None
        primary_email = None

        if primary_person:
            if primary_person.phones:
                primary_phone = phone_normalizer.normalize(primary_person.phones[0])
            if primary_person.emails:
                primary_email = primary_person.emails[0]

        duplicate_check = duplicate_detection_service.check_duplicate_before_save(
            company_name=extraction_result.company_name,
            phone=primary_phone,
            email=primary_email,
            visitor_name=primary_person.name if primary_person else None,
            exhibition_id=exhibition_id
        )

        # Step 6: Auto-segment lead based on designation
        designation = primary_person.designation if primary_person else None
        segment_info = lead_segmentation_service.segment_lead(designation)

        # Update lead with extracted data
        leads_repo.update_lead(
            lead_id=lead_id,
            company_name=extraction_result.company_name,
            primary_visitor_name=primary_person.name if primary_person else None,
            primary_visitor_designation=designation,
            primary_visitor_phone=primary_phone,
            primary_visitor_email=primary_email
        )

        # Update segment information
        lead_segmentation_service.update_lead_segment(
            lead_id=lead_id,
            segment=segment_info["segment"],
            priority=segment_info["priority"]
        )

        # Step 7: Store ALL persons (including primary for completeness)
        for idx, person in enumerate(extraction_result.persons):
            leads_repo.add_person(
                lead_id=lead_id,
                name=person.name,
                designation=person.designation,
                phone=person.phones[0] if person.phones else None,
                email=person.emails[0] if person.emails else None,
                is_primary=(idx == 0)
            )

        # Step 8: Store ALL phone numbers
        for phone in extraction_result.phones:
            normalized = phone_normalizer.normalize(phone)
            if normalized:
                try:
                    leads_repo.add_phone(lead_id, normalized)
                except Exception:
                    pass  # Skip duplicates

        # Step 9: Store ALL email addresses
        for email in extraction_result.emails:
            if email and '@' in email:
                try:
                    leads_repo.add_email(lead_id, email)
                except Exception:
                    pass  # Skip duplicates

        # Step 10: Store brands (for dealer cards)
        for brand in extraction_result.brands:
            try:
                leads_repo.add_brand(lead_id, brand.brand_name, brand.relationship)
            except Exception:
                pass  # Skip duplicates

        # Step 11: Store addresses
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

        # Step 12: Store websites
        for website in extraction_result.websites:
            leads_repo.add_website(lead_id, website)

        # Step 13: Store services
        for service in extraction_result.services:
            leads_repo.add_service(lead_id, service)

        # Step 10: Store raw JSON
        leads_repo.update_lead(
            lead_id=lead_id,
            raw_card_json=extraction_result.model_dump_json()
        )

        # Step 11: Add system message with segment info
        messages_repo.create_message(
            lead_id=lead_id,
            sender_type="system",
            message_text=f"📸 Card scanned. Confidence: {extraction_result.confidence:.0%} | Segment: {segment_info['segment']} (Priority {segment_info['priority']})"
        )

        # Step 12: Schedule smart drip sequence based on segment
        await followup_service.schedule_smart_drip_sequence(
            lead_id=lead_id,
            drip_template_type=segment_info["drip_template"]
        )

        # Add confirmation message
        messages_repo.create_message(
            lead_id=lead_id,
            sender_type="system",
            message_text=f"✅ Smart drip sequence scheduled (Template: {segment_info['drip_template']})"
        )

        # Note: WhatsApp greeting will be sent AFTER employee verification
        # Use POST /api/leads/{lead_id}/send-greeting when details are confirmed

        return {
            "success": True,
            "lead_id": lead_id,
            "extraction": extraction_result.model_dump(),
            "segment": segment_info["segment"],
            "priority": segment_info["priority"],
            "drip_template": segment_info["drip_template"],
            "drip_scheduled": True,
            "duplicate_check": duplicate_check,
            "message": "Card extracted successfully with smart drip sequence scheduled. Review and confirm to send greeting."
        }

    except Exception as e:
        print(f" Card extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice")
async def extract_voice(
    audio_file: UploadFile = File(...),
    lead_id: int = Form(...),
    employee_id: int = Form(...)
):
    """
    Transcribe and summarize voice note

    Flow:
    1. Save audio file
    2. Transcribe using Whisper
    3. Summarize using GPT
    4. Update lead
    5. Add to chat
    """
    try:
        # Step 1: Save audio file
        audio_path, audio_size, audio_mime = await file_storage_service.save_audio_note(
            audio_file, lead_id
        )

        attachments_repo.create_attachment(
            lead_id=lead_id,
            attachment_type="audio_note",
            file_url=audio_path,
            file_size_bytes=audio_size,
            mime_type=audio_mime
        )

        # Step 2: Transcribe and summarize
        audio_abs_path = file_storage_service.get_absolute_path(audio_path)
        voice_result = voice_transcriber.transcribe_and_summarize(audio_abs_path)

        # Step 3: Save transcript as message (always save the raw transcript)
        messages_repo.create_message(
            lead_id=lead_id,
            sender_type="employee",
            sender_employee_id=employee_id,
            message_text=voice_result.transcript
        )

        # Step 4: Add topics (non-critical, can save immediately)
        for topic in voice_result.topics:
            leads_repo.add_topic(lead_id, topic)

        # Step 5: Return analysis for confirmation - DON'T auto-save segment/priority/next_step
        # Frontend will show confirmation UI and call /confirm endpoint to save
        return {
            "success": True,
            "lead_id": lead_id,
            "transcript": voice_result.transcript,
            "summary": voice_result.summary,
            "topics": voice_result.topics,
            "next_step": voice_result.next_step,
            "segment": voice_result.segment,
            "priority": voice_result.priority,
            "interest_level": voice_result.interest_level,
            "confidence": voice_result.confidence,
            "requires_confirmation": True
        }

    except Exception as e:
        print(f" Voice extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/confirm")
async def confirm_voice_analysis(
    lead_id: int = Form(...),
    summary: str = Form(...),
    next_step: str = Form(None),
    segment: str = Form(...),
    priority: str = Form(...),
    interest_level: str = Form(None)
):
    """
    Confirm and save voice analysis after employee review
    Called after employee confirms/modifies the extracted segment/priority/next_step
    """
    try:
        # Extract concise next step - don't store full description
        # The NextStep column should only store short action codes or brief text
        # Full details are already in the discussion_summary

        # Update lead with confirmed values (skip next_step for now)
        leads_repo.update_lead(
            lead_id=lead_id,
            discussion_summary=summary,
            # Don't save next_step to avoid VARCHAR(50) truncation error
            # Next step details are already in the summary
            segment=segment,
            priority=priority
        )

        # Add system message with confirmed analysis (including full next step)
        segment_display = segment or "general"
        priority_display = priority or "medium"
        interest_display = interest_level or "warm"
        next_step_display = next_step or "No specific action"

        messages_repo.create_message(
            lead_id=lead_id,
            sender_type="system",
            message_text=f"✅ Voice analysis confirmed | Segment: {segment_display} | Priority: {priority_display} | Interest: {interest_display} | Next Step: {next_step_display}"
        )

        return {
            "success": True,
            "message": "Voice analysis confirmed and saved",
            "lead_id": lead_id,
            "segment": segment,
            "priority": priority,
            "next_step": next_step_display
        }

    except Exception as e:
        print(f" Voice confirmation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
