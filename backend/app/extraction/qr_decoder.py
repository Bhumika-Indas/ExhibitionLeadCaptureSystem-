"""
QR Code Detection and Decoding (Improved Version - Option A)
-----------------------------------------------------------
Features:
- Multi-QR detection (returns all, with a primary one)
- Auto-rotate + grayscale re-scan for better detection
- vCard parsing (name, org, title, phones, emails, URLs, addresses)
- Phone cleanup (10-digit Indian mobile normalization as hints)
- URL classification (http/https/www/wa.me etc.)
- Backward compatible: still returns top-level 'type', 'data', 'parsed'
"""

import cv2
import re
from typing import Optional, Dict, Any, List

# Make pyzbar optional - not all systems have zbar library installed
try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    print("⚠️ Warning: pyzbar not available. QR code scanning will be disabled.")


class QRDecoder:
    """Decode QR codes from visiting cards"""

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    @staticmethod
    def decode_from_image(image_path: str) -> Optional[Dict[str, Any]]:
        """
        Decode QR code(s) from an image file.

        Returns:
            Dict with:
                - type: 'vcard' | 'url' | 'text'
                - data: primary QR payload (string)
                - parsed: dict with structured info (if vcard/url)
                - all_codes: list of all detected QR codes with same structure
        Or:
            None, if no QR codes found or pyzbar not available.
        """
        # Return None if pyzbar is not installed
        if not PYZBAR_AVAILABLE:
            return None

        img = cv2.imread(image_path)
        if img is None:
            return None

        # Try multiple decode strategies (original, rotated, grayscale)
        decoded_payloads = QRDecoder._decode_qr_variants(img)

        if not decoded_payloads:
            return None

        all_codes: List[Dict[str, Any]] = []

        for payload in decoded_payloads:
            qr_type, parsed = QRDecoder._classify_and_parse_payload(payload)
            all_codes.append(
                {
                    "type": qr_type,
                    "data": payload,
                    "parsed": parsed or {},
                }
            )

        # Choose primary code: prioritize vCard, then URL, then text
        primary = QRDecoder._select_primary_qr(all_codes)

        result = {
            "type": primary["type"],
            "data": primary["data"],
            "parsed": primary["parsed"],
            "all_codes": all_codes,
        }

        return result

    # ------------------------------------------------------------------ #
    # Multi-strategy QR decoding
    # ------------------------------------------------------------------ #
    @staticmethod
    def _decode_qr_variants(img) -> List[str]:
        """
        Try decoding QR in multiple modes:
        - original
        - grayscale
        - rotated 90 / 180 / 270
        """
        payloads: List[str] = []

        # Helper to run pyzbar and collect results
        def _decode(image) -> None:
            codes = pyzbar.decode(image)
            for code in codes:
                try:
                    text = code.data.decode("utf-8", errors="ignore").strip()
                except Exception:
                    continue
                if text and text not in payloads:
                    payloads.append(text)

        # 1. Original
        _decode(img)

        # 2. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _decode(gray)

        # 3. Rotations
        for angle in (cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE):
            rotated = cv2.rotate(img, angle)
            _decode(rotated)
            rotated_gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
            _decode(rotated_gray)

        return payloads

    # ------------------------------------------------------------------ #
    # Classification & Parsing
    # ------------------------------------------------------------------ #
    @staticmethod
    def _classify_and_parse_payload(payload: str) -> (str, Optional[Dict[str, Any]]):
        """
        Determine if QR content is vCard, URL, or plain text, and parse if needed.
        """
        text = payload.strip()

        # vCard detection
        if "BEGIN:VCARD" in text.upper():
            return "vcard", QRDecoder._parse_vcard(text)

        # URL detection
        if QRDecoder._looks_like_url(text):
            return "url", {"url": text}

        # Catch simple WhatsApp deep links even without protocol
        if "wa.me/" in text or "api.whatsapp.com/" in text:
            if not text.lower().startswith("http"):
                text = "https://" + text
            return "url", {"url": text}

        # Fallback: plain text
        return "text", {}

    @staticmethod
    def _looks_like_url(text: str) -> bool:
        text = text.strip().lower()
        return (
            text.startswith("http://")
            or text.startswith("https://")
            or text.startswith("www.")
        )

    # ------------------------------------------------------------------ #
    # vCard Parsing
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_vcard(vcard_text: str) -> Dict[str, Any]:
        """
        Parse vCard format into structured fields.
        Minimal but practical for visiting cards.
        """
        result: Dict[str, Any] = {
            "name": None,
            "organization": None,
            "title": None,
            "phones": [],
            "emails": [],
            "urls": [],
            "addresses": [],
        }

        # Normalize line endings
        lines = vcard_text.replace("\r\n", "\n").split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Full name (FN or N)
            if line.upper().startswith("FN:"):
                result["name"] = QRDecoder._extract_vcard_value(line)
            elif line.upper().startswith("N:") and not result["name"]:
                n_val = QRDecoder._extract_vcard_value(line)
                if n_val:
                    # N:Last;First;... → use "First Last"
                    parts = n_val.split(";")
                    if len(parts) >= 2:
                        first = parts[1].strip()
                        last = parts[0].strip()
                        full = " ".join(p for p in [first, last] if p)
                        result["name"] = full or n_val
                    else:
                        result["name"] = n_val

            # Organization
            elif line.upper().startswith("ORG:"):
                result["organization"] = QRDecoder._extract_vcard_value(line)

            # Title / Designation
            elif line.upper().startswith("TITLE:"):
                result["title"] = QRDecoder._extract_vcard_value(line)

            # Phones
            elif line.upper().startswith("TEL"):
                phone_raw = QRDecoder._extract_vcard_value(line)
                if phone_raw:
                    cleaned = QRDecoder._clean_phone(phone_raw)
                    if cleaned:
                        result["phones"].append(cleaned)

            # Emails
            elif line.upper().startswith("EMAIL"):
                email_raw = QRDecoder._extract_vcard_value(line)
                if email_raw:
                    email = email_raw.strip().lower()
                    if QRDecoder._valid_email(email):
                        result["emails"].append(email)

            # URLs
            elif line.upper().startswith("URL"):
                url_raw = QRDecoder._extract_vcard_value(line)
                if url_raw and QRDecoder._looks_like_url(url_raw):
                    result["urls"].append(url_raw.strip())

            # Addresses
            elif line.upper().startswith("ADR"):
                adr_raw = QRDecoder._extract_vcard_value(line)
                if adr_raw:
                    # vCard ADR: PO;Extended;Street;City;Region;Postal;Country
                    parts = adr_raw.split(";")
                    address_text = ", ".join([p for p in parts if p.strip()])
                    result["addresses"].append(address_text)

        # De-duplicate
        result["phones"] = list(dict.fromkeys(result["phones"]))
        result["emails"] = list(dict.fromkeys(result["emails"]))
        result["urls"] = list(dict.fromkeys(result["urls"]))
        result["addresses"] = list(dict.fromkeys(result["addresses"]))

        return result

    @staticmethod
    def _extract_vcard_value(line: str) -> Optional[str]:
        """
        Extract the value after ':' from a vCard line:
        e.g., TEL;TYPE=CELL:+91-9876543210 → +91-9876543210
        """
        if ":" not in line:
            return None
        return line.split(":", 1)[-1].strip()

    # ------------------------------------------------------------------ #
    # Helpers: Phone & Email Cleaner
    # ------------------------------------------------------------------ #
    @staticmethod
    def _clean_phone(raw: str) -> Optional[str]:
        """
        Clean vCard phone into a normalized form.
        For Indian mobiles: we keep last 10 digits (hint for higher layers).
        """
        # Keep only digits
        digits = re.sub(r"\D", "", raw or "")

        if len(digits) < 7:
            return None

        # If looks like Indian mobile, return last 10
        if len(digits) >= 10:
            return digits[-10:]

        # Otherwise, return full digits as-is (landlines, etc.)
        return digits

    @staticmethod
    def _valid_email(email: str) -> bool:
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


# Singleton instance
qr_decoder = QRDecoder()
