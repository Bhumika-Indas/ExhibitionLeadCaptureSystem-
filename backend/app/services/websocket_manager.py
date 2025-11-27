"""
WebSocket Connection Manager for Real-time Chat
Handles WebSocket connections, message broadcasting, and connection lifecycle
"""
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time chat"""

    def __init__(self):
        # Store active connections: {employee_id: [WebSocket connections]}
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store connection metadata: {websocket: {employee_id, connected_at}}
        self.connection_metadata: Dict[WebSocket, Dict] = {}

    async def connect(self, websocket: WebSocket, employee_id: int):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        if employee_id not in self.active_connections:
            self.active_connections[employee_id] = []

        self.active_connections[employee_id].append(websocket)
        self.connection_metadata[websocket] = {
            "employee_id": employee_id,
            "connected_at": datetime.now().isoformat()
        }

        logger.info(f" WebSocket connected: Employee {employee_id} (Total connections: {self.get_connection_count()})")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.connection_metadata:
            metadata = self.connection_metadata[websocket]
            employee_id = metadata["employee_id"]

            # Remove from active connections
            if employee_id in self.active_connections:
                self.active_connections[employee_id].remove(websocket)

                # Clean up empty lists
                if not self.active_connections[employee_id]:
                    del self.active_connections[employee_id]

            # Remove metadata
            del self.connection_metadata[websocket]

            logger.info(f" WebSocket disconnected: Employee {employee_id} (Total connections: {self.get_connection_count()})")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {str(e)}")

    async def send_to_employee(self, message: dict, employee_id: int):
        """Send a message to all connections of a specific employee"""
        if employee_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[employee_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to employee {employee_id}: {str(e)}")
                    disconnected.append(connection)

            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(connection)

    async def broadcast(self, message: dict, exclude_employee: int = None):
        """Broadcast a message to all connected clients (optionally excluding one employee)"""
        disconnected = []

        for employee_id, connections in self.active_connections.items():
            if exclude_employee and employee_id == exclude_employee:
                continue

            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to employee {employee_id}: {str(e)}")
                    disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_to_exhibition(self, message: dict, exhibition_id: int):
        """Broadcast a message to all employees monitoring a specific exhibition"""
        # For now, broadcast to all. Can be filtered based on employee's selected exhibition
        await self.broadcast(message)

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())

    def get_active_employees(self) -> List[int]:
        """Get list of employee IDs with active connections"""
        return list(self.active_connections.keys())

    def is_employee_online(self, employee_id: int) -> bool:
        """Check if an employee has any active connections"""
        return employee_id in self.active_connections and len(self.active_connections[employee_id]) > 0


# Global connection manager instance
manager = ConnectionManager()
