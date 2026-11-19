/**
 * GREEN CORRIDOR AI PLATFORM - PHASES 8 & 9: REAL-TIME TRACKING & FAULT TOLERANCE
 *
 * Implements:
 *   - Mission-segregated WebSocket live GPS tracking
 *   - Automatic exponential backoff reconnection (CONNECTED, CONNECTING, DISCONNECTED, RECONNECTING)
 *   - Persistent browser IndexedDB offline GPS queue
 *   - Network auto-recovery & idempotent batch telemetry synchronization
 *   - Connection health monitoring & heartbeat indicators
 */

(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // IndexedDB Offline Telemetry Storage Helper
  // ---------------------------------------------------------------------------
  class OfflineStorage {
    constructor() {
      this.dbName = 'GreenCorridorOfflineDB';
      this.dbVersion = 1;
      this.storeName = 'pending_gps_updates';
      this.db = null;
    }

    async init() {
      if (this.db) return this.db;
      return new Promise((resolve, reject) => {
        const req = indexedDB.open(this.dbName, this.dbVersion);
        req.onupgradeneeded = (e) => {
          const db = e.target.result;
          if (!db.objectStoreNames.contains(this.storeName)) {
            const store = db.createObjectStore(this.storeName, { keyPath: 'idempotency_key' });
            store.createIndex('mission_id', 'mission_id', { unique: false });
            store.createIndex('timestamp', 'timestamp', { unique: false });
          }
        };
        req.onsuccess = (e) => {
          this.db = e.target.result;
          resolve(this.db);
        };
        req.onerror = (e) => {
          console.error('[OfflineStorage] IndexedDB open error:', e);
          reject(e);
        };
      });
    }

    async queueUpdate(update) {
      await this.init();
      return new Promise((resolve, reject) => {
        const tx = this.db.transaction([this.storeName], 'readwrite');
        const store = tx.objectStore(this.storeName);
        const req = store.put(update);
        req.onsuccess = () => resolve(true);
        req.onerror = (e) => reject(e);
      });
    }

    async getPendingUpdates(missionId = null) {
      await this.init();
      return new Promise((resolve, reject) => {
        const tx = this.db.transaction([this.storeName], 'readonly');
        const store = tx.objectStore(this.storeName);
        const req = store.getAll();
        req.onsuccess = () => {
          let items = req.result || [];
          if (missionId) {
            items = items.filter((item) => item.mission_id === missionId);
          }
          // Sort chronologically
          items.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
          resolve(items);
        };
        req.onerror = (e) => reject(e);
      });
    }

    async removeUpdates(keys) {
      if (!keys || keys.length === 0) return;
      await this.init();
      return new Promise((resolve, reject) => {
        const tx = this.db.transaction([this.storeName], 'readwrite');
        const store = tx.objectStore(this.storeName);
        keys.forEach((key) => store.delete(key));
        tx.oncomplete = () => resolve(true);
        tx.onerror = (e) => reject(e);
      });
    }

    async getCount(missionId = null) {
      const items = await this.getPendingUpdates(missionId);
      return items.length;
    }
  }

  const offlineStore = new OfflineStorage();

  // ---------------------------------------------------------------------------
  // Mission Tracker with Exponential Backoff & Sync
  // ---------------------------------------------------------------------------
  class MissionTracker {
    constructor() {
      this.ws = null;
      this.currentMissionId = null;
      this.ambulanceMarker = null;
      this.mapInstance = null;

      // State machine: CONNECTED, CONNECTING, DISCONNECTED, RECONNECTING
      this.state = 'DISCONNECTED';
      this.reconnectAttempts = 0;
      this.baseReconnectDelay = 1000;  // 1s
      this.maxReconnectDelay = 30000;  // 30s
      this.reconnectTimer = null;
      this.pingInterval = null;

      // Health metrics
      this.lastGpsTime = null;
      this.lastSyncTime = null;
      this.listeners = [];

      this.initNetworkListeners();
    }

    initNetworkListeners() {
      window.addEventListener('online', () => {
        console.log('[Tracking] Network restored online. Triggering immediate reconnect & sync.');
        this.reconnectAttempts = 0;
        if (this.currentMissionId) {
          this.connect(this.currentMissionId);
        }
      });

      window.addEventListener('offline', () => {
        console.warn('[Tracking] Network offline detected. Switching to offline queue mode.');
        this.setState('DISCONNECTED', '🔴 Network Offline (Queueing GPS)');
      });
    }

    setState(newState, statusText) {
      this.state = newState;
      this.updateStatusBadge(newState, statusText);
      this.updateHealthIndicators();
    }

    connect(missionId, options = {}) {
      if (!missionId) return;

      if (this.currentMissionId === missionId && this.ws && this.ws.readyState === WebSocket.OPEN) {
        return;
      }

      this.cleanupTimers();
      this.currentMissionId = missionId;
      if (options.map) this.mapInstance = options.map;
      if (options.marker) this.ambulanceMarker = options.marker;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/tracking/${encodeURIComponent(missionId)}`;

      this.setState('CONNECTING', '🟡 Connecting...');

      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = async () => {
          console.log(`[Tracking] WebSocket connected to mission: ${missionId}`);
          this.reconnectAttempts = 0;
          this.setState('CONNECTED', '🟢 Connected (Real-Time)');

          // Heartbeat keep-alive every 20 seconds
          this.pingInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
              this.ws.send('ping');
            }
          }, 20000);

          // Trigger automatic synchronization of offline queued updates
          await this.syncPendingOfflineUpdates(missionId);
        };

        this.ws.onmessage = (event) => {
          if (event.data === 'pong') return;
          try {
            const payload = JSON.parse(event.data);
            if (payload.type === 'gps_update' && payload.data) {
              this.handleGPSUpdate(payload.data);
            } else if (payload.type === 'gps_sync_completed') {
              console.log('[Tracking] Synchronization event received:', payload);
              if (payload.data) this.handleGPSUpdate(payload.data);
              this.updateHealthIndicators();
            } else if (payload.type === 'persistent_alert') {
              console.warn('[Tracking] Persistent alert event:', payload.data);
              if (typeof window.handleIncomingMissionAlert === 'function') {
                window.handleIncomingMissionAlert(payload.data);
              }
            } else if (payload.type === 'connection_established') {
              console.log('[Tracking] Connection handshake established:', payload);
            }
          } catch (e) {
            console.error('[Tracking] Message parse error:', e);
          }
        };

        this.ws.onclose = (event) => {
          console.warn(`[Tracking] WebSocket closed for mission ${missionId} (code: ${event.code})`);
          this.cleanupTimers();

          if (this.currentMissionId === missionId) {
            this.scheduleReconnect(missionId, options);
          } else {
            this.setState('DISCONNECTED', '⚪ Disconnected');
          }
        };

        this.ws.onerror = (err) => {
          console.error('[Tracking] WebSocket error:', err);
          this.setState('DISCONNECTED', '🔴 Connection Error');
        };
      } catch (err) {
        console.error('[Tracking] Failed to initialize WebSocket:', err);
        this.scheduleReconnect(missionId, options);
      }
    }

    scheduleReconnect(missionId, options) {
      this.reconnectAttempts += 1;
      // Exponential backoff with ±20% jitter
      const rawDelay = Math.min(
        this.maxReconnectDelay,
        this.baseReconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1)
      );
      const jitter = rawDelay * (0.8 + Math.random() * 0.4);
      const delayMs = Math.round(jitter);

      this.setState(
        'RECONNECTING',
        `🟡 Reconnecting (Attempt ${this.reconnectAttempts} in ${(delayMs / 1000).toFixed(1)}s)...`
      );

      this.reconnectTimer = setTimeout(() => {
        this.connect(missionId, options);
      }, delayMs);
    }

    async handleGPSUpdate(gps) {
      this.lastGpsTime = new Date();
      const lat = parseFloat(gps.latitude);
      const lng = parseFloat(gps.longitude);

      this.updateMapMarker(lat, lng, gps);
      this.updateDOMTelemetry(gps);
      this.updateHealthIndicators();

      this.listeners.forEach((fn) => {
        try {
          fn(gps);
        } catch (e) {
          console.error(e);
        }
      });
    }

    updateMapMarker(lat, lng, gps) {
      if (!this.mapInstance && typeof window.map !== 'undefined') {
        this.mapInstance = window.map;
      }
      if (!this.mapInstance) return;

      const popupHtml = `
        <div style="font-size:12px; line-height:1.4;">
          <strong style="color:#07899E; font-size:13px;">🚑 Ambulance ${gps.ambulance_id}</strong><br>
          <strong>Speed:</strong> ${gps.speed} km/h<br>
          <strong>Heading:</strong> ${gps.heading || 'N/A'}°<br>
          <strong>ETA:</strong> ${gps.eta_minutes ? gps.eta_minutes + ' mins' : 'Calculating'}<br>
          <span style="font-size:10px; color:${gps.is_simulated ? '#D97706' : '#218653'};">
            ${gps.is_simulated ? '⚡ Live Simulated Telemetry' : '📡 Real-Time GPS'}
          </span>
          ${gps.is_offline_sync ? '<br><span style="font-size:10px; color:#555;">(Synced from Offline Queue)</span>' : ''}
        </div>
      `;

      if (this.ambulanceMarker) {
        this.ambulanceMarker.setLatLng([lat, lng]);
        if (this.ambulanceMarker.getPopup()) {
          this.ambulanceMarker.getPopup().setContent(popupHtml);
        }
      } else {
        const ambIcon = L.divIcon({
          html: '<div style="font-size:24px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4)); animation: pulse 1.5s infinite;">🚑</div>',
          className: 'amb-live-map-icon',
          iconSize: [28, 28],
          iconAnchor: [14, 14],
        });

        this.ambulanceMarker = L.marker([lat, lng], { icon: ambIcon }).bindPopup(popupHtml);
        if (typeof window.markersLayer !== 'undefined') {
          window.markersLayer.addLayer(this.ambulanceMarker);
        } else {
          this.ambulanceMarker.addTo(this.mapInstance);
        }
      }
    }

    updateDOMTelemetry(gps) {
      document.querySelectorAll('.live-tracking-speed').forEach((el) => {
        el.textContent = `${gps.speed} km/h`;
      });
      document.querySelectorAll('.live-tracking-coords').forEach((el) => {
        el.textContent = `${gps.latitude.toFixed(4)}, ${gps.longitude.toFixed(4)}`;
      });
      document.querySelectorAll('.live-tracking-eta').forEach((el) => {
        if (gps.eta_minutes) el.textContent = `${gps.eta_minutes} Mins`;
      });
    }

    updateStatusBadge(state, text) {
      const badges = document.querySelectorAll('.tracking-status-badge');
      badges.forEach((badge) => {
        badge.textContent = text;
        badge.className = 'tracking-status-badge badge ' + (
          state === 'CONNECTED' ? 'badge-success' :
          state === 'CONNECTING' ? 'badge-warning' :
          state === 'RECONNECTING' ? 'badge-warning' :
          state === 'DISCONNECTED' ? 'badge-danger' : 'badge-neutral'
        );
      });
    }

    async updateHealthIndicators() {
      // Offline queue count
      const count = await offlineStore.getCount(this.currentMissionId);
      document.querySelectorAll('.offline-queue-count').forEach((el) => {
        el.textContent = count;
      });

      // Last GPS heartbeat time
      const gpsTimeEls = document.querySelectorAll('.last-gps-time');
      if (this.lastGpsTime) {
        const secs = Math.max(0, Math.round((new Date() - this.lastGpsTime) / 1000));
        gpsTimeEls.forEach((el) => {
          el.textContent = secs === 0 ? 'Just now' : `${secs}s ago`;
        });
      }

      // Last sync time
      const syncTimeEls = document.querySelectorAll('.last-sync-time');
      if (this.lastSyncTime) {
        syncTimeEls.forEach((el) => {
          el.textContent = this.lastSyncTime.toLocaleTimeString();
        });
      }
    }

    async queueOfflineGPS(gps) {
      const idempotencyKey = `OFFLINE_${gps.mission_id}_${gps.ambulance_id}_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
      const record = {
        idempotency_key: idempotencyKey,
        mission_id: gps.mission_id,
        ambulance_id: gps.ambulance_id,
        latitude: gps.latitude,
        longitude: gps.longitude,
        speed: gps.speed,
        heading: gps.heading || 0,
        timestamp: new Date().toISOString(),
        is_simulated: gps.is_simulated || false,
      };

      await offlineStore.queueUpdate(record);
      console.log(`[Tracking] Queued offline GPS update. Idempotency Key: ${idempotencyKey}`);
      await this.updateHealthIndicators();
      return idempotencyKey;
    }

    async syncPendingOfflineUpdates(missionId) {
      const pending = await offlineStore.getPendingUpdates(missionId);
      if (!pending || pending.length === 0) return;

      console.log(`[Tracking] Found ${pending.length} pending offline GPS updates. Synchronizing...`);

      try {
        const res = await fetch('/api/v1/tracking/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            mission_id: missionId,
            ambulance_id: pending[0].ambulance_id || 'AMB-001',
            updates: pending,
          }),
        });

        if (res.ok) {
          const result = await res.json();
          console.log('[Tracking] Synchronization successful:', result);
          const keys = pending.map((p) => p.idempotency_key);
          await offlineStore.removeUpdates(keys);
          this.lastSyncTime = new Date();
          await this.updateHealthIndicators();

          if (typeof window.showToast === 'function') {
            window.showToast(`Synchronized ${result.synced_count} offline GPS coordinates`, 'success');
          }
        }
      } catch (err) {
        console.error('[Tracking] Batch sync error:', err);
      }
    }

    cleanupTimers() {
      if (this.pingInterval) {
        clearInterval(this.pingInterval);
        this.pingInterval = null;
      }
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    }

    disconnect() {
      this.cleanupTimers();
      this.currentMissionId = null;
      if (this.ws) {
        try {
          this.ws.close();
        } catch (e) {}
        this.ws = null;
      }
      this.setState('DISCONNECTED', '⚪ Tracking Inactive');
    }

    onUpdate(fn) {
      this.listeners.push(fn);
    }
  }

  // Global Tracker instance
  window.GC_TRACKER = new MissionTracker();
  window.GC_OFFLINE_STORE = offlineStore;

  // Simulator helper controls
  window.startGpsSimulation = async function (missionId = 'GC-2024-001', ambulanceId = 'AMB-001') {
    try {
      const res = await fetch('/api/v1/tracking/simulator/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mission_id: missionId,
          ambulance_id: ambulanceId,
          interval_seconds: 1.5,
          speed_kmh: 62.0,
          loop: true,
        }),
      });
      const data = await res.json();
      if (typeof window.showToast === 'function') {
        window.showToast(`Simulated GPS tracking started for ${missionId}!`, 'success');
      }
      window.GC_TRACKER.connect(missionId);
      return data;
    } catch (err) {
      console.error('[Tracking] Failed to start simulator:', err);
    }
  };

  window.stopGpsSimulation = async function (missionId = null) {
    try {
      const url = missionId
        ? `/api/v1/tracking/simulator/stop?mission_id=${encodeURIComponent(missionId)}`
        : '/api/v1/tracking/simulator/stop';
      const res = await fetch(url, { method: 'POST' });
      const data = await res.json();
      if (typeof window.showToast === 'function') {
        window.showToast('GPS movement simulator stopped.', 'info');
      }
      return data;
    } catch (err) {
      console.error('[Tracking] Failed to stop simulator:', err);
    }
  };
})();
