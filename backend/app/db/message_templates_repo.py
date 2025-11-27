"""
Message Templates Repository
Handles CRUD operations for reusable message templates
"""

from typing import Dict, List, Any, Optional
from app.db.connection import db


class MessageTemplatesRepository:
    """Repository for managing message templates"""

    def get_all_templates(
        self,
        category: Optional[str] = None,
        message_type: Optional[str] = None,
        is_active: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all message templates with optional filters

        Args:
            category: Filter by category (thank_you, value_prop, etc.)
            message_type: Filter by type (text, image, video, document)
            is_active: Filter by active status

        Returns:
            List of template dictionaries
        """
        query = """
            SELECT
                TemplateId,
                Title,
                MessageType,
                MessageBody,
                MediaFilePath,
                Variables,
                Category,
                CreatedBy,
                CreatedAt,
                UpdatedAt,
                IsActive
            FROM MessageTemplates
            WHERE 1=1
        """
        params = []

        if category:
            query += " AND Category = ?"
            params.append(category)

        if message_type:
            query += " AND MessageType = ?"
            params.append(message_type)

        if is_active is not None:
            query += " AND IsActive = ?"
            params.append(1 if is_active else 0)

        query += " ORDER BY Category, Title"

        return db.execute_query(query, params, fetch_all=True)

    def get_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get a single template by ID"""
        query = """
            SELECT
                TemplateId,
                Title,
                MessageType,
                MessageBody,
                MediaFilePath,
                Variables,
                Category,
                CreatedBy,
                CreatedAt,
                UpdatedAt,
                IsActive
            FROM MessageTemplates
            WHERE TemplateId = ?
        """
        return db.execute_query(query, [template_id], fetch_one=True)

    def create_template(
        self,
        title: str,
        message_type: str,
        message_body: str,
        category: str = 'general',
        media_file_path: Optional[str] = None,
        variables: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> int:
        """
        Create a new message template

        Args:
            title: Template name
            message_type: text, image, video, document, audio
            message_body: Message content
            category: Template category
            media_file_path: Path to media file (if applicable)
            variables: JSON string of variable names
            created_by: Employee ID

        Returns:
            New template ID
        """
        query = """
            INSERT INTO MessageTemplates (
                Title, MessageType, MessageBody, MediaFilePath,
                Variables, Category, CreatedBy, IsActive
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 1);
            SELECT SCOPE_IDENTITY() AS TemplateId;
        """
        result = db.execute_query(
            query,
            [title, message_type, message_body, media_file_path, variables, category, created_by],
            fetch_one=True
        )
        return int(result["TemplateId"])

    def update_template(
        self,
        template_id: int,
        title: Optional[str] = None,
        message_type: Optional[str] = None,
        message_body: Optional[str] = None,
        category: Optional[str] = None,
        media_file_path: Optional[str] = None,
        variables: Optional[str] = None
    ) -> bool:
        """Update an existing template"""
        # Build dynamic UPDATE query
        updates = []
        params = []

        if title is not None:
            updates.append("Title = ?")
            params.append(title)

        if message_type is not None:
            updates.append("MessageType = ?")
            params.append(message_type)

        if message_body is not None:
            updates.append("MessageBody = ?")
            params.append(message_body)

        if category is not None:
            updates.append("Category = ?")
            params.append(category)

        if media_file_path is not None:
            updates.append("MediaFilePath = ?")
            params.append(media_file_path)

        if variables is not None:
            updates.append("Variables = ?")
            params.append(variables)

        if not updates:
            return False

        updates.append("UpdatedAt = GETDATE()")
        params.append(template_id)

        query = f"""
            UPDATE MessageTemplates
            SET {', '.join(updates)}
            WHERE TemplateId = ?
        """

        db.execute_query(query, params)
        return True

    def delete_template(self, template_id: int) -> bool:
        """Soft delete a template (set IsActive = 0)"""
        query = """
            UPDATE MessageTemplates
            SET IsActive = 0, UpdatedAt = GETDATE()
            WHERE TemplateId = ?
        """
        db.execute_query(query, [template_id])
        return True

    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all templates for a specific category"""
        return self.get_all_templates(category=category)


# Singleton instance
message_templates_repo = MessageTemplatesRepository()
