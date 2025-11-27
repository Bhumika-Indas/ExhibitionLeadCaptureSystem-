"""
Duplicate Lead Detection Service
Detects potential duplicate leads based on multiple criteria
"""

from typing import List, Dict, Any, Optional
from app.db.leads_repo import leads_repo
from app.utils.phone_normalizer import phone_normalizer


class DuplicateDetectionService:
    """Service for detecting duplicate leads"""

    def __init__(self):
        self.phone_weight = 0.5  # Phone match is very strong indicator
        self.email_weight = 0.3  # Email match is strong
        self.company_weight = 0.15  # Company name match is medium
        self.name_weight = 0.05  # Name alone is weak
        self.threshold = 0.7  # 70% match threshold for duplicate

    def check_duplicate_before_save(self,
                                    company_name: Optional[str] = None,
                                    phone: Optional[str] = None,
                                    email: Optional[str] = None,
                                    visitor_name: Optional[str] = None,
                                    exhibition_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Check if lead is duplicate before saving
        Returns duplicate info if found
        """

        # Get all leads (optionally filtered by exhibition)
        filters = {}
        if exhibition_id:
            filters['exhibition_id'] = exhibition_id

        all_leads = leads_repo.get_leads(**filters)

        potential_duplicates = []

        for lead in all_leads:
            score = self._calculate_similarity_score(
                company_name, phone, email, visitor_name,
                lead.get('CompanyName'),
                lead.get('PrimaryVisitorPhone'),
                lead.get('PrimaryVisitorEmail'),
                lead.get('PrimaryVisitorName')
            )

            if score >= self.threshold:
                potential_duplicates.append({
                    'lead_id': lead['LeadId'],
                    'company_name': lead.get('CompanyName'),
                    'visitor_name': lead.get('PrimaryVisitorName'),
                    'phone': lead.get('PrimaryVisitorPhone'),
                    'email': lead.get('PrimaryVisitorEmail'),
                    'similarity_score': round(score * 100, 1),
                    'created_at': lead.get('CreatedAt')
                })

        # Sort by similarity score descending
        potential_duplicates.sort(key=lambda x: x['similarity_score'], reverse=True)

        return {
            'is_duplicate': len(potential_duplicates) > 0,
            'duplicate_count': len(potential_duplicates),
            'duplicates': potential_duplicates[:5]  # Return top 5 matches
        }

    def find_duplicates_for_lead(self, lead_id: int) -> List[Dict[str, Any]]:
        """Find potential duplicates for an existing lead"""

        lead = leads_repo.get_lead_by_id(lead_id)
        if not lead:
            return []

        result = self.check_duplicate_before_save(
            company_name=lead.get('CompanyName'),
            phone=lead.get('PrimaryVisitorPhone'),
            email=lead.get('PrimaryVisitorEmail'),
            visitor_name=lead.get('PrimaryVisitorName'),
            exhibition_id=lead.get('ExhibitionId')
        )

        # Filter out the lead itself
        duplicates = [d for d in result['duplicates'] if d['lead_id'] != lead_id]

        return duplicates

    def _calculate_similarity_score(self,
                                   company1: Optional[str],
                                   phone1: Optional[str],
                                   email1: Optional[str],
                                   name1: Optional[str],
                                   company2: Optional[str],
                                   phone2: Optional[str],
                                   email2: Optional[str],
                                   name2: Optional[str]) -> float:
        """Calculate similarity score between two leads"""

        score = 0.0

        # Phone match (strongest indicator)
        if phone1 and phone2:
            normalized_phone1 = phone_normalizer.normalize(phone1) or phone1
            normalized_phone2 = phone_normalizer.normalize(phone2) or phone2

            if normalized_phone1 and normalized_phone2:
                # Extract just digits for comparison
                digits1 = ''.join(filter(str.isdigit, normalized_phone1))[-10:]  # Last 10 digits
                digits2 = ''.join(filter(str.isdigit, normalized_phone2))[-10:]

                if digits1 == digits2 and len(digits1) >= 10:
                    score += self.phone_weight

        # Email match (strong indicator)
        if email1 and email2:
            email1_clean = email1.lower().strip()
            email2_clean = email2.lower().strip()

            if email1_clean == email2_clean:
                score += self.email_weight

        # Company name match (medium indicator)
        if company1 and company2:
            company1_clean = self._clean_company_name(company1)
            company2_clean = self._clean_company_name(company2)

            if company1_clean and company2_clean:
                # Exact match
                if company1_clean == company2_clean:
                    score += self.company_weight
                # Fuzzy match (one contains the other)
                elif company1_clean in company2_clean or company2_clean in company1_clean:
                    score += self.company_weight * 0.7

        # Name match (weak indicator, only if other matches exist)
        if name1 and name2 and score > 0:
            name1_clean = name1.lower().strip()
            name2_clean = name2.lower().strip()

            if name1_clean == name2_clean:
                score += self.name_weight

        return min(score, 1.0)  # Cap at 1.0

    def _clean_company_name(self, company_name: str) -> str:
        """Clean company name for comparison"""
        if not company_name:
            return ""

        # Convert to lowercase
        cleaned = company_name.lower().strip()

        # Remove common suffixes
        suffixes = [' ltd', ' limited', ' pvt', ' private', ' inc', ' llc', ' corp', ' corporation',
                   ' co', ' company', ' & co', ' and co', '.', ',']

        for suffix in suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()

        # Remove extra spaces
        cleaned = ' '.join(cleaned.split())

        return cleaned

    def merge_leads(self, primary_lead_id: int, duplicate_lead_ids: List[int]) -> Dict[str, Any]:
        """
        Merge duplicate leads into primary lead
        Keeps primary lead, transfers data from duplicates, marks duplicates as merged
        """

        primary_lead = leads_repo.get_lead_by_id(primary_lead_id)
        if not primary_lead:
            return {'success': False, 'error': 'Primary lead not found'}

        merged_count = 0
        errors = []

        for dup_id in duplicate_lead_ids:
            try:
                # Get duplicate lead data
                dup_lead = leads_repo.get_lead_by_id(dup_id)
                if not dup_lead:
                    errors.append(f"Lead {dup_id} not found")
                    continue

                # Transfer additional contacts/phones/emails to primary
                # Get persons from duplicate
                dup_persons = leads_repo.get_lead_persons(dup_id)
                for person in dup_persons:
                    try:
                        leads_repo.add_person(
                            lead_id=primary_lead_id,
                            name=person['Name'],
                            designation=person.get('Designation'),
                            phone=person.get('Phone'),
                            email=person.get('Email'),
                            is_primary=False
                        )
                    except:
                        pass  # Skip if already exists

                # Get phones from duplicate
                dup_phones = leads_repo.get_lead_phones(dup_id)
                for phone in dup_phones:
                    try:
                        leads_repo.add_phone(primary_lead_id, phone['PhoneNumber'], phone.get('PhoneType'))
                    except:
                        pass

                # Get emails from duplicate
                dup_emails = leads_repo.get_lead_emails(dup_id)
                for email in dup_emails:
                    try:
                        leads_repo.add_email(primary_lead_id, email['EmailAddress'])
                    except:
                        pass

                # Mark duplicate as merged (update status)
                leads_repo.update_lead(
                    lead_id=dup_id,
                    status_code='merged',
                    next_step=f'Merged into Lead #{primary_lead_id}'
                )

                merged_count += 1

            except Exception as e:
                errors.append(f"Error merging lead {dup_id}: {str(e)}")

        return {
            'success': True,
            'merged_count': merged_count,
            'errors': errors if errors else None,
            'primary_lead_id': primary_lead_id
        }


# Singleton instance
duplicate_detection_service = DuplicateDetectionService()
