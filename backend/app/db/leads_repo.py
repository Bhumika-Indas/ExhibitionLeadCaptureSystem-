"""
Leads Repository - Database operations for Leads
Raw SQL queries using pyodbc
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.connection import db


class LeadsRepository:
    """Repository for Lead-related database operations"""

    @staticmethod
    def create_lead(
        exhibition_id: int,
        source_code: str,
        assigned_employee_id: Optional[int] = None,
        company_name: Optional[str] = None,
        primary_visitor_name: Optional[str] = None,
        primary_visitor_designation: Optional[str] = None,
        primary_visitor_phone: Optional[str] = None,
        primary_visitor_email: Optional[str] = None,
        discussion_summary: Optional[str] = None,
        next_step: Optional[str] = None,
        status_code: str = "new",
        raw_card_json: Optional[str] = None,
        raw_voice_transcript: Optional[str] = None
    ) -> int:
        """Create new lead and return LeadId"""
        query = """
        INSERT INTO Leads (
            ExhibitionId, SourceCode, AssignedEmployeeId,
            CompanyName, PrimaryVisitorName, PrimaryVisitorDesignation,
            PrimaryVisitorPhone, PrimaryVisitorEmail,
            DiscussionSummary, NextStep, StatusCode,
            RawCardJson, RawVoiceTranscript
        )
        OUTPUT INSERTED.LeadId
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        lead_id = db.execute_scalar(query, (
            exhibition_id, source_code, assigned_employee_id,
            company_name, primary_visitor_name, primary_visitor_designation,
            primary_visitor_phone, primary_visitor_email,
            discussion_summary, next_step, status_code,
            raw_card_json, raw_voice_transcript
        ))

        return lead_id

    @staticmethod
    def get_lead_by_id(lead_id: int) -> Optional[Dict[str, Any]]:
        """Get lead by ID with all details"""
        query = """
        SELECT
            l.*,
            e.Name AS ExhibitionName,
            emp.FullName AS AssignedEmployeeName,
            ls.Name AS SourceName,
            lst.Name AS StatusName
        FROM Leads l
        LEFT JOIN Exhibitions e ON l.ExhibitionId = e.ExhibitionId
        LEFT JOIN Employees emp ON l.AssignedEmployeeId = emp.EmployeeId
        LEFT JOIN LeadSources ls ON l.SourceCode = ls.SourceCode
        LEFT JOIN LeadStatuses lst ON l.StatusCode = lst.StatusCode
        WHERE l.LeadId = ?
        """
        return db.execute_query(query, (lead_id,), fetch_one=True)

    @staticmethod
    def get_leads(
        exhibition_id: Optional[int] = None,
        source_code: Optional[str] = None,
        status_code: Optional[str] = None,
        assigned_employee_id: Optional[int] = None,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get leads with filters (only active by default)"""
        conditions = []
        params = []

        # Only show active leads by default (requires migration 005)
        if not include_inactive:
            conditions.append("l.IsActive = 1")

        if exhibition_id:
            conditions.append("l.ExhibitionId = ?")
            params.append(exhibition_id)

        if source_code:
            conditions.append("l.SourceCode = ?")
            params.append(source_code)

        if status_code:
            conditions.append("l.StatusCode = ?")
            params.append(status_code)

        if assigned_employee_id:
            conditions.append("l.AssignedEmployeeId = ?")
            params.append(assigned_employee_id)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
        SELECT
            l.LeadId, l.ExhibitionId, l.SourceCode, l.StatusCode,
            l.CompanyName, l.PrimaryVisitorName, l.PrimaryVisitorPhone,
            l.PrimaryVisitorEmail, l.DiscussionSummary, l.NextStep,
            l.WhatsAppConfirmed, l.CreatedAt, l.UpdatedAt,
            e.Name AS ExhibitionName,
            emp.FullName AS AssignedEmployeeName,
            ls.Name AS SourceName,
            lst.Name AS StatusName
        FROM Leads l
        LEFT JOIN Exhibitions e ON l.ExhibitionId = e.ExhibitionId
        LEFT JOIN Employees emp ON l.AssignedEmployeeId = emp.EmployeeId
        LEFT JOIN LeadSources ls ON l.SourceCode = ls.SourceCode
        LEFT JOIN LeadStatuses lst ON l.StatusCode = lst.StatusCode
        {where_clause}
        ORDER BY l.CreatedAt DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        params.extend([offset, limit])
        return db.execute_query(query, tuple(params), fetch_all=True)

    @staticmethod
    def update_lead(
        lead_id: int,
        company_name: Optional[str] = None,
        primary_visitor_name: Optional[str] = None,
        primary_visitor_designation: Optional[str] = None,
        primary_visitor_phone: Optional[str] = None,
        primary_visitor_email: Optional[str] = None,
        discussion_summary: Optional[str] = None,
        next_step: Optional[str] = None,
        status_code: Optional[str] = None,
        whatsapp_confirmed: Optional[bool] = None,
        assigned_employee_id: Optional[int] = None,
        raw_card_json: Optional[str] = None,
        segment: Optional[str] = None,
        priority: Optional[str] = None
    ) -> bool:
        """Update lead fields"""
        updates = []
        params = []

        if company_name is not None:
            updates.append("CompanyName = ?")
            params.append(company_name)

        if primary_visitor_name is not None:
            updates.append("PrimaryVisitorName = ?")
            params.append(primary_visitor_name)

        if primary_visitor_designation is not None:
            updates.append("PrimaryVisitorDesignation = ?")
            params.append(primary_visitor_designation)

        if primary_visitor_phone is not None:
            updates.append("PrimaryVisitorPhone = ?")
            params.append(primary_visitor_phone)

        if primary_visitor_email is not None:
            updates.append("PrimaryVisitorEmail = ?")
            params.append(primary_visitor_email)

        if discussion_summary is not None:
            updates.append("DiscussionSummary = ?")
            params.append(discussion_summary)

        if next_step is not None:
            updates.append("NextStep = ?")
            params.append(next_step)

        if status_code is not None:
            updates.append("StatusCode = ?")
            params.append(status_code)

        if whatsapp_confirmed is not None:
            updates.append("WhatsAppConfirmed = ?")
            params.append(whatsapp_confirmed)
            if whatsapp_confirmed:
                updates.append("ConfirmedAt = SYSUTCDATETIME()")

        if assigned_employee_id is not None:
            updates.append("AssignedEmployeeId = ?")
            params.append(assigned_employee_id)

        if raw_card_json is not None:
            updates.append("RawCardJson = ?")
            params.append(raw_card_json)

        if segment is not None:
            updates.append("Segment = ?")
            params.append(segment)

        if priority is not None:
            updates.append("Priority = ?")
            params.append(priority)

        if not updates:
            return False

        updates.append("UpdatedAt = SYSUTCDATETIME()")
        params.append(lead_id)

        query = f"""
        UPDATE Leads
        SET {', '.join(updates)}
        WHERE LeadId = ?
        """

        rows_affected = db.execute_query(query, tuple(params))
        return rows_affected > 0

    @staticmethod
    def find_lead_by_phone(phone: str) -> Optional[Dict[str, Any]]:
        """
        Find existing lead by phone number
        Handles various phone formats: +919876543210, 919876543210, 9876543210
        """
        import re

        # Clean phone number to just digits
        cleaned = re.sub(r"[^\d]", "", phone)

        # Extract last 10 digits (handle +91, 91, or raw 10 digits)
        if len(cleaned) >= 10:
            cleaned = cleaned[-10:]

        # Search with multiple possible formats
        query = """
        SELECT TOP 1 *
        FROM Leads
        WHERE PrimaryVisitorPhone = ?
           OR PrimaryVisitorPhone = ?
           OR PrimaryVisitorPhone = ?
           OR RIGHT(REPLACE(REPLACE(PrimaryVisitorPhone, '+', ''), ' ', ''), 10) = ?
        ORDER BY CreatedAt DESC
        """
        # Try: raw input, cleaned 10 digits, with +91 prefix, and RIGHT match
        return db.execute_query(query, (phone, cleaned, f"+91{cleaned}", cleaned), fetch_one=True)

    @staticmethod
    def find_lead_by_partial_phone(partial_phone: str) -> Optional[Dict[str, Any]]:
        """
        Find lead by last 8 digits (fallback for LID numbers like 9198765...)
        Used when full phone doesn't match but last 8 digits might
        """
        import re

        # Clean to digits only
        cleaned = re.sub(r"[^\d]", "", partial_phone)

        # Get last 8 digits
        if len(cleaned) >= 8:
            last_8 = cleaned[-8:]
        else:
            return None

        query = """
        SELECT TOP 1 *
        FROM Leads
        WHERE RIGHT(REPLACE(REPLACE(PrimaryVisitorPhone, '+', ''), ' ', ''), 8) = ?
        ORDER BY CreatedAt DESC
        """
        return db.execute_query(query, (last_8,), fetch_one=True)

    @staticmethod
    def add_person(
        lead_id: int,
        name: str,
        designation: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        is_primary: bool = False
    ) -> int:
        """Add person to lead"""
        query = """
        INSERT INTO LeadPersons (LeadId, Name, Designation, Phone, Email, IsPrimary)
        OUTPUT INSERTED.LeadPersonId
        VALUES (?, ?, ?, ?, ?, ?)
        """
        return db.execute_scalar(query, (lead_id, name, designation, phone, email, is_primary))

    @staticmethod
    def add_address(
        lead_id: int,
        address_text: str,
        address_type: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        pin_code: Optional[str] = None
    ) -> int:
        """Add address to lead"""
        query = """
        INSERT INTO LeadAddresses (LeadId, AddressType, AddressText, City, State, Country, PinCode)
        OUTPUT INSERTED.LeadAddressId
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return db.execute_scalar(query, (lead_id, address_type, address_text, city, state, country, pin_code))

    @staticmethod
    def add_website(lead_id: int, website_url: str) -> int:
        """Add website to lead"""
        query = """
        INSERT INTO LeadWebsites (LeadId, WebsiteUrl)
        OUTPUT INSERTED.LeadWebsiteId
        VALUES (?, ?)
        """
        return db.execute_scalar(query, (lead_id, website_url))

    @staticmethod
    def add_service(lead_id: int, service_text: str) -> int:
        """Add service/product to lead"""
        query = """
        INSERT INTO LeadServices (LeadId, ServiceText)
        OUTPUT INSERTED.LeadServiceId
        VALUES (?, ?)
        """
        return db.execute_scalar(query, (lead_id, service_text))

    @staticmethod
    def add_topic(lead_id: int, topic_text: str) -> int:
        """Add topic to lead"""
        query = """
        INSERT INTO LeadTopics (LeadId, TopicText)
        OUTPUT INSERTED.LeadTopicId
        VALUES (?, ?)
        """
        return db.execute_scalar(query, (lead_id, topic_text))

    @staticmethod
    def add_brand(lead_id: int, brand_name: str, relationship: Optional[str] = None) -> int:
        """Add brand/supplier association to lead (for dealer cards)"""
        query = """
        INSERT INTO LeadBrands (LeadId, BrandName, Relationship)
        OUTPUT INSERTED.LeadBrandId
        VALUES (?, ?, ?)
        """
        return db.execute_scalar(query, (lead_id, brand_name, relationship))

    @staticmethod
    def add_phone(lead_id: int, phone_number: str, phone_type: Optional[str] = None) -> int:
        """Add phone number to lead"""
        query = """
        INSERT INTO LeadPhones (LeadId, PhoneNumber, PhoneType)
        OUTPUT INSERTED.LeadPhoneId
        VALUES (?, ?, ?)
        """
        return db.execute_scalar(query, (lead_id, phone_number, phone_type))

    @staticmethod
    def add_email(lead_id: int, email_address: str) -> int:
        """Add email to lead"""
        query = """
        INSERT INTO LeadEmails (LeadId, EmailAddress)
        OUTPUT INSERTED.LeadEmailId
        VALUES (?, ?)
        """
        return db.execute_scalar(query, (lead_id, email_address))

    @staticmethod
    def get_lead_persons(lead_id: int) -> List[Dict[str, Any]]:
        """Get all persons for a lead"""
        query = "SELECT * FROM LeadPersons WHERE LeadId = ? ORDER BY IsPrimary DESC, LeadPersonId"
        return db.execute_query(query, (lead_id,), fetch_all=True)

    @staticmethod
    def get_lead_addresses(lead_id: int) -> List[Dict[str, Any]]:
        """Get all addresses for a lead"""
        query = "SELECT * FROM LeadAddresses WHERE LeadId = ? ORDER BY LeadAddressId"
        return db.execute_query(query, (lead_id,), fetch_all=True)

    @staticmethod
    def get_lead_websites(lead_id: int) -> List[Dict[str, Any]]:
        """Get all websites for a lead"""
        query = "SELECT * FROM LeadWebsites WHERE LeadId = ? ORDER BY LeadWebsiteId"
        return db.execute_query(query, (lead_id,), fetch_all=True)

    @staticmethod
    def get_lead_services(lead_id: int) -> List[Dict[str, Any]]:
        """Get all services for a lead"""
        query = "SELECT * FROM LeadServices WHERE LeadId = ? ORDER BY LeadServiceId"
        return db.execute_query(query, (lead_id,), fetch_all=True)

    @staticmethod
    def get_lead_topics(lead_id: int) -> List[Dict[str, Any]]:
        """Get all topics for a lead"""
        query = "SELECT * FROM LeadTopics WHERE LeadId = ? ORDER BY LeadTopicId"
        return db.execute_query(query, (lead_id,), fetch_all=True)

    @staticmethod
    def get_lead_brands(lead_id: int) -> List[Dict[str, Any]]:
        """Get all brands/suppliers for a lead"""
        query = "SELECT * FROM LeadBrands WHERE LeadId = ? ORDER BY LeadBrandId"
        return db.execute_query(query, (lead_id,), fetch_all=True)

    @staticmethod
    def get_lead_phones(lead_id: int) -> List[Dict[str, Any]]:
        """Get all phones for a lead"""
        query = "SELECT * FROM LeadPhones WHERE LeadId = ? ORDER BY LeadPhoneId"
        return db.execute_query(query, (lead_id,), fetch_all=True)

    @staticmethod
    def get_lead_emails(lead_id: int) -> List[Dict[str, Any]]:
        """Get all emails for a lead"""
        query = "SELECT * FROM LeadEmails WHERE LeadId = ? ORDER BY LeadEmailId"
        return db.execute_query(query, (lead_id,), fetch_all=True)

    @staticmethod
    def delete_lead(lead_id: int) -> bool:
        """
        Soft delete lead by marking IsActive = 0 (keeps all data)
        NOTE: Requires migration 005 to be run. Falls back to hard delete message if column missing.
        Returns True if successful
        """
        try:
            # Try soft delete first (requires IsActive column)
            query = """
            UPDATE Leads
            SET IsActive = 0, UpdatedAt = GETDATE()
            WHERE LeadId = ?
            """
            db.execute_query(query, (lead_id,))
            return True
        except Exception as e:
            error_msg = str(e)
            if "IsActive" in error_msg:
                print(f"⚠️ IsActive column missing. Run migration 005. Lead {lead_id} not deleted.")
                return False
            print(f"Error marking lead {lead_id} as inactive: {e}")
            return False

    @staticmethod
    def restore_lead(lead_id: int) -> bool:
        """
        Restore a soft-deleted lead by marking IsActive = 1
        NOTE: Requires migration 005 to be run.
        Returns True if successful
        """
        try:
            query = """
            UPDATE Leads
            SET IsActive = 1, UpdatedAt = GETDATE()
            WHERE LeadId = ?
            """
            db.execute_query(query, (lead_id,))
            return True
        except Exception as e:
            error_msg = str(e)
            if "IsActive" in error_msg:
                print(f"⚠️ IsActive column missing. Run migration 005.")
                return False
            print(f"Error restoring lead {lead_id}: {e}")
            return False

    @staticmethod
    def hard_delete_lead(lead_id: int) -> bool:
        """
        HARD DELETE lead and all related data
        WARNING: This permanently removes the lead from database
        Use soft delete (delete_lead) instead for production
        """
        try:
            # Delete in correct order due to foreign key constraints
            tables = [
                "Messages",
                "Attachments",
                "Followups",
                "LeadPersons",
                "LeadAddresses",
                "LeadWebsites",
                "LeadServices",
                "LeadTopics",
                "LeadBrands",
                "LeadPhones",
                "LeadEmails",
                "Leads"
            ]

            for table in tables:
                query = f"DELETE FROM {table} WHERE LeadId = ?"
                db.execute_query(query, (lead_id,))

            return True
        except Exception as e:
            print(f"Error hard deleting lead {lead_id}: {e}")
            return False


# Export singleton instance
leads_repo = LeadsRepository()
