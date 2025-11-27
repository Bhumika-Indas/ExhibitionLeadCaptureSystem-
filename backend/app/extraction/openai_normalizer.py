"""
Regenerated OpenAI Normalizer for Visiting Cards & Voice Notes
Optimized for:
- EasyOCR pipeline
- Strong phone correction
- Stable JSON output
- Strict extraction rules
- Exhibition Lead Capture System
"""

import json
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI
from app.config import settings
from app.extraction.schemas import CardExtractionResult, VoiceExtractionResult

# ============================================================================
# PHONE EXTRACTION UTIL (Regex + OCR Correction)
# ============================================================================
def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract and clean Indian phone numbers from OCR text using regex.
    Handles:
    - Missing digits
    - Spaced numbers
    - Hyphens / dots / slashes
    - OCR errors: O->0, I->1, l->1, |->1
    """
    if not text:
        return []

    # Fix OCR mistakes
    clean = (
        text.replace("O", "0")
            .replace("o", "0")
            .replace("I", "1")
            .replace("l", "1")
            .replace("|", "1")
    )

    # Keep digits + plus + separators only
    clean = re.sub(r"[^0-9+\s\-]", " ", clean)

    # Pattern: strict Indian mobile numbers
    pattern = r"(\+91[\s\-]?\d{10}|[6-9]\d{9}|[6-9]\d{4}[\s\-]?\d{5})"
    matches = re.findall(pattern, clean)

    phones = []
    for m in matches:
        digits = re.sub(r"\D", "", m)
        if len(digits) >= 10:
            num = digits[-10:]
            if num[0] in "6789":
                phones.append(num)

    return list(set(phones))


# ============================================================================
# OPENAI NORMALIZER CLASS
# ============================================================================
class OpenAINormalizer:
    """Normalize OCR → Structured JSON using OpenAI Chat Models"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    # ----------------------------------------------------------------------
    # CARD NORMALIZER
    # ----------------------------------------------------------------------
    def normalize_card_data(
        self,
        front_ocr_text: str,
        back_ocr_text: Optional[str] = None,
        qr_data: Optional[Dict[str, Any]] = None,
        regex_phones: Optional[List[str]] = None
    ) -> CardExtractionResult:

        prompt = self._build_card_prompt(front_ocr_text, back_ocr_text, qr_data, regex_phones)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._system_rules()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                response_format={"type": "json_object"}
            )

            result_json = response.choices[0].message.content
            result_dict = json.loads(result_json)

            # Debug output
            print("=" * 90)
            print(" OPENAI CARD JSON OUTPUT:")
            print("=" * 90)
            print(json.dumps(result_dict, indent=2, ensure_ascii=False))
            print("=" * 90)

            # ------------------------
            # CONVERT NULL TO EMPTY LISTS
            # ------------------------
            # Ensure all list fields are lists, not null
            for field in ['persons', 'phones', 'emails', 'websites', 'addresses', 'services', 'brands']:
                if result_dict.get(field) is None:
                    result_dict[field] = []

            # Ensure person sub-fields are lists
            for person in result_dict.get('persons', []):
                if person.get('phones') is None:
                    person['phones'] = []
                if person.get('emails') is None:
                    person['emails'] = []

            # ------------------------
            # PHONE FALLBACK LOGIC
            # ------------------------
            if not result_dict.get("phones"):
                print("⚠️ OpenAI did not return phones → using regex fallback...")

                combined = f"{front_ocr_text} {back_ocr_text or ''}"
                fallback_phones = regex_phones or extract_phone_numbers(combined)

                if fallback_phones:
                    result_dict["phones"] = fallback_phones

                    if result_dict.get("persons"):
                        if "phones" not in result_dict["persons"][0] or not result_dict["persons"][0]["phones"]:
                            result_dict["persons"][0]["phones"] = fallback_phones

            # Convert back to pydantic model
            result = CardExtractionResult(**result_dict)
            result.raw_front_text = front_ocr_text
            result.raw_back_text = back_ocr_text
            return result

        except Exception as e:
            print(f"❌ OpenAI Normalization Error: {e}")
            return CardExtractionResult(
                raw_front_text=front_ocr_text,
                raw_back_text=back_ocr_text,
                confidence=0.0
            )

    # ----------------------------------------------------------------------
    # SYSTEM RULES FOR OPENAI
    # ----------------------------------------------------------------------
    def _system_rules(self) -> str:
        return """
You are an expert Indian Visiting Card Extraction Engine with ZERO HALLUCINATION POLICY.

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES - NO EXCEPTIONS
═══════════════════════════════════════════════════════════════════════════════
1. Extract ONLY what is 100% visible in the OCR text
2. If something is unclear or not present → set to null
3. NEVER guess, assume, or infer missing information
4. NEVER hallucinate names, companies, phones, emails
5. If OCR text is garbled for a field → null (don't guess)

═══════════════════════════════════════════════════════════════════════════════
MULTIPLE COMPANY NAMES (DEALER/DISTRIBUTOR CARDS)
═══════════════════════════════════════════════════════════════════════════════
Indian business cards often show MULTIPLE company/brand names:
- MAIN COMPANY: The dealer's own business (usually has the person's contact)
- BRANDS: Companies they represent (JK Paper, KRPL, etc.)

HOW TO IDENTIFY:
- Main company usually appears near person's name/contact
- Brands appear with "Dealer:", "Distributor:", "Authorized:", "Stockist of"
- Main company has unique email domain (karanpaper@gmail.com → Karan Paper Mart)

OUTPUT:
- company_name: Main business name only
- brands: Array of {brand_name, relationship} for each associated brand
- business_type: "Dealer" | "Distributor" | "Manufacturer" | "Wholesaler" | "Retailer"

Example: "Karan Paper Mart" + "JK Paper Ltd" + "KRPL"
→ company_name: "Karan Paper Mart"
→ brands: [{brand_name: "JK Paper Ltd", relationship: "Dealer"}, {brand_name: "KRPL", relationship: "Dealer"}]
→ business_type: "Dealer"

═══════════════════════════════════════════════════════════════════════════════
MULTIPLE PERSONS
═══════════════════════════════════════════════════════════════════════════════
Extract ALL persons visible on the card:
- First person with most contact info = is_primary: true
- Each person can have multiple phones and emails
- persons: [{name, designation, phones: [], emails: [], is_primary: true/false}]

═══════════════════════════════════════════════════════════════════════════════
MULTIPLE PHONES
═══════════════════════════════════════════════════════════════════════════════
- Extract ALL phone numbers (mobile + landline)
- Indian mobile: 10 digits starting with 6-9
- Landline: Usually starts with 0 (like 0120-4317716)
- Fix OCR errors: O→0, I→1, l→1, |→1
- Put in both: phones[] (all numbers) AND person.phones[] (person-specific)

═══════════════════════════════════════════════════════════════════════════════
MULTIPLE EMAILS
═══════════════════════════════════════════════════════════════════════════════
- Extract ALL email addresses
- Must have @ symbol
- Put in both: emails[] (all) AND person.emails[] (person-specific)

═══════════════════════════════════════════════════════════════════════════════
MULTIPLE ADDRESSES
═══════════════════════════════════════════════════════════════════════════════
- Extract ALL addresses with their types
- address_type: "Factory" | "Corporate" | "Branch" | "Registered" | "Works"
- Extract city, state, pin_code if visible

═══════════════════════════════════════════════════════════════════════════════
MESSY OCR HANDLING
═══════════════════════════════════════════════════════════════════════════════
- Fix ONLY clear OCR patterns: O→0, I→1, l→1, |→1, @→a (in email context)
- If text is completely garbled → null
- If phone has 9 digits but pattern is clear → try to infer missing digit
- If email domain looks like "gm@il.com" → correct to "gmail.com"

═══════════════════════════════════════════════════════════════════════════════
SERVICES/PRODUCTS
═══════════════════════════════════════════════════════════════════════════════
- Extract product/service descriptions
- NOT brand names (those go in brands[])
- Examples: "Wholesale Paper Merchants", "Coated Paper", "Packaging Materials"

═══════════════════════════════════════════════════════════════════════════════
CONFIDENCE SCORING
═══════════════════════════════════════════════════════════════════════════════
- 0.9-1.0: All fields clear, multiple contacts extracted
- 0.7-0.8: Most fields clear, some minor OCR issues
- 0.5-0.6: Some fields unclear, partial extraction
- 0.3-0.4: Many fields unclear, basic extraction only
- 0.0-0.2: Mostly garbled, minimal extraction

Return STRICT JSON only. Better to return null than wrong data.
"""

    # ----------------------------------------------------------------------
    # BUILD PROMPT
    # ----------------------------------------------------------------------
    def _build_card_prompt(self, front_text, back_text, qr_data, regex_phones) -> str:
        prompt = f"""
FRONT OCR TEXT:
{front_text}
"""
        if back_text:
            prompt += f"""
BACK OCR TEXT:
{back_text}
"""
        if qr_data:
            prompt += f"""
QR DATA:
{json.dumps(qr_data, indent=2)}
"""
        if regex_phones:
            prompt += f"""
REGEX PHONES (strong hints): {', '.join(regex_phones)}
"""

        prompt += """
Extract JSON with fields:
{
  "company_name": string|null,
  "persons": [
    { "name": string, "designation": string|null, "phones": [""], "email": string|null }
  ],
  "phones": ["10-digit cleaned numbers"],
  "emails": [string],
  "websites": [string],
  "addresses": [
    { "address_type": string|null, "address": string, "city": string|null,
      "state": string|null, "country": string|null, "pin_code": string|null }
  ],
  "services": [string],
  "is_two_sided": true/false,
  "back_side_type": "Info|Decorative|Products|Mixed|null",
  "confidence": 0.0 - 1.0
}

IMPORTANT:
- Return STRICT JSON only.
- Fix phone numbers using regex hints.
"""
        return prompt

    # ----------------------------------------------------------------------
    # VOICE NORMALIZATION - Enhanced with Segment/Priority/NextStep
    # Supports Hindi, English, and Hinglish (bilingual) transcripts
    # ----------------------------------------------------------------------
    def normalize_voice_transcript(self, transcript: str, context: str = "Exhibition lead discussion") -> VoiceExtractionResult:
        system_prompt = """You are an expert Exhibition Lead Analyst fluent in Hindi, English, and Hinglish (Hindi-English code-mixed language).

Analyze voice note transcripts from sales conversations at Indian trade shows/exhibitions.
The transcript may be in:
- Pure Hindi (Devanagari transliterated to Roman script)
- Pure English
- Hinglish (mix of Hindi and English words in same sentence)

LANGUAGE HANDLING:
- Understand Hindi words: "haan" (yes), "nahi" (no), "theek hai" (okay), "kitna" (how much), "kab" (when), "achha" (good/okay)
- Understand Hinglish: "price kya hai", "delivery kab milega", "sample bhejo", "order confirm karo"
- Common business Hindi: "quotation bhejo", "payment terms kya hai", "dealer margin", "bulk order", "credit period"

Your job is to:
1. Clean and correct the transcript (fix speech-to-text errors in ANY language)
2. Summarize the key discussion points IN ENGLISH (translate if needed)
3. Identify the SEGMENT of the lead based on conversation
4. Determine PRIORITY based on buying signals
5. Extract NEXT STEP (what action should be taken) IN ENGLISH
6. Identify topics discussed

SEGMENT CLASSIFICATION:
- "decision_maker": Can make purchase decisions, mentions budgets, timelines, orders
  Hindi signals: "order karna hai", "budget hai", "abhi chahiye", "confirm karo", "kitna lagega"
- "influencer": Technical evaluator, will recommend to others
  Hindi signals: "boss ko bataunga", "recommend karunga", "dekhte hain", "management se baat karni padegi"
- "researcher": Gathering information, early stage exploration
  Hindi signals: "jaankari chahiye", "details bhejo", "baad mein baat karte hain", "research kar rahe hain"
- "general": Casual interest, no clear buying intent
  Hindi signals: "bas dekh rahe hain", "abhi nahi", "time nahi hai", "filhaal koi plan nahi"

PRIORITY CLASSIFICATION:
- "high": Ready to buy, urgent need, specific requirements, asking for quotes
  Hindi signals: "jaldi chahiye", "urgent hai", "rate batao", "order dena hai", "aaj hi chahiye"
- "medium": Interested but no urgency, wants more information
  Hindi signals: "sochenge", "details bhejo", "baad mein baat karte hain", "next month dekhte hain"
- "low": Just exploring, no immediate need
  Hindi signals: "bas dekh rahe hain", "filhaal nahi", "next year maybe", "abhi koi plan nahi"

INTEREST LEVEL:
- "hot": Very interested, multiple follow-up questions, wants samples/quotes
  Hindi signals: "sample chahiye", "quote bhejo", "meeting fix karo"
- "warm": Interested, engaged in conversation
  Hindi signals: "interesting hai", "batao aur", "achha lagta hai"
- "cold": Minimal interest, just passing by
  Hindi signals: "dekhte hain", "pata nahi", "time nahi hai"

NEXT STEP EXAMPLES (always output in English):
- "Send quotation for 500 units of coated paper"
- "Schedule factory visit next week"
- "Email product catalog"
- "Call back after Diwali"
- "Send samples to their Noida office"
- "WhatsApp payment terms and dealer margin details"
- "Follow up in 2 weeks after they discuss with management"
- "No follow-up needed"

IMPORTANT:
- Always return summary, next_step, and topics in ENGLISH even if transcript is in Hindi/Hinglish
- Keep the cleaned transcript in original language (don't translate)
- Understand context from both Hindi and English keywords
"""

        prompt = f"""
CONTEXT: {context}

VOICE TRANSCRIPT:
{transcript}

Analyze this conversation and return JSON with these EXACT fields:
{{
  "transcript": "cleaned/corrected transcript text",
  "summary": "2-3 sentence summary of discussion",
  "topics": ["topic1", "topic2", "topic3"],
  "next_step": "specific action to take",
  "segment": "decision_maker | influencer | researcher | general",
  "priority": "high | medium | low",
  "interest_level": "hot | warm | cold",
  "confidence": 0.0 - 1.0
}}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                response_format={"type": "json_object"}
            )

            result_dict = json.loads(response.choices[0].message.content)

            # Ensure topics is a list
            if result_dict.get('topics') is None:
                result_dict['topics'] = []

            print(f"✅ Voice Analysis: segment={result_dict.get('segment')}, priority={result_dict.get('priority')}, next_step={result_dict.get('next_step')}")

            return VoiceExtractionResult(**result_dict)

        except Exception as e:
            print(f"❌ Voice normalization error: {e}")
            return VoiceExtractionResult(
                transcript=transcript,
                summary=transcript[:200],
                topics=[],
                next_step=None,
                segment="general",
                priority="medium",
                interest_level="warm",
                confidence=0.0
            )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # WHATSAPP INTENT CLASSIFIER - Supports Hindi/English/Hinglish
    # ----------------------------------------------------------------------
    def normalize_whatsapp_intent(self, message_text: str) -> Dict[str, Any]:
        """
        Classify WhatsApp message intent (YES/NO/CORRECTION/QUERY)
        Supports Hindi, English, and Hinglish messages
        Returns:
            dict with 'intent' & 'normalized_text'
        """

        prompt = f"""
Classify this WhatsApp message (may be in Hindi, English, or Hinglish):
"{message_text}"

Return JSON:
{{
  "intent": "CONFIRM_YES | CONFIRM_NO | CORRECTION_TEXT | DEMO_REQUEST | MEETING_SCHEDULE | PROBLEM_STATEMENT | REQUIREMENT_NOTE | FOLLOWUP_NOTE | TASK_ASSIGN | GENERAL_QUERY",
  "normalized_text": "cleaned message text in English"
}}

Classification rules (understand both Hindi and English):

CONFIRM_YES patterns:
- English: yes, ok, okay, correct, right, confirmed, done, fine, good
- Hindi: haan, ha, ji, theek hai, sahi hai, bilkul, zaroor, ho gaya, done hai

CONFIRM_NO patterns:
- English: no, wrong, incorrect, not right, cancel
- Hindi: nahi, na, galat, galat hai, nahi chahiye, cancel karo, mat karo

CORRECTION_TEXT patterns:
- English: "my name is...", "actually it's...", "correct this...", "change to...", "correction", "wrong name", "wrong company", "need correction"
- Hindi: "mera naam...", "sahi naam...", "ye galat hai...", "isko change karo...", "correction", "galat naam", "galat company"
- Structured corrections: "Name-XYZ", "Designation-HR", "Company-ABC", "Phone-9876...", "Email-test@..."
- IMPORTANT: If message contains name/company/phone/designation/email patterns, always classify as CORRECTION_TEXT

DEMO_REQUEST patterns:
- English: "schedule demo", "demo", "product demo", "book demo", "show demo", "demo tomorrow"
- Hindi: "demo dikhaao", "demo kab milega", "demo chahiye", "demo book karo"

MEETING_SCHEDULE patterns:
- English: "schedule meeting", "meeting", "call with", "appointment", "meet", "schedule call"
- Hindi: "meeting set karo", "call kab karoge", "milte hai", "appointment"

PROBLEM_STATEMENT patterns:
- English: "problem", "issue", "facing issue", "trouble", "not working", "error", "fault"
- Hindi: "problem hai", "issue", "kharaab", "kaam nahi kar raha"

REQUIREMENT_NOTE patterns:
- English: "need", "want", "requirement", "quotation", "costing", "price", "how much"
- Hindi: "chahiye", "requirement", "quotation", "price kya hai", "kitna"

FOLLOWUP_NOTE patterns:
- English: "follow up", "remind", "tomorrow ping", "check again", "please follow up"
- Hindi: "follow up karo", "yaad dilaana", "kal ping karo"

TASK_ASSIGN patterns:
- English: "assign task", "give task to", "allocate", "assign to", "send this to"
- Hindi: "task de do", "isko bhej do", "assign karo"

GENERAL_QUERY patterns:
- Any other question or statement
- "kya hai", "kab milega", "details do"

Return STRICT JSON only.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You classify WhatsApp reply intents. You understand Hindi, English, and Hinglish. Respond in strict JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=200,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"Intent classification error: {e}")
            return {
                "intent": "GENERAL_QUERY",
                "normalized_text": message_text
            }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================
openai_normalizer = OpenAINormalizer()
