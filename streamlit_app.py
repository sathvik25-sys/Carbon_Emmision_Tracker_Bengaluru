"""
Streamlit Companion Interface for Bengaluru Carbon Emission Tracker.
Provides an interactive data science dashboard utilizing the same underlying calculator and ML engine.
Run with: streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import (
    EMISSION_FACTORS,
    MODE_METADATA,
    DEMO_PRESETS,
    GRID_EMISSION_FACTOR_KWH,
    BENGALURU_URBAN_MONTHLY_BENCHMARK,
    INDIA_NATIONAL_MONTHLY_BENCHMARK,
)
from calculator import CommuterInput, compute_carbon_estimate
from ml_engine import ml_engine

st.set_page_config(
    page_title="Bengaluru Carbon Emission Tracker",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌱 Bengaluru Carbon Emission Tracker")
st.caption("Machine Learning & Tier-1 Factor Estimator for Daily Commuting and Household Electricity")

# Sidebar: Presets & Activity Inputs
st.sidebar.header("📋 Commuter Inputs")

# Preset selection
preset_keys = ["Custom", *list(DEMO_PRESETS.keys())]
preset_labels = ["Custom Input"] + [f"{v['name']}" for v in DEMO_PRESETS.values()]
selected_preset_idx = st.sidebar.selectbox(
    "Quick Demo Presets",
    range(len(preset_keys)),
    format_func=lambda i: preset_labels[i],
)

default_vals = {
    "main_mode": "two_wheeler",
    "one_way_km": 13.0,
    "days": 22,
    "rush_hour": 65.0,
    "vehicle_age": 4.0,
    "other_mode": "two_wheeler",
    "other_km": 25.0,
    "elec_kwh": 160.0,
    "members": 2,
}

if selected_preset_idx > 0:
    preset_id = preset_keys[selected_preset_idx]
    preset_data = DEMO_PRESETS[preset_id]["data"]
    default_vals = {
        "main_mode": preset_data["main_mode"],
        "one_way_km": float(preset_data["one_way_distance_km"]),
        "days": int(preset_data["commute_days_per_month"]),
        "rush_hour": float(preset_data["rush_hour_pct"]),
        "vehicle_age": float(preset_data["vehicle_age"]),
        "other_mode": preset_data["other_travel_mode"],
        "other_km": float(preset_data["other_travel_distance_km"]),
        "elec_kwh": float(preset_data["monthly_electricity_kwh"]),
        "members": int(preset_data["household_members"]),
    }

st.sidebar.subheader("1. Primary Daily Commute")
mode_options = list(MODE_METADATA.keys())
mode_display = {k: MODE_METADATA[k]["label"] for k in mode_options}

selected_main_mode = st.sidebar.selectbox(
    "Main Commute Mode",
    options=mode_options,
    index=mode_options.index(default_vals["main_mode"]) if default_vals["main_mode"] in mode_options else 1,
    format_func=lambda x: mode_display[x],
)

one_way_dist = st.sidebar.number_input(
    "One-way Distance (km)",
    min_value=0.0,
    max_value=300.0,
    value=default_vals["one_way_km"],
    step=0.5,
)

commute_days = st.sidebar.number_input(
    "Commute Days per Month",
    min_value=0,
    max_value=31,
    value=default_vals["days"],
    step=1,
)

rush_hour_pct = st.sidebar.slider(
    "Rush-Hour Congestion Share (%)",
    min_value=0.0,
    max_value=100.0,
    value=default_vals["rush_hour"],
    step=5.0,
    help="Peak traffic in Bengaluru (Silk Board, ORR) increases stop-and-go fuel loss.",
)

vehicle_age = 0.0
if MODE_METADATA[selected_main_mode]["requires_vehicle_age"]:
    vehicle_age = st.sidebar.number_input(
        "Vehicle Age (years)",
        min_value=0.0,
        max_value=30.0,
        value=default_vals["vehicle_age"],
        step=1.0,
        help="Accounts for engine and catalytic converter wear (+2%/yr).",
    )

st.sidebar.subheader("2. Other Weekly Travel")
selected_other_mode = st.sidebar.selectbox(
    "Other Travel Mode",
    options=mode_options,
    index=mode_options.index(default_vals["other_mode"]) if default_vals["other_mode"] in mode_options else 0,
    format_func=lambda x: mode_display[x],
    key="other_mode_select",
)

other_weekly_km = st.sidebar.number_input(
    "Weekly Distance (km)",
    min_value=0.0,
    max_value=1000.0,
    value=default_vals["other_km"],
    step=1.0,
)

st.sidebar.subheader("3. Household Electricity")
electricity_kwh = st.sidebar.number_input(
    "Monthly Consumption (kWh)",
    min_value=0.0,
    max_value=5000.0,
    value=default_vals["elec_kwh"],
    step=5.0,
    help="From your BESCOM electricity bill.",
)

household_members = st.sidebar.number_input(
    "Number of Household Members",
    min_value=1,
    max_value=50,
    value=default_vals["members"],
    step=1,
    help="Divides power consumption to calculate your personal per-capita share.",
)

# Calculation
input_obj = CommuterInput(
    main_mode=selected_main_mode,
    one_way_distance_km=one_way_dist,
    commute_days_per_month=commute_days,
    rush_hour_pct=rush_hour_pct,
    vehicle_age=vehicle_age,
    other_travel_mode=selected_other_mode,
    other_travel_distance_km=other_weekly_km,
    monthly_electricity_kwh=electricity_kwh,
    household_members=household_members,
)

calc_results = compute_carbon_estimate(input_obj)
summary = calc_results["summary"]
breakdown = calc_results["breakdown"]

# ML inference
ml_pred = ml_engine.predict(input_obj.model_dump())

# Layout: 4 KPI Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        "Monthly Total CO2e",
        f"{summary['monthly_total_co2_kg']:.1f} kg",
        f"{summary['bengaluru_delta_pct']:+.1f}% vs BLR avg",
        delta_color="inverse",
    )
with col2:
    st.metric("Daily Average", f"{summary['daily_average_co2_kg']:.2f} kg/day")
with col3:
    st.metric("Annualized Footprint", f"{summary['annual_total_co2_kg']:.0f} kg/year")
with col4:
    st.metric("Trees to Offset", f"{summary['trees_offset_needed']} trees/yr")

st.divider()

# Tab Layout
tab1, tab2, tab3, tab4 = st.tabs(["📊 Breakdown & Charts", "🤖 Machine Learning Model", "🔄 What-If Alternatives", "🧾 Carbon Receipt"])

with tab1:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Emission Breakdown by Source")
        df_pie = pd.DataFrame([
            {"Activity": "Daily Commute", "Emissions (kg CO2e)": breakdown["commute"]["monthly_commute_co2_kg"]},
            {"Activity": "Other Weekly Travel", "Emissions (kg CO2e)": breakdown["other_travel"]["monthly_other_co2_kg"]},
            {"Activity": "Household Electricity", "Emissions (kg CO2e)": breakdown["electricity"]["monthly_electricity_co2_kg"]},
        ])
        fig_pie = px.pie(
            df_pie,
            names="Activity",
            values="Emissions (kg CO2e)",
            color="Activity",
            color_discrete_map={
                "Daily Commute": "#10b981",
                "Other Weekly Travel": "#14b8a6",
                "Household Electricity": "#f59e0b",
            },
            hole=0.45,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.subheader("Detailed Itemization")
        st.write(f"**Commute:** {breakdown['commute']['monthly_commute_co2_kg']:.1f} kg CO2e ({breakdown['commute']['percentage']}%)")
        st.write(f"- Monthly distance: {breakdown['commute']['monthly_distance_km']} km")
        st.write(f"- Congestion multiplier: {breakdown['commute']['congestion_multiplier']}x")
        st.write(f"- Vehicle age multiplier: {breakdown['commute']['age_multiplier']}x")

        st.write(f"**Other Travel:** {breakdown['other_travel']['monthly_other_co2_kg']:.1f} kg CO2e ({breakdown['other_travel']['percentage']}%)")
        st.write(f"- Monthly distance: {breakdown['other_travel']['monthly_distance_km']} km")

        st.write(f"**Household Electricity:** {breakdown['electricity']['monthly_electricity_co2_kg']:.1f} kg CO2e ({breakdown['electricity']['percentage']}%)")
        st.write(f"- Per-capita power: {breakdown['electricity']['per_capita_kwh']:.1f} kWh/month")
        st.write(f"- Grid emission factor: {GRID_EMISSION_FACTOR_KWH} kg CO2e/kWh")

with tab2:
    st.subheader("Machine Learning Non-Linear Estimation")
    st.info("Simulated Model Output (Trained on 5,000 synthetic Bengaluru commuter profiles with non-linear congestion & aging dynamics) - for academic demonstration.")

    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.metric("ML Predicted Monthly", f"{ml_pred['predicted_monthly_co2_kg']:.1f} kg CO2e")
        st.caption(f"95% CI: [{ml_pred['confidence_interval_monthly'][0]} - {ml_pred['confidence_interval_monthly'][1]} kg]")
    with mc2:
        st.metric("Deterministic Factor Baseline", f"{summary['monthly_total_co2_kg']:.1f} kg CO2e")
    with mc3:
        diff_kg = ml_pred['predicted_monthly_co2_kg'] - summary['monthly_total_co2_kg']
        st.metric("Model Residual / Delta", f"{diff_kg:+.2f} kg CO2e")

    if ml_pred.get("top_features"):
        st.write("**Top Learned Feature Drivers in Bengaluru Traffic:**")
        feat_df = pd.DataFrame(list(ml_pred["top_features"].items()), columns=["Feature", "Importance (%)"])
        fig_feat = px.bar(feat_df.head(6), x="Importance (%)", y="Feature", orientation="h", color="Importance (%)", color_continuous_scale="Viridis")
        st.plotly_chart(fig_feat, use_container_width=True)

with tab3:
    st.subheader("What-If Alternatives Simulator")
    st.write("Compare shifting your commute mode to cleaner alternatives in Bengaluru:")

    scenarios = calc_results["what_if_scenarios"]
    sc_df = pd.DataFrame([
        {
            "Transit Alternative": s["label"],
            "Monthly Emissions (kg)": s["alternative_monthly_co2_kg"],
            "Monthly Saved (kg)": s["monthly_saved_kg"],
            "Percent Saved (%)": s["pct_saved"],
            "Trees Saved / Yr": s["annual_trees_saved"],
        }
        for s in scenarios
    ])

    fig_whatif = px.bar(
        sc_df,
        x="Transit Alternative",
        y="Monthly Emissions (kg)",
        color="Monthly Saved (kg)",
        color_continuous_scale="Tealgrn",
        text="Monthly Emissions (kg)",
    )
    st.plotly_chart(fig_whatif, use_container_width=True)
    st.markdown(sc_df.to_html(index=False, classes="table"), unsafe_allow_html=True)

with tab4:
    st.subheader("Itemized Thermal Carbon Receipt")
    receipt_text = f"""
==================================================
        BENGALURU URBAN CARBON AUDIT
    DAILY ACTIVITIES EMISSION ESTIMATOR
        BENGALURU, KARNATAKA, INDIA
==================================================
Date: Current Session
Ref : BLR-CARB-ST-2026

1. COMMUTE ({breakdown['commute']['mode_label']})
   - Monthly Distance: {breakdown['commute']['monthly_distance_km']} km
   - Effective Rate  : {breakdown['commute']['effective_factor_kg_pkm']} kg/pkm
   - Congestion Multiplier: {breakdown['commute']['congestion_multiplier']}x
   --> SUB-TOTAL    : {breakdown['commute']['monthly_commute_co2_kg']:.2f} kg CO2e

2. OTHER TRAVEL ({breakdown['other_travel']['mode_label']})
   - Monthly Distance: {breakdown['other_travel']['monthly_distance_km']} km
   --> SUB-TOTAL    : {breakdown['other_travel']['monthly_other_co2_kg']:.2f} kg CO2e

3. HOUSEHOLD ELECTRICITY (BESCOM GRID)
   - Per-Capita Power: {breakdown['electricity']['per_capita_kwh']:.1f} kWh/mo
   - Grid Rate       : {GRID_EMISSION_FACTOR_KWH} kg CO2e/kWh
   --> SUB-TOTAL    : {breakdown['electricity']['monthly_electricity_co2_kg']:.2f} kg CO2e
--------------------------------------------------
TOTAL MONTHLY EMISSIONS : {summary['monthly_total_co2_kg']:.2f} kg CO2e
DAILY AVERAGE           : {summary['daily_average_co2_kg']:.2f} kg/day
ANNUALIZED FOOTPRINT    : {summary['annual_total_co2_kg']:.1f} kg/year
SEQUESTRATION REQUIRED  : {summary['trees_offset_needed']} Trees/year
STATUS                  : {summary['tier_label']}
==================================================
*** SMALL CHOICES MAKE A GREEN BENGALURU ***
==================================================
"""
    st.code(receipt_text, language="text")
