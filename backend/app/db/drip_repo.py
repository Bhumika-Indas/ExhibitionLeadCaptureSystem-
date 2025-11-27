"""
Drip System Repository
Handles Message Master, Drip Configuration, and Drip Assignments
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.db.connection import db


class DripRepository:
    """Repository for Drip System V2"""

    # ==================== MESSAGE MASTER ====================

    @staticmethod
    def create_message(
        title: str,
        message_type: str,
        body: Optional[str] = None,
        file_url: Optional[str] = None,
        file_name: Optional[str] = None,
        file_mime_type: Optional[str] = None,
        variables: Optional[str] = None
    ) -> int:
        """Create a message template"""
        query = """
        INSERT INTO MessageMaster (MessageTitle, MessageType, MessageBody, FileUrl, FileName, FileMimeType, Variables)
        OUTPUT INSERTED.MessageId
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return db.execute_scalar(query, (title, message_type, body, file_url, file_name, file_mime_type, variables))

    @staticmethod
    def get_all_messages(active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all message templates"""
        query = "SELECT * FROM MessageMaster"
        if active_only:
            query += " WHERE IsActive = 1"
        query += " ORDER BY CreatedAt DESC"
        return db.execute_query(query, fetch_all=True) or []

    @staticmethod
    def get_message_by_id(message_id: int) -> Optional[Dict[str, Any]]:
        """Get single message by ID"""
        query = "SELECT * FROM MessageMaster WHERE MessageId = ?"
        return db.execute_query(query, (message_id,), fetch_one=True)

    @staticmethod
    def update_message(message_id: int, **kwargs) -> bool:
        """Update message template"""
        allowed = ['MessageTitle', 'MessageType', 'MessageBody', 'FileUrl', 'FileName', 'FileMimeType', 'Variables', 'IsActive']
        updates = []
        values = []
        for key, value in kwargs.items():
            # Convert snake_case to PascalCase
            pascal_key = ''.join(word.capitalize() for word in key.split('_'))
            if pascal_key in allowed:
                updates.append(f"{pascal_key} = ?")
                values.append(value)

        if not updates:
            return False

        query = f"UPDATE MessageMaster SET {', '.join(updates)}, UpdatedAt = SYSUTCDATETIME() WHERE MessageId = ?"
        values.append(message_id)
        rows = db.execute_query(query, tuple(values))
        return rows > 0

    @staticmethod
    def delete_message(message_id: int) -> bool:
        """Soft delete message (set IsActive = 0)"""
        query = "UPDATE MessageMaster SET IsActive = 0, UpdatedAt = SYSUTCDATETIME() WHERE MessageId = ?"
        rows = db.execute_query(query, (message_id,))
        return rows > 0

    # ==================== DRIP MASTER ====================

    @staticmethod
    def create_drip(name: str, description: Optional[str] = None) -> int:
        """Create a drip sequence"""
        query = """
        INSERT INTO DripMaster (DripName, DripDescription)
        OUTPUT INSERTED.DripId
        VALUES (?, ?)
        """
        return db.execute_scalar(query, (name, description))

    @staticmethod
    def get_all_drips(active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all drip sequences with message count"""
        query = """
        SELECT d.*,
            (SELECT COUNT(*) FROM DripMessages dm WHERE dm.DripId = d.DripId AND dm.IsActive = 1) AS MessageCount,
            (SELECT MAX(DayNumber) FROM DripMessages dm WHERE dm.DripId = d.DripId AND dm.IsActive = 1) AS TotalDays
        FROM DripMaster d
        """
        if active_only:
            query += " WHERE d.IsActive = 1"
        query += " ORDER BY d.CreatedAt DESC"
        return db.execute_query(query, fetch_all=True) or []

    @staticmethod
    def get_drip_by_id(drip_id: int) -> Optional[Dict[str, Any]]:
        """Get drip with all its messages"""
        drip_query = "SELECT * FROM DripMaster WHERE DripId = ?"
        drip = db.execute_query(drip_query, (drip_id,), fetch_one=True)

        if drip:
            messages_query = """
            SELECT dm.*, m.MessageTitle, m.MessageType, m.MessageBody, m.FileUrl
            FROM DripMessages dm
            JOIN MessageMaster m ON dm.MessageId = m.MessageId
            WHERE dm.DripId = ? AND dm.IsActive = 1
            ORDER BY dm.DayNumber, dm.SendTime, dm.SortOrder
            """
            drip['Messages'] = db.execute_query(messages_query, (drip_id,), fetch_all=True) or []

        return drip

    @staticmethod
    def update_drip(drip_id: int, **kwargs) -> bool:
        """Update drip sequence"""
        allowed = ['DripName', 'DripDescription', 'IsActive']
        updates = []
        values = []
        for key, value in kwargs.items():
            pascal_key = ''.join(word.capitalize() for word in key.split('_'))
            if pascal_key in allowed:
                updates.append(f"{pascal_key} = ?")
                values.append(value)

        if not updates:
            return False

        query = f"UPDATE DripMaster SET {', '.join(updates)}, UpdatedAt = SYSUTCDATETIME() WHERE DripId = ?"
        values.append(drip_id)
        rows = db.execute_query(query, tuple(values))
        return rows > 0

    @staticmethod
    def delete_drip(drip_id: int) -> bool:
        """Soft delete drip"""
        query = "UPDATE DripMaster SET IsActive = 0, UpdatedAt = SYSUTCDATETIME() WHERE DripId = ?"
        rows = db.execute_query(query, (drip_id,))
        return rows > 0

    # ==================== DRIP MESSAGES ====================

    @staticmethod
    def add_message_to_drip(
        drip_id: int,
        message_id: int,
        day_number: int = 0,
        send_time: str = "10:00",
        sort_order: int = 0
    ) -> int:
        """Add a message to a drip sequence"""
        query = """
        INSERT INTO DripMessages (DripId, MessageId, DayNumber, SendTime, SortOrder)
        OUTPUT INSERTED.DripMessageId
        VALUES (?, ?, ?, ?, ?)
        """
        return db.execute_scalar(query, (drip_id, message_id, day_number, send_time, sort_order))

    @staticmethod
    def update_drip_message(drip_message_id: int, **kwargs) -> bool:
        """Update drip message settings"""
        allowed = ['DayNumber', 'SendTime', 'SortOrder', 'IsActive']
        updates = []
        values = []
        for key, value in kwargs.items():
            pascal_key = ''.join(word.capitalize() for word in key.split('_'))
            if pascal_key in allowed:
                updates.append(f"{pascal_key} = ?")
                values.append(value)

        if not updates:
            return False

        query = f"UPDATE DripMessages SET {', '.join(updates)} WHERE DripMessageId = ?"
        values.append(drip_message_id)
        rows = db.execute_query(query, tuple(values))
        return rows > 0

    @staticmethod
    def remove_message_from_drip(drip_message_id: int) -> bool:
        """Remove message from drip"""
        query = "DELETE FROM DripMessages WHERE DripMessageId = ?"
        rows = db.execute_query(query, (drip_message_id,))
        return rows > 0

    # ==================== DRIP ASSIGNMENTS ====================

    @staticmethod
    def apply_drip_to_lead(lead_id: int, drip_id: int) -> int:
        """Apply a drip sequence to a lead and schedule all messages"""
        # First, stop any active drips for this lead
        DripRepository.stop_drip_for_lead(lead_id)

        # Create assignment
        query = """
        INSERT INTO LeadDripAssignments (LeadId, DripId, Status, StartedAt)
        OUTPUT INSERTED.AssignmentId
        VALUES (?, ?, 'active', SYSUTCDATETIME())
        """
        assignment_id = db.execute_scalar(query, (lead_id, drip_id))

        # Get all messages for this drip
        messages_query = """
        SELECT dm.DripMessageId, dm.MessageId, dm.DayNumber, dm.SendTime
        FROM DripMessages dm
        WHERE dm.DripId = ? AND dm.IsActive = 1
        ORDER BY dm.DayNumber, dm.SendTime
        """
        messages = db.execute_query(messages_query, (drip_id,), fetch_all=True) or []

        # Schedule each message
        now = datetime.utcnow()
        for msg in messages:
            day_number = msg['DayNumber']
            send_time = msg['SendTime']

            # Calculate scheduled datetime
            if day_number == 0:
                # Day 0 = immediate (within next minute)
                scheduled_at = now + timedelta(minutes=1)
            else:
                # Future days at specified time
                scheduled_date = now.date() + timedelta(days=day_number)
                # Parse time
                if isinstance(send_time, str):
                    time_parts = send_time.split(':')
                    hour, minute = int(time_parts[0]), int(time_parts[1]) if len(time_parts) > 1 else 0
                else:
                    hour, minute = send_time.hour, send_time.minute
                scheduled_at = datetime.combine(scheduled_date, datetime.min.time().replace(hour=hour, minute=minute))

            # Insert scheduled message
            schedule_query = """
            INSERT INTO ScheduledDripMessages (AssignmentId, LeadId, DripMessageId, MessageId, ScheduledAt, Status)
            VALUES (?, ?, ?, ?, ?, 'pending')
            """
            db.execute_query(schedule_query, (assignment_id, lead_id, msg['DripMessageId'], msg['MessageId'], scheduled_at))

        return assignment_id

    @staticmethod
    def stop_drip_for_lead(lead_id: int, assignment_id: Optional[int] = None) -> bool:
        """Stop drip sequence for a lead"""
        if assignment_id:
            # Stop specific assignment
            query = """
            UPDATE LeadDripAssignments
            SET Status = 'stopped', StoppedAt = SYSUTCDATETIME(), UpdatedAt = SYSUTCDATETIME()
            WHERE AssignmentId = ? AND Status = 'active'
            """
            db.execute_query(query, (assignment_id,))

            # Cancel pending messages
            cancel_query = """
            UPDATE ScheduledDripMessages
            SET Status = 'cancelled', UpdatedAt = SYSUTCDATETIME()
            WHERE AssignmentId = ? AND Status = 'pending'
            """
            db.execute_query(cancel_query, (assignment_id,))
        else:
            # Stop all active drips for lead
            query = """
            UPDATE LeadDripAssignments
            SET Status = 'stopped', StoppedAt = SYSUTCDATETIME(), UpdatedAt = SYSUTCDATETIME()
            WHERE LeadId = ? AND Status = 'active'
            """
            db.execute_query(query, (lead_id,))

            # Cancel all pending messages
            cancel_query = """
            UPDATE ScheduledDripMessages
            SET Status = 'cancelled', UpdatedAt = SYSUTCDATETIME()
            WHERE LeadId = ? AND Status = 'pending'
            """
            db.execute_query(cancel_query, (lead_id,))

        return True

    @staticmethod
    def pause_drip_for_lead(lead_id: int, assignment_id: Optional[int] = None) -> bool:
        """Pause drip sequence (can be resumed later)"""
        if assignment_id:
            query = """
            UPDATE LeadDripAssignments
            SET Status = 'paused', PausedAt = SYSUTCDATETIME(), UpdatedAt = SYSUTCDATETIME()
            WHERE AssignmentId = ? AND Status = 'active'
            """
            db.execute_query(query, (assignment_id,))
        else:
            query = """
            UPDATE LeadDripAssignments
            SET Status = 'paused', PausedAt = SYSUTCDATETIME(), UpdatedAt = SYSUTCDATETIME()
            WHERE LeadId = ? AND Status = 'active'
            """
            db.execute_query(query, (lead_id,))
        return True

    @staticmethod
    def resume_drip_for_lead(lead_id: int, assignment_id: Optional[int] = None) -> bool:
        """Resume a paused drip sequence"""
        if assignment_id:
            query = """
            UPDATE LeadDripAssignments
            SET Status = 'active', PausedAt = NULL, UpdatedAt = SYSUTCDATETIME()
            WHERE AssignmentId = ? AND Status = 'paused'
            """
            db.execute_query(query, (assignment_id,))
        else:
            query = """
            UPDATE LeadDripAssignments
            SET Status = 'active', PausedAt = NULL, UpdatedAt = SYSUTCDATETIME()
            WHERE LeadId = ? AND Status = 'paused'
            """
            db.execute_query(query, (lead_id,))
        return True

    @staticmethod
    def get_lead_drip_status(lead_id: int) -> Optional[Dict[str, Any]]:
        """Get current drip status for a lead"""
        query = """
        SELECT lda.*, d.DripName, d.DripDescription,
            (SELECT COUNT(*) FROM ScheduledDripMessages sm WHERE sm.AssignmentId = lda.AssignmentId AND sm.Status = 'sent') AS SentCount,
            (SELECT COUNT(*) FROM ScheduledDripMessages sm WHERE sm.AssignmentId = lda.AssignmentId AND sm.Status = 'pending') AS PendingCount,
            (SELECT COUNT(*) FROM ScheduledDripMessages sm WHERE sm.AssignmentId = lda.AssignmentId) AS TotalCount
        FROM LeadDripAssignments lda
        JOIN DripMaster d ON lda.DripId = d.DripId
        WHERE lda.LeadId = ? AND lda.Status IN ('active', 'paused')
        ORDER BY lda.CreatedAt DESC
        """
        return db.execute_query(query, (lead_id,), fetch_one=True)

    @staticmethod
    def get_scheduled_messages_for_lead(lead_id: int) -> List[Dict[str, Any]]:
        """Get all scheduled messages for a lead"""
        query = """
        SELECT sm.*, m.MessageTitle, m.MessageType, m.MessageBody
        FROM ScheduledDripMessages sm
        JOIN MessageMaster m ON sm.MessageId = m.MessageId
        WHERE sm.LeadId = ?
        ORDER BY sm.ScheduledAt
        """
        return db.execute_query(query, (lead_id,), fetch_all=True) or []

    @staticmethod
    def get_pending_messages_to_send() -> List[Dict[str, Any]]:
        """Get all messages that are due to be sent"""
        query = """
        SELECT sm.*, m.MessageTitle, m.MessageType, m.MessageBody, m.FileUrl,
            l.PrimaryVisitorName, l.PrimaryVisitorPhone, l.CompanyName,
            lda.Status AS AssignmentStatus
        FROM ScheduledDripMessages sm
        JOIN MessageMaster m ON sm.MessageId = m.MessageId
        JOIN Leads l ON sm.LeadId = l.LeadId
        JOIN LeadDripAssignments lda ON sm.AssignmentId = lda.AssignmentId
        WHERE sm.Status = 'pending'
            AND sm.ScheduledAt <= SYSUTCDATETIME()
            AND lda.Status = 'active'
        ORDER BY sm.ScheduledAt
        """
        return db.execute_query(query, fetch_all=True) or []

    @staticmethod
    def mark_message_sent(scheduled_id: int, wa_message_id: Optional[str] = None) -> bool:
        """Mark a scheduled message as sent"""
        query = """
        UPDATE ScheduledDripMessages
        SET Status = 'sent', SentAt = SYSUTCDATETIME(), WhatsAppMessageId = ?, UpdatedAt = SYSUTCDATETIME()
        WHERE ScheduledId = ?
        """
        rows = db.execute_query(query, (wa_message_id, scheduled_id))
        return rows > 0

    @staticmethod
    def mark_message_failed(scheduled_id: int, error_message: str) -> bool:
        """Mark a scheduled message as failed"""
        query = """
        UPDATE ScheduledDripMessages
        SET Status = 'failed', ErrorMessage = ?, UpdatedAt = SYSUTCDATETIME()
        WHERE ScheduledId = ?
        """
        rows = db.execute_query(query, (error_message, scheduled_id))
        return rows > 0

    @staticmethod
    def skip_message(scheduled_id: int) -> bool:
        """Skip a scheduled message"""
        query = """
        UPDATE ScheduledDripMessages
        SET Status = 'skipped', UpdatedAt = SYSUTCDATETIME()
        WHERE ScheduledId = ?
        """
        rows = db.execute_query(query, (scheduled_id,))
        return rows > 0

    @staticmethod
    def get_all_assignments(status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all drip assignments with details"""
        query = """
        SELECT TOP (?) lda.*, d.DripName,
            l.PrimaryVisitorName, l.CompanyName, l.PrimaryVisitorPhone,
            (SELECT COUNT(*) FROM ScheduledDripMessages sm WHERE sm.AssignmentId = lda.AssignmentId AND sm.Status = 'sent') AS SentCount,
            (SELECT COUNT(*) FROM ScheduledDripMessages sm WHERE sm.AssignmentId = lda.AssignmentId AND sm.Status = 'pending') AS PendingCount
        FROM LeadDripAssignments lda
        JOIN DripMaster d ON lda.DripId = d.DripId
        JOIN Leads l ON lda.LeadId = l.LeadId
        """
        params = [limit]

        if status:
            query += " WHERE lda.Status = ?"
            params.append(status)

        query += " ORDER BY lda.CreatedAt DESC"

        return db.execute_query(query, tuple(params), fetch_all=True) or []


# Export singleton instance
drip_repo = DripRepository()
