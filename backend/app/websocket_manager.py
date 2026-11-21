"""
WebSocket Connection Manager
Location: backend/app/websocket_manager.py

Manages active real-time WebSocket client connections grouped by order_id.
Handles handshakes, disconnections, memory cleanup, and broadcasting live events.
"""

from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """
    Switchboard that tracks live WebSocket connections for orders.
    active_connections structure:
    {
        order_id: [websocket_client_1, websocket_client_2, ...]
    }
    """

    def __init__(self):
        # Maps order_id (int) to a list of connected WebSockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, order_id: int, websocket: WebSocket):
        """
        1. Completes the initial HTTP-to-WebSocket upgrade handshake.
        2. Adds the client's socket to the channel for this order.
        """
        await websocket.accept()

        if order_id not in self.active_connections:
            self.active_connections[order_id] = []

        self.active_connections[order_id].append(websocket)
        print(f"📡 WebSocket connected for Order #{order_id} (Total listeners: {len(self.active_connections[order_id])})")

    def disconnect(self, order_id: int, websocket: WebSocket):
        """
        Removes a client when they close the browser tab.
        Cleans up empty lists to prevent server memory leaks!
        """
        if order_id in self.active_connections:
            if websocket in self.active_connections[order_id]:
                self.active_connections[order_id].remove(websocket)

            # If no one is listening to this order anymore, delete the channel
            if not self.active_connections[order_id]:
                del self.active_connections[order_id]

        print(f"🔌 WebSocket disconnected for Order #{order_id}")

    async def broadcast_order_update(self, order_id: int, event_data: dict):
        """
        Pushes a real-time JSON event down the pipe to ALL clients
        currently watching this specific order!
        """
        if order_id not in self.active_connections:
            # No clients are currently watching this order
            return

        dead_connections = []

        # Send the update to every listener on this order's channel
        for connection in self.active_connections[order_id]:
            try:
                await connection.send_json(event_data)
            except Exception as e:
                print(f"⚠️ Failed to send update to client, marking for cleanup: {e}")
                dead_connections.append(connection)

        # Clean up any stale sockets that abruptly lost connection
        for dead in dead_connections:
            self.disconnect(order_id, dead)


# Global singleton instance used across the application
ws_manager = ConnectionManager()