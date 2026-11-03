"""
Unit tests for emission calculator, input validations, edge cases, and what-if simulation.
"""

import unittest
from pydantic import ValidationError
from config import (
    EMISSION_FACTORS,
    GRID_EMISSION_FACTOR_KWH,
    CONGESTION_MAX_PENALTY,
    VEHICLE_AGE_PENALTY_PER_YEAR,
    MAX_VEHICLE_AGE_PENALTY,
)
from calculator import (
    CommuterInput,
    calculate_commute_details,
    calculate_other_travel_details,
    calculate_electricity_details,
    compute_carbon_estimate,
    compute_what_if_scenarios,
)


class TestCalculatorCore(unittest.TestCase):
    """Tests for core math, factors, and emission equations."""

    def test_walking_has_zero_emissions(self):
        result = calculate_commute_details(
            main_mode="walk_cycle",
            one_way_distance_km=5.0,
            commute_days_per_month=20,
            rush_hour_pct=100.0,
            vehicle_age=10.0,
        )
        self.assertEqual(result["monthly_commute_co2_kg"], 0.0)
        self.assertEqual(result["base_factor_kg_pkm"], 0.0)
        self.assertEqual(result["congestion_multiplier"], 1.0)
        self.assertEqual(result["age_multiplier"], 1.0)

    def test_metro_unaffected_by_congestion(self):
        # 10 km one way, 20 days -> 400 km
        # Factor 0.018 kg/km -> 7.2 kg CO2e
        result = calculate_commute_details(
            main_mode="namma_metro",
            one_way_distance_km=10.0,
            commute_days_per_month=20,
            rush_hour_pct=100.0,
            vehicle_age=5.0,
        )
        self.assertEqual(result["congestion_multiplier"], 1.0)
        self.assertEqual(result["age_multiplier"], 1.0)
        self.assertAlmostEqual(result["monthly_commute_co2_kg"], 7.2, places=2)

    def test_car_congestion_and_age_penalties(self):
        # 10 km one way, 10 days -> 200 km
        # Base factor car = 0.155 kg/km
        # Rush hour = 100% -> congestion multiplier = 1 + 0.35 = 1.35
        # Vehicle age = 5 years -> age penalty = 5 * 0.02 = 0.10 -> multiplier = 1.10
        # Effective factor = 0.155 * 1.35 * 1.10 = 0.230175
        # Monthly CO2 = 200 * 0.230175 = 46.035 kg
        result = calculate_commute_details(
            main_mode="car",
            one_way_distance_km=10.0,
            commute_days_per_month=10,
            rush_hour_pct=100.0,
            vehicle_age=5.0,
        )
        self.assertAlmostEqual(result["congestion_multiplier"], 1.35, places=2)
        self.assertAlmostEqual(result["age_multiplier"], 1.10, places=2)
        expected_co2 = 200.0 * (0.155 * 1.35 * 1.10)
        self.assertAlmostEqual(result["monthly_commute_co2_kg"], round(expected_co2, 3), places=2)

    def test_vehicle_age_penalty_capping(self):
        # Age penalty capped at MAX_VEHICLE_AGE_PENALTY (30% -> 1.30x)
        result = calculate_commute_details(
            main_mode="car",
            one_way_distance_km=10.0,
            commute_days_per_month=10,
            rush_hour_pct=0.0,
            vehicle_age=25.0,  # 25 * 0.02 = 0.50, but should be capped at 0.30
        )
        self.assertAlmostEqual(result["age_multiplier"], 1.0 + MAX_VEHICLE_AGE_PENALTY, places=2)

    def test_electricity_per_capita_division(self):
        # 200 kWh shared by 4 people -> 50 kWh per person
        # Grid factor 0.716 -> 50 * 0.716 = 35.8 kg CO2e
        result = calculate_electricity_details(
            monthly_electricity_kwh=200.0,
            household_members=4,
        )
        self.assertEqual(result["per_capita_kwh"], 50.0)
        self.assertAlmostEqual(result["monthly_electricity_co2_kg"], 35.8, places=2)
        self.assertAlmostEqual(result["total_household_monthly_co2_kg"], 143.2, places=2)

    def test_division_by_zero_protection(self):
        # 0 or negative members handled gracefully to prevent ZeroDivisionError
        result = calculate_electricity_details(
            monthly_electricity_kwh=100.0,
            household_members=0,
        )
        self.assertEqual(result["household_members"], 1)
        self.assertEqual(result["per_capita_kwh"], 100.0)


class TestInputValidations(unittest.TestCase):
    """Tests for Pydantic input schema constraints."""

    def test_valid_input_passes(self):
        payload = CommuterInput(
            main_mode="two_wheeler",
            one_way_distance_km=15.0,
            commute_days_per_month=22,
            rush_hour_pct=50.0,
            vehicle_age=3.0,
            other_travel_mode="auto",
            other_travel_distance_km=20.0,
            monthly_electricity_kwh=150.0,
            household_members=3,
        )
        self.assertEqual(payload.main_mode, "two_wheeler")
        self.assertEqual(payload.household_members, 3)

    def test_negative_distance_raises_error(self):
        with self.assertRaises(ValidationError):
            CommuterInput(
                main_mode="car",
                one_way_distance_km=-5.0,
                commute_days_per_month=20,
                monthly_electricity_kwh=100.0,
            )

    def test_excessive_distance_raises_error(self):
        with self.assertRaises(ValidationError):
            CommuterInput(
                main_mode="car",
                one_way_distance_km=450.0,  # Max allowed is 300 km
                commute_days_per_month=20,
                monthly_electricity_kwh=100.0,
            )

    def test_invalid_commute_days_raises_error(self):
        with self.assertRaises(ValidationError):
            CommuterInput(
                main_mode="car",
                one_way_distance_km=10.0,
                commute_days_per_month=35,  # Max 31 days
                monthly_electricity_kwh=100.0,
            )

    def test_zero_or_negative_members_raises_error(self):
        with self.assertRaises(ValidationError):
            CommuterInput(
                main_mode="car",
                one_way_distance_km=10.0,
                commute_days_per_month=20,
                monthly_electricity_kwh=100.0,
                household_members=0,  # Min 1
            )

    def test_unknown_transit_mode_raises_error(self):
        with self.assertRaises(ValidationError):
            CommuterInput(
                main_mode="supersonic_jet",
                one_way_distance_km=10.0,
                commute_days_per_month=20,
                monthly_electricity_kwh=100.0,
            )


class TestWhatIfScenarios(unittest.TestCase):
    """Tests for what-if alternative transit calculations."""

    def test_what_if_savings_positive_when_switching_from_car(self):
        # Car commute: 15 km, 20 days -> 600 km
        # Current car co2 ~ 93 kg
        scenarios = compute_what_if_scenarios(
            current_monthly_commute_co2=93.0,
            one_way_distance_km=15.0,
            commute_days_per_month=20,
            current_mode="car",
        )
        self.assertGreater(len(scenarios), 3)

        # Metro scenario should save emissions
        metro = next(s for s in scenarios if s["id"] == "namma_metro")
        self.assertGreater(metro["monthly_saved_kg"], 0.0)
        self.assertGreater(metro["pct_saved"], 80.0)

        # Walk/cycle scenario should save 100% of commute emissions
        walk = next(s for s in scenarios if s["id"] == "walk_cycle")
        self.assertEqual(walk["alternative_monthly_co2_kg"], 0.0)
        self.assertAlmostEqual(walk["monthly_saved_kg"], 93.0, places=1)


class TestCompleteEstimate(unittest.TestCase):
    """End-to-end integration test for complete estimate pipeline."""

    def test_compute_carbon_estimate_structure(self):
        inp = CommuterInput(
            main_mode="two_wheeler",
            one_way_distance_km=12.0,
            commute_days_per_month=22,
            rush_hour_pct=50.0,
            vehicle_age=2.0,
            other_travel_mode="auto",
            other_travel_distance_km=15.0,
            monthly_electricity_kwh=180.0,
            household_members=2,
        )
        res = compute_carbon_estimate(inp)

        self.assertEqual(res["status"], "success")
        self.assertIn("summary", res)
        self.assertIn("breakdown", res)
        self.assertIn("what_if_scenarios", res)
        self.assertIn("recommendations", res)
        self.assertIn("methodology", res)

        # Total should equal sum of components
        total = res["summary"]["monthly_total_co2_kg"]
        parts_sum = (
            res["breakdown"]["commute"]["monthly_commute_co2_kg"]
            + res["breakdown"]["other_travel"]["monthly_other_co2_kg"]
            + res["breakdown"]["electricity"]["monthly_electricity_co2_kg"]
        )
        self.assertAlmostEqual(total, parts_sum, places=1)

        # Percentages sum to 100%
        pct_sum = (
            res["breakdown"]["commute"]["percentage"]
            + res["breakdown"]["other_travel"]["percentage"]
            + res["breakdown"]["electricity"]["percentage"]
        )
        self.assertAlmostEqual(pct_sum, 100.0, delta=0.5)


if __name__ == "__main__":
    unittest.main()
