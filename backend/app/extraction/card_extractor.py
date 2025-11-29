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
        DISABLED: Auto-rotation was causing excessive memory usage
        Users should take photos in correct orientation
        """
        print("   ⏭️ Auto-rotation disabled (memory optimization)")
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
    # INTERNAL OCR - Optimized single pass to save memory
    # ======================================================================
    def _perform_ocr(self, enhanced_img, raw_path) -> str:
        print("\n🧠 OCR — Single optimized pass")
        reader = self._get_reader()  # Lazy load
        result = reader.readtext(enhanced_img)
        text = "\n".join([r[1] for r in result]).strip()
        print(f"✓ OCR extracted {len(text)} chars")

        # Only fallback to raw if enhanced gave very poor results
        if len(text) < 10:
            print("\n⚠️ Fallback to raw image...")
            raw_img = cv2.imread(raw_path)
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
