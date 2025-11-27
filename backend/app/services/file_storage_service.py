"""
File Storage Service
Handles saving card images, audio files, and documents to local filesystem
"""

import os
import hashlib
from datetime import datetime
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from app.config import settings


class FileStorageService:
    """Service for storing uploaded files"""

    def __init__(self, base_path: str = None):
        self.base_path = base_path or settings.UPLOAD_DIR

    async def save_card_image(
        self,
        file: UploadFile,
        lead_id: int,
        image_type: str  # 'front' or 'back'
    ) -> Tuple[str, int, str]:
        """
        Save visiting card image

        Returns:
            Tuple[file_url, file_size_bytes, mime_type]
        """
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        ext = self._get_extension(file.filename)
        if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {settings.ALLOWED_IMAGE_EXTENSIONS}"
            )

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate size
        max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max: {settings.MAX_FILE_SIZE_MB}MB"
            )

        # Create folder structure: /uploads/cards/YYYY/MM/
        now = datetime.now()
        folder = os.path.join(
            self.base_path,
            "cards",
            str(now.year),
            f"{now.month:02d}"
        )
        os.makedirs(folder, exist_ok=True)

        # Generate filename with timestamp to handle multiple uploads
        timestamp = int(now.timestamp())
        filename = f"lead_{lead_id}_{image_type}_{timestamp}{ext}"
        file_path = os.path.join(folder, filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(content)

        # Return relative path for DB storage
        relative_path = f"/uploads/cards/{now.year}/{now.month:02d}/{filename}"
        mime_type = file.content_type or f"image/{ext[1:]}"

        return relative_path, file_size, mime_type

    async def save_audio_note(
        self,
        file: UploadFile,
        lead_id: int
    ) -> Tuple[str, int, str]:
        """
        Save voice note audio file

        Returns:
            Tuple[file_url, file_size_bytes, mime_type]
        """
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        ext = self._get_extension(file.filename)
        if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid audio type. Allowed: {settings.ALLOWED_AUDIO_EXTENSIONS}"
            )

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate size
        max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max: {settings.MAX_FILE_SIZE_MB}MB"
            )

        # Create folder structure: /uploads/audio/YYYY/MM/
        now = datetime.now()
        folder = os.path.join(
            self.base_path,
            "audio",
            str(now.year),
            f"{now.month:02d}"
        )
        os.makedirs(folder, exist_ok=True)

        # Generate filename
        timestamp = int(now.timestamp())
        filename = f"lead_{lead_id}_audio_{timestamp}{ext}"
        file_path = os.path.join(folder, filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(content)

        # Return relative path
        relative_path = f"/uploads/audio/{now.year}/{now.month:02d}/{filename}"
        mime_type = file.content_type or f"audio/{ext[1:]}"

        return relative_path, file_size, mime_type

    def get_absolute_path(self, relative_path: str) -> str:
        """Convert relative path to absolute filesystem path"""
        # Remove leading slash if present
        if relative_path.startswith("/"):
            relative_path = relative_path[1:]

        # Remove 'uploads/' prefix since base_path already includes it
        if relative_path.startswith("uploads/"):
            relative_path = relative_path[8:]  # Remove 'uploads/'

        return os.path.join(self.base_path, relative_path)

    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists"""
        abs_path = self.get_absolute_path(relative_path)
        return os.path.exists(abs_path)

    def delete_file(self, relative_path: str) -> bool:
        """Delete file from filesystem"""
        abs_path = self.get_absolute_path(relative_path)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
                return True
            except Exception as e:
                print(f"Error deleting file {abs_path}: {e}")
                return False
        return False

    @staticmethod
    def _get_extension(filename: str) -> str:
        """Extract file extension"""
        return os.path.splitext(filename)[1].lower()

    @staticmethod
    def _generate_file_hash(content: bytes) -> str:
        """Generate SHA256 hash of file content"""
        return hashlib.sha256(content).hexdigest()


# Singleton instance
file_storage_service = FileStorageService()
