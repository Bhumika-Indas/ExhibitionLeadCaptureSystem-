"""
Phone Number Normalization Utilities
"""

import re


class PhoneNormalizer:
    """Normalize phone numbers to consistent format"""

    @staticmethod
    def normalize(phone: str, country_code: str = "91") -> str:
        """
        Normalize phone number to +{country_code}{number} format

        Args:
            phone: Raw phone number
            country_code: Default country code (default: 91 for India)

        Returns:
            Normalized phone number
        """
        if not phone:
            return ""

        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)

        # Handle different formats
        if len(digits) == 10:
            # Indian 10-digit mobile
            return f"+{country_code}{digits}"

        elif len(digits) == 12 and digits.startswith(country_code):
            # Already has country code
            return f"+{digits}"

        elif len(digits) == 11 and digits.startswith("0"):
            # With leading 0 (some formats)
            return f"+{country_code}{digits[1:]}"

        elif digits.startswith(country_code):
            # Has country code but variable length
            return f"+{digits}"

        else:
            # Unknown format, return as-is with +
            return f"+{digits}"

    @staticmethod
    def is_valid_indian_mobile(phone: str) -> bool:
        """Check if valid Indian mobile number"""
        normalized = PhoneNormalizer.normalize(phone)
        # Indian mobile: +91 followed by 10 digits starting with 6-9
        pattern = r'^\+91[6-9]\d{9}$'
        return bool(re.match(pattern, normalized))

    @staticmethod
    def extract_numbers_from_text(text: str) -> list:
        """Extract potential phone numbers from text"""
        # Match patterns like: 9876543210, +91-9876543210, (98) 7654-3210, etc.
        patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # International
            r'\d{10}',  # Simple 10-digit
            r'\d{5}[-.\s]?\d{5}',  # Split format
        ]

        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            numbers.extend(matches)

        # Normalize and de-duplicate
        normalized = [PhoneNormalizer.normalize(num) for num in numbers]
        return list(set(normalized))


# Singleton instance
phone_normalizer = PhoneNormalizer()
