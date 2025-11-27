"""
Lead Segmentation Service
Automatically categorizes leads based on extracted card data
"""

from typing import Optional, Dict, List
from app.db.connection import db


class LeadSegmentationService:
    """Service for automatically segmenting leads based on their profile"""

    # Segment definitions
    SEGMENTS = {
        "DECISION_MAKER": {
            "keywords": ["owner", "director", "ceo", "coo", "cfo", "founder", "partner", "president", "gm", "general manager", "managing director", "md"],
            "priority": 1,
            "drip_template": "decision_maker_drip"
        },
        "TECHNICAL": {
            "keywords": ["manager", "engineer", "technical", "production", "head", "incharge", "in-charge", "supervisor", "asst manager", "assistant manager", "sr engineer", "senior engineer"],
            "priority": 2,
            "drip_template": "technical_drip"
        },
        "PURCHASE": {
            "keywords": ["purchase", "procurement", "buyer", "purchasing", "sourcing", "supply chain"],
            "priority": 2,
            "drip_template": "purchase_drip"
        },
        "SALES": {
            "keywords": ["sales", "marketing", "business development", "bd", "account manager", "executive"],
            "priority": 3,
            "drip_template": "sales_drip"
        },
        "GENERAL": {
            "keywords": ["student", "intern", "trainee", "vendor", "supplier", "consultant", "visitor"],
            "priority": 4,
            "drip_template": "general_drip"
        }
    }

    def segment_lead(self, designation: Optional[str]) -> Dict[str, any]:
        """
        Segment a lead based on their designation

        Args:
            designation: Job title/designation from visiting card

        Returns:
            Dict with segment, priority, and drip_template
        """
        if not designation:
            return {
                "segment": "UNKNOWN",
                "priority": 5,
                "drip_template": "general_drip"
            }

        designation_lower = designation.lower()

        # Check each segment's keywords
        for segment_name, segment_info in self.SEGMENTS.items():
            for keyword in segment_info["keywords"]:
                if keyword in designation_lower:
                    return {
                        "segment": segment_name,
                        "priority": segment_info["priority"],
                        "drip_template": segment_info["drip_template"]
                    }

        # Default to GENERAL if no match
        return {
            "segment": "GENERAL",
            "priority": 4,
            "drip_template": "general_drip"
        }

    def update_lead_segment(self, lead_id: int, segment: str, priority: int) -> bool:
        """
        Update lead's segment in database

        Args:
            lead_id: Lead ID
            segment: Segment name
            priority: Priority level

        Returns:
            True if successful
        """
        try:
            query = """
            UPDATE Leads
            SET Segment = ?, Priority = ?, UpdatedAt = SYSUTCDATETIME()
            WHERE LeadId = ?
            """
            db.execute_query(query, (segment, priority, lead_id))
            return True
        except Exception as e:
            print(f"Error updating lead segment: {e}")
            return False

    def get_segment_stats(self) -> List[Dict]:
        """Get statistics for each segment"""
        query = """
        SELECT
            Segment,
            COUNT(*) as LeadCount,
            AVG(CAST(Priority AS FLOAT)) as AvgPriority,
            SUM(CASE WHEN Status = 'confirmed' THEN 1 ELSE 0 END) as ConfirmedCount
        FROM Leads
        WHERE Segment IS NOT NULL
        GROUP BY Segment
        ORDER BY AvgPriority ASC
        """

        results = db.execute_query(query, fetch_all=True)
        return results or []

    def get_high_priority_leads(self, limit: int = 20) -> List[Dict]:
        """Get high priority leads (Decision Makers & Technical)"""
        query = """
        SELECT TOP (?)
            LeadId, PrimaryVisitorName, CompanyName, Segment, Priority,
            PrimaryVisitorDesignation, PrimaryVisitorPhone, Status
        FROM Leads
        WHERE Priority IN (1, 2) AND Status != 'lost'
        ORDER BY Priority ASC, CreatedAt DESC
        """

        results = db.execute_query(query, (limit,), fetch_all=True)
        return results or []


# Singleton instance
lead_segmentation_service = LeadSegmentationService()
