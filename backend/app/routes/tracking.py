"""
Real-Time Tracking & WebSocket Router
Location: backend/app/routes/tracking.py

Exposes:
1. Bidirectional WebSocket endpoint (/ws/orders/{order_id}) for live status and ETA streaming.
2. REST logistics endpoint (/api/orders/{order_id}/logistics) for map coordinates and Haversine distance.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

# Import database session and Order model
from app.database import get_db
from app.models import Order

# Import our WebSocket connection manager and Logistics engine
from app.websocket_manager import ws_manager
from app.logistics import compute_order_logistics

router = APIRouter(
    tags=["Real-Time Tracking & WebSockets"]
)


# =============================================================
# 1. LIVE WEBSOCKET ENDPOINT (Full-Duplex TCP Streaming)
# =============================================================

@router.websocket("/ws/orders/{order_id}")
async def order_tracking_websocket(
    websocket: WebSocket,
    order_id: int,
    db: Session = Depends(get_db)
):
    """
    Live WebSocket pipe for an order:
    1. Verifies order exists in MySQL.
    2. Accepts connection and joins the channel for order_id.
    3. Computes and immediately pushes initial ETA & logistics.
    4. Keeps socket alive to receive live kitchen updates in 0ms!
    """
    # 1. Verify that the requested order exists in the database
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        # If order doesn't exist, reject the socket connection
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 2. Connect client to the WebSocket Switchboard
    await ws_manager.connect(order_id, websocket)

    try:
        # 3. Calculate initial logistics and send immediate greeting state
        logistics = compute_order_logistics(order.status.value, order.delivery_address)
        
        initial_event = {
            "event": "INITIAL_STATE",
            "order_id": order.id,
            "status": order.status.value,
            "logistics": logistics
        }
        await websocket.send_json(initial_event)

        # 4. Keep the connection open and listen for any client messages
        while True:
            # Keeps the socket connection alive in the event loop
            client_msg = await websocket.receive_text()
            
            # If client sends a ping, respond with pong
            if client_msg.strip().lower() == "ping":
                await websocket.send_json({"event": "PONG"})

    except WebSocketDisconnect:
        # Safely unplug the client when they close the browser tab
        ws_manager.disconnect(order_id, websocket)
    except Exception as e:
        print(f"⚠️ Unexpected WebSocket error on Order #{order_id}: {e}")
        ws_manager.disconnect(order_id, websocket)


# =============================================================
# 2. REST LOGISTICS ENDPOINT (Standard HTTP)
# =============================================================

@router.get("/api/orders/{order_id}/logistics", summary="Get GPS coordinates and Haversine distance for an order")
def get_order_logistics(order_id: int, db: Session = Depends(get_db)):
    """
    HTTP REST endpoint to fetch coordinates, Haversine distance, and ETA
    for map rendering and initial page load.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} does not exist."
        )

    logistics = compute_order_logistics(order.status.value, order.delivery_address)
    
    return {
        "order_id": order.id,
        "customer_name": order.customer_name,
        "delivery_address": order.delivery_address,
        "status": order.status.value,
        "logistics": logistics
    }