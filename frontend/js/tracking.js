/* =============================================================
   ORDER TRACKING & REAL-TIME TELEMETRY MODULE
   Location: frontend/js/tracking.js

   Responsibilities:
   1. Fetches authentic order & logistics telemetry with JWT authentication.
   2. Initializes Leaflet.js with Esri World Street Map (No API Key & No Watermark).
   3. Draws route polyline and custom markers with XSS-sanitized popups (SEC-05 Patched).
   4. Connects to the full-duplex WebSocket channel with token handshake (SEC-07 Patched).
   5. Dynamic Protocol Resolver: Automatically uses wss:// on HTTPS and ws:// on HTTP.
   6. Listens for live kitchen broadcasts and handles all states (including CANCELLED)!
   7. Provides interactive customer order cancellation controls using unified design modals.
   ============================================================= */

// Global holders for Leaflet map elements, WebSocket connection, and active order
let map = null;
let restaurantMarker = null;
let customerMarker = null;
let riderMarker = null;
let routePolyline = null;
let socket = null;
let currentOrderId = null;


// =============================================================
// 1. PAGE INITIALIZATION ON DOM READY
// =============================================================

document.addEventListener("DOMContentLoaded", async () => {
    // 1. Extract ?order_id=... from the browser URL address bar
    const urlParams = new URLSearchParams(window.location.search);
    const orderId = urlParams.get("order_id");

    if (!orderId) {
        await showAppAlert({
            title: "Missing Order ID",
            tag: "Navigation",
            message: "No order ID was provided. Returning to the home storefront.",
            confirmText: "Back to Home",
            type: "warning"
        });
        window.location.href = "index.html";
        return;
    }

    currentOrderId = orderId;
    document.getElementById("display-order-id").textContent = orderId;

    try {
        // 2. Fetch authentic order record from MySQL via authenticated REST
        const order = await getOrderById(orderId);
        console.log("[Tracking] Order data loaded from MySQL:", order);

        // 3. Populate customer delivery details
        document.getElementById("track-name").textContent = order.customer_name;
        document.getElementById("track-phone").textContent = order.customer_phone;
        document.getElementById("track-address").textContent = order.delivery_address;
        document.getElementById("track-payment").textContent = order.payment_method;

        // 4. Populate financial receipt summary
        const formattedTotal = `$${parseFloat(order.total_amount).toFixed(2)}`;
        document.getElementById("track-subtotal").textContent = formattedTotal;
        document.getElementById("track-total").textContent = formattedTotal;

        // 5. Render frozen snapshot receipt items
        const itemsContainer = document.getElementById("track-items-list");
        if (itemsContainer && order.items) {
            itemsContainer.innerHTML = order.items.map(item => `
                <div class="receipt-item-row">
                    <div>
                        <strong>${escapeHtml(item.item_name_snapshot)}</strong>
                        <small>Qty: ${item.quantity} × $${parseFloat(item.price_per_unit).toFixed(2)}</small>
                    </div>
                    <span>$${(parseFloat(item.price_per_unit) * item.quantity).toFixed(2)}</span>
                </div>
            `).join("");
        }

        // 6. Fetch initial logistics coordinates, distance, and dynamic ETA (Authenticated via apiRequest)
        const logisticsData = await apiRequest(`/orders/${orderId}/logistics`);
        console.log("[Tracking] Initial Logistics Telemetry:", logisticsData);

        // 7. Mount the Leaflet map and place markers
        initLeafletMap(order, logisticsData.logistics);

        // 8. Update initial visual stepper, metrics, and cancellation controls
        updateUIState(order.status, logisticsData.logistics);

        // 9. Open persistent full-duplex WebSocket connection with token handshake
        connectTrackingWebSocket(orderId);

    } catch (error) {
        console.error("[Tracking] Failed to load order tracking details:", error);
        await showAppAlert({
            title: "Access Denied or Not Found",
            tag: "Security Guard",
            message: error.message || `Order #${orderId} could not be retrieved.`,
            confirmText: "Go to Storefront",
            type: "danger"
        });
        window.location.href = "index.html";
    }
});


// =============================================================
// 2. LEAFLET MAP INITIALIZATION & MARKER PLACEMENT
// =============================================================

/**
 * Initializes the Leaflet map with Esri World Street Map tiles, custom
 * markers, and a dashed geodesic route line.
 * SEC-05 Patched: Sanitizes customer name and address before popup interpolation.
 */
function initLeafletMap(order, logistics) {
    const restCoords = [logistics.restaurant_coordinates.lat, logistics.restaurant_coordinates.lon];
    const custCoords = [logistics.customer_coordinates.lat, logistics.customer_coordinates.lon];

    // 1. Create Leaflet map centered at the restaurant
    map = L.map('tracking-map', {
        zoomControl: true,
        attributionControl: false
    }).setView(restCoords, 13);

    // 2. Add Esri World Street Map layer (High-resolution, No API Key, No Watermark)
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, TomTom',
        maxZoom: 19
    }).addTo(map);

    // 3. Custom Icons using Leaflet L.divIcon
    const kitchenIcon = L.divIcon({
        className: 'custom-map-icon icon-kitchen',
        html: '<span class="map-pin-badge kitchen-pin">K</span>',
        iconSize: [36, 36],
        iconAnchor: [18, 18]
    });

    const customerIcon = L.divIcon({
        className: 'custom-map-icon icon-customer',
        html: '<span class="map-pin-badge customer-pin">C</span>',
        iconSize: [36, 36],
        iconAnchor: [18, 18]
    });

    const riderIcon = L.divIcon({
        className: 'custom-map-icon icon-rider',
        html: '<span class="map-pin-badge rider-pin">R</span>',
        iconSize: [42, 42],
        iconAnchor: [21, 21]
    });

    // 4. Place Restaurant pin
    restaurantMarker = L.marker(restCoords, { icon: kitchenIcon })
        .addTo(map)
        .bindPopup("<b>FoodExpress Kitchen</b><br>Downtown Central Store");

    // SEC-05 Patched: Neutralize raw HTML before binding Leaflet popup
    const safeCustomerName = escapeHtml(order.customer_name);
    const safeCustomerAddress = escapeHtml(order.delivery_address);

    customerMarker = L.marker(custCoords, { icon: customerIcon })
        .addTo(map)
        .bindPopup(`<b>${safeCustomerName}</b><br>${safeCustomerAddress}`);

    // 5. Draw connecting route polyline
    routePolyline = L.polyline([restCoords, custCoords], {
        color: '#4F46E5',
        weight: 4,
        opacity: 0.8,
        dashArray: '8, 8'
    }).addTo(map);

    // 6. Compute initial rider position based on current order status
    if (order.status !== "CANCELLED") {
        const initialRiderCoords = calculateRiderPosition(order.status, restCoords, custCoords);
        riderMarker = L.marker(initialRiderCoords, { icon: riderIcon })
            .addTo(map)
            .bindPopup("<b>Delivery Partner</b><br>On the move");
    }

    // 7. Auto-fit camera bounds so the entire route is neatly framed
    map.fitBounds(routePolyline.getBounds(), { padding: [50, 50] });
}

/**
 * Calculates delivery rider GPS coordinates along the route line
 * based on the current order lifecycle stage.
 */
function calculateRiderPosition(status, restCoords, custCoords) {
    if (status === "PENDING" || status === "PREPARING") {
        return restCoords;
    } else if (status === "OUT_FOR_DELIVERY") {
        const lat = restCoords[0] + (custCoords[0] - restCoords[0]) * 0.65;
        const lon = restCoords[1] + (custCoords[1] - restCoords[1]) * 0.65;
        return [lat, lon];
    } else if (status === "DELIVERED") {
        return custCoords;
    }
    return restCoords;
}


// =============================================================
// 3. REAL-TIME WEBSOCKET CLIENT WITH TOKEN HANDSHAKE
// =============================================================

/**
 * Dynamically resolves the full WebSocket endpoint:
 * 1. Honors explicit window.FOODEXPRESS_WS_URL override.
 * 2. Parses window.FOODEXPRESS_API_BASE_URL if configured for separate backend host.
 * 3. Fallbacks to 127.0.0.1:8000 on local development.
 * 4. Resolves wss:// on HTTPS domains and ws:// on plain HTTP domains.
 */
function resolveTrackingWsUrl(orderId) {
    const token = getStoredToken();
    const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : "";

    // 1. Explicit global override for custom WebSocket proxy
    if (typeof window !== "undefined" && window.FOODEXPRESS_WS_URL) {
        const base = window.FOODEXPRESS_WS_URL.replace(/\/+$/, "");
        return `${base}/ws/orders/${orderId}${tokenQuery}`;
    }

    // 2. Derive from API Base URL if configured
    if (typeof window !== "undefined" && window.FOODEXPRESS_API_BASE_URL) {
        try {
            const parsedApi = new URL(window.FOODEXPRESS_API_BASE_URL, window.location.href);
            const wsProto = parsedApi.protocol === "https:" ? "wss:" : "ws:";
            return `${wsProto}//${parsedApi.host}/ws/orders/${orderId}${tokenQuery}`;
        } catch (e) {
            // Proceed to standard environment detection if URL parse fails
        }
    }

    // 3. Local development fallback
    const isLocalDevelopment = typeof window !== "undefined" && (
        window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1" ||
        window.location.protocol === "file:" ||
        window.location.hostname === ""
    );

    if (isLocalDevelopment) {
        return `ws://127.0.0.1:8000/ws/orders/${orderId}${tokenQuery}`;
    }

    // 4. Production cloud domain (wss:// on https:, ws:// on http:)
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/ws/orders/${orderId}${tokenQuery}`;
}

function connectTrackingWebSocket(orderId) {
    const wsUrl = resolveTrackingWsUrl(orderId);

    console.log(`[WebSocket] Initiating authenticated handshake with: ${wsUrl}`);

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log("[WebSocket] Connection authenticated & established. Streaming live events.");
        document.getElementById("ws-status-text").textContent = "Live Socket Active";
        document.getElementById("ws-dot").style.background = "#22C55E";
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log("[WebSocket] Live event received from server:", data);

            if (data.event === "INITIAL_STATE" || data.event === "STATUS_UPDATE") {
                const newStatus = data.status;
                const logistics = data.logistics;

                // Instantly update stepper, ETA, badge, and cancellation UI
                updateUIState(newStatus, logistics);

                // Smoothly update or remove the courier marker
                if (map) {
                    if (newStatus === "CANCELLED") {
                        if (riderMarker && map.hasLayer(riderMarker)) {
                            map.removeLayer(riderMarker);
                        }
                    } else if (logistics) {
                        const restCoords = [logistics.restaurant_coordinates.lat, logistics.restaurant_coordinates.lon];
                        const custCoords = [logistics.customer_coordinates.lat, logistics.customer_coordinates.lon];
                        const newRiderCoords = calculateRiderPosition(newStatus, restCoords, custCoords);

                        if (riderMarker) {
                            if (!map.hasLayer(riderMarker)) riderMarker.addTo(map);
                            riderMarker.setLatLng(newRiderCoords);
                        }
                    }
                }
            }
        } catch (e) {
            console.error("[WebSocket] Error processing frame:", e);
        }
    };

    socket.onerror = (err) => {
        console.error("[WebSocket] Error:", err);
        document.getElementById("ws-status-text").textContent = "Socket Disconnected";
        document.getElementById("ws-dot").style.background = "#EF4444";
    };

    socket.onclose = (event) => {
        // If server severed connection due to security policy (1008), do not spam reconnect
        if (event.code === 1008) {
            console.warn("[WebSocket] Severed by server: Policy Violation (403 Unauthorized). Halting reconnect.");
            document.getElementById("ws-status-text").textContent = "Socket Forbidden";
            document.getElementById("ws-dot").style.background = "#EF4444";
            return;
        }

        console.warn("[WebSocket] Connection closed. Retrying in 5 seconds...");
        document.getElementById("ws-status-text").textContent = "Reconnecting...";
        document.getElementById("ws-dot").style.background = "#F59E0B";

        setTimeout(() => {
            connectTrackingWebSocket(orderId);
        }, 5000);
    };
}


// =============================================================
// 4. UI METRIC & STEPPER SYNCHRONIZATION
// =============================================================

/**
 * Updates visual stepper, dynamic ETA, cancellation button, and handles CANCELLED state
 */
function updateUIState(status, logistics) {
    const headerEta = document.getElementById("header-eta-text");
    const topBadge = document.querySelector(".tracking-header .success-badge");
    const stepperCard = document.querySelector(".stepper-card");
    const wsDot = document.getElementById("ws-dot");
    const wsStatusText = document.getElementById("ws-status-text");

    // Manage Cancel Button: visible ONLY while status is PENDING
    manageCancelOrderButton(status);

    // =========================================================
    // CASE A: ORDER IS CANCELLED
    // =========================================================
    if (status === "CANCELLED") {
        if (topBadge) {
            topBadge.textContent = "Order Cancelled";
            topBadge.style.cssText = "background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5;";
        }

        if (headerEta) {
            headerEta.innerHTML = `<span style="color: #DC2626; font-weight: 700;">Order Cancelled</span>`;
        }

        let banner = document.getElementById("order-cancellation-banner");
        if (!banner && stepperCard) {
            banner = document.createElement("div");
            banner.id = "order-cancellation-banner";
            banner.className = "order-cancelled-banner";
            banner.innerHTML = `
                <div>
                    <div style="font-size: 1.05rem; font-weight: 800;">This Order Has Been Cancelled</div>
                    <div style="font-size: 0.88rem; opacity: 0.9; margin-top: 3px;">
                        This order was cancelled. If you paid online via our Sandbox Gateway, your refund will be automatically credited.
                    </div>
                </div>
            `;
            stepperCard.insertAdjacentElement("beforebegin", banner);
        }

        if (stepperCard) {
            stepperCard.style.opacity = "0.4";
            stepperCard.style.filter = "grayscale(80%)";
        }
        updateStepper(null);

        document.getElementById("map-status-desc").textContent = "Order cancelled. Courier dispatch halted.";
        document.getElementById("map-distance-info").innerHTML = `<strong style="color: #DC2626;">Dispatch Status: Voided</strong>`;

        if (wsStatusText) wsStatusText.textContent = "Order Inactive";
        if (wsDot) wsDot.style.background = "#64748B";

        return;
    }

    // =========================================================
    // CASE B: ACTIVE / DELIVERED ORDER
    // =========================================================

    const existingBanner = document.getElementById("order-cancellation-banner");
    if (existingBanner) existingBanner.remove();

    if (stepperCard) {
        stepperCard.style.opacity = "1";
        stepperCard.style.filter = "none";
    }

    if (topBadge) {
        if (status === "DELIVERED") {
            topBadge.textContent = "Delivery Complete";
            topBadge.style.cssText = "background: #DCFCE7; color: #166534; border: 1px solid #86EFAC;";
        } else {
            topBadge.textContent = "Order Live Telemetry";
            topBadge.style.cssText = "";
        }
    }

    updateStepper(status);

    if (!logistics) return;

    if (status === "DELIVERED") {
        headerEta.innerHTML = `<span style="color: #16A34A; font-weight: 700;">Delivered! Enjoy your meal!</span>`;
    } else {
        headerEta.textContent = `~${logistics.estimated_minutes} Minutes (${logistics.distance_km} km away)`;
    }

    document.getElementById("map-status-desc").textContent = logistics.status_message;
    document.getElementById("map-distance-info").innerHTML = `
        <strong>Haversine Distance:</strong> ${logistics.distance_km} km • <strong>ETA:</strong> ${logistics.estimated_minutes} mins
    `;
}

/**
 * Highlights the stepper circles and connecting lines up to the current stage
 */
function updateStepper(status) {
    const stages = ["PENDING", "PREPARING", "OUT_FOR_DELIVERY", "DELIVERED"];
    const currentIndex = status ? stages.indexOf(status) : -1;

    stages.forEach((stage, idx) => {
        const stepEl = document.getElementById(`step-${stage}`);
        if (stepEl) {
            if (currentIndex !== -1 && idx <= currentIndex) {
                stepEl.classList.add("active");
            } else {
                stepEl.classList.remove("active");
            }
        }
    });

    for (let i = 1; i <= 3; i++) {
        const lineEl = document.getElementById(`line-${i}`);
        if (lineEl) {
            if (currentIndex !== -1 && currentIndex >= i) {
                lineEl.classList.add("active");
            } else {
                lineEl.classList.remove("active");
            }
        }
    }
}


// =============================================================
// 5. CUSTOMER ORDER CANCELLATION HANDLERS
// =============================================================

function manageCancelOrderButton(status) {
    const existingContainer = document.getElementById("customer-cancel-container");

    if (status === "PENDING") {
        if (!existingContainer) {
            const container = document.createElement("div");
            container.id = "customer-cancel-container";
            container.style.cssText = "margin-top: 14px; text-align: center;";
            container.innerHTML = `
                <button id="btn-cancel-order" onclick="handleCustomerCancelOrder()" 
                    style="background: #FFF1F2; color: #E11D48; border: 1.5px solid #FECDD3; padding: 9px 20px; border-radius: var(--radius-sm, 8px); font-weight: 700; font-size: 0.92rem; cursor: pointer; transition: all 0.2s ease;">
                    Cancel Order
                </button>
            `;
            const headerEl = document.querySelector(".tracking-header");
            if (headerEl) {
                headerEl.appendChild(container);
            }
        }
    } else {
        if (existingContainer) {
            existingContainer.remove();
        }
    }
}

async function handleCustomerCancelOrder() {
    if (!currentOrderId) return;

    const confirmed = await showAppConfirm({
        title: "Cancel Order",
        tag: "Order Cancellation",
        message: "Are you sure you want to cancel this order? This action cannot be undone.",
        confirmText: "Yes, Cancel Order",
        cancelText: "Keep Order",
        isDanger: true
    });

    if (!confirmed) return;

    const cancelBtn = document.getElementById("btn-cancel-order");
    if (cancelBtn) {
        cancelBtn.disabled = true;
        cancelBtn.textContent = "Cancelling Order...";
        cancelBtn.style.opacity = "0.6";
        cancelBtn.style.cursor = "not-allowed";
    }

    try {
        const updatedOrder = await cancelOrder(currentOrderId);
        console.log("[Cancellation] Order cancelled successfully:", updatedOrder);
        updateUIState("CANCELLED", null);
    } catch (error) {
        console.error("[Cancellation] Error:", error);
        await showAppAlert({
            title: "Cancellation Failed",
            tag: "State Machine",
            message: error.message || "Could not cancel order.",
            confirmText: "Understand",
            type: "danger"
        });

        if (cancelBtn) {
            cancelBtn.disabled = false;
            cancelBtn.textContent = "Cancel Order";
            cancelBtn.style.opacity = "1";
            cancelBtn.style.cursor = "pointer";
        }
    }
}

window.handleCustomerCancelOrder = handleCustomerCancelOrder;