"""
Optimized Image Preprocessing for Visiting Cards (EasyOCR Version)
------------------------------------------------------------------
This pipeline is designed SPECIFICALLY for EasyOCR.

DO NOT:
- threshold
- binarize
- dilate/erode
- edge-detect
- invert

DO:
- rotation correction
- deskew
- denoise
- CLAHE contrast boost
- preserve grayscale intensity
"""

import cv2
import numpy as np
from typing import Tuple, Optional


class ImagePreprocessor:
    """Preprocess visiting card images for optimal EasyOCR performance."""

    # ======================================================================
    # PUBLIC PREPROCESS FUNCTION
    # ======================================================================
    @staticmethod
    def preprocess(image_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess the card image and return:
            1. Original BGR image
            2. Enhanced grayscale image (OCR-ready)

        Returns:
            (original_bgr, enhanced_gray)
        """
        img = cv2.imread(image_path)

        if img is None:
            raise ValueError(f"❌ Could not read image: {image_path}")

        original = img.copy()

        # 1. Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Auto-rotate (if needed)
        gray = ImagePreprocessor._auto_rotate(gray)

        # 3. Deskew (based on contours)
        gray = ImagePreprocessor._deskew(gray)

        # 4. Denoise (light)
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # 5. Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # ⚠️ DO NOT APPLY THRESHOLDING — BAD FOR EASYOCR
        # ⚠️ DO NOT APPLY ADAPTIVE THRESHOLD — DAMAGES FONTS
        # ⚠️ DO NOT INVERT OR EDGE-DETECT

        return original, gray

    # ======================================================================
    # AUTO ROTATE USING HOUGH LINES
    # ======================================================================
    @staticmethod
    def _auto_rotate(image: np.ndarray) -> np.ndarray:
        """
        Detect dominant angles and correct rotation.
        Keeps EasyOCR accurate for rotated/slanted business cards.
        """
        try:
            edges = cv2.Canny(image, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100,
                                    minLineLength=150, maxLineGap=20)

            if lines is None:
                return image

            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                angles.append(angle)

            if len(angles) == 0:
                return image

            median_angle = np.median(angles)

            # Normalize large angles
            if median_angle > 45:
                median_angle -= 90
            if median_angle < -45:
                median_angle += 90

            # Only rotate if significant misalignment
            if abs(median_angle) < 5:
                return image

            (h, w) = image.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(
                image, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )

            print(f"↻ Auto-rotated by {median_angle:.2f} degrees")
            return rotated

        except Exception:
            return image

    # ======================================================================
    # DESKEW BASED ON MIN-AREA BOUNDING BOX
    # ======================================================================
    @staticmethod
    def _deskew(image: np.ndarray) -> np.ndarray:
        """
        Deskew image using min area rectangle approach.
        Corrects slanted business cards.
        """
        coords = np.column_stack(np.where(image > 0))

        if len(coords) < 30:
            return image

        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        if abs(angle) < 0.5:
            return image

        (h, w) = image.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        print(f"↻ Deskewed by {angle:.2f} degrees")
        return rotated

    # ======================================================================
    # OPTIONAL: CARD CROPPING
    # ======================================================================
    @staticmethod
    def crop_card(image: np.ndarray) -> np.ndarray:
        """
        Detect and crop the business card from background.
        Safe because no thresholding is used here.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255,
                                  cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return image

        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)

        margin = 15
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(image.shape[1] - x, w + margin * 2)
        h = min(image.shape[0] - y, h + margin * 2)

        return image[y:y + h, x:x + w]


# Singleton instance
image_preprocessor = ImagePreprocessor()
