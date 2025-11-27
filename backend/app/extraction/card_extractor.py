"""
Final Corrected EasyOCR-based Card Extractor
Optimized for business cards with:
- zero thresholding
- enhanced OCR fallback
- improved phone regex
- OpenAI fallback + regex merging
"""

import easyocr
import cv2
import numpy as np
import re
from typing import Optional, List

from app.extraction.schemas import CardExtractionResult
from app.extraction.qr_decoder import qr_decoder
from app.extraction.openai_normalizer import openai_normalizer


class CardExtractor:

    def __init__(self):
        print("🔧 Initializing EasyOCR (English)...")
        self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        print("✅ EasyOCR initialized successfully")

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
        Auto-detect and fix image rotation using OCR confidence
        Tries 0°, 90°, 180°, 270° and picks the best orientation
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Try all 4 orientations
        best_angle = 0
        best_text_length = 0

        for angle in [0, 90, 180, 270]:
            if angle == 0:
                rotated = img
            elif angle == 90:
                rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            elif angle == 180:
                rotated = cv2.rotate(img, cv2.ROTATE_180)
            elif angle == 270:
                rotated = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

            # Quick OCR test to see which orientation has most text
            try:
                result = self.reader.readtext(rotated, detail=0, paragraph=False)
                text_length = sum(len(t) for t in result)

                if text_length > best_text_length:
                    best_text_length = text_length
                    best_angle = angle
            except:
                continue

        # Apply best rotation
        if best_angle == 0:
            print(f"   Image is correctly oriented (0°)")
            return img
        elif best_angle == 90:
            print(f"   🔄 Rotating image 90° clockwise")
            return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif best_angle == 180:
            print(f"   🔄 Rotating image 180°")
            return cv2.rotate(img, cv2.ROTATE_180)
        elif best_angle == 270:
            print(f"   🔄 Rotating image 270° clockwise (90° counter-clockwise)")
            return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

        return img

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
    # INTERNAL OCR with fallback (Enhanced → Raw → Second-pass Enhanced)
    # ======================================================================
    def _perform_ocr(self, enhanced_img, raw_path) -> str:
        print("\n🧠 OCR PASS 1 — Enhanced Image")
        result1 = self.reader.readtext(enhanced_img)
        text1 = "\n".join([r[1] for r in result1]).strip()
        print(f"✓ Enhanced OCR chars: {len(text1)}")

        if len(text1) >= 25:
            return text1

        # ------------------------------------------------------------------
        print("\n⚠️ Enhanced too weak, trying RAW image...")
        raw_img = cv2.imread(raw_path)
        result2 = self.reader.readtext(raw_img)
        text2 = "\n".join([r[1] for r in result2]).strip()
        print(f"✓ Raw OCR chars: {len(text2)}")

        if len(text2) > len(text1):
            best = text2
        else:
            best = text1

        # ------------------------------------------------------------------
        if len(best) < 25:
            print("\n⚠️ OCR still weak — running second-pass enhancement...")
            twice = self._enhance_card_image(raw_path)
            result3 = self.reader.readtext(twice)
            text3 = "\n".join([r[1] for r in result3]).strip()
            print(f"✓ Pass-3 OCR chars: {len(text3)}")

            best = max([text1, text2, text3], key=len)

        print(f"📄 Final OCR text size: {len(best)} chars")
        return best

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
        qr_data = qr_decoder.decode_from_image(front_image_path)

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

        print(f"\n🎉 FINAL EXTRACTION COMPLETE — Confidence: {result.confidence:.2f}")
        print("=================================================================\n")
        return result


# Singleton
card_extractor = CardExtractor()
