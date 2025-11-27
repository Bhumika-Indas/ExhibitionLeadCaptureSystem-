"""
Advanced Intent Classifier
Uses OpenAI GPT-4 for comprehensive intent detection with context awareness
"""

from typing import Dict, Any, Optional
from openai import OpenAI
from app.config import settings
import json


class AdvancedIntentClassifier:
    """Advanced intent classification with conversation context"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def classify_with_context(
        self,
        message_text: str,
        conversation_state: Optional[str] = None,
        sender_type: str = "visitor",
        lead_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Classify intent with full conversation context

        Args:
            message_text: The message to classify
            conversation_state: Current state (awaiting_confirmation, needs_correction, etc.)
            sender_type: "visitor" or "employee"
            lead_data: Lead information for context

        Returns:
            Dict with intent, entities, confidence, and suggested_action
        """

        # Build context-aware prompt
        context_info = self._build_context(conversation_state, sender_type, lead_data)

        prompt = f"""
You are an AI assistant for an Exhibition Lead Capture System. Analyze this WhatsApp message and classify the intent.

**Context:**
{context_info}

**Message from {sender_type}:**
"{message_text}"

**Your Task:**
Classify the intent and extract entities. Return STRICT JSON with this structure:
{{
  "intent": "<PRIMARY_INTENT>",
  "sub_intent": "<OPTIONAL_SUB_INTENT>",
  "confidence": 0.0-1.0,
  "entities": {{
    "datetime": "extracted datetime if present",
    "employee_name": "employee name if mentioned",
    "field_updates": {{"field": "value"}},
    "sentiment": "positive/negative/neutral"
  }},
  "suggested_action": "what system should do next"
}}

**Available Intents:**

PRIMARY INTENTS:
1. DEMO_SCHEDULE - User wants to schedule a product demo
2. MEETING_SCHEDULE - User wants to schedule a meeting/call
3. CORRECTION - User wants to correct their information
4. CONFIRMATION - User confirms information is correct (Yes/OK/Correct)
5. NEGATION - User rejects or says no
6. VOICE_NOTE_INSTRUCTION - User is giving instructions via voice note
7. REMARK - User is adding a remark or comment
8. FOLLOWUP_REQUEST - User wants a follow-up
9. PROBLEM_REPORT - User is reporting an issue
10. REQUIREMENT_INQUIRY - User asking about requirements/quotation
11. NEXT_STEP_QUERY - User asking about next steps
12. GENERAL_QUERY - General question
13. GREETING - Hello/Hi/Namaste
14. THANK_YOU - Gratitude expression
15. EMPLOYEE_INTERNAL_NOTE - Employee adding internal note

SUB INTENTS (for specificity):
- DEMO_SCHEDULE_URGENT - Needs demo immediately
- CORRECTION_DESIGNATION - Correcting designation specifically
- CORRECTION_NAME - Correcting name
- CORRECTION_COMPANY - Correcting company
- CORRECTION_PHONE - Correcting phone
- MEETING_RESCHEDULE - Rescheduling existing meeting

**Examples:**

Input: "Schedule demo with Minesh tomorrow at 3 PM"
Output:
{{
  "intent": "DEMO_SCHEDULE",
  "confidence": 0.95,
  "entities": {{
    "datetime": "tomorrow at 3 PM",
    "employee_name": "Minesh"
  }},
  "suggested_action": "create_demo_followup_and_notify_minesh"
}}

Input: "Designation - Head R&D"
Output:
{{
  "intent": "CORRECTION",
  "sub_intent": "CORRECTION_DESIGNATION",
  "confidence": 0.98,
  "entities": {{
    "field_updates": {{"designation": "Head R&D"}}
  }},
  "suggested_action": "update_designation_and_confirm"
}}

Input: "Yes, everything is correct"
Output:
{{
  "intent": "CONFIRMATION",
  "confidence": 0.99,
  "entities": {{}},
  "suggested_action": "mark_lead_confirmed"
}}

**Important Rules:**
- If conversation_state = "awaiting_confirmation", prioritize CONFIRMATION/NEGATION
- If sender_type = "employee", consider EMPLOYEE_INTERNAL_NOTE
- Extract datetime in natural language (don't convert)
- Extract all mentioned employee names
- For corrections, identify which field is being corrected

Return STRICT JSON ONLY.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert intent classifier for a business lead management system. You understand English, Hindi, and Hinglish. Always respond in strict JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            print(f"🤖 Advanced Intent Classification: {result.get('intent')} (confidence: {result.get('confidence')})")

            return result

        except Exception as e:
            print(f"❌ Intent classification error: {e}")
            # Fallback
            return {
                "intent": "GENERAL_QUERY",
                "confidence": 0.5,
                "entities": {},
                "suggested_action": "log_and_acknowledge"
            }

    def _build_context(
        self,
        conversation_state: Optional[str],
        sender_type: str,
        lead_data: Optional[Dict]
    ) -> str:
        """Build context string for the prompt"""

        context_parts = []

        if conversation_state:
            context_parts.append(f"- Conversation State: {conversation_state}")

        context_parts.append(f"- Sender Type: {sender_type}")

        if lead_data:
            if lead_data.get('PrimaryVisitorName'):
                context_parts.append(f"- Lead Name: {lead_data['PrimaryVisitorName']}")
            if lead_data.get('CompanyName'):
                context_parts.append(f"- Company: {lead_data['CompanyName']}")
            if lead_data.get('StatusCode'):
                context_parts.append(f"- Lead Status: {lead_data['StatusCode']}")

        return "\n".join(context_parts) if context_parts else "No additional context"


# Singleton instance
advanced_intent_classifier = AdvancedIntentClassifier()
