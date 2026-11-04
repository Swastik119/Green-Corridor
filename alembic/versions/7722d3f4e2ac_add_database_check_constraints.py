
"""add database check constraints

Revision ID: 7722d3f4e2ac
Revises: 6016499e7992
"""

from typing import Sequence, Union

from alembic import op


revision: str = '7722d3f4e2ac'
down_revision: Union[str, Sequence[str], None] = '6016499e7992'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # 1. User role validation
    op.create_check_constraint(
        'check_user_role',
        'users',
        "role IN ('admin', 'ambulance_operator', 'police_officer', 'hospital_staff')"
    )

    # 2. Ambulance status validation
    op.create_check_constraint(
        'check_ambulance_status',
        'ambulances',
        "status IN ('available', 'on_trip', 'maintenance', 'offline')"
    )

    # 3. Emergency priority validation
    op.create_check_constraint(
        'check_emergency_priority',
        'emergency_requests',
        "priority IN ('low', 'medium', 'high', 'critical')"
    )

    # 4. Emergency request status validation
    op.create_check_constraint(
        'check_emergency_status',
        'emergency_requests',
        "status IN ('pending', 'approved', 'active', 'completed', 'cancelled')"
    )

    # 5. Trip status validation
    op.create_check_constraint(
        'check_trip_status',
        'trips',
        "status IN ('planned', 'active', 'completed', 'cancelled')"
    )

    # 6. Station alert delivery status validation
    op.create_check_constraint(
        'check_alert_delivery_status',
        'station_alerts',
        "delivery_status IN ('pending', 'sent', 'failed')"
    )

    # 7. Alert acknowledgment status validation
    op.create_check_constraint(
        'check_acknowledgment_status',
        'alert_acknowledgments',
        "acknowledgment_status IN ('acknowledged', 'action_started', 'unable_to_respond')"
    )


def downgrade() -> None:

    op.drop_constraint(
        'check_acknowledgment_status',
        'alert_acknowledgments',
        type_='check'
    )

    op.drop_constraint(
        'check_alert_delivery_status',
        'station_alerts',
        type_='check'
    )

    op.drop_constraint(
        'check_trip_status',
        'trips',
        type_='check'
    )

    op.drop_constraint(
        'check_emergency_status',
        'emergency_requests',
        type_='check'
    )

    op.drop_constraint(
        'check_emergency_priority',
        'emergency_requests',
        type_='check'
    )

    op.drop_constraint(
        'check_ambulance_status',
        'ambulances',
        type_='check'
    )

    op.drop_constraint(
        'check_user_role',
        'users',
        type_='check'
    )
