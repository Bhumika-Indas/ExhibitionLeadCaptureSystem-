"""
Correction Parser - Automatically parse and apply corrections to lead fields
Handles patterns like:
- "Designation-HR"
- "Name: Ritesh Gupta"
- "Phone: 9782345678"
- "Company-ABC Limited"
"""

import re
from typing import Dict, Optional, Any


class CorrectionParser:
    """Parse correction text and extract field updates"""

    # Field patterns with various separators (: - space)
    PATTERNS = {
        "designation": r"(?:designation|role|post|position)[:\-\s]+([^\n]+)",
        "name": r"(?:name|naam)[:\-\s]+([^\n]+)",
        "company": r"(?:company|firm|organization|organisation)[:\-\s]+([^\n]+)",
        "phone": r"(?:phone|mobile|number|contact)[:\-\s]+([0-9\+\-\s]+)",
        "email": r"(?:email|mail|e-mail)[:\-\s]+([^\s@]+@[^\s@]+\.[^\s@]+)",
    }

    @staticmethod
    def parse_correction(text: str) -> Dict[str, Any]:
        """
        Parse correction text and extract field updates

        Args:
            text: Correction text from user

        Returns:
            Dict with field names as keys and corrected values as values
            Example: {"designation": "HR", "company": "ABC Limited"}
        """
        corrections = {}
        text_lower = text.lower().strip()

        # Try each pattern
        for field_name, pattern in CorrectionParser.PATTERNS.items():
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean up the value
                value = value.strip('.,;')
                if value:
                    corrections[field_name] = value

        # Handle simple single-word designation (like just "HR" or "Manager")
        # Only if no other fields detected and text is short
        if not corrections and len(text.split()) <= 3:
            # Check if text contains common designation keywords
            designation_keywords = [
                "hr", "manager", "ceo", "cto", "director", "executive",
                "engineer", "developer", "designer", "analyst", "consultant",
                "officer", "head", "lead", "senior", "junior", "assistant"
            ]
            if any(keyword in text_lower for keyword in designation_keywords):
                corrections["designation"] = text.strip()

        return corrections

    @staticmethod
    def apply_corrections_to_lead(lead_id: int, corrections: Dict[str, Any]) -> bool:
        """
        Apply parsed corrections to a lead in the database

        Args:
            lead_id: ID of the lead to update
            corrections: Dict of field corrections

        Returns:
            True if successful, False otherwise
        """
        if not corrections:
            return False

        from app.db.connection import db

        # Map correction keys to database columns
        field_mapping = {
            "designation": "PrimaryVisitorDesignation",
            "name": "PrimaryVisitorName",
            "company": "CompanyName",
            "phone": "PrimaryVisitorPhone",
            "email": "PrimaryVisitorEmail",
        }

        # Build UPDATE query dynamically
        updates = []
        params = []

        for field_key, value in corrections.items():
            if field_key in field_mapping:
                db_column = field_mapping[field_key]
                updates.append(f"{db_column} = ?")
                params.append(value)

        if not updates:
            return False

        # Add ConversationState and UpdatedAt
        updates.append("ConversationState = 'correction_applied'")
        updates.append("StatusCode = 'confirmed'")
        updates.append("UpdatedAt = SYSUTCDATETIME()")

        # Add LeadId parameter at the end
        params.append(lead_id)

        query = f"""
        UPDATE Leads
        SET {', '.join(updates)}
        WHERE LeadId = ?
        """

        try:
            db.execute_query(query, tuple(params))
            print(f"✅ Applied corrections to Lead {lead_id}: {corrections}")

            # Re-run segmentation if designation was changed
            if "designation" in corrections:
                CorrectionParser._recalculate_segmentation(lead_id)

            return True
        except Exception as e:
            print(f"❌ Error applying corrections: {e}")
            return False

    @staticmethod
    def _recalculate_segmentation(lead_id: int):
        """Re-run lead segmentation after designation change"""
        try:
            from app.services.lead_segmentation_service import lead_segmentation_service

            # Get updated lead data
            lead_query = """
            SELECT LeadId, PrimaryVisitorDesignation
            FROM Leads
            WHERE LeadId = ?
            """
            lead = db.execute_query(lead_query, (lead_id,), fetch_one=True)

            if lead and lead.get('PrimaryVisitorDesignation'):
                # Re-classify lead
                segment = lead_segmentation_service.classify_lead(
                    lead.get('PrimaryVisitorDesignation')
                )
                print(f"🔄 Recalculated segment for Lead {lead_id}: {segment}")

        except Exception as e:
            print(f"⚠️ Error recalculating segmentation: {e}")


# Singleton instance
correction_parser = CorrectionParser()
