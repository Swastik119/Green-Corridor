"""add performance indexes

Revision ID: f5c0c32657ac
Revises: 7722d3f4e2ac
Create Date: 2026-11-04 19:42:10.200443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5c0c32657ac'
down_revision: Union[str, Sequence[str], None] = '7722d3f4e2ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alert acknowledgment indexes
    op.create_index(
        'idx_alert_acknowledgments_acknowledged_by',
        'alert_acknowledgments', ['acknowledged_by'], unique=False
    )
    op.create_index(
        'idx_alert_acknowledgments_station_alert_id',
        'alert_acknowledgments', ['station_alert_id'], unique=False
    )

    # Ambulance indexes
    op.create_index(
        'idx_ambulances_current_operator_id',
        'ambulances', ['current_operator_id'], unique=False
    )
    op.create_index(
        'idx_ambulances_status',
        'ambulances', ['status'], unique=False
    )

    # Emergency request indexes
    op.create_index(
        'idx_emergency_requests_ambulance_id',
        'emergency_requests', ['ambulance_id'], unique=False
    )
    op.create_index(
        'idx_emergency_requests_destination_hospital_id',
        'emergency_requests', ['destination_hospital_id'], unique=False
    )
    op.create_index(
        'idx_emergency_requests_priority',
        'emergency_requests', ['priority'], unique=False
    )
    op.create_index(
        'idx_emergency_requests_requested_by',
        'emergency_requests', ['requested_by'], unique=False
    )
    op.create_index(
        'idx_emergency_requests_status',
        'emergency_requests', ['status'], unique=False
    )

    # Hospital indexes
    op.create_index(
        'idx_hospitals_city', 'hospitals', ['city'], unique=False
    )
    op.create_index(
        'idx_hospitals_is_active', 'hospitals', ['is_active'], unique=False
    )

    # Location update index
    op.create_index(
        'idx_location_updates_trip_id',
        'location_updates', ['trip_id'], unique=False
    )

    # Police station indexes
    op.create_index(
        'idx_police_stations_city',
        'police_stations', ['city'], unique=False
    )
    op.create_index(
        'idx_police_stations_is_active',
        'police_stations', ['is_active'], unique=False
    )

    # Route update index
    op.create_index(
        'idx_route_updates_trip_id',
        'route_updates', ['trip_id'], unique=False
    )

    # Station alert indexes
    op.create_index(
        'idx_station_alerts_delivery_status',
        'station_alerts', ['delivery_status'], unique=False
    )
    op.create_index(
        'idx_station_alerts_trip_station_id',
        'station_alerts', ['trip_station_id'], unique=False
    )

    # Trip station index
    op.create_index(
        'idx_trip_stations_police_station_id',
        'trip_stations', ['police_station_id'], unique=False
    )

    # Trip indexes
    op.create_index(
        'idx_trips_started_at', 'trips', ['started_at'], unique=False
    )
    op.create_index(
        'idx_trips_status', 'trips', ['status'], unique=False
    )

    # User indexes
    op.create_index(
        'idx_users_is_active', 'users', ['is_active'], unique=False
    )
    op.create_index(
        'idx_users_role', 'users', ['role'], unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_is_active', table_name='users')

    op.drop_index('idx_trips_status', table_name='trips')
    op.drop_index('idx_trips_started_at', table_name='trips')

    op.drop_index(
        'idx_trip_stations_police_station_id',
        table_name='trip_stations'
    )

    op.drop_index(
        'idx_station_alerts_trip_station_id',
        table_name='station_alerts'
    )
    op.drop_index(
        'idx_station_alerts_delivery_status',
        table_name='station_alerts'
    )

    op.drop_index(
        'idx_route_updates_trip_id',
        table_name='route_updates'
    )

    op.drop_index(
        'idx_police_stations_is_active',
        table_name='police_stations'
    )
    op.drop_index(
        'idx_police_stations_city',
        table_name='police_stations'
    )

    op.drop_index(
        'idx_location_updates_trip_id',
        table_name='location_updates'
    )

    op.drop_index(
        'idx_hospitals_is_active',
        table_name='hospitals'
    )
    op.drop_index(
        'idx_hospitals_city',
        table_name='hospitals'
    )

    op.drop_index(
        'idx_emergency_requests_status',
        table_name='emergency_requests'
    )
    op.drop_index(
        'idx_emergency_requests_requested_by',
        table_name='emergency_requests'
    )
    op.drop_index(
        'idx_emergency_requests_priority',
        table_name='emergency_requests'
    )
    op.drop_index(
        'idx_emergency_requests_destination_hospital_id',
        table_name='emergency_requests'
    )
    op.drop_index(
        'idx_emergency_requests_ambulance_id',
        table_name='emergency_requests'
    )

    op.drop_index(
        'idx_ambulances_status',
        table_name='ambulances'
    )
    op.drop_index(
        'idx_ambulances_current_operator_id',
        table_name='ambulances'
    )

    op.drop_index(
        'idx_alert_acknowledgments_station_alert_id',
        table_name='alert_acknowledgments'
    )
    op.drop_index(
        'idx_alert_acknowledgments_acknowledged_by',
        table_name='alert_acknowledgments'
    )
