"""
Logistics & Spatial Calculation Engine
Location: backend/app/logistics.py

Implements:
1. Haversine spherical trigonometric formula for real-world GPS distance calculation.
2. Dynamic Estimated Time of Arrival (ETA) based on order status and transit speed.
3. Coordinate geocoding simulation for customer delivery addresses.
"""

import math
import hashlib
from typing import Dict, Any, Tuple

# Earth's mean radius in kilometers
EARTH_RADIUS_KM = 6371.0

# Fixed GPS coordinates for FoodExpress Restaurant Kitchen
# Example: Central Bengaluru / Downtown Tech Hub
RESTAURANT_LAT = 12.9716
RESTAURANT_LON = 77.5946

# Average city delivery bike speed in km/h
AVERAGE_BIKE_SPEED_KMH = 25.0

# Base kitchen preparation time in minutes
BASE_COOKING_TIME_MINS = 15.0

# Fixed buffer for doorstep delivery, elevator, and traffic lights
TRAFFIC_BUFFER_MINS = 4.0


# =============================================================
# 1. HAVERSINE SPHERICAL DISTANCE CALCULATION
# =============================================================

def calculate_haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculates the great-circle distance between two GPS points on Earth in kilometers.
    Uses spherical trigonometry to account for Earth's curvature.
    """
    # Convert decimal degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))

    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance_km = EARTH_RADIUS_KM * c

    return round(distance_km, 2)


# =============================================================
# 2. ADDRESS TO GPS COORDINATE SIMULATOR
# =============================================================

def get_coordinates_for_address(address: str) -> Tuple[float, float]:
    """
    Deterministic Coordinate Generator for Sandbox / Demo:
    Uses a hash of the customer's address string to generate realistic,
    consistent GPS coordinates within a 2 to 8 km radius of the restaurant.
    """
    # Hash the address text into a repeatable integer
    addr_hash = int(hashlib.md5(address.lower().strip().encode("utf-8")).hexdigest(), 16)

    # Generate slight offsets around the restaurant (between ~0.02 and ~0.06 degrees)
    lat_offset = ((addr_hash % 60) - 30) / 1000.0
    lon_offset = (((addr_hash >> 8) % 60) - 30) / 1000.0

    customer_lat = round(RESTAURANT_LAT + lat_offset, 6)
    customer_lon = round(RESTAURANT_LON + lon_offset, 6)

    return customer_lat, customer_lon


# =============================================================
# 3. DYNAMIC ESTIMATED TIME OF ARRIVAL (ETA)
# =============================================================

def calculate_delivery_eta(
    order_status: str,
    distance_km: float
) -> Dict[str, Any]:
    """
    Dynamically computes delivery ETA and transit metrics based on order lifecycle:
    - PENDING: Cooking Time + Travel Time + Buffer
    - PREPARING: Half Cooking Time + Travel Time + Buffer
    - OUT_FOR_DELIVERY: Travel Time + Buffer (Food is already on the bike!)
    - DELIVERED: 0 mins (Order completed)
    - CANCELLED: 0 mins (Order voided)
    """
    # Transit time: (distance / speed) * 60 minutes
    transit_time_mins = (distance_km / AVERAGE_BIKE_SPEED_KMH) * 60.0

    if order_status == "PENDING":
        eta_mins = BASE_COOKING_TIME_MINS + transit_time_mins + TRAFFIC_BUFFER_MINS
        message = "Order received. Kitchen will begin preparation shortly."
    elif order_status == "PREPARING":
        eta_mins = (BASE_COOKING_TIME_MINS / 2.0) + transit_time_mins + TRAFFIC_BUFFER_MINS
        message = "Chef is currently cooking your food hot and fresh."
    elif order_status == "OUT_FOR_DELIVERY":
        eta_mins = transit_time_mins + (TRAFFIC_BUFFER_MINS / 2.0)
        message = "Driver has picked up your food and is on the way!"
    elif order_status == "DELIVERED":
        eta_mins = 0.0
        message = "Order delivered. Enjoy your meal!"
    elif order_status == "CANCELLED":
        eta_mins = 0.0
        message = "This order has been cancelled."
    else:
        eta_mins = transit_time_mins + BASE_COOKING_TIME_MINS
        message = "Processing order."

    rounded_eta = max(int(round(eta_mins)), 0)

    return {
        "distance_km": distance_km,
        "estimated_minutes": rounded_eta,
        "status": order_status,
        "status_message": message,
        "restaurant_coordinates": {
            "lat": RESTAURANT_LAT,
            "lon": RESTAURANT_LON
        }
    }


def compute_order_logistics(order_status: str, delivery_address: str) -> Dict[str, Any]:
    """
    Main Entry Point: Combines geocoding, Haversine distance, and ETA calculations.
    """
    cust_lat, cust_lon = get_coordinates_for_address(delivery_address)
    distance_km = calculate_haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, cust_lat, cust_lon)

    eta_data = calculate_delivery_eta(order_status, distance_km)
    eta_data["customer_coordinates"] = {
        "lat": cust_lat,
        "lon": cust_lon
    }

    return eta_data