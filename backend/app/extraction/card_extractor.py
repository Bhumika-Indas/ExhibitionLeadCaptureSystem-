"""
Final Corrected EasyOCR-based Card Extractor
Optimized for business cards with:
- Lazy loading (memory optimization)
- Single-pass OCR (reduced memory usage)
- No auto-rotation (prevents memory spike)
- Improved phone regex
- OpenAI fallback + regex merging
"""

import easyocr
import cv2
import numpy as np
import re
import gc
from typing import Optional, List

from app.extraction.schemas import CardExtractionResult
from app.extraction.qr_decoder import qr_decoder
from app.extraction.openai_normalizer import openai_normalizer


class CardExtractor:

    def __init__(self):
        print("🔧 CardExtractor initialized (EasyOCR will load on first use)")
        self.reader = None  # Lazy load to save memory

    def _get_reader(self):
        """Lazy load EasyOCR only when needed"""
        if self.reader is None:
            print("🔧 Loading EasyOCR (English)...")
            self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            print("✅ EasyOCR loaded successfully")
        return self.reader

    # ======================================================================
    # IMAGE ENHANCEMENT (Light enhancement only — NO THRESHOLDING)
    # ======================================================================
    def _enhance_card_image(self, img_path: str) -> np.ndarray:
        img = cv2.imread(img_path)

        if img is None:
            raise ValueError(f"Error: cannot read image at path {img_path}")

        print(f"📸 Original image: {img.shape}")

        # 0. Auto-rotate image if needed (detect and fix rotation)
        img = self._auto_rotate_image(img)
        print("✓ Auto-rotation checked")

        # 1. Denoise lightly
        img = cv2.fastNlMeansDenoisingColored(img, None, 5, 5, 7, 21)
        print("✓ Denoised")

        # 2. CLAHE contrast boost
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        l2 = clahe.apply(l)
        lab = cv2.merge((l2, a, b))
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        print("✓ CLAHE applied")

        # 3. Mild sharpen
        kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]])
        img = cv2.filter2D(img, -1, kernel)
        print("✓ Sharpened")

        print(f"📸 Enhanced image: {img.shape}")
        return img

    def _auto_rotate_image(self, img: np.ndarray) -> np.ndarray:
        """
        Smart auto-rotation: Try all 4 orientations and pick the one with most text.
        Memory-efficient: Uses downscaled image for testing, applies rotation to full image.
        """
        print("   🔄 Smart auto-rotation: testing 4 orientations...")

        # Downscale for testing (much faster and less memory)
        # Reduced from 800 to 600 to save even more memory on server
        max_dimension = 600
        h, w = img.shape[:2]
        scale = min(max_dimension / max(h, w), 1.0)

        if scale < 1.0:
            test_img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            print(f"   📉 Testing with downscaled image: {test_img.shape[:2]} (saves memory)")
        else:
            test_img = img

        reader = self._get_reader()

        # Test all 4 rotations on small image
        rotations = [
            (0, test_img),
            (90, cv2.rotate(test_img, cv2.ROTATE_90_CLOCKWISE)),
            (180, cv2.rotate(test_img, cv2.ROTATE_180)),
            (270, cv2.rotate(test_img, cv2.ROTATE_90_COUNTERCLOCKWISE))
        ]

        best_angle = 0
        best_text_length = 0

        for angle, rotated_test_img in rotations:
            # Quick OCR test on downscaled image
            try:
                result = reader.readtext(rotated_test_img, detail=0)
                text = " ".join(result)
                text_length = len(text.strip())

                if text_length > best_text_length:
                    best_text_length = text_length
                    best_angle = angle
            except Exception as e:
                print(f"   ⚠️ OCR failed for {angle}°: {e}")
                continue

        # Apply best rotation to FULL-SIZE image
        if best_angle == 0:
            print(f"   ✓ Original orientation is best ({best_text_length} chars)")
            # Clean up test image
            del test_img
            gc.collect()
            return img
        elif best_angle == 90:
            rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif best_angle == 180:
            rotated = cv2.rotate(img, cv2.ROTATE_180)
        else:  # 270
            rotated = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Clean up test image
        del test_img
        gc.collect()

        print(f"   ✓ Best orientation: {best_angle}° (extracted {best_text_length} chars from test)")
        return rotated

    # ======================================================================
    # STRONG PHONE EXTRACTION (Fixes OCR mistakes like O→0, I→1)
    # ======================================================================
    def _extract_phones_from_text(self, text: str) -> List[str]:
        if not text:
            return []

        print("\n🔍 Running phone regex on OCR text...")

        # Fix common OCR mistakes
        t = (
            text.replace("O", "0")
                .replace("o", "0")
                .replace("I", "1")
                .replace("|", "1")
                .replace("l", "1")
        )

        # Clean all junk except digits, spaces, +, -
        t = re.sub(r"[^0-9+\s\-]", " ", t)

        # Match Indian numbers robustly
        pattern = r"(\+91[\s\-]?\d{10}|[6-9]\d{9}|[6-9]\d{4}[\s\-]?\d{5})"
        matches = re.findall(pattern, t)

        phones = []
        for m in matches:
            num = re.sub(r"\D", "", m)
            if len(num) >= 10:
                num = num[-10:]
                if num[0] in "6789":
                    phones.append(num)

        phones = list(set(phones))

        print(f"📞 Regex phones extracted: {phones}")
        return phones

    # ======================================================================
    # INTERNAL OCR - Optimized single pass to save memory
    # ======================================================================
    def _perform_ocr(self, enhanced_img, raw_path) -> str:
        print("\n🧠 OCR — Single optimized pass")
        reader = self._get_reader()  # Lazy load

        # CRITICAL: Downscale to max 1920px to prevent OOM on server
        max_dimension = 1920  # Reduce from 4000x3000 to manageable size
        h, w = enhanced_img.shape[:2]
        scale = min(max_dimension / max(h, w), 1.0)

        if scale < 1.0:
            ocr_img = cv2.resize(enhanced_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            print(f"   📉 Downscaled for OCR: {enhanced_img.shape[:2]} → {ocr_img.shape[:2]} (prevents OOM)")
        else:
            ocr_img = enhanced_img

        result = reader.readtext(ocr_img)
        text = "\n".join([r[1] for r in result]).strip()
        print(f"✓ OCR extracted {len(text)} chars")

        # Only fallback to raw if enhanced gave very poor results
        if len(text) < 10:
            print("\n⚠️ Fallback to raw image...")
            raw_img = cv2.imread(raw_path)

            # Also downscale fallback image
            h2, w2 = raw_img.shape[:2]
            scale2 = min(max_dimension / max(h2, w2), 1.0)
            if scale2 < 1.0:
                raw_img = cv2.resize(raw_img, None, fx=scale2, fy=scale2, interpolation=cv2.INTER_AREA)
                print(f"   📉 Downscaled fallback: {(h2, w2)} → {raw_img.shape[:2]}")

            result2 = reader.readtext(raw_img)
            text2 = "\n".join([r[1] for r in result2]).strip()
            if len(text2) > len(text):
                text = text2
                print(f"✓ Raw OCR gave {len(text)} chars")

        print(f"📄 Final OCR text: {len(text)} chars")
        return text

    # ======================================================================
    # PUBLIC EXTRACT METHOD
    # ======================================================================
    def extract(self, front_image_path: str, back_image_path: Optional[str] = None) -> CardExtractionResult:

        print(f"\n===================================================")
        print(f"🔍 Extracting card → front={front_image_path}, back={back_image_path}")
        print(f"===================================================\n")

        # ----------------- FRONT OCR ----------------------
        enhanced_front = self._enhance_card_image(front_image_path)
        front_text = self._perform_ocr(enhanced_front, front_image_path)

        print("\n📝 FRONT OCR TEXT:")
        print(front_text[:400] + "\n...")

        front_phones = self._extract_phones_from_text(front_text)

        # ----------------- QR CODE -------------------------
        # DISABLED: QR code detection disabled as per requirements
        # If QR is detected, we skip the card entirely
        print("\n🚫 QR code detection DISABLED - skipping QR scan")
        qr_data = None

        # ----------------- BACK OCR ------------------------
        back_text = None
        back_phones = []

        if back_image_path:
            enhanced_back = self._enhance_card_image(back_image_path)
            back_text = self._perform_ocr(enhanced_back, back_image_path)

            print("\n📝 BACK OCR TEXT:")
            print(back_text[:400] + "\n...")

            back_phones = self._extract_phones_from_text(back_text)

            if not qr_data:
                qr_data = qr_decoder.decode_from_image(back_image_path)

        # Combine phones
        all_phones = list(set(front_phones + back_phones))
        print(f"\n📞 ALL PHONES FOUND → {all_phones}")

        # ----------------- OPENAI NORMALIZATION ------------------------
        print("\n🤖 Normalizing with OpenAI...")
        result = openai_normalizer.normalize_card_data(
            front_ocr_text=front_text,
            back_ocr_text=back_text,
            qr_data=qr_data,
            regex_phones=all_phones,
        )

        # Clean up memory after processing
        del enhanced_front
        if back_image_path:
            del enhanced_back
        gc.collect()
        print("🧹 Memory cleaned up")

        print(f"\n🎉 FINAL EXTRACTION COMPLETE — Confidence: {result.confidence:.2f}")
        print("=================================================================\n")
        return result


# Singleton
card_extractor = CardExtractor()
