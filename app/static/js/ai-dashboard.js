/**
 * GREEN CORRIDOR AI PLATFORM - PHASE 10: AI MISSION INTELLIGENCE & HUMAN-IN-THE-LOOP RESPONSE
 *
 * Provides:
 *   - Real-time XGBoost Mission Delay Risk assessment
 *   - SHAP explainability visualizer
 *   - Isolation Forest anomaly detection alerts
 *   - ML dynamic ETA prediction
 *   - Alternative route recommendation & operator approval workflow
 */

(function () {
  'use strict';

  class AIMissionIntelligence {
    constructor() {
      this.currentMissionId = 'GC-2024-001';
      this.currentPrediction = null;
      this.pendingRecommendation = null;
    }

    /**
     * Evaluates delay risk using current mission telemetry.
     */
    async evaluateMissionRisk(missionId = null) {
      const mid = missionId || this.currentMissionId;
      const mission = (window.GC_DATA && window.GC_DATA.getMissionById(mid)) || {
        id: mid,
        speed: 48.0,
        distanceRemaining: 7.2,
        etaMinutes: 12.0,
      };

      try {
        const payload = {
          mission_id: mid,
          speed_current: mission.speed || 52.0,
          speed_avg_recent: (mission.speed || 52.0) * 0.95,
          distance_remaining_km: mission.distanceRemaining || 7.2,
          osrm_duration_min: mission.etaMinutes || 12.0,
          elapsed_time_min: 4.5,
          traffic_congestion_level: 1,
          delayed_junctions_count: 0,
          route_deviation_flag: 0,
          gps_gap_seconds: 2.0,
          hour_of_day: new Date().getHours(),
          day_of_week: new Date().getDay(),
        };

        const res = await fetch('/api/v1/ai/predict-delay', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (res.ok) {
          this.currentPrediction = await res.json();
          this.renderAIIntelligence(this.currentPrediction);
          return this.currentPrediction;
        }
      } catch (err) {
        console.error('[AI] Delay prediction error:', err);
      }
    }

    /**
     * Renders prediction metrics, SHAP factors, and recommendations to the DOM.
     */
    renderAIIntelligence(pred) {
      if (!pred) return;

      // 1. Risk probability badge & bar
      const probPct = Math.round(pred.delay_probability * 100);
      const probEl = document.getElementById('ai-delay-prob');
      if (probEl) probEl.textContent = `${probPct}%`;

      const barEl = document.getElementById('ai-delay-bar');
      if (barEl) {
        barEl.style.width = `${probPct}%`;
        barEl.style.backgroundColor = (
          pred.risk_category === 'CRITICAL' ? '#C53030' :
          pred.risk_category === 'HIGH' ? '#D97706' :
          pred.risk_category === 'MEDIUM' ? '#2B6CB0' : '#218653'
        );
      }

      const riskBadge = document.getElementById('ai-risk-badge');
      if (riskBadge) {
        riskBadge.textContent = pred.risk_category;
        riskBadge.className = 'badge ' + (
          pred.risk_category === 'CRITICAL' ? 'badge-danger' :
          pred.risk_category === 'HIGH' ? 'badge-warning' :
          pred.risk_category === 'MEDIUM' ? 'badge-blue' : 'badge-green'
        );
      }

      // 2. Action suggestion text
      const actionEl = document.getElementById('ai-action-suggestion');
      if (actionEl) actionEl.textContent = pred.suggested_action;

      // 3. SHAP Contributing Factors Breakdown
      const factorsContainer = document.getElementById('ai-shap-factors');
      if (factorsContainer && pred.top_contributing_factors) {
        factorsContainer.innerHTML = '';
        pred.top_contributing_factors.forEach((f) => {
          const isIncrease = f.impact === 'increases_delay_risk';
          const tag = document.createElement('div');
          tag.style.cssText = `
            font-size: 11px;
            padding: 4px 8px;
            margin-bottom: 4px;
            border-left: 3px solid ${isIncrease ? '#C53030' : '#218653'};
            background: #F8F9FA;
            display: flex;
            justify-content: space-between;
          `;
          tag.innerHTML = `
            <span>${f.description}</span>
            <span style="font-weight:bold; color:${isIncrease ? '#C53030' : '#218653'};">
              ${isIncrease ? '▲ +' : '▼ -'}${Math.abs(f.shap_value * 100).toFixed(1)}%
            </span>
          `;
          factorsContainer.appendChild(tag);
        });
      }

      // 4. Check for high risk alternative route recommendation
      if (pred.risk_category === 'HIGH' || pred.risk_category === 'CRITICAL') {
        this.fetchAlternativeRoute(pred.mission_id);
      } else {
        const altCard = document.getElementById('ai-alternative-route-card');
        if (altCard) altCard.style.display = 'none';
      }
    }

    /**
     * Retrieves alternative route recommendation when risk is elevated.
     */
    async fetchAlternativeRoute(missionId) {
      try {
        const res = await fetch(`/api/v1/ai/alternative-route/${encodeURIComponent(missionId)}`);
        if (res.ok) {
          const rec = await res.json();
          this.pendingRecommendation = rec;
          this.renderAlternativeRouteCard(rec);
        }
      } catch (e) {
        console.error('[AI] Alternative route error:', e);
      }
    }

    renderAlternativeRouteCard(rec) {
      const card = document.getElementById('ai-alternative-route-card');
      if (!card) return;

      card.style.display = 'block';
      const timeSaveEl = document.getElementById('ai-alt-time-saved');
      if (timeSaveEl) timeSaveEl.textContent = `${rec.potential_time_saved_min} mins`;

      const etaEl = document.getElementById('ai-alt-eta');
      if (etaEl) etaEl.textContent = `${rec.alternative_route_eta_min} mins`;

      const noteEl = document.getElementById('ai-alt-notes');
      if (noteEl) noteEl.textContent = rec.operator_notes || 'Bypasses congested sector via parallel arterial.';
    }

    /**
     * Human-in-the-loop operator approval
     */
    async approveAlternativeRoute() {
      const mid = this.currentMissionId;
      try {
        const res = await fetch('/api/v1/ai/route-change/approve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            mission_id: mid,
            operator_name: 'Central Control Supervisor',
            notes: 'Approved via Control Room AI Console.',
          }),
        });
        if (res.ok) {
          const data = await res.json();
          const card = document.getElementById('ai-alternative-route-card');
          if (card) card.style.display = 'none';
          if (typeof window.showToast === 'function') {
            window.showToast(`✅ Route change APPROVED for ${mid}! New corridor active.`, 'success');
          }
        }
      } catch (e) {
        console.error(e);
      }
    }

    async rejectAlternativeRoute() {
      const mid = this.currentMissionId;
      try {
        await fetch('/api/v1/ai/route-change/reject', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mission_id: mid }),
        });
        const card = document.getElementById('ai-alternative-route-card');
        if (card) card.style.display = 'none';
        if (typeof window.showToast === 'function') {
          window.showToast(`Route change rejected. Maintaining designated corridor for ${mid}.`, 'info');
        }
      } catch (e) {
        console.error(e);
      }
    }
  }

  // Global AI Intelligence Instance
  window.GC_AI = new AIMissionIntelligence();

  // Global listener for incoming persistent alerts & AI warnings over WebSocket
  window.handleIncomingMissionAlert = function (alertData) {
    if (typeof window.showToast === 'function') {
      const toastType = alertData.severity === 'critical' ? 'danger' : 'warning';
      window.showToast(`🚨 [${alertData.alert_type}] ${alertData.message}`, toastType);
    }
  };

  // Auto-evaluate when control room opens
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
      if (window.GC_AI) {
        window.GC_AI.evaluateMissionRisk('GC-2024-001');
      }
    }, 1500);
  });
})();
