"""
Messages Repository - Chat messages for leads
"""

from typing import List, Dict, Any, Optional
from app.db.connection import db


class MessagesRepository:
    """Repository for LeadMessages"""

    @staticmethod
    def create_message(
        lead_id: int,
        sender_type: str,
        message_text: str,
        sender_employee_id: Optional[int] = None,
        whatsapp_message_id: Optional[str] = None
    ) -> int:
        """Create chat message and return MessageId"""
        query = """
        INSERT INTO LeadMessages (LeadId, SenderType, MessageText, SenderEmployeeId, WhatsAppMessageId)
        OUTPUT INSERTED.MessageId
        VALUES (?, ?, ?, ?, ?)
        """
        return db.execute_scalar(query, (lead_id, sender_type, message_text, sender_employee_id, whatsapp_message_id))

    @staticmethod
    def get_messages_by_lead(lead_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all messages for a lead"""
        query = """
        SELECT
            m.*,
            e.FullName AS SenderEmployeeName
        FROM LeadMessages m
        LEFT JOIN Employees e ON m.SenderEmployeeId = e.EmployeeId
        WHERE m.LeadId = ?
        ORDER BY m.CreatedAt ASC
        OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
        """
        return db.execute_query(query, (lead_id, limit), fetch_all=True)

    @staticmethod
    def get_recent_messages(lead_id: int, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages"""
        query = """
        SELECT TOP (?) * FROM LeadMessages
        WHERE LeadId = ?
        ORDER BY CreatedAt DESC
        """
        messages = db.execute_query(query, (count, lead_id), fetch_all=True)
        return list(reversed(messages))  # Return in chronological order


# Export singleton instance
messages_repo = MessagesRepository()
