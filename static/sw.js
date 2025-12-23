/**
 * YuKyu Premium - Service Worker
 * Provides offline functionality and optimized caching for PWA
 * Versión optimizada con estrategias de caché mejoradas
 */

const CACHE_VERSION = '1.2';
const CACHE_NAME = `yukyu-premium-v${CACHE_VERSION}`;
const CACHE_STATIC = `${CACHE_NAME}-static`;
const CACHE_DYNAMIC = `${CACHE_NAME}-dynamic`;
const CACHE_API = `${CACHE_NAME}-api`;

// Assets críticos para precarga
const CRITICAL_ASSETS = [
  '/',
  '/static/css/main.css',
  '/static/js/app.js',
  '/static/manifest.json'
];

// Assets opcionales (se cachean bajo demanda)
const OPTIONAL_ASSETS = [
  'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+JP:wght@400;500;700&family=JetBrains+Mono:wght@400&display=swap'
];

// Assets que se cachean con estrategia stale-while-revalidate
const REVALIDATE_ASSETS = [
  '/static/js/modules/'
];

// Tiempo de expiración para caché de API (5 minutos)
const API_CACHE_EXPIRATION = 5 * 60 * 1000;

// Install event - cache critical assets only
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker v' + CACHE_VERSION);
  event.waitUntil(
    caches.open(CACHE_STATIC)
      .then((cache) => {
        console.log('[SW] Caching critical assets');
        // Cachear assets críticos primero
        return cache.addAll(CRITICAL_ASSETS);
      })
      .then(() => {
        // Cachear assets opcionales sin bloquear instalación
        return caches.open(CACHE_STATIC).then((cache) => {
          return Promise.allSettled(
            OPTIONAL_ASSETS.map(url =>
              cache.add(url).catch(err => {
                console.warn('[SW] Optional asset failed:', url, err);
              })
            )
          );
        });
      })
      .then(() => {
        console.log('[SW] Installation complete');
        return self.skipWaiting();
      })
      .catch(err => {
        console.error('[SW] Installation failed:', err);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker v' + CACHE_VERSION);

  const expectedCaches = [CACHE_STATIC, CACHE_DYNAMIC, CACHE_API];

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => !expectedCaches.includes(cacheName))
            .map((cacheName) => {
              console.log('[SW] Removing old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('[SW] Activation complete');
        return self.clients.claim();
      })
  );
});

// Helper: Verifica si el request es cacheable
function isCacheable(request) {
  const url = new URL(request.url);

  // No cachear requests con query params de tiempo
  if (url.searchParams.has('_t') || url.searchParams.has('timestamp')) {
    return false;
  }

  return true;
}

// Helper: Verifica si la caché de API está expirada
function isApiCacheExpired(response) {
  if (!response) return true;

  const cachedTime = response.headers.get('sw-cache-time');
  if (!cachedTime) return true;

  const age = Date.now() - parseInt(cachedTime, 10);
  return age > API_CACHE_EXPIRATION;
}

// Estrategia: Network First (para APIs)
async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);

    // Solo cachear respuestas exitosas
    if (response.ok && isCacheable(request)) {
      const cache = await caches.open(cacheName);
      const clonedResponse = response.clone();

      // Agregar timestamp para control de expiración
      const headers = new Headers(clonedResponse.headers);
      headers.append('sw-cache-time', Date.now().toString());

      const modifiedResponse = new Response(clonedResponse.body, {
        status: clonedResponse.status,
        statusText: clonedResponse.statusText,
        headers: headers
      });

      cache.put(request, modifiedResponse);
    }

    return response;
  } catch (error) {
    // Fallback a caché si falla la red
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[SW] Serving from cache (offline):', request.url);
      return cachedResponse;
    }

    throw error;
  }
}

// Estrategia: Cache First (para assets estáticos)
async function cacheFirst(request, cacheName) {
  const cachedResponse = await caches.match(request);

  if (cachedResponse) {
    // Revalidar en segundo plano para módulos
    if (REVALIDATE_ASSETS.some(pattern => request.url.includes(pattern))) {
      fetch(request)
        .then(response => {
          if (response.ok) {
            caches.open(cacheName).then(cache => {
              cache.put(request, response);
            });
          }
        })
        .catch(() => {});
    }

    return cachedResponse;
  }

  // No está en caché, obtener de red
  try {
    const response = await fetch(request);

    if (response.ok && isCacheable(request)) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }

    return response;
  } catch (error) {
    console.error('[SW] Fetch failed:', request.url, error);
    throw error;
  }
}

// Estrategia: Stale While Revalidate (para recursos que cambian poco)
async function staleWhileRevalidate(request, cacheName) {
  const cachedResponse = await caches.match(request);

  const fetchPromise = fetch(request)
    .then(response => {
      if (response.ok) {
        caches.open(cacheName).then(cache => {
          cache.put(request, response.clone());
        });
      }
      return response;
    })
    .catch(() => cachedResponse);

  return cachedResponse || fetchPromise;
}

// Fetch event - estrategias de caché optimizadas
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Solo manejar GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Estrategia para API: Network First con fallback a caché
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request, CACHE_API));
    return;
  }

  // Estrategia para CSS/JS: Stale-While-Revalidate para recibir updates sin romper offline
  if (url.pathname.endsWith('.css') ||
      url.pathname.endsWith('.js') ||
      url.pathname.includes('/static/js/modules/')) {
    event.respondWith(staleWhileRevalidate(request, CACHE_STATIC));
    return;
  }

  // Estrategia para fuentes: Stale While Revalidate
  if (url.hostname.includes('fonts.googleapis.com') ||
      url.hostname.includes('fonts.gstatic.com')) {
    event.respondWith(staleWhileRevalidate(request, CACHE_STATIC));
    return;
  }

  // Estrategia para CDN (Chart.js, ApexCharts): Cache First con TTL largo
  if (url.hostname.includes('cdn.jsdelivr.net')) {
    event.respondWith(cacheFirst(request, CACHE_STATIC));
    return;
  }

  // Estrategia para HTML: Network First
  if (url.pathname === '/' || request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirst(request, CACHE_DYNAMIC));
    return;
  }

  // Por defecto: Network First
  event.respondWith(networkFirst(request, CACHE_DYNAMIC));
});

// Handle push notifications (for future use)
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : '新しい通知があります',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    }
  };

  event.waitUntil(
    self.registration.showNotification('YuKyu Premium', options)
  );
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow('/')
  );
});

console.log('[SW] Service Worker loaded');
