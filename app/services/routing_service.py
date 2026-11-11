import requests
from fastapi import HTTPException

# Public OSRM routing server (free, no API key required)
OSRM_BASE_URL = "http://router.project-osrm.org"

def get_route_from_osrm(start_lon: float, start_lat: float, end_lon: float, end_lat: float):
    """
    Fetches route geometry, distance, and duration between two GPS coordinates using OSRM.
    Coordinates format: [longitude, latitude]
    """
    url = f"{OSRM_BASE_URL}/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("code") != "Ok":
            raise HTTPException(status_code=400, detail="Could not calculate route from OSRM.")
            
        route = data["routes"][0]
        return {
            "distance_meters": route["distance"],          # Total distance in meters
            "duration_seconds": route["duration"],        # Estimated travel time in seconds
            "geometry": route["geometry"]                 # GeoJSON coordinates for map visualization
        }
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Routing service unavailable.")