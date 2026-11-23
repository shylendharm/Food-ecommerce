/* =============================================================
   ORDER TRACKING & REAL-TIME TELEMETRY MODULE
   Location: frontend/js/tracking.js

   Responsibilities:
   1. Fetches authentic order & logistics telemetry from FastAPI REST.
   2. Initializes Leaflet.js with Esri World Street Map (No API Key & No Watermark).
   3. Draws route polyline and custom emoji markers (Restaurant, Customer, Rider).
   4. Connects to the full-duplex WebSocket channel (/ws/orders/{id}).
   5. Listens for live kitchen broadcasts and handles all states (including CANCELLED)!
   ============================================================= */

// Global holders for Leaflet map elements and WebSocket connection
let map = null;
let restaurantMarker = null;
let customerMarker = null;
let riderMarker = null;
let routePolyline = null;
let socket = null;


// =============================================================
// 1. PAGE INITIALIZATION ON DOM READY
// =============================================================

document.addEventListener("DOMContentLoaded", async () => {
    // 1. Extract ?order_id=... from the browser URL address bar
    const urlParams = new URLSearchParams(window.location.search);
    const orderId = urlParams.get("order_id");

    if (!orderId) {
        alert("No order ID provided. Returning to home page.");
        window.location.href = "index.html";
        return;
    }

    document.getElementById("display-order-id").textContent = orderId;

    try {
        // 2. Fetch the authentic order record from MySQL via FastAPI REST
        const order = await getOrderById(orderId);
        console.log(" Order data loaded from MySQL:", order);

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
                        <strong>${item.item_name_snapshot}</strong>
                        <small>Qty: ${item.quantity} × $${parseFloat(item.price_per_unit).toFixed(2)}</small>
                    </div>
                    <span>$${(parseFloat(item.price_per_unit) * item.quantity).toFixed(2)}</span>
                </div>
            `).join("");
        }

        // 6. Fetch initial logistics coordinates, distance, and dynamic ETA
        const logisticsRes = await fetch(`http://localhost:8000/api/orders/${orderId}/logistics`);
        const logisticsData = await logisticsRes.json();
        console.log(" Initial Logistics Telemetry:", logisticsData);

        // 7. Mount the Leaflet map and place markers
        initLeafletMap(order, logisticsData.logistics);

        // 8. Update initial visual stepper and metrics
        updateUIState(order.status, logisticsData.logistics);

        // 9. Open persistent full-duplex WebSocket connection!
        connectTrackingWebSocket(orderId);

    } catch (error) {
        console.error("Failed to load order tracking details:", error);
        alert(`Order #${orderId} was not found in the database.`);
        window.location.href = "index.html";
    }
});


// =============================================================
// 2. LEAFLET MAP INITIALIZATION & MARKER PLACEMENT
// =============================================================

/**
 * Initializes the Leaflet map with Esri World Street Map tiles, custom emoji
 * markers, and a dashed geodesic route line.
 */
function initLeafletMap(order, logistics) {
    const restCoords = [logistics.restaurant_coordinates.lat, logistics.restaurant_coordinates.lon];
    const custCoords = [logistics.customer_coordinates.lat, logistics.customer_coordinates.lon];

    // 1. Create Leaflet map centered at the restaurant
    map = L.map('tracking-map', {
        zoomControl: true,
        attributionControl: false
    }).setView(restCoords, 13);

    // 2. Add Esri World Street Map layer (High-resolution, No API Key, No Watermark!)
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, TomTom',
        maxZoom: 19
    }).addTo(map);

    // 3. Custom Emoji Icons using Leaflet's L.divIcon
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

    // 4. Place Restaurant and Customer pins
    restaurantMarker = L.marker(restCoords, { icon: kitchenIcon })
        .addTo(map)
        .bindPopup("<b>FoodExpress Kitchen</b><br>Downtown Central Store");

    customerMarker = L.marker(custCoords, { icon: customerIcon })
        .addTo(map)
        .bindPopup(`<b>${order.customer_name}</b><br>${order.delivery_address}`);

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
// 3. REAL-TIME WEBSOCKET CLIENT & AUTO-RECONNECT
// =============================================================

function connectTrackingWebSocket(orderId) {
    const wsUrl = `ws://localhost:8000/ws/orders/${orderId}`;
    console.log(` Initiating WebSocket handshake with: ${wsUrl}`);

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log(" WebSocket connection established! Streaming live events.");
        document.getElementById("ws-status-text").textContent = "Live Socket Active";
        document.getElementById("ws-dot").style.background = "#22C55E";
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log(" Live event received from server:", data);

            if (data.event === "INITIAL_STATE" || data.event === "STATUS_UPDATE") {
                const newStatus = data.status;
                const logistics = data.logistics;

                // Instantly update stepper, ETA, badge, and cancellation UI
                updateUIState(newStatus, logistics);

                // Smoothly glide or remove the scooter marker
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
            console.error("Error processing WebSocket frame:", e);
        }
    };

    socket.onerror = (err) => {
        console.error(" WebSocket error:", err);
        document.getElementById("ws-status-text").textContent = "Socket Disconnected";
        document.getElementById("ws-dot").style.background = "#EF4444";
    };

    socket.onclose = () => {
        console.warn(" WebSocket connection closed. Retrying in 5 seconds...");
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
 * Updates visual stepper, dynamic ETA, and handles CANCELLED state
 */
function updateUIState(status, logistics) {
    const headerEta = document.getElementById("header-eta-text");
    const topBadge = document.querySelector(".tracking-header .success-badge");
    const stepperCard = document.querySelector(".stepper-card");
    const wsDot = document.getElementById("ws-dot");
    const wsStatusText = document.getElementById("ws-status-text");

    // =========================================================
    // CASE A: ORDER IS CANCELLED
    // =========================================================
    if (status === "CANCELLED") {
        // 1. Update Top Hero Badge
        if (topBadge) {
            topBadge.textContent = "Order Cancelled";
            topBadge.style.cssText = "background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5;";
        }

        // 2. Update Header ETA text
        if (headerEta) {
            headerEta.innerHTML = `<span style="color: #DC2626; font-weight: 700;">Order Cancelled by Restaurant</span>`;
        }

        // 3. Render or display the cancellation alert banner
        let banner = document.getElementById("order-cancellation-banner");
        if (!banner && stepperCard) {
            banner = document.createElement("div");
            banner.id = "order-cancellation-banner";
            banner.className = "order-cancelled-banner";
            banner.innerHTML = `
                
                <div>
                    <div style="font-size: 1.05rem; font-weight: 800;">This Order Has Been Cancelled</div>
                    <div style="font-size: 0.88rem; opacity: 0.9; margin-top: 3px;">
                        The restaurant voided this order. If you paid online via our Sandbox Gateway, your refund will be automatically credited.
                    </div>
                </div>
            `;
            stepperCard.insertAdjacentElement("beforebegin", banner);
        }

        // 4. Dim the stepper to indicate inactivity
        if (stepperCard) {
            stepperCard.style.opacity = "0.4";
            stepperCard.style.filter = "grayscale(80%)";
        }
        updateStepper(null);

        // 5. Update Map descriptions
        document.getElementById("map-status-desc").textContent = "Order cancelled. Courier dispatch halted.";
        document.getElementById("map-distance-info").innerHTML = `<strong style="color: #DC2626;">Dispatch Status: Voided</strong>`;

        if (wsStatusText) wsStatusText.textContent = "Order Inactive";
        if (wsDot) wsDot.style.background = "#64748B";

        return;
    }

    // =========================================================
    // CASE B: ACTIVE / DELIVERED ORDER
    // =========================================================

    // Clean up any cancellation banner if status was refreshed
    const existingBanner = document.getElementById("order-cancellation-banner");
    if (existingBanner) existingBanner.remove();

    if (stepperCard) {
        stepperCard.style.opacity = "1";
        stepperCard.style.filter = "none";
    }

    // Update Top Hero Badge
    if (topBadge) {
        if (status === "DELIVERED") {
            topBadge.textContent = "Delivery Complete";
            topBadge.style.cssText = "background: #DCFCE7; color: #166534; border: 1px solid #86EFAC;";
        } else {
            topBadge.textContent = "Order Live Telemetry";
            topBadge.style.cssText = "";
        }
    }

    // Advance 4-Stage Stepper
    updateStepper(status);

    if (!logistics) return;

    // Update Header ETA text
    if (status === "DELIVERED") {
        headerEta.innerHTML = `<span style="color: #16A34A; font-weight: 700;">Delivered! Enjoy your meal!</span>`;
    } else {
        headerEta.textContent = `~${logistics.estimated_minutes} Minutes (${logistics.distance_km} km away)`;
    }

    // Update Map Subtitle and Distance Footer
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

    // Update Circle Badges
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

    // Update Connecting Progress Bars (line-1, line-2, line-3)
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