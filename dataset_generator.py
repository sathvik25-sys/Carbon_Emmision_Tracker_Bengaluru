"""
Synthetic Commuter Activity Dataset Generator for Bengaluru Carbon Emission Estimation.

Generates representative Bengaluru commuter activity patterns with realistic distributions
for educational demonstration and machine learning training.

Note: Clearly labeled as simulated synthetic dataset reflecting Bengaluru urban mobility
characteristics (BMRCL Metro, BMTC, Silk Board traffic congestion, BESCOM grid factors).
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, Any

from config import (
    EMISSION_FACTORS,
    GRID_EMISSION_FACTOR_KWH,
    CONGESTION_MAX_PENALTY,
    VEHICLE_AGE_PENALTY_PER_YEAR,
    MAX_VEHICLE_AGE_PENALTY,
)

MODES = ["walk_cycle", "namma_metro", "bmtc_bus", "auto", "two_wheeler", "car", "cab"]

# Bengaluru modal split probability distribution (simulated representative urban sample)
MODE_WEIGHTS = [0.08, 0.22, 0.26, 0.12, 0.20, 0.08, 0.04]


def generate_synthetic_data(num_samples: int = 5000, random_seed: int = 42) -> pd.DataFrame:
    """
    Synthesizes realistic commuter activity records for Bengaluru with non-linear
    congestion, vehicle wear, and per-capita household power use.
    """
    np.random.seed(random_seed)

    records = []

    for _ in range(num_samples):
        # Sample primary commute mode
        main_mode = np.random.choice(MODES, p=MODE_WEIGHTS)

        # Distance distribution dependent on mode
        if main_mode == "walk_cycle":
            one_way_dist = float(np.clip(np.random.gamma(shape=2.0, scale=1.2), 0.5, 6.0))
        elif main_mode in ["namma_metro", "bmtc_bus"]:
            one_way_dist = float(np.clip(np.random.gamma(shape=3.5, scale=3.5), 2.0, 35.0))
        elif main_mode == "two_wheeler":
            one_way_dist = float(np.clip(np.random.gamma(shape=3.0, scale=3.8), 1.5, 30.0))
        elif main_mode == "auto":
            one_way_dist = float(np.clip(np.random.gamma(shape=2.5, scale=2.8), 1.0, 20.0))
        else:  # car, cab
            one_way_dist = float(np.clip(np.random.gamma(shape=4.0, scale=4.0), 3.0, 45.0))

        # Commute days per month (centered around 20-24 working days)
        commute_days = int(np.clip(np.random.normal(loc=21.5, scale=3.0), 4, 30))

        # Rush hour share (0-100%) - Bengaluru has heavy peak rush hours (8-11am, 5-8pm)
        rush_hour_pct = float(np.clip(np.random.beta(a=2.5, b=2.0) * 100.0, 0.0, 100.0))

        # Vehicle age in years (0 for walk, metro, bus; 0-15 for personal/IPT)
        if main_mode in ["walk_cycle", "namma_metro", "bmtc_bus"]:
            vehicle_age = 0.0
        else:
            vehicle_age = float(np.clip(np.random.exponential(scale=4.5), 0.0, 16.0))

        # Other travel weekly distance and mode
        other_mode = np.random.choice(MODES, p=[0.15, 0.15, 0.18, 0.22, 0.18, 0.08, 0.04])
        other_weekly_km = float(np.clip(np.random.exponential(scale=18.0), 0.0, 80.0))

        # Household electricity use in kWh/month
        # Typical Bengaluru apartment: 80-350 kWh/month depending on AC, geyser, appliances
        household_kwh = float(np.clip(np.random.gamma(shape=3.2, scale=55.0), 40.0, 600.0))

        # Number of household members
        household_members = int(np.random.choice([1, 2, 3, 4, 5, 6], p=[0.15, 0.30, 0.25, 0.20, 0.07, 0.03]))

        # --- Calculate Ground Truth Physical Emissions ---
        # 1. Commute
        base_factor = EMISSION_FACTORS[main_mode]
        rush_mult = 1.0 + (CONGESTION_MAX_PENALTY.get(main_mode, 0.0) * (rush_hour_pct / 100.0))
        age_mult = 1.0 + min(vehicle_age * VEHICLE_AGE_PENALTY_PER_YEAR, MAX_VEHICLE_AGE_PENALTY) if main_mode in ["car", "cab", "auto", "two_wheeler"] else 1.0

        # Real-world stochastic variation (e.g. driving aggression, AC on, terrain, vehicle loading)
        driving_efficiency_noise = float(np.random.normal(loc=1.0, scale=0.04))

        commute_km_month = one_way_dist * 2.0 * commute_days
        commute_co2 = commute_km_month * base_factor * rush_mult * age_mult * driving_efficiency_noise

        # 2. Other travel
        other_base_factor = EMISSION_FACTORS[other_mode]
        other_km_month = other_weekly_km * (52.0 / 12.0)
        other_co2 = other_km_month * other_base_factor * float(np.random.normal(loc=1.0, scale=0.03))

        # 3. Electricity per capita
        per_capita_kwh = household_kwh / household_members
        elec_co2 = per_capita_kwh * GRID_EMISSION_FACTOR_KWH

        # Total monthly CO2
        total_monthly_co2 = max(0.0, commute_co2 + other_co2 + elec_co2)

        records.append({
            "main_mode": main_mode,
            "one_way_distance_km": round(one_way_dist, 2),
            "commute_days_per_month": commute_days,
            "rush_hour_pct": round(rush_hour_pct, 1),
            "vehicle_age": round(vehicle_age, 1),
            "other_travel_mode": other_mode,
            "other_weekly_km": round(other_weekly_km, 2),
            "household_kwh": round(household_kwh, 1),
            "household_members": household_members,
            "per_capita_kwh": round(per_capita_kwh, 2),
            "commute_monthly_km": round(commute_km_month, 2),
            "commute_co2_kg": round(commute_co2, 3),
            "other_co2_kg": round(other_co2, 3),
            "electricity_co2_kg": round(elec_co2, 3),
            "total_monthly_co2_kg": round(total_monthly_co2, 3),
        })

    df = pd.DataFrame(records)
    return df


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "bengaluru_commute_dataset.csv")

    print(f"Generating synthetic Bengaluru commute dataset (5,000 samples)...")
    df = generate_synthetic_data(num_samples=5000)
    df.to_csv(output_path, index=False)
    print(f"Dataset successfully saved to: {output_path}")
    print(f"Summary Statistics:\n{df[['commute_monthly_km', 'per_capita_kwh', 'total_monthly_co2_kg']].describe()}")


if __name__ == "__main__":
    main()
