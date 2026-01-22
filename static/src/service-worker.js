/**
 * Service Worker for YuKyu PWA
 * Enables offline functionality and caching strategies
 */

// eslint-disable-next-line no-undef
const CACHE_VERSION = 'v1';
const CACHE_NAMES = {
  app: `app-${CACHE_VERSION}`,
  api: `api-${CACHE_VERSION}`,
  assets: `assets-${CACHE_VERSION}`,
};

// Workbox configuration (injected by webpack)
// eslint-disable-next-line no-undef
importScripts(...self.__WB_MANIFEST.map(entry => entry.url));

/**
 * Install event - precache assets
 */
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    Promise.all([
      // Precache app shell
      caches.open(CACHE_NAMES.app).then((cache) => {
        return cache.addAll([
          '/',
          '/index.html',
          '/static/css/main.css',
          '/static/css/design-system/tokens.css',
          '/offline.html', // Fallback offline page
        ]);
      }),
    ]).then(() => {
      // Skip waiting and activate immediately
      return self.skipWaiting();
    })
  );
});

/**
 * Activate event - clean old caches
 */
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Delete old caches
          if (!Object.values(CACHE_NAMES).includes(cacheName)) {
            console.log(`[Service Worker] Deleting old cache: ${cacheName}`);
            return caches.delete(cacheName);
          }
          return Promise.resolve();
        })
      );
    }).then(() => {
      // Claim all clients immediately
      return self.clients.claim();
    })
  );
});

/**
 * Fetch event - handle network requests
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip external URLs
  if (url.origin !== self.location.origin) {
    return;
  }

  // API requests - Network First with Cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful API responses
          if (response && response.status === 200) {
            const cache = caches.open(CACHE_NAMES.api);
            cache.then((c) => c.put(request, response.clone()));
          }
          return response;
        })
        .catch(() => {
          // Return cached response if network fails
          return caches.match(request).then((cachedResponse) => {
            return cachedResponse || new Response(
              JSON.stringify({ error: 'offline' }),
              { status: 503, headers: { 'Content-Type': 'application/json' } }
            );
          });
        })
    );
    return;
  }

  // Static assets - Cache First with Network fallback
  if (
    url.pathname.match(/\.(js|css|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$/) ||
    url.pathname.startsWith('/dist/')
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        return cachedResponse || fetch(request).then((response) => {
          // Cache new responses
          if (response && response.status === 200) {
            const cache = caches.open(CACHE_NAMES.assets);
            cache.then((c) => c.put(request, response.clone()));
          }
          return response;
        }).catch(() => {
          // Return placeholder for failed images
          if (url.pathname.match(/\.(png|jpg|jpeg|gif|svg)$/)) {
            return new Response(
              '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect fill="#ddd" width="100" height="100"/></svg>',
              { headers: { 'Content-Type': 'image/svg+xml' } }
            );
          }
          return new Response('Not available offline', { status: 503 });
        });
      })
    );
    return;
  }

  // HTML documents - Network First
  if (
    request.mode === 'navigate' ||
    url.pathname.endsWith('.html')
  ) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.status === 200) {
            const cache = caches.open(CACHE_NAMES.app);
            cache.then((c) => c.put(request, response.clone()));
          }
          return response;
        })
        .catch(() => {
          return caches.match(request).then((cachedResponse) => {
            return cachedResponse || caches.match('/offline.html');
          });
        })
    );
  }
});

/**
 * Message event - handle client communication
 */
self.addEventListener('message', (event) => {
  if (event.data.action === 'skipWaiting') {
    self.skipWaiting();
  }

  if (event.data.action === 'clearCache') {
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => caches.delete(cacheName))
      );
    }).then(() => {
      event.ports[0].postMessage({ success: true });
    });
  }
});

/**
 * Background sync for offline submissions
 */
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-leave-request') {
    event.waitUntil(syncPendingRequest());
  }
});

/**
 * Sync pending leave request from IndexedDB
 */
async function syncPendingRequest() {
  try {
    // Get pending request from IndexedDB
    const db = new Promise((resolve, reject) => {
      const request = self.indexedDB.open('yukyu');
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    // Retry submission
    const response = await fetch('/api/v1/leave-requests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        /* pending request data */
      }),
    });

    if (response.ok) {
      // Clear pending request from IndexedDB
      console.log('[Service Worker] Synced pending request');
    }
  } catch (error) {
    console.error('[Service Worker] Sync failed:', error);
    throw error; // Retry sync
  }
}
