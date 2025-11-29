"""
QR Code Detection and Decoding - DISABLED
-----------------------------------------------------------
QR code scanning has been disabled to reduce memory usage and dependencies.
This module now returns None for all QR scan requests.

The pyzbar library is not imported and will not be loaded into memory.
"""

from typing import Optional, Dict, Any


class QRDecoder:
    """QR Code Decoder - Disabled for memory optimization"""

    @staticmethod
    def decode_from_image(image_path: str) -> Optional[Dict[str, Any]]:
        """
        QR Code scanning is DISABLED.
        Always returns None.

        Args:
            image_path: Path to image file (ignored)

        Returns:
            None (QR scanning disabled)
        """
        # QR scanning disabled - always return None
        return None


# Singleton instance
qr_decoder = QRDecoder()
