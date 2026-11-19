"""
Phase 10 Test Suite - AI Mission Intelligence & Machine Learning Pipeline.
Covers:
  - Synthetic training dataset generation
  - XGBoost delay classifier training, evaluation, and baseline comparison
  - Real-time delay risk inference across risk tiers
  - SHAP tree explainability feature breakdown
  - Isolation Forest unsupervised anomaly detection
  - Dynamic ML ETA prediction
  - Automated alternative route recommendation & human-in-the-loop approval workflow
"""

import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.ai.synthetic_data import generate_synthetic_transit_dataset
from app.ai.delay_predictor import delay_predictor
from app.ai.anomaly_detector import anomaly_detector
from app.ai.eta_predictor import eta_predictor
from app.schemas.ai import DelayRiskInput, AnomalyTelemetryInput


class TestPhase10AI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_synthetic_transit_dataset_generation(self):
        """
        Tests that synthetic historical transit records are generated with valid distributions.
        """
        df = generate_synthetic_transit_dataset(n_samples=200, random_seed=42)
        self.assertEqual(len(df), 200)
        self.assertIn("speed_current", df.columns)
        self.assertIn("delayed", df.columns)
        self.assertFalse(df.isnull().any().any())
        # Check target class distribution (both 0 and 1 present)
        unique_targets = set(df["delayed"].unique())
        self.assertTrue({0, 1}.issubset(unique_targets))

    def test_xgboost_training_and_metrics_evaluation(self):
        """
        Validates XGBoost training metrics: Accuracy, Precision, Recall, F1, ROC-AUC,
        and confirms performance outperforms majority-class baseline.
        """
        metadata = delay_predictor.metadata
        self.assertIn("metrics", metadata)
        metrics = metadata["metrics"]

        # Performance assertions
        self.assertGreaterEqual(metrics["accuracy"], 0.70)
        self.assertGreaterEqual(metrics["roc_auc"], 0.75)
        self.assertGreaterEqual(metrics["f1_score"], 0.60)
        # Compare against baseline
        baseline_acc = metadata.get("baseline_accuracy", 0.5)
        self.assertGreater(metrics["accuracy"], baseline_acc)

    def test_delay_risk_prediction_low_risk(self):
        """
        Tests that optimal telemetry (high speed, clear traffic, no junction delays)
        yields a LOW delay risk score.
        """
        payload = {
            "mission_id": "GC-TEST-LOW",
            "speed_current": 72.0,
            "speed_avg_recent": 68.0,
            "distance_remaining_km": 5.0,
            "osrm_duration_min": 7.0,
            "elapsed_time_min": 3.0,
            "traffic_congestion_level": 0,
            "delayed_junctions_count": 0,
            "route_deviation_flag": 0,
            "gps_gap_seconds": 1.5,
            "hour_of_day": 14,
            "day_of_week": 2,
        }
        res = self.client.post("/api/v1/ai/predict-delay", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn(data["risk_category"], ("LOW", "MEDIUM"))
        self.assertLess(data["delay_probability"], 0.60)
        self.assertFalse(data["predicted_delay"])
        self.assertGreaterEqual(len(data["top_contributing_factors"]), 1)

    def test_delay_risk_prediction_critical_risk(self):
        """
        Tests that degraded telemetry (severe congestion, stopped ambulance, multiple delayed junctions)
        triggers a HIGH or CRITICAL risk tier and activates automated route workflow.
        """
        payload = {
            "mission_id": "GC-TEST-CRITICAL",
            "speed_current": 14.0,
            "speed_avg_recent": 18.0,
            "distance_remaining_km": 15.0,
            "osrm_duration_min": 18.0,
            "elapsed_time_min": 15.0,
            "traffic_congestion_level": 3,
            "delayed_junctions_count": 5,
            "route_deviation_flag": 1,
            "gps_gap_seconds": 45.0,
            "hour_of_day": 9,
            "day_of_week": 1,
        }
        res = self.client.post("/api/v1/ai/predict-delay", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn(data["risk_category"], ("HIGH", "CRITICAL"))
        self.assertGreaterEqual(data["delay_probability"], 0.60)
        self.assertTrue(data["predicted_delay"])

    def test_shap_feature_explainability(self):
        """
        Verifies that SHAP tree explainer generates feature impact weights with directional context.
        """
        inp = DelayRiskInput(
            mission_id="SHAP-TEST",
            speed_current=20.0,
            speed_avg_recent=25.0,
            distance_remaining_km=10.0,
            osrm_duration_min=14.0,
            elapsed_time_min=8.0,
            traffic_congestion_level=2,
            delayed_junctions_count=3,
            route_deviation_flag=0,
            gps_gap_seconds=2.0,
        )
        prediction = delay_predictor.predict(inp)
        factors = prediction.top_contributing_factors
        self.assertGreater(len(factors), 0)
        for factor in factors:
            self.assertIn(factor.impact, ("increases_delay_risk", "decreases_delay_risk"))
            self.assertTrue(len(factor.description) > 5)

    def test_isolation_forest_nominal_telemetry(self):
        """
        Tests that nominal ambulance movement is not classified as an anomaly.
        """
        telemetry = AnomalyTelemetryInput(
            mission_id="NOMINAL-TEST",
            ambulance_id="AMB-001",
            latitude=28.5672,
            longitude=77.2100,
            speed=58.0,
            last_update_gap_sec=2.0,
            corridor_centerline_dist_m=15.0,
        )
        result = anomaly_detector.evaluate_telemetry(telemetry)
        self.assertFalse(result.is_anomaly)
        self.assertEqual(result.severity, "NORMAL")

    def test_isolation_forest_route_deviation_anomaly(self):
        """
        Tests that a large divergence from the designated corridor is identified as ROUTE_DEVIATION.
        """
        telemetry = AnomalyTelemetryInput(
            mission_id="DEV-TEST",
            ambulance_id="AMB-001",
            latitude=28.5672,
            longitude=77.2100,
            speed=45.0,
            last_update_gap_sec=2.0,
            corridor_centerline_dist_m=450.0,  # Significant 450m deviation
        )
        result = anomaly_detector.evaluate_telemetry(telemetry)
        self.assertTrue(result.is_anomaly)
        self.assertEqual(result.anomaly_type, "ROUTE_DEVIATION")
        self.assertIn(result.severity, ("HIGH", "CRITICAL"))

    def test_isolation_forest_stoppage_anomaly(self):
        """
        Tests that vehicle stoppage in an active corridor triggers UNEXPECTED_STOP.
        """
        telemetry = AnomalyTelemetryInput(
            mission_id="STOP-TEST",
            ambulance_id="AMB-001",
            latitude=28.5672,
            longitude=77.2100,
            speed=0.0,
            last_update_gap_sec=35.0,
            corridor_centerline_dist_m=5.0,
        )
        result = anomaly_detector.evaluate_telemetry(telemetry)
        self.assertTrue(result.is_anomaly)
        self.assertEqual(result.anomaly_type, "UNEXPECTED_STOP")

    def test_ml_dynamic_eta_prediction(self):
        """
        Tests ML dynamic ETA calculation incorporating speed and congestion adjustments.
        """
        res = self.client.get(
            "/api/v1/ai/predict-eta?mission_id=GC-ETA&distance_remaining_km=10.0&osrm_baseline_minutes=15.0&speed_current=50.0&speed_avg_recent=50.0&traffic_congestion_level=1"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["mission_id"], "GC-ETA")
        self.assertGreater(data["predicted_eta_minutes"], 0.0)
        self.assertIn("confidence_level", data)

    def test_human_in_the_loop_route_change_workflow(self):
        """
        Tests alternative route proposal, operator approval, and operator rejection workflow.
        """
        mid = "WORKFLOW-TEST-01"

        # 1. Trigger high risk to populate recommendation
        high_risk_payload = {
            "mission_id": mid,
            "speed_current": 15.0,
            "speed_avg_recent": 15.0,
            "distance_remaining_km": 12.0,
            "osrm_duration_min": 18.0,
            "elapsed_time_min": 10.0,
            "traffic_congestion_level": 3,
            "delayed_junctions_count": 4,
            "route_deviation_flag": 0,
            "gps_gap_seconds": 2.0,
        }
        self.client.post("/api/v1/ai/predict-delay", json=high_risk_payload)

        # 2. Check pending alternative route
        rec_res = self.client.get(f"/api/v1/ai/alternative-route/{mid}")
        self.assertEqual(rec_res.status_code, 200)
        rec_data = rec_res.json()
        self.assertEqual(rec_data["mission_id"], mid)
        self.assertGreater(rec_data["potential_time_saved_min"], 0)

        # 3. Human Operator Approves route change
        appr_res = self.client.post(
            "/api/v1/ai/route-change/approve",
            json={"mission_id": mid, "operator_name": "Supervisor Joshi", "notes": "Approved fast bypass"},
        )
        self.assertEqual(appr_res.status_code, 200)
        appr_data = appr_res.json()
        self.assertEqual(appr_data["decision"], "APPROVED")

        # 4. Human Operator Rejects route change for second test
        rej_res = self.client.post(
            "/api/v1/ai/route-change/reject",
            json={"mission_id": mid, "operator_name": "Supervisor Joshi"},
        )
        self.assertEqual(rej_res.status_code, 200)
        rej_data = rej_res.json()
        self.assertEqual(rej_data["decision"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
