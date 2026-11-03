"""
Unit tests for Machine Learning Pipeline, dataset generation, predictions, and fallback handling.
"""

import unittest
import os
import pandas as pd
from dataset_generator import generate_synthetic_data
from ml_engine import CarbonMLEngine, ml_engine, extract_features_df


class TestMLEngine(unittest.TestCase):
    """Tests for dataset generation and ML model inference."""

    def test_synthetic_dataset_generation(self):
        df = generate_synthetic_data(num_samples=100, random_seed=99)
        self.assertEqual(len(df), 100)
        self.assertIn("main_mode", df.columns)
        self.assertIn("one_way_distance_km", df.columns)
        self.assertIn("total_monthly_co2_kg", df.columns)
        # All emissions must be strictly non-negative
        self.assertTrue((df["total_monthly_co2_kg"] >= 0).all())

    def test_feature_extraction(self):
        sample_df = pd.DataFrame([{
            "one_way_distance_km": 15.0,
            "commute_days_per_month": 20,
            "rush_hour_pct": 50.0,
            "household_kwh": 200.0,
            "household_members": 2,
        }])
        feats = extract_features_df(sample_df)
        self.assertEqual(feats["commute_monthly_km"].iloc[0], 600.0)
        self.assertEqual(feats["per_capita_kwh"].iloc[0], 100.0)
        self.assertEqual(feats["congestion_distance_interaction"].iloc[0], 300.0)

    def test_ml_prediction_output(self):
        input_data = {
            "main_mode": "car",
            "one_way_distance_km": 18.0,
            "commute_days_per_month": 22,
            "rush_hour_pct": 80.0,
            "vehicle_age": 5.0,
            "other_travel_mode": "cab",
            "other_travel_distance_km": 30.0,
            "monthly_electricity_kwh": 250.0,
            "household_members": 2,
        }
        res = ml_engine.predict(input_data)

        self.assertIn("predicted_monthly_co2_kg", res)
        self.assertIn("confidence_interval_monthly", res)
        self.assertIn("simulation_label", res)
        self.assertGreater(res["predicted_monthly_co2_kg"], 0.0)
        # Confidence interval lower bound <= prediction <= upper bound
        ci = res["confidence_interval_monthly"]
        self.assertLessEqual(ci[0], res["predicted_monthly_co2_kg"])
        self.assertGreaterEqual(ci[1], res["predicted_monthly_co2_kg"])

    def test_ml_fallback_mechanism(self):
        # Create an uninitialized engine instance to simulate missing model
        engine = CarbonMLEngine()
        engine.model = None  # simulate model load failure
        engine.metadata = None

        input_data = {
            "main_mode": "two_wheeler",
            "one_way_distance_km": 10.0,
            "commute_days_per_month": 20,
            "rush_hour_pct": 50.0,
            "vehicle_age": 3.0,
            "other_travel_mode": "auto",
            "other_travel_distance_km": 15.0,
            "monthly_electricity_kwh": 140.0,
            "household_members": 2,
        }
        res = engine.predict(input_data)

        # Fallback must succeed and return valid numbers
        self.assertTrue(res["is_fallback"])
        self.assertGreater(res["predicted_monthly_co2_kg"], 0.0)
        self.assertIn("Fallback", res["model_status"])


if __name__ == "__main__":
    unittest.main()
