/**
 * 285IQ Service Worker
 * - Cache-first for static assets
 * - Network-first for API calls
 * - Offline queue for POST /api/attempts/ via IndexedDB
 * - Offline fallback page when network unavailable
 */

const CACHE_NAME = '285iq-v1';
const STATIC_CACHE_URLS = [
  '/',
  '/static/offline.html',
  '/static/manifest.json',
];
const API_PRECACHE_URLS = [
  '/api/flashcards/due-count/',
  '/api/loop-metrics/',
];
const OFFLINE_FALLBACK = '/static/offline.html';
const IDB_NAME = '285iq-queue';
const IDB_STORE = 'attempts';

// ── IndexedDB helpers ─────────────────────────────────────────────────────────

function openQueue() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(IDB_NAME, 1);
    req.onupgradeneeded = (e) => {
      e.target.result.createObjectStore(IDB_STORE, {
        keyPath: 'id',
        autoIncrement: true,
      });
    };
    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror = (e) => reject(e.target.error);
  });
}

async function enqueueAttempt(request) {
  const body = await request.clone().text();
  const headers = {};
  request.headers.forEach((value, key) => { headers[key] = value; });
  const db = await openQueue();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(IDB_STORE, 'readwrite');
    tx.objectStore(IDB_STORE).add({
      url: request.url,
      method: request.method,
      headers,
      body,
      timestamp: Date.now(),
    });
    tx.oncomplete = resolve;
    tx.onerror = (e) => reject(e.target.error);
  });
}

async function replayQueue() {
  const db = await openQueue();
  const items = await new Promise((resolve, reject) => {
    const tx = db.transaction(IDB_STORE, 'readonly');
    const req = tx.objectStore(IDB_STORE).getAll();
    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror = (e) => reject(e.target.error);
  });

  if (!items.length) return;

  const replayed = [];
  for (const item of items) {
    try {
      const res = await fetch(item.url, {
        method: item.method,
        headers: item.headers,
        body: item.body,
      });
      if (res.ok) replayed.push(item.id);
    } catch (_) {
      // Still offline — leave in queue
    }
  }

  if (replayed.length) {
    const tx = db.transaction(IDB_STORE, 'readwrite');
    const store = tx.objectStore(IDB_STORE);
    replayed.forEach((id) => store.delete(id));
  }
}

// ── Install ───────────────────────────────────────────────────────────────────

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      // Pre-cache static + API endpoints best-effort (failures non-fatal)
      Promise.allSettled(
        [...STATIC_CACHE_URLS, ...API_PRECACHE_URLS].map((url) =>
          cache.add(url).catch(() => {})
        )
      )
    ).then(() => self.skipWaiting())
  );
});

// ── Activate ──────────────────────────────────────────────────────────────────

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch ─────────────────────────────────────────────────────────────────────

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle same-origin requests
  if (url.origin !== self.location.origin) return;

  // Queue offline POST /api/attempts/
  if (
    request.method === 'POST' &&
    url.pathname.startsWith('/api/attempts/')
  ) {
    event.respondWith(
      fetch(request.clone()).catch(async () => {
        await enqueueAttempt(request);
        return new Response(
          JSON.stringify({ queued: true, message: 'Attempt queued for sync' }),
          {
            status: 202,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      })
    );
    return;
  }

  // Network-first for API calls
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;
          return new Response(
            JSON.stringify({ error: 'Offline — no cached data available' }),
            {
              status: 503,
              headers: { 'Content-Type': 'application/json' },
            }
          );
        })
    );
    return;
  }

  // Cache-first for static assets and navigation
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(async () => {
          if (request.mode === 'navigate') {
            const fallback = await caches.match(OFFLINE_FALLBACK);
            if (fallback) return fallback;
          }
          return new Response('Offline', { status: 503 });
        });
    })
  );
});

// ── Background sync: replay queue on reconnect ────────────────────────────────

self.addEventListener('sync', (event) => {
  if (event.tag === 'replay-attempts') {
    event.waitUntil(replayQueue());
  }
});

// Fallback message-based replay (for browsers without Background Sync API)
self.addEventListener('message', (event) => {
  if (event.data === 'REPLAY_QUEUE') {
    replayQueue();
  }
});
