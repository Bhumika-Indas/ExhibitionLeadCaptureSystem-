"""
WhatsApp Messages Repository
"""

from typing import List, Dict, Any, Optional
from app.db.connection import db


class WhatsAppRepository:
    """Repository for WhatsAppMessages"""

    @staticmethod
    def create_message(
        lead_id: Optional[int],
        direction: str,
        from_number: str,
        to_number: str,
        message_type: str,
        body: Optional[str] = None,
        media_url: Optional[str] = None,
        template_id: Optional[str] = None,
        wa_message_id_external: Optional[str] = None,
        raw_payload_json: Optional[str] = None,
        status: str = "sent"
    ) -> int:
        """Create WhatsApp message record"""
        query = """
        INSERT INTO WhatsAppMessages (
            LeadId, Direction, FromNumber, ToNumber, MessageType,
            Body, MediaUrl, TemplateId, WaMessageIdExternal, RawPayloadJson, Status
        )
        OUTPUT INSERTED.WaMessageId
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return db.execute_scalar(query, (
            lead_id, direction, from_number, to_number, message_type,
            body, media_url, template_id, wa_message_id_external, raw_payload_json, status
        ))

    @staticmethod
    def get_messages_by_lead(lead_id: int) -> List[Dict[str, Any]]:
        """Get all WhatsApp messages for a lead"""
        query = """
        SELECT * FROM WhatsAppMessages
        WHERE LeadId = ?
        ORDER BY CreatedAt ASC
        """
        return db.execute_query(query, (lead_id,), fetch_all=True)

    @staticmethod
    def get_messages_by_phone(phone: str) -> List[Dict[str, Any]]:
        """Get all WhatsApp messages from a phone number"""
        query = """
        SELECT * FROM WhatsAppMessages
        WHERE FromNumber = ?
        ORDER BY CreatedAt DESC
        """
        return db.execute_query(query, (phone,), fetch_all=True)

    @staticmethod
    def update_message_status(wa_message_id: int, status: str) -> bool:
        """Update WhatsApp message status"""
        query = """
        UPDATE WhatsAppMessages
        SET Status = ?, UpdatedAt = SYSUTCDATETIME()
        WHERE WaMessageId = ?
        """
        rows_affected = db.execute_query(query, (status, wa_message_id))
        return rows_affected > 0

    @staticmethod
    def update_message_lead(wa_message_id: int, lead_id: int) -> bool:
        """Link WhatsApp message to a lead"""
        query = """
        UPDATE WhatsAppMessages
        SET LeadId = ?, UpdatedAt = SYSUTCDATETIME()
        WHERE WaMessageId = ?
        """
        rows_affected = db.execute_query(query, (lead_id, wa_message_id))
        return rows_affected > 0

    @staticmethod
    def find_by_external_id(wa_message_id_external: str) -> Optional[Dict[str, Any]]:
        """Find message by WhatsApp's external ID"""
        query = """
        SELECT * FROM WhatsAppMessages
        WHERE WaMessageIdExternal = ?
        """
        return db.execute_query(query, (wa_message_id_external,), fetch_one=True)

    @staticmethod
    def find_by_sender_lid(lid_phone: str) -> Optional[Dict[str, Any]]:
        """
        Find most recent WhatsApp message from a specific LID (masked phone)
        Used to detect duplicate submissions from same WhatsApp user with LID
        """
        query = """
        SELECT TOP 1 * FROM WhatsAppMessages
        WHERE FromNumber = ? AND LeadId IS NOT NULL
        ORDER BY CreatedAt DESC
        """
        return db.execute_query(query, (lid_phone,), fetch_one=True)


# Export singleton instance
whatsapp_repo = WhatsAppRepository()
