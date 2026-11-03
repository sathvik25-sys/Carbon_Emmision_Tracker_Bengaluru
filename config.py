"""
Configuration and Emission Factors for Bengaluru Carbon Emission Tracker.

All factors are transparently documented with sources and illustrative assumptions.
References:
1. Central Electricity Authority (CEA), Govt. of India - CO2 Baseline Database for the Indian Power Sector (User Guide Version 19.0).
2. Automotive Research Association of India (ARAI) - Emission Factor Database for Indian In-Use Vehicles.
3. Bureau of Energy Efficiency (BEE) - India Greenhouse Gas (GHG) Program.
4. Bangalore Metropolitan Transport Corporation (BMTC) & BMRCL (Namma Metro) sustainability reporting metrics.
5. Urban Mobility Institute - Congestion and fuel penalties in Indian metropolitan traffic corridors.
"""

from typing import Dict, Any

# ==============================================================================
# BASE EMISSION FACTORS (kg CO2e per passenger-kilometer)
# ==============================================================================
# Sources:
# - walk_cycle: Zero tailpipe / direct operational emissions.
# - namma_metro: Electric rapid rail transit on Southern Indian Grid (CEA) with ~60% average load factor (~0.018 kg CO2e/pkm).
# - bmtc_bus: BMTC urban city bus fleet (CNG/Diesel/Electric mix) average load factor ~40 passengers (~0.028 kg CO2e/pkm).
# - auto: 3-wheeler autorickshaw (LPG/CNG/4-stroke petrol, average occupancy 1.3 passengers) (~0.065 kg CO2e/pkm).
# - two_wheeler: 100-150cc petrol scooter/motorcycle, solo rider (~0.048 kg CO2e/pkm).
# - car: Average private passenger ICE car (petrol/diesel, 1.2 passenger occupancy) in urban driving (~0.155 kg CO2e/pkm).
# - cab: Ride-hailing taxi (Uber/Ola/BluSmart mix), including ~20% deadhead/empty cruising km (~0.185 kg CO2e/pkm).
# - ev_two_wheeler: Electric scooter charged on Karnataka grid (~0.015 kg CO2e/pkm).

EMISSION_FACTORS: Dict[str, float] = {
    "walk_cycle": 0.000,
    "namma_metro": 0.018,
    "bmtc_bus": 0.028,
    "auto": 0.065,
    "two_wheeler": 0.048,
    "car": 0.155,
    "cab": 0.185,
    "ev_two_wheeler": 0.015,
}

# Human-readable labels and descriptions for UI
MODE_METADATA: Dict[str, Dict[str, Any]] = {
    "walk_cycle": {
        "label": "Walking / Cycling",
        "category": "Active Mobility",
        "unit": "kg CO2e/pkm",
        "factor": 0.000,
        "requires_vehicle_age": False,
        "congestion_sensitive": False,
        "description": "Zero operational emissions; healthy active mobility."
    },
    "namma_metro": {
        "label": "Namma Metro (BMRCL)",
        "category": "Mass Rapid Transit",
        "unit": "kg CO2e/pkm",
        "factor": 0.018,
        "requires_vehicle_age": False,
        "congestion_sensitive": False,
        "description": "Electrified mass transit; grade-separated, immune to road congestion."
    },
    "bmtc_bus": {
        "label": "BMTC Bus",
        "category": "Public Bus Transit",
        "unit": "kg CO2e/pkm",
        "factor": 0.028,
        "requires_vehicle_age": False,
        "congestion_sensitive": True,
        "description": "High-capacity urban public bus network serving Bengaluru."
    },
    "auto": {
        "label": "Auto Rickshaw (3-Wheeler)",
        "category": "Intermediate Public Transport",
        "unit": "kg CO2e/pkm",
        "factor": 0.065,
        "requires_vehicle_age": True,
        "congestion_sensitive": True,
        "description": "LPG/CNG 3-wheeler intermediate public transport."
    },
    "two_wheeler": {
        "label": "Two-Wheeler (Motorcycle / Scooter)",
        "category": "Personal Motorized",
        "unit": "kg CO2e/pkm",
        "factor": 0.048,
        "requires_vehicle_age": True,
        "congestion_sensitive": True,
        "description": "100-150cc petrol 2-wheeler, predominant mode in Bengaluru."
    },
    "car": {
        "label": "Personal Car (Solo / Drive)",
        "category": "Personal Motorized",
        "unit": "kg CO2e/pkm",
        "factor": 0.155,
        "requires_vehicle_age": True,
        "congestion_sensitive": True,
        "description": "Private passenger car (petrol/diesel) in urban driving conditions."
    },
    "cab": {
        "label": "Cab / Taxi (Uber / Ola)",
        "category": "On-Demand Ride Hailing",
        "unit": "kg CO2e/pkm",
        "factor": 0.185,
        "requires_vehicle_age": True,
        "congestion_sensitive": True,
        "description": "App-based cab including deadhead repositioning mileage."
    },
}

# ==============================================================================
# ELECTRICITY GRID EMISSION FACTOR (kg CO2e per kWh)
# ==============================================================================
# Central Electricity Authority (CEA) CO2 Baseline Database for Indian Power Sector (Southern Region):
# Karnataka mix has significant renewable share (Pavagada solar, wind, Sharavathi hydro) combined with thermal base load.
# Grid emission factor: ~0.716 kg CO2e per kWh (Illustrative standard for BESCOM territory).
GRID_EMISSION_FACTOR_KWH = 0.716

# ==============================================================================
# TRAFFIC CONGESTION / RUSH HOUR PENALTY
# ==============================================================================
# Bengaluru traffic speed during peak hours drops drastically (e.g. Silk Board, ORR, Whitefield).
# Stop-and-go driving increases fuel consumption by up to:
# - Car: +35%
# - Cab: +35%
# - Auto: +25%
# - Two-Wheeler: +20% (partial traffic filtering)
# - BMTC Bus: +15% (dedicated lane segments & thermal bus idle)
# - Metro & Active mobility: 0%
CONGESTION_MAX_PENALTY: Dict[str, float] = {
    "walk_cycle": 0.00,
    "namma_metro": 0.00,
    "bmtc_bus": 0.15,
    "auto": 0.25,
    "two_wheeler": 0.20,
    "car": 0.35,
    "cab": 0.35,
}

# ==============================================================================
# VEHICLE AGE DEGRADATION FACTOR
# ==============================================================================
# Older vehicles have catalytic converter wear, older BS norms (BS3/BS4 vs BS6), and engine degradation.
# Assumption: +2.0% emission increase per year of age, capped at +30% (max 15 years considered).
VEHICLE_AGE_PENALTY_PER_YEAR = 0.020
MAX_VEHICLE_AGE_PENALTY = 0.30

# ==============================================================================
# BENCHMARKS AND EQUIVALENCIES
# ==============================================================================
# Annual CO2 absorbed by one mature tropical tree: ~21.0 kg CO2 / year (~1.75 kg CO2 / month).
TREE_SEQUESTRATION_KG_PER_YEAR = 21.0

# India national per-capita monthly carbon emission benchmark: ~160 kg CO2e / month (~1.9 tonnes/yr).
INDIA_NATIONAL_MONTHLY_BENCHMARK = 160.0

# Global per-capita monthly average: ~390 kg CO2e / month (~4.7 tonnes/yr).
GLOBAL_MONTHLY_BENCHMARK = 390.0

# Bengaluru urban middle-class benchmark (transport + electricity): ~120 - 150 kg CO2e / month.
BENGALURU_URBAN_MONTHLY_BENCHMARK = 135.0

# ==============================================================================
# DEMONSTRATION PRESETS
# ==============================================================================
DEMO_PRESETS: Dict[str, Dict[str, Any]] = {
    "whitefield_techie": {
        "name": "Whitefield IT Professional (Solo Car Driver)",
        "description": "Daily solo car commute through Silk Board & Outer Ring Road congestion.",
        "data": {
            "main_mode": "car",
            "one_way_distance_km": 18.0,
            "commute_days_per_month": 22,
            "rush_hour_pct": 85.0,
            "vehicle_age": 6,
            "other_travel_distance_km": 35.0,
            "other_travel_mode": "cab",
            "monthly_electricity_kwh": 260.0,
            "household_members": 2,
        }
    },
    "metro_commuter": {
        "name": "Indiranagar Metro Commuter (Purple Line)",
        "description": "Daily commuter using Namma Metro for daily tech-park transit.",
        "data": {
            "main_mode": "namma_metro",
            "one_way_distance_km": 14.0,
            "commute_days_per_month": 21,
            "rush_hour_pct": 70.0,
            "vehicle_age": 0,
            "other_travel_distance_km": 20.0,
            "other_travel_mode": "auto",
            "monthly_electricity_kwh": 180.0,
            "household_members": 3,
        }
    },
    "twowheeler_rider": {
        "name": "Electronic City Scooter Commuter",
        "description": "Navigates South Bengaluru traffic on a 125cc petrol scooter.",
        "data": {
            "main_mode": "two_wheeler",
            "one_way_distance_km": 13.0,
            "commute_days_per_month": 22,
            "rush_hour_pct": 65.0,
            "vehicle_age": 4,
            "other_travel_distance_km": 25.0,
            "other_travel_mode": "two_wheeler",
            "monthly_electricity_kwh": 160.0,
            "household_members": 2,
        }
    },
    "college_student": {
        "name": "Koramangala College Student (BMTC + Walking)",
        "description": "Eco-friendly student commute relying on BMTC buses and walking.",
        "data": {
            "main_mode": "bmtc_bus",
            "one_way_distance_km": 8.5,
            "commute_days_per_month": 24,
            "rush_hour_pct": 50.0,
            "vehicle_age": 0,
            "other_travel_distance_km": 15.0,
            "other_travel_mode": "walk_cycle",
            "monthly_electricity_kwh": 120.0,
            "household_members": 4,
        }
    },
    "remote_worker": {
        "name": "HSR Layout Remote Freelancer",
        "description": "Works from home with minimal vehicle travel but higher home AC/electricity.",
        "data": {
            "main_mode": "walk_cycle",
            "one_way_distance_km": 1.5,
            "commute_days_per_month": 8,
            "rush_hour_pct": 0.0,
            "vehicle_age": 0,
            "other_travel_distance_km": 15.0,
            "other_travel_mode": "auto",
            "monthly_electricity_kwh": 220.0,
            "household_members": 1,
        }
    }
}
