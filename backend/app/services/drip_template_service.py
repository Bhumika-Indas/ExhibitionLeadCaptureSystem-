"""
Drip Template Service
Manages drip message templates with personalization variables
"""

from typing import Optional, Dict, List
from app.db.connection import db


class DripTemplateService:
    """Service for managing drip message templates"""

    # Default drip timeline (in days from lead creation)
    DRIP_TIMELINE = {
        "drip_0": {"day": 0, "name": "Instant Thanks + Confirmation"},
        "drip_1": {"day": 1, "name": "Product/Service Micro Intro"},
        "drip_2": {"day": 2, "name": "Short Case Study"},
        "drip_4": {"day": 4, "name": "Video Link (30 sec demo)"},
        "drip_7": {"day": 7, "name": "Benefits + Short Questionnaire"},
        "drip_14": {"day": 14, "name": "Strong CTA (Schedule Demo)"}
    }

    # Default templates for Decision Makers
    DECISION_MAKER_TEMPLATES = {
        "drip_0": "Hi {lead_name}, Thank you for visiting us at {exhibition_name}! It was great meeting you. We're excited to help {company_name} achieve better results. - Team {company_our_name}",
        "drip_1": "Hi {lead_name}, As discussed, we specialize in helping companies like {company_name} streamline operations and boost productivity. Would you like a quick overview?",
        "drip_2": "Hi {lead_name}, Here's a quick success story: One of our clients reduced their processing time by 40% in just 3 months. Similar results are possible for {company_name}. Interested?",
        "drip_4": "Hi {lead_name}, Here's a 30-second demo showing exactly how our solution works: {demo_video_link}. Let me know what you think!",
        "drip_7": "Hi {lead_name}, Key benefits for {company_name}: ✅ Save 50% time ✅ Reduce errors by 80% ✅ Real-time tracking. Quick question: What's your biggest operational challenge right now?",
        "drip_14": "Hi {lead_name}, I'd love to schedule a personalized demo for {company_name}. How does this week look? Just reply YES and I'll arrange everything. - {assigned_employee_name}"
    }

    # Technical/Production Templates
    TECHNICAL_TEMPLATES = {
        "drip_0": "Hi {lead_name}, Thanks for stopping by our stall at {exhibition_name}! We'd love to show you how our solution can enhance your production workflow.",
        "drip_1": "Hi {lead_name}, Our system integrates seamlessly with existing processes. Perfect for technical teams like yours at {company_name}.",
        "drip_2": "Hi {lead_name}, Case study: A production unit reduced downtime by 35% using our dashboard. Similar setup as {company_name}.",
        "drip_4": "Hi {lead_name}, Check out this quick technical demo: {demo_video_link}. Shows the actual interface your team would use.",
        "drip_7": "Hi {lead_name}, Top features for production: ✅ Real-time monitoring ✅ Automated alerts ✅ Performance analytics. What features matter most to your team?",
        "drip_14": "Hi {lead_name}, Ready for a technical walkthrough? I can show you the backend, API integrations, and customization options. Interested? Reply YES."
    }

    # Purchase/Procurement Templates
    PURCHASE_TEMPLATES = {
        "drip_0": "Hi {lead_name}, Thank you for visiting us at {exhibition_name}! We'd be happy to send you a detailed quotation for {company_name}.",
        "drip_1": "Hi {lead_name}, Our pricing is competitive with flexible payment options. Perfect for procurement teams like yours.",
        "drip_2": "Hi {lead_name}, ROI case study: Typical payback period is 6-8 months with 3x ROI over 2 years. Worth exploring for {company_name}?",
        "drip_4": "Hi {lead_name}, Quick product overview video: {demo_video_link}. Shows exactly what you're investing in.",
        "drip_7": "Hi {lead_name}, Value proposition: ✅ 40% cost reduction ✅ Faster processing ✅ Better accuracy. What's your budget planning timeline?",
        "drip_14": "Hi {lead_name}, Shall I send you a customized quotation for {company_name}? Just reply YES with your requirements."
    }

    # Sales/General Templates
    SALES_TEMPLATES = {
        "drip_0": "Hi {lead_name}, Thanks for meeting us at {exhibition_name}! We'd love to explore opportunities with {company_name}.",
        "drip_1": "Hi {lead_name}, Our solution helps businesses grow faster with better client management. Great fit for sales teams!",
        "drip_2": "Hi {lead_name}, Success story: A company increased their conversions by 60% using our CRM features. Similar potential for you?",
        "drip_4": "Hi {lead_name}, Quick demo showing the sales dashboard: {demo_video_link}. Very user-friendly!",
        "drip_7": "Hi {lead_name}, Key benefits: ✅ Track all leads ✅ Automated follow-ups ✅ Performance reports. What's your current lead management process?",
        "drip_14": "Hi {lead_name}, Would you like a demo focused on sales features? I can show you everything. Reply YES if interested!"
    }

    # General Templates
    GENERAL_TEMPLATES = {
        "drip_0": "Hi {lead_name}, Thank you for visiting us at {exhibition_name}! Feel free to reach out if you have any questions.",
        "drip_1": "Hi {lead_name}, Here's a quick intro to what we do: We help businesses automate and optimize their operations.",
        "drip_2": "Hi {lead_name}, Here's a quick case study showing real results from our solution. Take a look!",
        "drip_4": "Hi {lead_name}, Check out this 30-sec overview: {demo_video_link}",
        "drip_7": "Hi {lead_name}, Our solution offers: ✅ Easy to use ✅ Affordable ✅ Great support. Any questions?",
        "drip_14": "Hi {lead_name}, Would you like more information? Happy to schedule a quick call. Reply YES!"
    }

    TEMPLATE_MAP = {
        "decision_maker_drip": DECISION_MAKER_TEMPLATES,
        "technical_drip": TECHNICAL_TEMPLATES,
        "purchase_drip": PURCHASE_TEMPLATES,
        "sales_drip": SALES_TEMPLATES,
        "general_drip": GENERAL_TEMPLATES
    }

    def get_template(self, drip_template_type: str, drip_number: int) -> Optional[str]:
        """
        Get template message for a specific drip

        Args:
            drip_template_type: Type of template (decision_maker_drip, technical_drip, etc.)
            drip_number: Drip number (0, 1, 2, 4, 7, 14)

        Returns:
            Template string or None
        """
        drip_key = f"drip_{drip_number}"
        templates = self.TEMPLATE_MAP.get(drip_template_type, self.GENERAL_TEMPLATES)
        return templates.get(drip_key)

    def personalize_message(self, template: str, variables: Dict[str, str]) -> str:
        """
        Replace variables in template with actual values

        Args:
            template: Template string with {variable} placeholders
            variables: Dict of variable_name: value

        Returns:
            Personalized message
        """
        message = template

        # Default variables
        defaults = {
            "lead_name": "there",
            "company_name": "your company",
            "exhibition_name": "the exhibition",
            "demo_video_link": "https://yourdemo.link",
            "assigned_employee_name": "Our Team",
            "company_our_name": "Our Company"
        }

        # Merge with provided variables
        all_vars = {**defaults, **variables}

        # Replace all variables
        for var_name, var_value in all_vars.items():
            message = message.replace(f"{{{var_name}}}", str(var_value))

        return message

    def get_drip_day(self, drip_number: int) -> int:
        """Get the day offset for a drip number"""
        drip_key = f"drip_{drip_number}"
        return self.DRIP_TIMELINE.get(drip_key, {}).get("day", 0)

    def get_all_drip_days(self) -> List[int]:
        """Get list of all drip days"""
        return [0, 1, 2, 4, 7, 14]


# Singleton instance
drip_template_service = DripTemplateService()
