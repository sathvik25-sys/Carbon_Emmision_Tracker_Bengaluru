"""
Unit tests for FastAPI REST API endpoints and static templates.
"""

import unittest
from starlette.testclient import TestClient
from app import app


class TestAPIEndpoints(unittest.TestCase):
    """Tests for FastAPI HTTP endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_get_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Bengaluru Carbon Tracker", response.text)
        self.assertIn("Carbon Receipt", response.text)

    def test_get_config(self):
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("emission_factors", data)
        self.assertIn("grid_factor_kwh", data)
        self.assertEqual(data["grid_factor_kwh"], 0.716)

    def test_get_presets(self):
        response = self.client.get("/api/presets")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("whitefield_techie", data)
        self.assertIn("metro_commuter", data)

    def test_post_calculate_valid(self):
        payload = {
            "main_mode": "two_wheeler",
            "one_way_distance_km": 12.0,
            "commute_days_per_month": 22,
            "rush_hour_pct": 50.0,
            "vehicle_age": 3.0,
            "other_travel_mode": "auto",
            "other_travel_distance_km": 20.0,
            "monthly_electricity_kwh": 160.0,
            "household_members": 2,
        }
        response = self.client.post("/api/calculate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["summary"]["monthly_total_co2_kg"], 0.0)
        self.assertIn("what_if_scenarios", data)
        self.assertIn("recommendations", data)

    def test_post_calculate_invalid_negative(self):
        payload = {
            "main_mode": "car",
            "one_way_distance_km": -10.0,  # Invalid
            "commute_days_per_month": 22,
            "monthly_electricity_kwh": 100.0,
            "household_members": 1,
        }
        response = self.client.post("/api/calculate", json=payload)
        self.assertEqual(response.status_code, 422)  # Pydantic validation error

    def test_post_predict_ml(self):
        payload = {
            "main_mode": "car",
            "one_way_distance_km": 15.0,
            "commute_days_per_month": 20,
            "rush_hour_pct": 75.0,
            "vehicle_age": 4.0,
            "other_travel_mode": "cab",
            "other_travel_distance_km": 25.0,
            "monthly_electricity_kwh": 200.0,
            "household_members": 2,
        }
        response = self.client.post("/api/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("ml_prediction", data)
        self.assertIn("factor_baseline", data)
        self.assertIn("comparison", data)

    def test_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")


if __name__ == "__main__":
    unittest.main()
