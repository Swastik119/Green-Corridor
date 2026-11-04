
"""create initial database tables

Revision ID: 6016499e7992
Revises:
Create Date: 2026-11-04 16:30:25.464445

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '6016499e7992'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        'hospitals',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=15), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column(
            'location',
            geoalchemy2.types.Geography(
                geometry_type='POINT',
                srid=4326,
                dimension=2,
                from_text='ST_GeogFromText',
                name='geography',
                nullable=False
            ),
            nullable=False
        ),
        sa.Column('available_beds', sa.Integer(), nullable=False),
        sa.Column('has_emergency', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'police_stations',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=15), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column(
            'location',
            geoalchemy2.types.Geography(
                geometry_type='POINT',
                srid=4326,
                dimension=2,
                from_text='ST_GeogFromText',
                name='geography',
                nullable=False
            ),
            nullable=False
        ),
        sa.Column('jurisdiction_radius', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=15), nullable=True),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('role', sa.String(length=30), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('phone')
    )

    op.create_table(
        'ambulances',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('registration_number', sa.String(length=20), nullable=False),
        sa.Column('vehicle_model', sa.String(length=100), nullable=True),
        sa.Column('ambulance_type', sa.String(length=30), nullable=False),
        sa.Column('current_operator_id', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['current_operator_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('registration_number')
    )

    op.create_table(
        'emergency_requests',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('request_number', sa.String(length=30), nullable=False),
        sa.Column('ambulance_id', sa.BigInteger(), nullable=False),
        sa.Column('requested_by', sa.BigInteger(), nullable=False),
        sa.Column('destination_hospital_id', sa.BigInteger(), nullable=False),
        sa.Column(
            'pickup_location',
            geoalchemy2.types.Geography(
                geometry_type='POINT',
                srid=4326,
                dimension=2,
                from_text='ST_GeogFromText',
                name='geography',
                nullable=False
            ),
            nullable=False
        ),
        sa.Column('emergency_type', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['ambulance_id'], ['ambulances.id']),
        sa.ForeignKeyConstraint(
            ['destination_hospital_id'],
            ['hospitals.id']
        ),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_number')
    )

    op.create_table(
        'trips',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('trip_number', sa.String(length=30), nullable=False),
        sa.Column('emergency_request_id', sa.BigInteger(), nullable=False),
        sa.Column(
            'start_location',
            geoalchemy2.types.Geography(
                geometry_type='POINT',
                srid=4326,
                dimension=2,
                from_text='ST_GeogFromText',
                name='geography',
                nullable=False
            ),
            nullable=False
        ),
        sa.Column(
            'end_location',
            geoalchemy2.types.Geography(
                geometry_type='POINT',
                srid=4326,
                dimension=2,
                from_text='ST_GeogFromText',
                name='geography',
                nullable=False
            ),
            nullable=False
        ),
        sa.Column(
            'route_geometry',
            geoalchemy2.types.Geography(
                geometry_type='LINESTRING',
                srid=4326,
                dimension=2,
                from_text='ST_GeogFromText',
                name='geography'
            ),
            nullable=True
        ),
        sa.Column('total_distance_meters', sa.Float(), nullable=True),
        sa.Column('estimated_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('actual_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['emergency_request_id'],
            ['emergency_requests.id']
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('emergency_request_id'),
        sa.UniqueConstraint('trip_number')
    )

    op.create_table(
        'location_updates',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('trip_id', sa.BigInteger(), nullable=False),
        sa.Column(
            'location',
            geoalchemy2.types.Geography(
                geometry_type='POINT',
                srid=4326,
                dimension=2,
                from_text='ST_GeogFromText',
                name='geography',
                nullable=False
            ),
            nullable=False
        ),
        sa.Column('speed_kmh', sa.Float(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'route_updates',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('trip_id', sa.BigInteger(), nullable=False),
        sa.Column(
            'route_geometry',
            geoalchemy2.types.Geography(
                geometry_type='LINESTRING',
                srid=4326,
                dimension=2,
                from_text='ST_GeogFromText',
                name='geography',
                nullable=False
            ),
            nullable=False
        ),
        sa.Column('distance_meters', sa.Float(), nullable=False),
        sa.Column(
            'estimated_duration_seconds',
            sa.Integer(),
            nullable=False
        ),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trip_id', 'version_number')
    )

    op.create_table(
        'trip_stations',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('trip_id', sa.BigInteger(), nullable=False),
        sa.Column('police_station_id', sa.BigInteger(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('distance_from_start_meters', sa.Float(), nullable=False),
        sa.Column('estimated_arrival_seconds', sa.Integer(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['police_station_id'], ['police_stations.id']),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trip_id', 'police_station_id'),
        sa.UniqueConstraint('trip_id', 'sequence_number')
    )

    op.create_table(
        'station_alerts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('trip_station_id', sa.BigInteger(), nullable=False),
        sa.Column('alert_message', sa.Text(), nullable=False),
        sa.Column('ambulance_latitude', sa.Float(), nullable=False),
        sa.Column('ambulance_longitude', sa.Float(), nullable=False),
        sa.Column('ambulance_speed', sa.Float(), nullable=False),
        sa.Column('eta_seconds', sa.Integer(), nullable=False),
        sa.Column('delivery_status', sa.String(length=20), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['trip_station_id'], ['trip_stations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'alert_acknowledgments',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('station_alert_id', sa.BigInteger(), nullable=False),
        sa.Column('acknowledged_by', sa.BigInteger(), nullable=False),
        sa.Column('acknowledgment_status', sa.String(length=30), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id']),
        sa.ForeignKeyConstraint(['station_alert_id'], ['station_alerts.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table('alert_acknowledgments')
    op.drop_table('station_alerts')
    op.drop_table('trip_stations')
    op.drop_table('route_updates')
    op.drop_table('location_updates')
    op.drop_table('trips')
    op.drop_table('emergency_requests')
    op.drop_table('ambulances')
    op.drop_table('users')
    op.drop_table('police_stations')
    op.drop_table('hospitals')
