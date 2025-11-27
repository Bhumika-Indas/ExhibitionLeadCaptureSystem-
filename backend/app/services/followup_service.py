"""
Follow-up and Drip Sequence Management Service
Handles automated follow-ups for lead confirmations
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from app.db.connection import db
from app.services.whatsapp_service import whatsapp_service
from app.services.drip_template_service import drip_template_service
import asyncio


class FollowUpService:
    """Manage follow-up sequences and reminders"""

    # Drip sequence timings (in hours)
    DRIP_1_DELAY = 24  # 24 hours after initial message
    DRIP_2_DELAY = 72  # 72 hours (3 days) after initial
    DRIP_3_DELAY = 120  # 120 hours (5 days) after initial

    def __init__(self):
        pass

    async def schedule_smart_drip_sequence(
        self,
        lead_id: int,
        drip_template_type: str,
        lead_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Schedule smart drip sequence based on lead segment

        Args:
            lead_id: ID of the lead
            drip_template_type: Type of drip template (decision_maker_drip, technical_drip, etc.)
            lead_data: Optional lead data for personalization
        """
        # Get all drip days from template service
        drip_days = drip_template_service.get_all_drip_days()
        now = datetime.utcnow()

        query = """
        INSERT INTO FollowUps (LeadId, ScheduledAt, ActionType, Notes, Status, CreatedAt)
        VALUES (?, ?, ?, ?, ?, SYSUTCDATETIME())
        """

        for drip_day in drip_days:
            scheduled_at = now + timedelta(days=drip_day)
            action_type = f"drip_{drip_day}"
            notes = f"Drip template: {drip_template_type}"

            db.execute_query(
                query,
                (lead_id, scheduled_at, action_type, notes, 'pending')
            )

    async def schedule_drip_sequence(self, lead_id: int) -> None:
        """
        Schedule drip sequence for a lead that hasn't confirmed

        Args:
            lead_id: ID of the lead
        """
        # Create follow-up records
        now = datetime.utcnow()

        drips = [
            {
                'lead_id': lead_id,
                'scheduled_at': now + timedelta(hours=self.DRIP_1_DELAY),
                'drip_number': 1,
                'status': 'pending'
            },
            {
                'lead_id': lead_id,
                'scheduled_at': now + timedelta(hours=self.DRIP_2_DELAY),
                'drip_number': 2,
                'status': 'pending'
            },
            {
                'lead_id': lead_id,
                'scheduled_at': now + timedelta(hours=self.DRIP_3_DELAY),
                'drip_number': 3,
                'status': 'pending'
            },
        ]

        query = """
        INSERT INTO FollowUps (LeadId, ScheduledAt, ActionType, Status, CreatedAt)
        VALUES (?, ?, ?, ?, SYSUTCDATETIME())
        """

        for drip in drips:
            db.execute_query(
                query,
                (drip['lead_id'], drip['scheduled_at'], f"drip_{drip['drip_number']}", drip['status'])
            )

    async def cancel_drip_sequence(self, lead_id: int) -> None:
        """
        Cancel all pending drips for a lead (when they confirm)

        Args:
            lead_id: ID of the lead
        """
        query = """
        UPDATE FollowUps
        SET Status = 'cancelled', UpdatedAt = SYSUTCDATETIME()
        WHERE LeadId = ? AND Status = 'pending'
        """
        db.execute_query(query, (lead_id,))

    async def process_pending_followups(self) -> int:
        """
        Process all pending follow-ups that are due
        Should be called by a cron job/scheduler

        Returns:
            Number of follow-ups processed
        """
        # Get pending follow-ups that are due
        query = """
        SELECT f.FollowUpId, f.LeadId, f.ActionType,
               l.PrimaryVisitorName, l.CompanyName, l.PrimaryVisitorPhone,
               l.WhatsAppConfirmed, l.StatusCode
        FROM FollowUps f
        JOIN Leads l ON f.LeadId = l.LeadId
        WHERE f.Status = 'pending'
          AND f.ScheduledAt <= SYSUTCDATETIME()
          AND l.WhatsAppConfirmed = 0
          AND l.StatusCode != 'confirmed'
        """

        pending = db.execute_query(query, fetch_all=True)

        if not pending:
            return 0

        processed = 0
        for followup in pending:
            try:
                await self._send_drip_message(followup)

                # Mark as completed
                update_query = """
                UPDATE FollowUps
                SET Status = 'completed', CompletedAt = SYSUTCDATETIME(), UpdatedAt = SYSUTCDATETIME()
                WHERE FollowUpId = ?
                """
                db.execute_query(update_query, (followup['FollowUpId'],))
                processed += 1

            except Exception as e:
                print(f"Failed to process follow-up {followup['FollowUpId']}: {str(e)}")

                # Mark as failed
                update_query = """
                UPDATE FollowUps
                SET Status = 'failed', UpdatedAt = SYSUTCDATETIME()
                WHERE FollowUpId = ?
                """
                db.execute_query(update_query, (followup['FollowUpId'],))

        return processed

    async def _send_drip_message(self, followup: Dict[str, Any]) -> None:
        """Send appropriate drip message based on drip number"""
        action_type = followup['ActionType']
        drip_number = int(action_type.split('_')[1]) if 'drip_' in action_type else 1

        name = followup['PrimaryVisitorName'] or 'there'
        company = followup['CompanyName'] or 'your company'
        phone = followup['PrimaryVisitorPhone']

        # Generate message based on drip number
        if drip_number == 1:
            message = self._generate_drip_1_message(name, company)
        elif drip_number == 2:
            message = self._generate_drip_2_message(name, company)
        else:
            message = self._generate_drip_3_message(name, company)

        # Send via WhatsApp
        if phone:
            await whatsapp_service.send_text_message(phone, message)

    def _generate_drip_1_message(self, name: str, company: str) -> str:
        """Friendly reminder - 24 hours"""
        return f"""Hi {name} ji! 

Thank you for visiting our booth and sharing your details for {company}.

Just a gentle reminder - could you please confirm your details by replying with YES or NO?

It will help us serve you better! 

- INDAS Team"""

    def _generate_drip_2_message(self, name: str, company: str) -> str:
        """Stronger reminder - 3 days"""
        return f"""Hello {name}!

Hope you're doing well!

We noticed we haven't received confirmation for your details ({company}) from our recent exhibition.

Could you please take a moment to reply:
• YES if details are correct
• NO if any corrections needed

Looking forward to connecting with you!

Best regards,
INDAS Analytics"""

    def _generate_drip_3_message(self, name: str, company: str) -> str:
        """Final reminder - 5 days"""
        return f"""Dear {name},

This is our final reminder regarding your visit to INDAS booth.

We would love to assist {company} with our solutions, but we need your confirmation to proceed.

Please reply YES or NO at your earliest convenience.

If we don't hear from you, we'll assume you're not interested at this time.

Thank you for your time!

Warm regards,
INDAS Analytics Team"""

    async def get_lead_followups(self, lead_id: int) -> List[Dict[str, Any]]:
        """Get all follow-ups for a specific lead"""
        query = """
        SELECT FollowUpId, LeadId, ActionType, ScheduledAt, Status,
               CompletedAt, CreatedAt, UpdatedAt
        FROM FollowUps
        WHERE LeadId = ?
        ORDER BY ScheduledAt ASC
        """
        return db.execute_query(query, (lead_id,), fetch_all=True) or []

    async def create_manual_followup(
        self,
        lead_id: int,
        action_type: str,
        scheduled_at: datetime,
        notes: Optional[str] = None
    ) -> int:
        """
        Create a manual follow-up task

        Args:
            lead_id: ID of the lead
            action_type: Type of action (call, email, meeting, etc.)
            scheduled_at: When to execute this follow-up
            notes: Optional notes

        Returns:
            FollowUpId
        """
        query = """
        INSERT INTO FollowUps (LeadId, ActionType, ScheduledAt, Status, Notes, CreatedAt)
        OUTPUT INSERTED.FollowUpId
        VALUES (?, ?, ?, 'pending', ?, SYSUTCDATETIME())
        """

        result = db.execute_query(
            query,
            (lead_id, action_type, scheduled_at, notes),
            fetch_one=True
        )

        return result['FollowUpId'] if result else None


# Singleton instance
followup_service = FollowUpService()
