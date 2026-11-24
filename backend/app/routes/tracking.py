# =============================================================
# FILE: backend/app/routes/tracking.py
# =============================================================

"""
Real-Time Tracking & WebSocket Router
Location: backend/app/routes/tracking.py

Exposes:
1. Bidirectional WebSocket endpoint (/ws/orders/{order_id}) with token handshake auth (SEC-07 Patched).
2. REST logistics endpoint (/api/orders/{order_id}/logistics) with ownership enforcement (SEC-07 Patched).
"""

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


# =============================================================
# 1. LIVE WEBSOCKET ENDPOINT (Token Handshake & Ownership Guard)
# =============================================================

@router.websocket("/ws/orders/{order_id}")
async def order_tracking_websocket(
    websocket: WebSocket,
    order_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Live WebSocket pipe for an order.
    SEC-07 Patched:
    1. Verifies order exists in MySQL.
    2. Validates cryptographically signed JWT token passed via query param (?token=...).
    3. Ownership Guard: Asserts order.user_id == token.sub (or role == ADMIN).
    4. Rejects unauthorized connections with WS_1008_POLICY_VIOLATION before accepting.
    5. Streams real-time ETA and courier GPS coordinates exclusively to authorized parties.
    """
    # Step 1: Verify order exists in MySQL
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Step 2: Validate JWT Token presence
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Step 3: Cryptographically decode token and extract claims
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


# =============================================================
# 2. REST LOGISTICS ENDPOINT (Ownership Protected)
# =============================================================

@router.get("/api/orders/{order_id}/logistics", summary="Get GPS coordinates and Haversine distance (Ownership Protected)")
def get_order_logistics(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    HTTP REST endpoint to fetch coordinates, Haversine distance, and ETA.
    SEC-07 Patched: Requires valid authentication and enforces order ownership.
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