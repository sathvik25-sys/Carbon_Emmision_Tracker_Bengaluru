"""
Emission Calculator and What-If Analysis Engine for Bengaluru Daily Activities.

Provides deterministic, reproducible, Tier-1 IPCC/CEA factor-based calculations
with congestion and vehicle aging corrections, input validation, and what-if simulation.
"""

from typing import Dict, Any, List, Optional
import math
from pydantic import BaseModel, Field, field_validator

from config import (
    EMISSION_FACTORS,
    MODE_METADATA,
    GRID_EMISSION_FACTOR_KWH,
    CONGESTION_MAX_PENALTY,
    VEHICLE_AGE_PENALTY_PER_YEAR,
    MAX_VEHICLE_AGE_PENALTY,
    TREE_SEQUESTRATION_KG_PER_YEAR,
    INDIA_NATIONAL_MONTHLY_BENCHMARK,
    GLOBAL_MONTHLY_BENCHMARK,
    BENGALURU_URBAN_MONTHLY_BENCHMARK,
)

WEEKS_PER_MONTH = 52.0 / 12.0  # 4.3333 weeks per month
DAYS_PER_MONTH_AVG = 365.25 / 12.0  # ~30.4375 days


class CommuterInput(BaseModel):
    """Input payload representing daily travel and electricity usage."""
    main_mode: str = Field(..., description="Primary commute transit mode")
    one_way_distance_km: float = Field(..., ge=0.0, le=300.0, description="One-way commute distance in km")
    commute_days_per_month: int = Field(..., ge=0, le=31, description="Commute days per month")
    rush_hour_pct: float = Field(0.0, ge=0.0, le=100.0, description="Approximate share of trips during rush hour")
    vehicle_age: float = Field(0.0, ge=0.0, le=40.0, description="Vehicle age in years (when relevant)")
    other_travel_distance_km: float = Field(0.0, ge=0.0, le=1000.0, description="Other weekly travel distance in km")
    other_travel_mode: str = Field("walk_cycle", description="Transit mode for other weekly travel")
    monthly_electricity_kwh: float = Field(..., ge=0.0, le=10000.0, description="Household electricity consumption in kWh")
    household_members: int = Field(1, ge=1, le=50, description="Number of people sharing electricity use")

    @field_validator("main_mode")
    @classmethod
    def validate_main_mode(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in EMISSION_FACTORS:
            valid_modes = ", ".join(EMISSION_FACTORS.keys())
            raise ValueError(f"Invalid commute mode '{v}'. Must be one of: {valid_modes}")
        return v_clean

    @field_validator("other_travel_mode")
    @classmethod
    def validate_other_mode(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in EMISSION_FACTORS:
            valid_modes = ", ".join(EMISSION_FACTORS.keys())
            raise ValueError(f"Invalid other travel mode '{v}'. Must be one of: {valid_modes}")
        return v_clean


def calculate_commute_details(
    main_mode: str,
    one_way_distance_km: float,
    commute_days_per_month: int,
    rush_hour_pct: float,
    vehicle_age: float,
) -> Dict[str, Any]:
    """Calculates commute emissions with non-linear congestion & aging penalties."""
    clean_mode = main_mode.strip().lower()
    base_factor = EMISSION_FACTORS.get(clean_mode, 0.0)
    meta = MODE_METADATA.get(clean_mode, {})

    # Round trip and monthly distances
    round_trip_km = one_way_distance_km * 2.0
    monthly_km = round_trip_km * commute_days_per_month

    # Congestion penalty
    congestion_max = CONGESTION_MAX_PENALTY.get(clean_mode, 0.0)
    rush_fraction = max(0.0, min(100.0, rush_hour_pct)) / 100.0
    congestion_multiplier = 1.0 + (congestion_max * rush_fraction)

    # Vehicle age penalty (only for personal motorized / IPT)
    if meta.get("requires_vehicle_age", False) and vehicle_age > 0:
        age_penalty = min(vehicle_age * VEHICLE_AGE_PENALTY_PER_YEAR, MAX_VEHICLE_AGE_PENALTY)
        age_multiplier = 1.0 + age_penalty
    else:
        age_multiplier = 1.0

    effective_factor = base_factor * congestion_multiplier * age_multiplier

    monthly_co2 = monthly_km * effective_factor
    daily_commute_co2 = round_trip_km * effective_factor if commute_days_per_month > 0 else 0.0

    return {
        "mode": clean_mode,
        "mode_label": meta.get("label", clean_mode),
        "one_way_km": round(one_way_distance_km, 2),
        "round_trip_km": round(round_trip_km, 2),
        "commute_days_per_month": commute_days_per_month,
        "monthly_distance_km": round(monthly_km, 2),
        "base_factor_kg_pkm": round(base_factor, 4),
        "congestion_multiplier": round(congestion_multiplier, 3),
        "age_multiplier": round(age_multiplier, 3),
        "effective_factor_kg_pkm": round(effective_factor, 4),
        "daily_commute_co2_kg": round(daily_commute_co2, 3),
        "monthly_commute_co2_kg": round(monthly_co2, 3),
    }


def calculate_other_travel_details(
    other_travel_mode: str,
    other_travel_distance_km: float,
) -> Dict[str, Any]:
    """Calculates weekly other travel emissions annualized to monthly."""
    clean_mode = other_travel_mode.strip().lower()
    base_factor = EMISSION_FACTORS.get(clean_mode, 0.0)
    meta = MODE_METADATA.get(clean_mode, {})

    monthly_distance_km = other_travel_distance_km * WEEKS_PER_MONTH
    monthly_co2 = monthly_distance_km * base_factor
    daily_avg_co2 = monthly_co2 / DAYS_PER_MONTH_AVG

    return {
        "mode": clean_mode,
        "mode_label": meta.get("label", clean_mode),
        "weekly_distance_km": round(other_travel_distance_km, 2),
        "monthly_distance_km": round(monthly_distance_km, 2),
        "factor_kg_pkm": round(base_factor, 4),
        "daily_other_co2_kg": round(daily_avg_co2, 3),
        "monthly_other_co2_kg": round(monthly_co2, 3),
    }


def calculate_electricity_details(
    monthly_electricity_kwh: float,
    household_members: int,
) -> Dict[str, Any]:
    """Calculates household and per-capita electricity emissions."""
    members = max(1, household_members)
    per_capita_kwh = monthly_electricity_kwh / members
    monthly_co2 = per_capita_kwh * GRID_EMISSION_FACTOR_KWH
    daily_co2 = monthly_co2 / DAYS_PER_MONTH_AVG
    total_household_co2 = monthly_electricity_kwh * GRID_EMISSION_FACTOR_KWH

    return {
        "household_kwh": round(monthly_electricity_kwh, 2),
        "household_members": members,
        "per_capita_kwh": round(per_capita_kwh, 2),
        "grid_factor_kg_kwh": round(GRID_EMISSION_FACTOR_KWH, 4),
        "daily_electricity_co2_kg": round(daily_co2, 3),
        "monthly_electricity_co2_kg": round(monthly_co2, 3),
        "total_household_monthly_co2_kg": round(total_household_co2, 3),
    }


def compute_carbon_estimate(data: CommuterInput) -> Dict[str, Any]:
    """
    Executes complete emission estimation, itemized receipt breakdown,
    what-if alternatives, and reduction suggestions.
    """
    # 1. Component calculations
    commute = calculate_commute_details(
        main_mode=data.main_mode,
        one_way_distance_km=data.one_way_distance_km,
        commute_days_per_month=data.commute_days_per_month,
        rush_hour_pct=data.rush_hour_pct,
        vehicle_age=data.vehicle_age,
    )

    other = calculate_other_travel_details(
        other_travel_mode=data.other_travel_mode,
        other_travel_distance_km=data.other_travel_distance_km,
    )

    electricity = calculate_electricity_details(
        monthly_electricity_kwh=data.monthly_electricity_kwh,
        household_members=data.household_members,
    )

    # 2. Aggregations
    monthly_commute_co2 = commute["monthly_commute_co2_kg"]
    monthly_other_co2 = other["monthly_other_co2_kg"]
    monthly_elec_co2 = electricity["monthly_electricity_co2_kg"]

    monthly_total_co2 = monthly_commute_co2 + monthly_other_co2 + monthly_elec_co2
    daily_average_co2 = monthly_total_co2 / DAYS_PER_MONTH_AVG
    annual_total_co2 = monthly_total_co2 * 12.0

    # Trees equivalent (annual CO2 divided by 21 kg CO2/tree/yr)
    trees_offset_needed = math.ceil(annual_total_co2 / TREE_SEQUESTRATION_KG_PER_YEAR) if annual_total_co2 > 0 else 0

    # Percentages
    if monthly_total_co2 > 0:
        commute_pct = round((monthly_commute_co2 / monthly_total_co2) * 100.0, 1)
        other_pct = round((monthly_other_co2 / monthly_total_co2) * 100.0, 1)
        elec_pct = round((monthly_elec_co2 / monthly_total_co2) * 100.0, 1)
    else:
        commute_pct = 0.0
        other_pct = 0.0
        elec_pct = 0.0

    # Footprint tier category
    if monthly_total_co2 < 60.0:
        tier_code = "LOW"
        tier_label = "Low Carbon Champion"
        tier_color = "emerald"
        tier_desc = "Your emissions are well below both Bengaluru and national urban averages."
    elif monthly_total_co2 < 140.0:
        tier_code = "MODERATE"
        tier_label = "Moderate Commuter"
        tier_color = "amber"
        tier_desc = "Your footprint aligns closely with typical Bengaluru urban residents."
    elif monthly_total_co2 < 240.0:
        tier_code = "HIGH"
        tier_label = "High Carbon Footprint"
        tier_color = "orange"
        tier_desc = "Your emissions exceed the Bengaluru average, primarily driven by travel or electricity."
    else:
        tier_code = "CRITICAL"
        tier_label = "Intensive Footprint"
        tier_color = "rose"
        tier_desc = "Significant reduction potential exists through transit modal shifts and energy conservation."

    # Benchmark comparison
    bengaluru_delta_pct = round(((monthly_total_co2 - BENGALURU_URBAN_MONTHLY_BENCHMARK) / BENGALURU_URBAN_MONTHLY_BENCHMARK) * 100.0, 1)
    india_delta_pct = round(((monthly_total_co2 - INDIA_NATIONAL_MONTHLY_BENCHMARK) / INDIA_NATIONAL_MONTHLY_BENCHMARK) * 100.0, 1)

    # 3. What-if Alternatives Analysis
    what_if_scenarios = compute_what_if_scenarios(
        current_monthly_commute_co2=monthly_commute_co2,
        one_way_distance_km=data.one_way_distance_km,
        commute_days_per_month=data.commute_days_per_month,
        current_mode=data.main_mode,
    )

    # 4. Reduction Action Tips
    recommendations = generate_actionable_tips(
        commute_details=commute,
        electricity_details=electricity,
        other_details=other,
        monthly_total=monthly_total_co2,
    )

    return {
        "status": "success",
        "inputs": data.model_dump(),
        "summary": {
            "daily_average_co2_kg": round(daily_average_co2, 2),
            "monthly_total_co2_kg": round(monthly_total_co2, 2),
            "annual_total_co2_kg": round(annual_total_co2, 1),
            "trees_offset_needed": trees_offset_needed,
            "tier_code": tier_code,
            "tier_label": tier_label,
            "tier_color": tier_color,
            "tier_description": tier_desc,
            "bengaluru_benchmark_kg": BENGALURU_URBAN_MONTHLY_BENCHMARK,
            "bengaluru_delta_pct": bengaluru_delta_pct,
            "india_benchmark_kg": INDIA_NATIONAL_MONTHLY_BENCHMARK,
            "india_delta_pct": india_delta_pct,
        },
        "breakdown": {
            "commute": {
                **commute,
                "percentage": commute_pct,
            },
            "other_travel": {
                **other,
                "percentage": other_pct,
            },
            "electricity": {
                **electricity,
                "percentage": elec_pct,
            },
        },
        "what_if_scenarios": what_if_scenarios,
        "recommendations": recommendations,
        "methodology": {
            "standards": "IPCC Tier-1 Activity Factor & Central Electricity Authority (CEA) India Database",
            "electricity_factor": f"{GRID_EMISSION_FACTOR_KWH} kg CO2e / kWh (Southern Regional Grid / Karnataka)",
            "vehicle_factors_source": "ARAI & India GHG Program urban fleet standards with congestion corrections",
            "congestion_model": "Peak-hour speed loss idle & acceleration penalty (up to +35% for ICE)",
            "age_model": f"+{int(VEHICLE_AGE_PENALTY_PER_YEAR*100)}% per year engine & emissions degradation (capped at {int(MAX_VEHICLE_AGE_PENALTY*100)}%)",
        }
    }


def compute_what_if_scenarios(
    current_monthly_commute_co2: float,
    one_way_distance_km: float,
    commute_days_per_month: int,
    current_mode: str,
) -> List[Dict[str, Any]]:
    """Evaluates practical Bengaluru alternative commute modes."""
    total_monthly_km = one_way_distance_km * 2.0 * commute_days_per_month
    scenarios: List[Dict[str, Any]] = []

    alternatives = [
        {
            "id": "namma_metro",
            "label": "Shift to Namma Metro",
            "mode": "namma_metro",
            "factor": EMISSION_FACTORS["namma_metro"],
            "description": "Grade-separated electric rail; bypasses Silk Board & ORR traffic completely.",
            "feasibility": "High if near Purple, Green, or Yellow line corridors.",
        },
        {
            "id": "bmtc_bus",
            "label": "Shift to BMTC City Bus",
            "mode": "bmtc_bus",
            "factor": EMISSION_FACTORS["bmtc_bus"],
            "description": "Shared public transit; extensive network covering all Bengaluru routes.",
            "feasibility": "Very high network coverage across major arterial roads.",
        },
        {
            "id": "carpool_2",
            "label": "Carpool / Rideshare (2 People)",
            "mode": "car",
            "factor": EMISSION_FACTORS["car"] / 2.0,
            "description": "Sharing your car commute halves fuel burned per person.",
            "feasibility": "Practical for colleagues living along similar tech-corridors.",
        },
        {
            "id": "ev_two_wheeler",
            "label": "Electric Two-Wheeler (EV Scooter)",
            "mode": "ev_two_wheeler",
            "factor": EMISSION_FACTORS["ev_two_wheeler"],
            "description": "Zero tailpipe emission; charged on Karnataka grid mix.",
            "feasibility": "High for commutes under 25 km with home/office charging.",
        },
        {
            "id": "walk_cycle",
            "label": "Active Mobility (Walk / Cycle)",
            "mode": "walk_cycle",
            "factor": EMISSION_FACTORS["walk_cycle"],
            "description": "Zero operational carbon and zero fuel cost.",
            "feasibility": "Ideal for first/last mile or commutes under 5 km.",
        },
    ]

    for alt in alternatives:
        alt_monthly_co2 = total_monthly_km * alt["factor"]
        monthly_saved = current_monthly_commute_co2 - alt_monthly_co2
        pct_saved = (monthly_saved / current_monthly_commute_co2 * 100.0) if current_monthly_commute_co2 > 0 else 0.0
        annual_saved = max(0.0, monthly_saved * 12.0)
        annual_trees = round(annual_saved / TREE_SEQUESTRATION_KG_PER_YEAR, 1)

        scenarios.append({
            "id": alt["id"],
            "label": alt["label"],
            "mode": alt["mode"],
            "description": alt["description"],
            "feasibility": alt["feasibility"],
            "alternative_monthly_co2_kg": round(alt_monthly_co2, 2),
            "monthly_saved_kg": round(monthly_saved, 2),
            "pct_saved": round(pct_saved, 1),
            "annual_saved_kg": round(annual_saved, 1),
            "annual_trees_saved": annual_trees,
            "is_current_mode": (current_mode == alt["mode"] and alt["id"] not in ["carpool_2"]),
        })

    return scenarios


def generate_actionable_tips(
    commute_details: Dict[str, Any],
    electricity_details: Dict[str, Any],
    other_details: Dict[str, Any],
    monthly_total: float,
) -> List[Dict[str, str]]:
    """Generates context-aware, highly practical tips tailored to Bengaluru."""
    tips: List[Dict[str, str]] = []

    commute_mode = commute_details["mode"]
    commute_co2 = commute_details["monthly_commute_co2_kg"]
    rush_mult = commute_details["congestion_multiplier"]
    elec_kwh = electricity_details["per_capita_kwh"]

    # Tip 1: Travel optimization
    if commute_mode in ["car", "cab"]:
        tips.append({
            "category": "Mobility Shift",
            "title": "Switch to Namma Metro or BMTC Vajra",
            "impact": "High (up to 80% commute reduction)",
            "text": "Cars in Bengaluru average ~0.155 kg CO2/km plus heavy congestion penalties. Switching just 2 days a week to Metro or BMTC can save 30-50 kg CO2e monthly."
        })
        if rush_mult > 1.15:
            tips.append({
                "category": "Traffic Timing",
                "title": "Shift Peak Commute Hours",
                "impact": "Medium (15-25% fuel savings)",
                "text": "Your commute incurs significant rush-hour congestion penalty. Negotiating flexible hours (e.g., travel before 8:00 AM or after 10:30 AM) cuts stop-and-go fuel waste."
            })
    elif commute_mode == "two_wheeler":
        tips.append({
            "category": "Clean Vehicle",
            "title": "Adopt an Electric 2-Wheeler (EV)",
            "impact": "Medium (70% emissions reduction)",
            "text": "EV two-wheelers charged in Karnataka emit only ~0.015 kg CO2/km compared to ~0.048 kg/km for petrol scooters, saving fuel cost and city tailpipe pollution."
        })
    elif commute_mode in ["namma_metro", "bmtc_bus"]:
        tips.append({
            "category": "Transit Champion",
            "title": "Maintain Public Transit Habits",
            "impact": "High Sustainability",
            "text": "You are already using low-carbon mass transit! Combine with electric autos or feeder Yulu cycles for first/last mile connectivity."
        })

    # Tip 2: Household electricity
    if elec_kwh > 100.0:
        tips.append({
            "category": "Home Energy",
            "title": "Optimize Air Conditioning & Water Heaters",
            "impact": "Medium-High (15-30 kg CO2e/month)",
            "text": f"Your per-capita power use is {elec_kwh:.1f} kWh/month. Setting AC thermostats to 24°C instead of 18-20°C and using 5-star BEE water geysers saves 30-60 kWh monthly."
        })
    else:
        tips.append({
            "category": "Home Energy",
            "title": "Rooftop Solar & Energy Star Appliances",
            "impact": "Long-term Net Zero",
            "text": "Consider BESCOM rooftop solar net metering (Surya Ghar Muft Bijli Yojana) to offset the remaining grid carbon intensity."
        })

    # Tip 3: Weekend / Other travel
    if other_details["monthly_other_co2_kg"] > 20.0:
        tips.append({
            "category": "Lifestyle",
            "title": "Bundle Weekly Errands & Use Active Mobility",
            "impact": "Low-Medium (10-20 kg CO2e/month)",
            "text": "Batch weekend shopping trips or walk/cycle for local neighborhood errands within 2 km instead of taking cabs or cars."
        })

    return tips
