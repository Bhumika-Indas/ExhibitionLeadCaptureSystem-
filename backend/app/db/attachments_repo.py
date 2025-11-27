"""
Attachments Repository - File path storage
"""

from typing import List, Dict, Any, Optional
from app.db.connection import db


class AttachmentsRepository:
    """Repository for LeadAttachments"""

    @staticmethod
    def create_attachment(
        lead_id: int,
        attachment_type: str,
        file_url: str,
        file_size_bytes: Optional[int] = None,
        mime_type: Optional[str] = None
    ) -> int:
        """Create attachment record and return AttachmentId"""
        query = """
        INSERT INTO LeadAttachments (LeadId, AttachmentType, FileUrl, FileSizeBytes, MimeType)
        OUTPUT INSERTED.AttachmentId
        VALUES (?, ?, ?, ?, ?)
        """
        return db.execute_scalar(query, (lead_id, attachment_type, file_url, file_size_bytes, mime_type))

    @staticmethod
    def get_attachments_by_lead(lead_id: int) -> List[Dict[str, Any]]:
        """Get all attachments for a lead"""
        query = """
        SELECT * FROM LeadAttachments
        WHERE LeadId = ?
        ORDER BY CreatedAt DESC
        """
        return db.execute_query(query, (lead_id,), fetch_all=True)

    @staticmethod
    def get_attachment_by_id(attachment_id: int) -> Optional[Dict[str, Any]]:
        """Get single attachment by ID"""
        query = "SELECT * FROM LeadAttachments WHERE AttachmentId = ?"
        return db.execute_query(query, (attachment_id,), fetch_one=True)

    @staticmethod
    def get_attachments_by_type(lead_id: int, attachment_type: str) -> List[Dict[str, Any]]:
        """Get attachments of specific type"""
        query = """
        SELECT * FROM LeadAttachments
        WHERE LeadId = ? AND AttachmentType = ?
        ORDER BY CreatedAt DESC
        """
        return db.execute_query(query, (lead_id, attachment_type), fetch_all=True)

    @staticmethod
    def delete_attachment(attachment_id: int) -> bool:
        """Delete attachment record (file remains on disk)"""
        query = "DELETE FROM LeadAttachments WHERE AttachmentId = ?"
        rows_affected = db.execute_query(query, (attachment_id,))
        return rows_affected > 0


# Export singleton instance
attachments_repo = AttachmentsRepository()
