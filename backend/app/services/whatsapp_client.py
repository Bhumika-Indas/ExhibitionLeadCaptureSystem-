"""
WhatsApp Client for sending messages
Integrates with third-party WhatsApp API (http://103.150.136.76:8090)
"""

import httpx
from typing import Optional, Dict, Any
from app.config import settings


class WhatsAppClient:
    """Client for third-party WhatsApp API integration"""

    def __init__(self):
        # Third-party API configuration
        self.api_url = settings.WHATSAPP_API_URL  # http://103.150.136.76:8090
        self.api_key = settings.WHATSAPP_API_KEY  # X-API-Key header
        self.account_token = settings.WHATSAPP_ACCOUNT_TOKEN  # Bearer token
        self.phone_number = settings.WHATSAPP_PHONE_NUMBER
        self.client = httpx.AsyncClient(timeout=30.0)

    async def send_template(
        self,
        to: str,
        template_name: str,
        template_data: dict
    ) -> Dict[str, Any]:
        """
        Send WhatsApp template message using third-party API

        Args:
            to: Recipient phone number (9876543210)
            template_name: Template identifier
            template_data: Template variable values as dict (e.g., {"name": "John"})

        Returns:
            Response dict with message_id and status
        """
        # Validate phone number before sending
        if not self._is_valid_phone(to):
            print(f"❌ BLOCKED: Invalid phone number: {to}")
            return {
                "success": False,
                "error": f"Invalid phone number: {to}",
                "status": "blocked"
            }

        payload = {
            "to": self._normalize_phone_for_api(to),
            "template": template_name,
            "templateData": template_data
        }

        return await self._send_request("/api/send-message", payload)

    async def send_text(
        self,
        to: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Send plain text message using third-party API

        Args:
            to: Recipient phone number (9876543210)
            text: Message text

        Returns:
            Response dict with message_id and status
        """
        # Validate phone number before sending
        if not self._is_valid_phone(to):
            print(f"❌ BLOCKED: Invalid phone number: {to}")
            return {
                "success": False,
                "error": f"Invalid phone number: {to}",
                "status": "blocked"
            }

        payload = {
            "to": self._normalize_phone_for_api(to),
            "message": text
        }

        return await self._send_request("/api/send-message", payload)

    async def send_media(
        self,
        to: str,
        file_path: str,
        caption: Optional[str] = None,
        media_type: str = "image"
    ) -> Dict[str, Any]:
        """
        Send media message using third-party API (multipart/form-data)

        Args:
            to: Recipient phone number (9876543210)
            file_path: Path to local file
            caption: Optional caption
            media_type: image | document | video | audio

        Returns:
            Response dict with message_id and status
        """
        # Use multipart form data for media
        import aiofiles

        async with aiofiles.open(file_path, 'rb') as f:
            file_content = await f.read()

        files = {"file": (file_path.split('/')[-1], file_content)}
        data = {
            "to": self._normalize_phone_for_api(to)
        }

        if caption:
            data["caption"] = caption

        return await self._send_media_request("/api/send-media", data, files)

    async def _send_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON API request to third-party WhatsApp gateway"""
        headers = {
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {self.account_token}",
            "Content-Type": "application/json"
        }

        full_url = f"{self.api_url}{endpoint}"
        print(f"📤 WhatsApp API Request:")
        print(f"   URL: {full_url}")
        print(f"   Payload: {payload}")
        print(f"   Headers: X-API-Key={self.api_key[:20]}..., Bearer={self.account_token[:20]}...")

        try:
            response = await self.client.post(
                full_url,
                json=payload,
                headers=headers
            )

            response.raise_for_status()
            result = response.json()
            print(f"✅ WhatsApp API Success: {result}")

            return {
                "success": result.get("success", True),
                "message_id": result.get("messageId"),
                "status": result.get("status", "sent")
            }

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else str(e)
            print(f"❌ WhatsApp API HTTP Error {e.response.status_code}:")
            print(f"   Response: {error_detail}")
            print(f"   Request URL: {full_url}")
            print(f"   Request Payload: {payload}")
            return {
                "success": False,
                "error": error_detail,
                "status": "failed"
            }

        except Exception as e:
            print(f"❌ WhatsApp send error (Exception): {type(e).__name__}")
            print(f"   Message: {str(e)}")
            print(f"   Request URL: {full_url}")
            print(f"   Request Payload: {payload}")
            return {
                "success": False,
                "error": str(e),
                "status": "failed"
            }

    async def _send_media_request(self, endpoint: str, data: Dict[str, str], files: Dict) -> Dict[str, Any]:
        """Send multipart/form-data request for media messages"""
        headers = {
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {self.account_token}"
            # Note: Don't set Content-Type - httpx will set it automatically with boundary
        }

        try:
            response = await self.client.post(
                f"{self.api_url}{endpoint}",
                data=data,
                files=files,
                headers=headers
            )

            response.raise_for_status()
            result = response.json()

            return {
                "success": result.get("success", True),
                "message_id": result.get("messageId"),
                "status": result.get("status", "sent"),
                "media_type": result.get("mediaType")
            }

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else str(e)
            print(f"❌ WhatsApp media error: {error_detail}")
            return {
                "success": False,
                "error": error_detail,
                "status": "failed"
            }

        except Exception as e:
            print(f"❌ WhatsApp media send error: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "failed"
            }

    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """
        Validate if phone number is valid for sending messages.

        Blocks:
        - Numbers with @lid suffix (WhatsApp Limited Identifiers - fake/masked numbers)
        - Numbers with @newsletter suffix (WhatsApp Channels - can't send direct messages)
        - Numbers longer than 15 digits (invalid per E.164 standard)
        - Empty or None values

        Args:
            phone: Phone number to validate

        Returns:
            True if valid, False if should be blocked
        """
        if not phone:
            return False

        # Block LID (Limited Identifier) - these are masked/garbage numbers
        if "@lid" in phone.lower():
            print(f"   🚫 BLOCKED: LID detected - {phone}")
            return False

        # Block newsletter/channel messages - can't send direct messages to channels
        if "@newsletter" in phone.lower():
            print(f"   🚫 BLOCKED: Newsletter/Channel detected - {phone}")
            return False

        # Block group messages - can't process group messages
        if "@g.us" in phone.lower():
            print(f"   🚫 BLOCKED: WhatsApp Group detected - {phone}")
            return False

        # Remove @ suffix to get raw number
        clean_phone = phone.split("@")[0] if "@" in phone else phone

        # Extract digits only
        digits = ''.join(c for c in clean_phone if c.isdigit())

        # Block if too long (E.164 max is 15 digits)
        if len(digits) > 15:
            print(f"   🚫 BLOCKED: Number too long ({len(digits)} digits) - {phone}")
            return False

        # Block if too short (minimum 7 digits for landlines)
        if len(digits) < 7:
            print(f"   🚫 BLOCKED: Number too short ({len(digits)} digits) - {phone}")
            return False

        return True

    @staticmethod
    def _normalize_phone_for_api(phone: str) -> str:
        """
        Normalize phone number for third-party API

        The API accepts BOTH formats (tested):
        - WITH + sign: +919876543210
        - WITHOUT + sign: 919876543210

        We'll use the format WITH country code but NO + sign.

        Handles:
        - Indian 10-digit: 9876543210 → 919876543210
        - International: 237309945499749 → 237309945499749
        - With +: +919876543210 → 919876543210
        - JID format: 919876543210@lid → 919876543210
        """
        # Remove @lid/@s.whatsapp.net/@c.us suffixes (JID formats)
        if "@" in phone:
            phone = phone.split("@")[0]

        # Remove all non-digit characters (including +)
        clean = ''.join(c for c in phone if c.isdigit())

        # Validate length (max 15 digits per E.164 standard)
        if len(clean) > 15:
            print(f"⚠️ Phone number too long ({len(clean)} digits): {clean}")

        if len(clean) < 10:
            print(f"⚠️ Phone number too short ({len(clean)} digits): {clean}")

        # If exactly 10 digits, assume Indian number and add country code
        if len(clean) == 10:
            result = f"91{clean}"
            print(f"📞 Normalized phone: {phone} → {result} (added country code 91)")
            return result

        # Otherwise return as-is (already has country code)
        print(f"📞 Normalized phone: {phone} → {clean} (kept as international)")
        return clean

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Singleton instance
whatsapp_client = WhatsAppClient()
