# Green Corridor Database Design

## 1. Users Table

Purpose:
Stores login accounts for all system users.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | Primary Key, Auto Increment |
| full_name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| phone | VARCHAR(15) | UNIQUE |
| password_hash | TEXT | NOT NULL |
| role | VARCHAR(30) | NOT NULL |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Allowed Roles:
- admin
- ambulance_operator
- police_officer
- hospital_staff

Password Storage:
Passwords will be stored as secure hashes, never as plain text.

## 2. Ambulances Table

Purpose:
Stores registered ambulance and vehicle information.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | Primary Key, Auto Increment |
| registration_number | VARCHAR(20) | UNIQUE, NOT NULL |
| vehicle_model | VARCHAR(100) | NULL allowed |
| ambulance_type | VARCHAR(30) | NOT NULL |
| current_operator_id | BIGINT | Foreign Key → users.id, NULL allowed |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'available' |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Allowed Statuses:
- available
- on_trip
- maintenance
- offline

Relationship:
- One user can be assigned to an ambulance.
- An ambulance can have one currently assigned operator.
- current_operator_id references users.id.

## 3. Hospitals Table

Purpose:
Stores hospital information, contact details,
availability and geographical location.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | Primary Key, Auto Increment |
| name | VARCHAR(150) | NOT NULL |
| address | TEXT | NOT NULL |
| city | VARCHAR(100) | NOT NULL |
| state | VARCHAR(100) | NOT NULL |
| phone | VARCHAR(15) | NOT NULL |
| email | VARCHAR(255) | NULL allowed |
| location | GEOGRAPHY(POINT, 4326) | NOT NULL |
| available_beds | INTEGER | DEFAULT 0 |
| has_emergency | BOOLEAN | DEFAULT TRUE |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

PostGIS:
- location stores latitude and longitude.
- SRID 4326 represents the WGS84 coordinate system.
- Used for nearby hospital searches.

Relationships:
- A hospital can receive multiple emergency trips.

## 4. Police Stations Table

Purpose:
Stores police station information, contact details
and geographical locations.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | Primary Key, Auto Increment |
| name | VARCHAR(150) | NOT NULL |
| address | TEXT | NOT NULL |
| city | VARCHAR(100) | NOT NULL |
| state | VARCHAR(100) | NOT NULL |
| phone | VARCHAR(15) | NOT NULL |
| email | VARCHAR(255) | NULL allowed |
| location | GEOGRAPHY(POINT, 4326) | NOT NULL |
| jurisdiction_radius | INTEGER | DEFAULT 1000 |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

PostGIS:
- location stores latitude and longitude.
- SRID 4326 represents WGS84.
- Used to identify stations near the ambulance route.

Relationships:
- A police station can receive multiple alerts.
- A police station can be assigned to multiple trips.

## 5. Emergency Requests Table

Purpose:
Stores emergency requests submitted by ambulance operators.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | Primary Key, Auto Increment |
| request_number | VARCHAR(30) | UNIQUE, NOT NULL |
| ambulance_id | BIGINT | FK → ambulances.id, NOT NULL |
| requested_by | BIGINT | FK → users.id, NOT NULL |
| destination_hospital_id | BIGINT | FK → hospitals.id, NOT NULL |
| pickup_location | GEOGRAPHY(POINT, 4326) | NOT NULL |
| emergency_type | VARCHAR(50) | NOT NULL |
| priority | VARCHAR(20) | NOT NULL |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'pending' |
| description | TEXT | NULL allowed |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Allowed Priorities:
- low
- medium
- high
- critical

Allowed Statuses:
- pending
- approved
- processing
- completed
- cancelled

Relationships:
- Many emergency requests can belong to one ambulance.
- Many emergency requests can be submitted by one user.
- Many emergency requests can target one hospital.

## 6. Trips Table

Purpose:
Stores the optimized ambulance journey generated from an emergency request.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | Primary Key, Auto Increment |
| trip_number | VARCHAR(30) | UNIQUE, NOT NULL |
| emergency_request_id | BIGINT | FK → emergency_requests.id, UNIQUE, NOT NULL |
| start_location | GEOGRAPHY(POINT, 4326) | NOT NULL |
| end_location | GEOGRAPHY(POINT, 4326) | NOT NULL |
| route_geometry | GEOGRAPHY(LINESTRING, 4326) | NULL allowed initially |
| total_distance_meters | DOUBLE PRECISION | NULL allowed |
| estimated_duration_seconds | INTEGER | NULL allowed |
| actual_duration_seconds | INTEGER | NULL allowed |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'planned' |
| started_at | TIMESTAMPTZ | NULL allowed |
| completed_at | TIMESTAMPTZ | NULL allowed |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Allowed Statuses:
- planned
- active
- completed
- cancelled

Relationships:
- One emergency request can generate at most one trip.
- Each trip belongs to one emergency request.

Important:
- route_geometry stores the optimized route as a PostGIS LINESTRING.
- Distance is stored in meters.
- Duration is stored in seconds.
- Actual duration can later be used for ETA prediction.

## 7. Trip Stations Table

Purpose:
Connects ambulance trips with police stations along or near the optimized route.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | Primary Key, Auto Increment |
| trip_id | BIGINT | FK → trips.id, NOT NULL |
| police_station_id | BIGINT | FK → police_stations.id, NOT NULL |
| sequence_number | INTEGER | NOT NULL |
| distance_from_start_meters | DOUBLE PRECISION | NULL allowed |
| estimated_arrival_seconds | INTEGER | NULL allowed |
| created_at | TIMESTAMPTZ | NOT NULL |

Constraints:
- UNIQUE(trip_id, police_station_id)
- UNIQUE(trip_id, sequence_number)

Relationships:
- One trip can involve multiple police stations.
- One police station can participate in multiple trips.

Important:
- sequence_number determines the order in which stations appear along the route.
- distance_from_start_meters stores the station's distance from the route starting point.
- estimated_arrival_seconds stores the estimated time until ambulance arrival.

## 8. Station Alerts Table

Purpose:
Stores notifications generated for police stations about approaching ambulances.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | Primary Key, Auto Increment |
| trip_station_id | BIGINT | FK → trip_stations.id, NOT NULL |
| alert_message | TEXT | NOT NULL |
| ambulance_latitude | DOUBLE PRECISION | NULL allowed |
| ambulance_longitude | DOUBLE PRECISION | NULL allowed |
| ambulance_speed | DOUBLE PRECISION | NULL allowed |
| estimated_arrival_seconds | INTEGER | NULL allowed |
| delivery_status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' |
| sent_at | TIMESTAMPTZ | NULL allowed |
| created_at | TIMESTAMPTZ | NOT NULL |

Allowed Delivery Statuses:
- pending
- sent
- failed

Relationships:
- One trip-station association can generate multiple alerts.
- Each alert belongs to one trip-station association.

Important:
- An alert can be regenerated when the ambulance's ETA or location changes.
- 'sent' means successfully dispatched, not acknowledged by a police officer.

## 9. Location Updates Table

Purpose:
Stores periodic GPS location and speed updates for ambulances during trips.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | Primary Key, Auto Increment |
| trip_id | BIGINT | FK → trips.id, NOT NULL |
| location | GEOGRAPHY(POINT, 4326) | NOT NULL |
| speed_kmh | DOUBLE PRECISION | NULL allowed |
| recorded_at | TIMESTAMPTZ | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |

Relationships:
- One trip can have thousands of location updates.
- Each location update belongs to one trip.

Important:
- PostGIS stores coordinates as POINT(longitude latitude).
- speed_kmh is measured in kilometres per hour.
- recorded_at represents when the GPS reading was captured.
- Location updates will power live ambulance tracking.

## 10. Route Updates Table

Purpose:
Maintains the history of optimized route changes during an ambulance trip.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | Primary Key, Auto Increment |
| trip_id | BIGINT | FK → trips.id, NOT NULL |
| route_geometry | GEOGRAPHY(LINESTRING, 4326) | NOT NULL |
| distance_meters | DOUBLE PRECISION | NULL allowed |
| estimated_duration_seconds | INTEGER | NULL allowed |
| change_reason | TEXT | NULL allowed |
| version_number | INTEGER | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |

Constraints:
- UNIQUE(trip_id, version_number)

Relationships:
- One trip can have multiple route updates.
- Each route update belongs to one trip.

Important:
- trips stores the current route.
- route_updates stores previous and revised route versions.
- version_number increases whenever a new route is generated.

## 11. Alert Acknowledgments Table

Purpose:
Tracks police officers' responses to alerts sent by the backend.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | Primary Key, Auto Increment |
| station_alert_id | BIGINT | FK → station_alerts.id, NOT NULL |
| acknowledged_by | BIGINT | FK → users.id, NOT NULL |
| acknowledgment_status | VARCHAR(30) | NOT NULL |
| remarks | TEXT | NULL allowed |
| acknowledged_at | TIMESTAMPTZ | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |

Allowed Statuses:
- acknowledged
- action_started
- unable_to_respond

Relationships:
- One station alert can receive multiple acknowledgment records.
- Each acknowledgment belongs to one police officer.
- Each acknowledgment refers to one station alert.

Important:
- This table tracks officer responses, not notification delivery.
- station_alerts.delivery_status tracks whether the notification was sent.
- acknowledged_at records when the officer responded.

## 12. Database-wide Design Rules

1. All primary keys use BIGINT.
2. Foreign keys must reference valid records.
3. created_at defaults to CURRENT_TIMESTAMP.
4. updated_at defaults to CURRENT_TIMESTAMP and is
   updated whenever a record changes.
5. Geographical columns use SRID 4326.
6. Spatial columns should have GiST indexes.
7. Frequently queried foreign keys should have indexes.
8. Status and priority columns should use CHECK constraints.
9. Passwords must always be stored as secure hashes.
10. Database credentials must remain in the .env file.