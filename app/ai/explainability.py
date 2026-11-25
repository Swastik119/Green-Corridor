"""
Phase 10 - SHAP Explainability Engine for XGBoost Delay Predictions.

Calculates exact Shapley feature values explaining why a specific mission
has received a high or low delay-risk score.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

FEATURE_DESCRIPTIONS: Dict[str, str] = {
    "speed_current": "Current ambulance velocity",
    "speed_avg_recent": "Recent rolling average speed",
    "distance_remaining_km": "Remaining distance to recipient hospital",
    "osrm_duration_min": "OSRM baseline planned duration",
    "elapsed_time_min": "Transit time elapsed since harvest",
    "traffic_congestion_level": "Corridor traffic density level",
    "delayed_junctions_count": "Junctions with clearance delays",
    "route_deviation_flag": "Route corridor deviation",
    "gps_gap_seconds": "GPS telemetry update latency",
    "hour_of_day": "Diurnal traffic cycle (time of day)",
    "day_of_week": "Day of week transit pattern",
}


class SHAPExplainer:
    """
    Computes and formats SHAP explanations for tree-based models.
    """

    def __init__(self, model: Any, feature_names: List[str]) -> None:
        self.model = model
        self.feature_names = feature_names
        self._explainer = None

    def _get_explainer(self):
        if self._explainer is None:
            import shap
            # Use TreeExplainer for fast, exact tree-based Shapley value computation
            self._explainer = shap.TreeExplainer(self.model)
        return self._explainer

    def explain_instance(self, feature_vector: np.ndarray, top_n: int = 4) -> List[dict]:
        """
        Calculates feature contributions for a single instance.
        Returns top_n most influential features sorted by absolute SHAP impact.
        """
        try:
            explainer = self._get_explainer()
            shap_values = explainer.shap_values(feature_vector)

            # If binary classifier returns 2D array [samples, classes], take positive class index 1
            if isinstance(shap_values, list) and len(shap_values) == 2:
                vals = shap_values[1][0]
            elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 2:
                vals = shap_values[0]
            else:
                vals = np.array(shap_values).flatten()

            contributions = []
            features_1d = feature_vector.flatten()

            for i, name in enumerate(self.feature_names):
                shap_val = float(vals[i])
                feat_val = float(features_1d[i])
                impact = "increases_delay_risk" if shap_val > 0 else "decreases_delay_risk"

                desc = self._format_description(name, feat_val, shap_val)

                contributions.append({
                    "feature": name,
                    "feature_value": feat_val,
                    "shap_value": round(shap_val, 4),
                    "impact": impact,
                    "description": desc,
                })

            # Sort by descending absolute impact
            contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
            return contributions[:top_n]

        except Exception as exc:
            logger.warning("SHAP explainability computation error: %s. Using fallback feature importances.", exc)
            return self._fallback_explanation(feature_vector, top_n)

    def _format_description(self, feature: str, value: float, shap_val: float) -> str:
        pct = abs(round(shap_val * 100, 1))
        direction = "raised" if shap_val > 0 else "reduced"

        if feature == "speed_current":
            return f"Current speed ({value:.1f} km/h) {direction} delay risk by ~{pct}%"
        elif feature == "speed_avg_recent":
            return f"Average rolling speed ({value:.1f} km/h) {direction} delay risk by ~{pct}%"
        elif feature == "traffic_congestion_level":
            level_str = ["Low", "Moderate", "Heavy", "Severe"][min(3, int(value))]
            return f"{level_str} traffic congestion {direction} delay risk by ~{pct}%"
        elif feature == "delayed_junctions_count":
            return f"{int(value)} junction clearance delay(s) {direction} delay risk by ~{pct}%"
        elif feature == "route_deviation_flag":
            return f"Corridor route deviation {direction} delay risk by ~{pct}%" if value > 0 else f"On-corridor alignment {direction} delay risk by ~{pct}%"
        elif feature == "gps_gap_seconds":
            return f"GPS telemetry latency ({value:.1f}s) {direction} delay risk by ~{pct}%"
        else:
            name_clean = FEATURE_DESCRIPTIONS.get(feature, feature).capitalize()
            return f"{name_clean} {direction} risk impact by ~{pct}%"

    def _fallback_explanation(self, feature_vector: np.ndarray, top_n: int) -> List[dict]:
        """Graceful fallback if SHAP native library is unavailable."""
        importances = getattr(self.model, "feature_importances_", None)
        if importances is None:
            return []
        indices = np.argsort(importances)[::-1][:top_n]
        results = []
        for idx in indices:
            name = self.feature_names[idx]
            val = float(feature_vector.flatten()[idx])
            results.append({
                "feature": name,
                "feature_value": val,
                "shap_value": round(float(importances[idx]), 4),
                "impact": "increases_delay_risk",
                "description": f"{name} is a major predictor ({importances[idx]*100:.1f}% relative weight)",
            })
        return results
