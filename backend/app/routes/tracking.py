"""Real-time order tracking and WebSocket location streaming."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError

# Import database session, models, and security providers
from app.database import get_db
from app.models import Order, User, UserRole
from app.security import get_current_user, SECRET_KEY, ALGORITHM
from app.websocket_manager import ws_manager
from app.logistics import compute_order_logistics

router = APIRouter(
    tags=["Real-Time Tracking & WebSockets"]
)


# WebSocket tracking stream

@router.websocket("/ws/orders/{order_id}")
async def order_tracking_websocket(
    websocket: WebSocket,
    order_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Stream real-time driver coordinates and order updates over WebSocket."""
    # Verify order exists
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Validate JWT token
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Decode token claims
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        role_str = payload.get("role")
        if not user_id_str:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        token_user_id = int(user_id_str)
    except (JWTError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Step 4: Ownership Verification (IDOR Defense on Real-Time Socket)
    is_owner = (order.user_id == token_user_id)
    is_admin = (role_str == UserRole.ADMIN.value)
    if not is_owner and not is_admin:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Step 5: Authorization confirmed! Accept socket handshake
    await ws_manager.connect(order_id, websocket)

    try:
        # Calculate initial logistics and send immediate greeting frame
        logistics = compute_order_logistics(order.status.value, order.delivery_address)
        
        initial_event = {
            "event": "INITIAL_STATE",
            "order_id": order.id,
            "status": order.status.value,
            "logistics": logistics
        }
        await websocket.send_json(initial_event)

        # Keep connection alive in the event loop
        while True:
            client_msg = await websocket.receive_text()
            if client_msg.strip().lower() == "ping":
                await websocket.send_json({"event": "PONG"})

    except WebSocketDisconnect:
        ws_manager.disconnect(order_id, websocket)
    except Exception as e:
        print(f"[WebSocket] Disconnected on Order #{order_id}: {e}")
        ws_manager.disconnect(order_id, websocket)


# Tracking details endpoint

@router.get("/api/orders/{order_id}/logistics", summary="Get GPS coordinates and Haversine distance (Ownership Protected)")
def get_order_logistics(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get delivery route details, distance, and ETA.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} does not exist."
        )

    # Ownership Guard (IDOR Defense)
    if order.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view delivery telemetry for this order."
        )

    logistics = compute_order_logistics(order.status.value, order.delivery_address)
    return {"order_id": order_id, "logistics": logistics}