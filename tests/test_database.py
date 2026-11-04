from app.database.session import SessionLocal
from app.models import User
from sqlalchemy import text
from app.models import Ambulance
from app.models import Hospital
from app.models import EmergencyRequest
from app.models import Trip
from app.models import PoliceStation
from app.models import TripStation
from app.models import StationAlert
from app.models import AlertAcknowledgment
from sqlalchemy import func



def test_acknowledgment_insert():

    db = SessionLocal()

    try:
        existing_ack = db.query(AlertAcknowledgment).filter(
            AlertAcknowledgment.station_alert_id == 1,
            AlertAcknowledgment.acknowledged_by == 1
        ).first()

        if existing_ack:
            print("\nTest acknowledgment already exists!")
            print("Acknowledgment ID:", existing_ack.id)
            return

        acknowledgment = AlertAcknowledgment(
            station_alert_id=1,
            acknowledged_by=1,
            acknowledgment_status="acknowledged",
            remarks="Police station received the ambulance alert.",
            acknowledged_at=func.now()
        )

        db.add(acknowledgment)
        db.commit()
        db.refresh(acknowledgment)

        print("\nAcknowledgment inserted successfully!")
        print("Acknowledgment ID:", acknowledgment.id)
        print("Alert ID:", acknowledgment.station_alert_id)
        print("Officer/User ID:", acknowledgment.acknowledged_by)
        print("Status:", acknowledgment.acknowledgment_status)

    except Exception as error:
        db.rollback()
        print("Acknowledgment insertion failed:", error)
        raise

    finally:
        db.close()

def test_station_alert_insert():

    db = SessionLocal()

    try:
        existing_alert = db.query(StationAlert).filter(
            StationAlert.trip_station_id == 1
        ).first()

        if existing_alert:
            print("\nTest station alert already exists!")
            print("Alert ID:", existing_alert.id)
            return

        alert = StationAlert(
            trip_station_id=1,
            alert_message="Emergency ambulance approaching. Prepare traffic clearance.",
            ambulance_latitude=12.9600,
            ambulance_longitude=77.5800,
            ambulance_speed=60.0,
            eta_seconds=120,
            delivery_status="pending"
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)

        print("\nStation alert inserted successfully!")
        print("Alert ID:", alert.id)
        print("Trip Station ID:", alert.trip_station_id)
        print("Ambulance Speed:", alert.ambulance_speed)
        print("ETA:", alert.eta_seconds)
        print("Delivery Status:", alert.delivery_status)

    except Exception as error:
        db.rollback()
        print("Station alert insertion failed:", error)
        raise

    finally:
        db.close()

def test_trip_station_insert():

    db = SessionLocal()

    try:
        existing_record = db.query(TripStation).filter(
            TripStation.trip_id == 1,
            TripStation.police_station_id == 1
        ).first()

        if existing_record:
            print("\nTrip-station link already exists!")
            print("Record ID:", existing_record.id)
            return

        trip_station = TripStation(
            trip_id=1,
            police_station_id=1,
            sequence_number=1,
            distance_from_start_meters=800,
            estimated_arrival_seconds=120
        )

        db.add(trip_station)
        db.commit()
        db.refresh(trip_station)

        print("\nTrip-station link created successfully!")
        print("Record ID:", trip_station.id)
        print("Trip ID:", trip_station.trip_id)
        print("Police Station ID:", trip_station.police_station_id)
        print("Sequence:", trip_station.sequence_number)
        print("Distance:", trip_station.distance_from_start_meters)

    except Exception as error:
        db.rollback()
        print("Trip-station insertion failed:", error)
        raise

    finally:
        db.close()

def test_user_insert():

    db = SessionLocal()

    try:
        existing_user = db.query(User).filter(
            User.email == "testadmin@greencorridor.com"
        ).first()

        if existing_user:
            print("\nTest user already exists!")
            print("User ID:", existing_user.id)
            return

        user = User(
            full_name="Test Admin",
            email="testadmin@greencorridor.com",
            phone="9999999999",
            password_hash="dummy_test_hash",
            role="admin",
            is_active=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print("\nUser inserted successfully!")
        print("User ID:", user.id)

    except Exception as error:
        db.rollback()
        print("Database test failed:", error)
        raise

    finally:
        db.close()


def test_user_retrieval():

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.email == "testadmin@greencorridor.com"
        ).first()

        if user:
            print("\nUser retrieved successfully!")
            print("ID:", user.id)
            print("Name:", user.full_name)
            print("Role:", user.role)
        else:
            print("User not found!")

    finally:
        db.close()

def test_user_relationship():

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.email == "testadmin@greencorridor.com"
        ).first()

        if user:
            print("\nUser relationship test successful!")
            print("User:", user.full_name)
            print("Operated ambulances:", len(user.operated_ambulances))
            print("Emergency requests:", len(user.emergency_requests))
            print("Alert acknowledgments:", len(user.alert_acknowledgments))

    finally:
        db.close()
def test_postgis():

    db = SessionLocal()

    try:
        result = db.execute(
            text("""
                SELECT
                    ST_AsText(
                        ST_SetSRID(
                            ST_MakePoint(77.5946, 12.9716),
                            4326
                        )
                    ),
                    ST_SRID(
                        ST_SetSRID(
                            ST_MakePoint(77.5946, 12.9716),
                            4326
                        )
                    );
            """)
        )

        row = result.fetchone()

        print("\nPostGIS test successful!")
        print("Location:", row[0])
        print("SRID:", row[1])

    finally:
        db.close()

def test_ambulance_insert():

    db = SessionLocal()

    try:
        existing_ambulance = db.query(Ambulance).filter(
            Ambulance.registration_number == "GC-TEST-001"
        ).first()

        if existing_ambulance:
            print("\nTest ambulance already exists!")
            print("Ambulance ID:", existing_ambulance.id)
            return

        ambulance = Ambulance(
            registration_number="GC-TEST-001",
            vehicle_model="Toyota HiAce",
            ambulance_type="Advanced Life Support",
            current_operator_id=1,
            status="available",
            is_active=True
        )

        db.add(ambulance)
        db.commit()
        db.refresh(ambulance)

        print("\nAmbulance inserted successfully!")
        print("Ambulance ID:", ambulance.id)
        print("Registration:", ambulance.registration_number)
        print("Operator ID:", ambulance.current_operator_id)

    except Exception as error:
        db.rollback()
        print("Ambulance insertion failed:", error)
        raise

    finally:
        db.close()

def test_ambulance_relationship():

    db = SessionLocal()

    try:
        ambulance = db.query(Ambulance).filter(
            Ambulance.registration_number == "GC-TEST-001"
        ).first()

        if ambulance:
            print("\nAmbulance relationship test successful!")
            print("Registration:", ambulance.registration_number)
            print("Operator:", ambulance.current_operator.full_name)

    finally:
        db.close()
def test_hospital_insert():

    db = SessionLocal()

    try:
        existing_hospital = db.query(Hospital).filter(
            Hospital.name == "Green Corridor Test Hospital"
        ).first()

        if existing_hospital:
            print("\nTest hospital already exists!")
            print("Hospital ID:", existing_hospital.id)
            return

        hospital = Hospital(
            name="Green Corridor Test Hospital",
            address="MG Road, Bengaluru",
            city="Bengaluru",
            state="Karnataka",
            phone="8888888888",
            email="hospital@greencorridor.com",
            location="SRID=4326;POINT(77.5946 12.9716)",
            available_beds=50,
            has_emergency=True,
            is_active=True
        )

        db.add(hospital)
        db.commit()
        db.refresh(hospital)

        print("\nHospital inserted successfully!")
        print("Hospital ID:", hospital.id)
        print("Hospital Name:", hospital.name)
        print("Available Beds:", hospital.available_beds)

    except Exception as error:
        db.rollback()
        print("Hospital insertion failed:", error)
        raise

    finally:
        db.close()

def test_hospital_relationship():

    db = SessionLocal()

    try:
        hospital = db.query(Hospital).filter(
            Hospital.name == "Green Corridor Test Hospital"
        ).first()

        if hospital:
            print("\nHospital relationship test successful!")
            print("Hospital:", hospital.name)
            print("Emergency requests:", len(hospital.emergency_requests))

    finally:
        db.close()

def test_emergency_request_insert():

    db = SessionLocal()

    try:
        existing_request = db.query(EmergencyRequest).filter(
            EmergencyRequest.request_number == "GC-REQ-001"
        ).first()

        if existing_request:
            print("\nTest emergency request already exists!")
            print("Request ID:", existing_request.id)
            return

        emergency_request = EmergencyRequest(
            request_number="GC-REQ-001",
            ambulance_id=1,
            requested_by=1,
            destination_hospital_id=1,
            pickup_location="SRID=4326;POINT(77.5800 12.9600)",
            emergency_type="Cardiac Emergency",
            priority="critical",
            status="approved",
            description="Sample emergency request for database testing"
        )

        db.add(emergency_request)
        db.commit()
        db.refresh(emergency_request)

        print("\nEmergency request inserted successfully!")
        print("Request ID:", emergency_request.id)
        print("Request Number:", emergency_request.request_number)
        print("Ambulance ID:", emergency_request.ambulance_id)
        print("Hospital ID:", emergency_request.destination_hospital_id)

    except Exception as error:
        db.rollback()
        print("Emergency request insertion failed:", error)
        raise

    finally:
        db.close()

def test_emergency_request_relationship():

    db = SessionLocal()

    try:
        request = db.query(EmergencyRequest).filter(
            EmergencyRequest.request_number == "GC-REQ-001"
        ).first()

        if request:
            print("\nEmergency request relationship test successful!")
            print("Request:", request.request_number)
            print("Ambulance:", request.ambulance.registration_number)
            print("Requester:", request.requester.full_name)
            print("Hospital:", request.destination_hospital.name)
            print("Trip exists:", request.trip is not None)

    finally:
        db.close()

def test_trip_insert():

    db = SessionLocal()

    try:
        existing_trip = db.query(Trip).filter(
            Trip.trip_number == "GC-TRIP-001"
        ).first()

        if existing_trip:
            print("\nTest trip already exists!")
            print("Trip ID:", existing_trip.id)
            return

        trip = Trip(
            trip_number="GC-TRIP-001",
            emergency_request_id=1,
            start_location="SRID=4326;POINT(77.5800 12.9600)",
            end_location="SRID=4326;POINT(77.5946 12.9716)",
            total_distance_meters=2500,
            estimated_duration_seconds=600,
            status="planned"
        )

        db.add(trip)
        db.commit()
        db.refresh(trip)

        print("\nTrip inserted successfully!")
        print("Trip ID:", trip.id)
        print("Trip Number:", trip.trip_number)
        print("Emergency Request ID:", trip.emergency_request_id)
        print("Trip Status:", trip.status)

    except Exception as error:
        db.rollback()
        print("Trip insertion failed:", error)
        raise

    finally:
        db.close()

def test_trip_relationship():

    db = SessionLocal()

    try:
        trip = db.query(Trip).filter(
            Trip.trip_number == "GC-TRIP-001"
        ).first()

        if trip:
            print("\nTrip relationship test successful!")
            print("Trip:", trip.trip_number)
            print("Emergency Request:", trip.emergency_request.request_number)
            print("Ambulance:", trip.emergency_request.ambulance.registration_number)
            print("Hospital:", trip.emergency_request.destination_hospital.name)

            print(
                "Reverse relationship:",
                trip.emergency_request.trip.trip_number
            )

    finally:
        db.close()

def test_police_station_insert():

    db = SessionLocal()

    try:
        existing_station = db.query(PoliceStation).filter(
            PoliceStation.name == "Green Corridor Test Police Station"
        ).first()

        if existing_station:
            print("\nTest police station already exists!")
            print("Police Station ID:", existing_station.id)
            return

        station = PoliceStation(
            name="Green Corridor Test Police Station",
            address="MG Road, Bengaluru",
            city="Bengaluru",
            state="Karnataka",
            phone="7777777777",
            email="police@greencorridor.com",
            location="SRID=4326;POINT(77.5850 12.9650)",
            jurisdiction_radius=1000,
            is_active=True
        )

        db.add(station)
        db.commit()
        db.refresh(station)

        print("\nPolice station inserted successfully!")
        print("Police Station ID:", station.id)
        print("Station Name:", station.name)
        print("Jurisdiction Radius:", station.jurisdiction_radius)

    except Exception as error:
        db.rollback()
        print("Police station insertion failed:", error)
        raise

    finally:
        db.close()
def test_police_station_relationship():

    db = SessionLocal()

    try:
        station = db.query(PoliceStation).filter(
            PoliceStation.name == "Green Corridor Test Police Station"
        ).first()

        if station:
            print("\nPolice station relationship test successful!")
            print("Station:", station.name)
            print("Associated trips:", len(station.trip_stations))

    finally:
        db.close()

def test_trip_station_relationship():

    db = SessionLocal()

    try:
        record = db.query(TripStation).filter(
            TripStation.trip_id == 1,
            TripStation.police_station_id == 1
        ).first()

        if record:
            print("\nTripStation relationship test successful!")
            print("Trip:", record.trip.trip_number)
            print("Police Station:", record.police_station.name)
            print("Station sequence:", record.sequence_number)

    finally:
        db.close()

def test_station_alert_relationship():

    db = SessionLocal()

    try:
        alert = db.query(StationAlert).filter(
            StationAlert.id == 1
        ).first()

        if alert:
            print("\nStation alert relationship test successful!")
            print("Alert ID:", alert.id)
            print("Trip:", alert.trip_station.trip.trip_number)
            print("Police Station:", alert.trip_station.police_station.name)
            print("Acknowledgments:", len(alert.acknowledgments))

    finally:
        db.close()

def test_acknowledgment_relationship():

    db = SessionLocal()

    try:
        acknowledgment = db.query(AlertAcknowledgment).filter(
            AlertAcknowledgment.id == 1
        ).first()

        if acknowledgment:
            print("\nAcknowledgment relationship test successful!")
            print("Acknowledgment ID:", acknowledgment.id)
            print("Alert ID:", acknowledgment.station_alert.id)
            print("Acknowledged by:", acknowledgment.acknowledged_user.full_name)
            print("Status:", acknowledgment.acknowledgment_status)

    finally:
        db.close()
if __name__ == "__main__":
    test_user_insert()
    test_user_retrieval()
    test_user_relationship()
    test_postgis()
    test_ambulance_insert()
    test_ambulance_relationship()
    test_hospital_insert()
    test_hospital_relationship()
    test_emergency_request_insert()
    test_emergency_request_relationship()
    test_trip_insert()
    test_trip_relationship()
    test_police_station_insert()
    test_police_station_relationship()
    test_trip_station_insert()
    test_trip_station_relationship()
    test_station_alert_insert()
    test_station_alert_relationship()
    test_acknowledgment_insert()
    test_acknowledgment_relationship()