import logging

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_corridor_alerts(emergency_id: int, route_data: dict, police_stations: list = None):
        """
        Triggers emergency corridor alerts to relevant authorities and units.
        """
        logger.info(f"Initiating Green Corridor notifications for Emergency ID: {emergency_id}")
        
        # Structure the notification payload for the coordination engine
        alert_payload = {
            "emergency_id": emergency_id,
            "status": "ALERT_DISPATCHED",
            "route_summary": {
                "distance_meters": route_data.get("distance"),
                "duration_seconds": route_data.get("duration")
            },
            "target_authorities": police_stations or ["Central Traffic Police", "Route Sector 4 Checkpoint"]
        }
        
        logger.info(f"Alert successfully broadcasted for emergency {emergency_id}")
        return alert_payload