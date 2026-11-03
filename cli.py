"""
Command-Line Interface (CLI) for Bengaluru Carbon Emission Tracker.
Allows testing calculations, running demo presets, and viewing the Carbon Receipt in terminal.
Usage:
    python cli.py --preset whitefield_techie
    python cli.py --mode car --distance 15 --days 22 --kwh 200 --members 2
"""

import argparse
import sys
from config import DEMO_PRESETS, MODE_METADATA, GRID_EMISSION_FACTOR_KWH
from calculator import CommuterInput, compute_carbon_estimate
from ml_engine import ml_engine


def print_receipt(result: dict):
    b = result["breakdown"]
    s = result["summary"]
    commute = b["commute"]
    other = b["other_travel"]
    elec = b["electricity"]

    print("\n" + "=" * 55)
    print("           BENGALURU URBAN CARBON AUDIT")
    print("      DAILY ACTIVITIES EMISSION ESTIMATOR")
    print("           BENGALURU, KARNATAKA, INDIA")
    print("=" * 55)
    print(f"Ref : BLR-CARB-CLI-2026")
    print("-" * 55)
    print(f"1. COMMUTE [{commute['mode_label']}]")
    print(f"   Monthly Distance : {commute['monthly_distance_km']} km")
    print(f"   Effective Rate   : {commute['effective_factor_kg_pkm']} kg/pkm")
    print(f"   Congestion Boost : {commute['congestion_multiplier']}x")
    print(f"   --> SUB-TOTAL    : {commute['monthly_commute_co2_kg']:.2f} kg CO2e ({commute['percentage']}%)")
    print("-" * 55)
    print(f"2. OTHER TRAVEL [{other['mode_label']}]")
    print(f"   Monthly Distance : {other['monthly_distance_km']} km")
    print(f"   --> SUB-TOTAL    : {other['monthly_other_co2_kg']:.2f} kg CO2e ({other['percentage']}%)")
    print("-" * 55)
    print(f"3. HOUSEHOLD ELECTRICITY [BESCOM GRID]")
    print(f"   Per-Capita Power : {elec['per_capita_kwh']:.1f} kWh/month ({elec['household_members']} pax)")
    print(f"   Grid Factor      : {GRID_EMISSION_FACTOR_KWH} kg CO2e/kWh")
    print(f"   --> SUB-TOTAL    : {elec['monthly_electricity_co2_kg']:.2f} kg CO2e ({elec['percentage']}%)")
    print("=" * 55)
    print(f"TOTAL MONTHLY CO2e   : {s['monthly_total_co2_kg']:.2f} kg CO2e")
    print(f"DAILY AVERAGE        : {s['daily_average_co2_kg']:.2f} kg/day")
    print(f"ANNUAL FOOTPRINT     : {s['annual_total_co2_kg']:.1f} kg/year")
    print(f"TREES TO OFFSET      : {s['trees_offset_needed']} Trees/year")
    print(f"STATUS RATING        : {s['tier_label']}")
    print("=" * 55)

    print("\n[WHAT-IF COMMUTE ALTERNATIVES]")
    for alt in result["what_if_scenarios"]:
        saved_str = f"Saves {alt['monthly_saved_kg']:+.1f} kg/mo ({alt['pct_saved']}%)" if alt['monthly_saved_kg'] > 0 else "Baseline"
        print(f" - {alt['label']:<32} : {alt['alternative_monthly_co2_kg']:>6.1f} kg/mo | {saved_str}")

    print("\n[RECOMMENDATIONS]")
    for rec in result["recommendations"]:
        print(f" * [{rec['category']}] {rec['title']} - {rec['text']}")
    print("=" * 55 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Bengaluru Carbon Emission Estimator CLI")
    parser.add_argument("--preset", type=str, choices=list(DEMO_PRESETS.keys()), help="Run a demo preset profile")
    parser.add_argument("--mode", type=str, default="two_wheeler", choices=list(MODE_METADATA.keys()))
    parser.add_argument("--distance", type=float, default=13.0, help="One-way commute distance in km")
    parser.add_argument("--days", type=int, default=22, help="Commute days per month")
    parser.add_argument("--rush-hour", type=float, default=60.0, help="Rush hour share (0-100%%)")
    parser.add_argument("--vehicle-age", type=float, default=3.0, help="Vehicle age in years")
    parser.add_argument("--other-mode", type=str, default="auto", choices=list(MODE_METADATA.keys()))
    parser.add_argument("--other-distance", type=float, default=20.0, help="Weekly other travel distance in km")
    parser.add_argument("--kwh", type=float, default=160.0, help="Monthly household electricity in kWh")
    parser.add_argument("--members", type=int, default=2, help="Household members sharing electricity")

    args = parser.parse_args()

    if args.preset:
        p = DEMO_PRESETS[args.preset]["data"]
        payload = CommuterInput(**p)
        print(f"Loaded preset: {DEMO_PRESETS[args.preset]['name']}")
    else:
        payload = CommuterInput(
            main_mode=args.mode,
            one_way_distance_km=args.distance,
            commute_days_per_month=args.days,
            rush_hour_pct=args.rush_hour,
            vehicle_age=args.vehicle_age,
            other_travel_mode=args.other_mode,
            other_travel_distance_km=args.other_distance,
            monthly_electricity_kwh=args.kwh,
            household_members=args.members,
        )

    result = compute_carbon_estimate(payload)
    print_receipt(result)

    # ML comparison
    ml_res = ml_engine.predict(payload.model_dump())
    print("[MACHINE LEARNING MODEL ESTIMATE]")
    print(f"ML Model Output     : {ml_res['predicted_monthly_co2_kg']:.2f} kg CO2e / month")
    print(f"95% Confidence Band : [{ml_res['confidence_interval_monthly'][0]} - {ml_res['confidence_interval_monthly'][1]} kg]")
    print(f"Model Description   : {ml_res['simulation_label']}")
    print("-" * 55)


if __name__ == "__main__":
    main()
