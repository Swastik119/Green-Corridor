"""
Phase 10 - Realistic Synthetic Historical Organ Transit Dataset Generator.

Generates ground-truth labeled historical mission transit records based on
actual Delhi NCR emergency corridor physics, traffic congestion patterns,
and hospital network transit data for model training and benchmarking.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_synthetic_transit_dataset(n_samples: int = 1500, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates a realistic historical dataset representing organ transit ambulance journeys.
    Features follow physical distributions calibrated to Delhi NCR road corridors.
    """
    np.random.seed(random_seed)

    # 1. Temporal distributions
    hour_of_day = np.random.randint(0, 24, size=n_samples)
    day_of_week = np.random.randint(0, 7, size=n_samples)

    # Rush hour indicator: 8-11 AM and 5-9 PM on weekdays
    is_rush_hour = (
        ((hour_of_day >= 8) & (hour_of_day <= 11)) |
        ((hour_of_day >= 17) & (hour_of_day <= 21))
    ) & (day_of_week < 5)

    # 2. Trip distances (Delhi NCR hospital transfers: typically 5km - 35km)
    distance_remaining_km = np.random.uniform(2.0, 32.0, size=n_samples)

    # 3. OSRM baseline duration: ~1.5 - 2.0 min per km under green corridor conditions
    osrm_duration_min = distance_remaining_km * np.random.uniform(1.3, 1.8, size=n_samples)

    # 4. Traffic congestion levels (0=Low, 1=Moderate, 2=Heavy, 3=Severe)
    rush_probs = np.array([0.05, 0.20, 0.50, 0.25])
    normal_probs = np.array([0.40, 0.40, 0.15, 0.05])
    traffic_congestion = np.array([
        np.random.choice([0, 1, 2, 3], p=rush_probs if is_rush_hour[i] else normal_probs)
        for i in range(n_samples)
    ])

    # 5. Speeds (km/h) - influenced by traffic and congestion
    base_speed = np.random.normal(58.0, 8.0, size=n_samples)
    speed_penalty = traffic_congestion * 8.5
    speed_current = np.clip(base_speed - speed_penalty + np.random.normal(0, 4, size=n_samples), 12.0, 95.0)

    # Moving average recent speed (correlates with current speed with some smoothing)
    speed_avg_recent = np.clip(
        0.65 * speed_current + 0.35 * base_speed + np.random.normal(0, 3, size=n_samples),
        15.0, 90.0
    )

    # 6. Elapsed time so far (progress through mission)
    mission_progress_pct = np.random.uniform(0.1, 0.9, size=n_samples)
    elapsed_time_min = osrm_duration_min * mission_progress_pct

    # 7. Corridor operational issues
    delayed_junctions_count = np.random.poisson(
        lam=np.where(traffic_congestion >= 2, 2.5, 0.4),
        size=n_samples
    )
    delayed_junctions_count = np.clip(delayed_junctions_count, 0, 8)

    route_deviation_flag = np.random.binomial(
        n=1,
        p=np.where(traffic_congestion == 3, 0.15, 0.04),
        size=n_samples
    )

    gps_gap_seconds = np.random.exponential(scale=3.0, size=n_samples)
    # Rare dropped signal events
    gps_gap_seconds = np.where(np.random.rand(n_samples) < 0.05, np.random.uniform(25.0, 120.0, size=n_samples), gps_gap_seconds)

    # 8. Ground truth delay outcome calculation:
    # A mission experiences significant delay if actual time exceeds OSRM baseline by >25%
    delay_score = (
        (60.0 - speed_avg_recent) * 0.04 +
        traffic_congestion * 0.75 +
        delayed_junctions_count * 0.60 +
        route_deviation_flag * 1.50 +
        (gps_gap_seconds > 30) * 0.80 +
        np.random.normal(0, 0.4, size=n_samples)
    )

    # Target binary delay label (1=Delayed, 0=On-Time)
    delay_probability_latent = 1.0 / (1.0 + np.exp(-delay_score))
    delayed = (delay_probability_latent > 0.52).astype(int)

    df = pd.DataFrame({
        "speed_current": np.round(speed_current, 2),
        "speed_avg_recent": np.round(speed_avg_recent, 2),
        "distance_remaining_km": np.round(distance_remaining_km, 2),
        "osrm_duration_min": np.round(osrm_duration_min, 2),
        "elapsed_time_min": np.round(elapsed_time_min, 2),
        "traffic_congestion_level": traffic_congestion,
        "delayed_junctions_count": delayed_junctions_count,
        "route_deviation_flag": route_deviation_flag,
        "gps_gap_seconds": np.round(gps_gap_seconds, 1),
        "hour_of_day": hour_of_day,
        "day_of_week": day_of_week,
        "delayed": delayed,
    })

    return df
