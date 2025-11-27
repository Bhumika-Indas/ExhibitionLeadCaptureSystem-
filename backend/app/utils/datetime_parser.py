"""
Advanced Date/Time Parser for Natural Language Processing
Handles expressions like:
- "tomorrow at 3 PM"
- "next Monday at 11 AM"
- "day after tomorrow"
- "in 2 days at 4:30"
"""

import dateparser
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import re


class DateTimeParser:
    """Parse natural language date/time expressions"""

    @staticmethod
    def parse_datetime_from_text(text: str) -> Optional[Dict[str, Any]]:
        """
        Extract date and time from natural language text

        Args:
            text: Natural language text like "tomorrow at 3 PM"

        Returns:
            Dict with 'datetime', 'date_str', 'time_str', or None if not found
        """
        text_lower = text.lower().strip()

        # Try dateparser (handles most natural language)
        settings = {
            'PREFER_DATES_FROM': 'future',
            'RETURN_AS_TIMEZONE_AWARE': False,
            'RELATIVE_BASE': datetime.now()
        }

        parsed_dt = dateparser.parse(text, settings=settings)

        if parsed_dt:
            return {
                'datetime': parsed_dt,
                'date_str': parsed_dt.strftime('%Y-%m-%d'),
                'time_str': parsed_dt.strftime('%H:%M:%S'),
                'formatted': parsed_dt.strftime('%d %B %Y at %I:%M %p')
            }

        # Fallback: Try manual patterns
        return DateTimeParser._manual_parse(text_lower)

    @staticmethod
    def _manual_parse(text: str) -> Optional[Dict[str, Any]]:
        """Manual parsing for common patterns"""

        now = datetime.now()

        # Pattern: "tomorrow" or "kal"
        if 'tomorrow' in text or 'kal' in text:
            result_dt = now + timedelta(days=1)

            # Extract time if present
            time_match = re.search(r'(\d{1,2})\s*(?::(\d{2}))?\s*(am|pm|AM|PM)?', text)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                am_pm = time_match.group(3)

                if am_pm and am_pm.lower() == 'pm' and hour < 12:
                    hour += 12
                elif am_pm and am_pm.lower() == 'am' and hour == 12:
                    hour = 0

                result_dt = result_dt.replace(hour=hour, minute=minute, second=0)
            else:
                # Default: 4 PM
                result_dt = result_dt.replace(hour=16, minute=0, second=0)

            return {
                'datetime': result_dt,
                'date_str': result_dt.strftime('%Y-%m-%d'),
                'time_str': result_dt.strftime('%H:%M:%S'),
                'formatted': result_dt.strftime('%d %B %Y at %I:%M %p')
            }

        # Pattern: "today"
        if 'today' in text or 'aaj' in text:
            result_dt = now

            # Extract time
            time_match = re.search(r'(\d{1,2})\s*(?::(\d{2}))?\s*(am|pm|AM|PM)?', text)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                am_pm = time_match.group(3)

                if am_pm and am_pm.lower() == 'pm' and hour < 12:
                    hour += 12
                elif am_pm and am_pm.lower() == 'am' and hour == 12:
                    hour = 0

                result_dt = result_dt.replace(hour=hour, minute=minute, second=0)
            else:
                # Default: 4 PM
                result_dt = result_dt.replace(hour=16, minute=0, second=0)

            return {
                'datetime': result_dt,
                'date_str': result_dt.strftime('%Y-%m-%d'),
                'time_str': result_dt.strftime('%H:%M:%S'),
                'formatted': result_dt.strftime('%d %B %Y at %I:%M %p')
            }

        # Pattern: "in X days"
        days_match = re.search(r'in\s+(\d+)\s+days?', text)
        if days_match:
            days = int(days_match.group(1))
            result_dt = now + timedelta(days=days)

            # Extract time
            time_match = re.search(r'(\d{1,2})\s*(?::(\d{2}))?\s*(am|pm|AM|PM)?', text)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                am_pm = time_match.group(3)

                if am_pm and am_pm.lower() == 'pm' and hour < 12:
                    hour += 12

                result_dt = result_dt.replace(hour=hour, minute=minute, second=0)
            else:
                result_dt = result_dt.replace(hour=16, minute=0, second=0)

            return {
                'datetime': result_dt,
                'date_str': result_dt.strftime('%Y-%m-%d'),
                'time_str': result_dt.strftime('%H:%M:%S'),
                'formatted': result_dt.strftime('%d %B %Y at %I:%M %p')
            }

        # Pattern: specific day names
        day_names = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }

        for day_name, day_num in day_names.items():
            if day_name in text:
                # Find next occurrence of this day
                current_day = now.weekday()
                days_ahead = (day_num - current_day) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next week

                result_dt = now + timedelta(days=days_ahead)

                # Extract time
                time_match = re.search(r'(\d{1,2})\s*(?::(\d{2}))?\s*(am|pm|AM|PM)?', text)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    am_pm = time_match.group(3)

                    if am_pm and am_pm.lower() == 'pm' and hour < 12:
                        hour += 12

                    result_dt = result_dt.replace(hour=hour, minute=minute, second=0)
                else:
                    result_dt = result_dt.replace(hour=16, minute=0, second=0)

                return {
                    'datetime': result_dt,
                    'date_str': result_dt.strftime('%Y-%m-%d'),
                    'time_str': result_dt.strftime('%H:%M:%S'),
                    'formatted': result_dt.strftime('%d %B %Y at %I:%M %p')
                }

        return None

    @staticmethod
    def extract_employee_name(text: str) -> Optional[str]:
        """
        Extract employee name from text like "schedule with Minesh"

        Args:
            text: Input text

        Returns:
            Employee name or None
        """
        patterns = [
            r'with\s+([A-Z][a-z]+)',  # "with Minesh"
            r'by\s+([A-Z][a-z]+)',    # "by Minesh"
            r'from\s+([A-Z][a-z]+)',  # "from Minesh"
            r'to\s+([A-Z][a-z]+)',    # "to Minesh"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None


# Singleton instance
datetime_parser = DateTimeParser()
