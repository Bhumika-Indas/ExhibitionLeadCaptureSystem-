"""
WebSocket Router for Real-time Chat Messaging
Provides WebSocket endpoints for bidirectional real-time communication
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from fastapi.exceptions import WebSocketException
from app.services.websocket_manager import manager
from app.utils.jwt_utils import jwt_manager
from app.db.connection import db
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_employee_from_token(token: str) -> int:
    """Verify JWT token and extract employee ID"""
    try:
        payload = jwt_manager.decode_token(token)
        if not payload:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

        # Check for employee_id in payload (could be 'sub' or 'employee_id')
        employee_id = payload.get("employee_id") or payload.get("sub")
        if not employee_id:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

        return int(employee_id)
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {str(e)}")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    employee_id: int = Query(1, description="Employee ID")
):
    """
    WebSocket endpoint for real-time chat messaging

    Connection URL: ws://localhost:8000/ws/chat?employee_id=<id>

    Message Types:
    - new_message: New chat message received
    - typing_indicator: User is typing
    - lead_update: Lead status changed
    - connection_status: Connection/disconnection events
    """
    try:
        # Connect to WebSocket manager
        await manager.connect(websocket, employee_id)

        # Send connection success message
        await manager.send_personal_message({
            "type": "connection_status",
            "status": "connected",
            "employee_id": employee_id,
            "timestamp": datetime.now().isoformat(),
            "message": "Successfully connected to chat server"
        }, websocket)

        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                logger.info(f" Received message from Employee {employee_id}: {message_type}")

                # Handle different message types
                if message_type == "new_message":
                    await handle_new_message(message, employee_id)

                elif message_type == "typing_indicator":
                    await handle_typing_indicator(message, employee_id)

                elif message_type == "lead_update":
                    await handle_lead_update(message, employee_id)

                elif message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)

                else:
                    logger.warning(f"Unknown message type: {message_type}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from Employee {employee_id}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)

    except WebSocketDisconnect:
        if employee_id:
            manager.disconnect(websocket)
            logger.info(f" Employee {employee_id} disconnected normally")

    except WebSocketException as e:
        logger.error(f"WebSocket exception: {str(e)}")
        if employee_id:
            manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"Unexpected error in WebSocket: {str(e)}")
        if employee_id:
            manager.disconnect(websocket)


async def handle_new_message(message: dict, employee_id: int):
    """Handle new chat message from employee"""
    lead_id = message.get("lead_id")
    message_text = message.get("message", "").strip()
    exhibition_id = message.get("exhibition_id")

    if not lead_id or not message_text:
        logger.warning(f"Invalid message data from Employee {employee_id}")
        return

    try:
        # Store message in database
        query = """
        INSERT INTO Messages (LeadId, SenderType, Message, SentAt)
        VALUES (?, 'employee', ?, GETDATE())
        """
        db.execute_query(query, params=(lead_id, message_text))

        # Get lead details for broadcasting
        lead_query = """
        SELECT LeadId, PrimaryVisitorName, CompanyName, ExhibitionId
        FROM Leads
        WHERE LeadId = ?
        """
        lead = db.execute_query(lead_query, params=(lead_id,), fetch_one=True)

        if lead:
            # Broadcast new message to all connected employees
            broadcast_message = {
                "type": "new_message",
                "lead_id": lead_id,
                "lead_name": lead.get("PrimaryVisitorName", "Unknown"),
                "company_name": lead.get("CompanyName", "No Company"),
                "message": message_text,
                "sender_type": "employee",
                "employee_id": employee_id,
                "exhibition_id": lead.get("ExhibitionId"),
                "timestamp": datetime.now().isoformat()
            }

            # Broadcast to all employees (they'll filter by exhibition on frontend)
            await manager.broadcast(broadcast_message)

            logger.info(f" Message broadcast: Lead {lead_id} from Employee {employee_id}")

    except Exception as e:
        logger.error(f"Failed to handle new message: {str(e)}")


async def handle_typing_indicator(message: dict, employee_id: int):
    """Handle typing indicator from employee"""
    lead_id = message.get("lead_id")
    is_typing = message.get("is_typing", False)
    exhibition_id = message.get("exhibition_id")

    if not lead_id:
        return

    # Broadcast typing indicator to other employees
    typing_message = {
        "type": "typing_indicator",
        "lead_id": lead_id,
        "employee_id": employee_id,
        "is_typing": is_typing,
        "exhibition_id": exhibition_id,
        "timestamp": datetime.now().isoformat()
    }

    # Broadcast to all except the sender
    await manager.broadcast(typing_message, exclude_employee=employee_id)


async def handle_lead_update(message: dict, employee_id: int):
    """Handle lead status update"""
    lead_id = message.get("lead_id")
    new_status = message.get("status")
    exhibition_id = message.get("exhibition_id")

    if not lead_id or not new_status:
        return

    try:
        # Update lead status in database
        query = """
        UPDATE Leads
        SET StatusCode = ?, UpdatedAt = GETDATE()
        WHERE LeadId = ?
        """
        db.execute_query(query, params=(new_status, lead_id))

        # Get updated lead details
        lead_query = """
        SELECT LeadId, PrimaryVisitorName, CompanyName, StatusCode, ExhibitionId
        FROM Leads
        WHERE LeadId = ?
        """
        lead = db.execute_query(lead_query, params=(lead_id,), fetch_one=True)

        if lead:
            # Broadcast lead update to all employees
            update_message = {
                "type": "lead_update",
                "lead_id": lead_id,
                "lead_name": lead.get("PrimaryVisitorName", "Unknown"),
                "company_name": lead.get("CompanyName", "No Company"),
                "status": lead.get("StatusCode"),
                "exhibition_id": lead.get("ExhibitionId"),
                "updated_by": employee_id,
                "timestamp": datetime.now().isoformat()
            }

            await manager.broadcast(update_message)

            logger.info(f" Lead update broadcast: Lead {lead_id} status changed to {new_status}")

    except Exception as e:
        logger.error(f"Failed to handle lead update: {str(e)}")


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": manager.get_connection_count(),
        "active_employees": manager.get_active_employees(),
        "status": "operational"
    }
