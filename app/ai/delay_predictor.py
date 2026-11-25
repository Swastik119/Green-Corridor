"""
Phase 10 - XGBoost Mission Delay Risk Prediction Engine.

Predicts the probability of significant transit delay for active organ transport missions
using structured operational telemetry, calibrated risk tiers, and SHAP explainability.
"""

from __future__ import annotations

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.dummy import DummyClassifier

from app.schemas.ai import DelayRiskInput, DelayRiskPrediction, FeatureContribution
from app.ai.synthetic_data import generate_synthetic_transit_dataset
from app.ai.explainability import SHAPExplainer

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "speed_current",
    "speed_avg_recent",
    "distance_remaining_km",
    "osrm_duration_min",
    "elapsed_time_min",
    "traffic_congestion_level",
    "delayed_junctions_count",
    "route_deviation_flag",
    "gps_gap_seconds",
    "hour_of_day",
    "day_of_week",
]

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "xgb_delay_model.json"
METADATA_PATH = MODEL_DIR / "xgb_delay_metadata.json"


class DelayPredictor:
    """
    XGBoost-powered organ transit delay risk classification engine.
    """

    def __init__(self) -> None:
        self.model: Optional[XGBClassifier] = None
        self.metadata: Dict[str, Any] = {}
        self.explainer: Optional[SHAPExplainer] = None
        self.feature_names = FEATURE_COLUMNS
        self._ensure_model_loaded()

    def _ensure_model_loaded(self) -> None:
        """Loads trained model from disk or initiates training if absent."""
        if MODEL_PATH.exists() and METADATA_PATH.exists():
            try:
                self.model = XGBClassifier()
                self.model.load_model(str(MODEL_PATH))
                with open(METADATA_PATH, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                self.explainer = SHAPExplainer(self.model, self.feature_names)
                logger.info("Loaded pre-trained XGBoost delay model (v%s)", self.metadata.get("version", "1.0.0"))
                return
            except Exception as exc:
                logger.warning("Failed to load existing model: %s. Re-training...", exc)

        self.train_and_evaluate()

    def train_and_evaluate(self, n_samples: int = 1500, random_seed: int = 42) -> Dict[str, Any]:
        """
        Trains the XGBoost classifier, computes evaluation metrics, and persists artifacts.
        """
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        df = generate_synthetic_transit_dataset(n_samples=n_samples, random_seed=random_seed)

        X = df[self.feature_names].values
        y = df["delayed"].values

        # Stratified Train/Test Split (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=random_seed, stratify=y
        )

        # Baseline: Dummy Classifier (predicts most frequent class)
        baseline = DummyClassifier(strategy="most_frequent")
        baseline.fit(X_train, y_train)
        baseline_acc = float(baseline.score(X_test, y_test))

        # XGBoost Classifier
        clf = XGBClassifier(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            eval_metric="logloss",
            random_state=random_seed,
        )
        clf.fit(X_train, y_train)

        # Evaluation metrics
        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test)[:, 1]

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        roc_auc = float(roc_auc_score(y_test, y_prob))
        cm = confusion_matrix(y_test, y_pred).tolist()

        metadata = {
            "model_name": "XGBoost-Mission-Delay-Classifier",
            "version": "1.0.0",
            "trained_at": datetime.utcnow().isoformat(),
            "n_training_samples": len(X_train),
            "n_testing_samples": len(X_test),
            "baseline_accuracy": round(baseline_acc, 4),
            "metrics": {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(roc_auc, 4),
                "confusion_matrix": cm,
            },
            "feature_names": self.feature_names,
            "hyperparameters": {
                "n_estimators": 120,
                "max_depth": 4,
                "learning_rate": 0.08,
                "subsample": 0.85,
            },
        }

        # Save artifacts
        clf.save_model(str(MODEL_PATH))
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        self.model = clf
        self.metadata = metadata
        self.explainer = SHAPExplainer(self.model, self.feature_names)

        logger.info(
            "XGBoost training complete. Accuracy: %.2f%% | ROC-AUC: %.2f%% (vs Baseline: %.2f%%)",
            acc * 100,
            roc_auc * 100,
            baseline_acc * 100,
        )
        return metadata

    def predict(self, input_data: DelayRiskInput) -> DelayRiskPrediction:
        """
        Executes real-time inference for a mission and returns risk category and SHAP explanation.
        """
        if self.model is None:
            self._ensure_model_loaded()

        now = datetime.utcnow()
        hour = input_data.hour_of_day if input_data.hour_of_day is not None else now.hour
        weekday = input_data.day_of_week if input_data.day_of_week is not None else now.weekday()

        features = np.array([
            input_data.speed_current,
            input_data.speed_avg_recent,
            input_data.distance_remaining_km,
            input_data.osrm_duration_min,
            input_data.elapsed_time_min,
            float(input_data.traffic_congestion_level),
            float(input_data.delayed_junctions_count),
            float(input_data.route_deviation_flag),
            input_data.gps_gap_seconds,
            float(hour),
            float(weekday),
        ]).reshape(1, -1)

        # XGBoost probability
        prob = float(self.model.predict_proba(features)[0, 1])
        prob_clamped = max(0.0, min(1.0, prob))

        # Risk Tier Classification
        if prob_clamped >= 0.80:
            risk = "CRITICAL"
            action = "🚨 CRITICAL DELAY IMMINENT: Initiate automated signal preemption and review alternate arterial corridor."
        elif prob_clamped >= 0.60:
            risk = "HIGH"
            action = "⚠️ HIGH DELAY RISK: Alert South Traffic Command to prioritize upcoming junction clearances."
        elif prob_clamped >= 0.30:
            risk = "MEDIUM"
            action = "🟡 MODERATE RISK: Maintain convoy velocity; monitor upcoming bottleneck intersections."
        else:
            risk = "LOW"
            action = "🟢 OPTIMAL CONVOY PROGRESS: Corridor speed is within target parameters."

        # SHAP feature contributions
        contributions = []
        if self.explainer:
            raw_contribs = self.explainer.explain_instance(features, top_n=4)
            for c in raw_contribs:
                contributions.append(FeatureContribution(**c))

        return DelayRiskPrediction(
            mission_id=input_data.mission_id,
            delay_probability=round(prob_clamped, 4),
            risk_category=risk,
            predicted_delay=bool(prob_clamped >= 0.50),
            prediction_timestamp=now,
            model_version=self.metadata.get("version", "1.0.0"),
            top_contributing_factors=contributions,
            suggested_action=action,
        )


# Global singleton instance
delay_predictor = DelayPredictor()
