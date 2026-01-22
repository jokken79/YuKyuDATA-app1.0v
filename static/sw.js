/**
 * YuKyuDATA - Enhanced Service Worker
 * Provides offline functionality, background sync, and optimized caching for PWA
 * @version 2.0
 */

const CACHE_VERSION = '2.0';
const CACHE_NAME = `yukyu-pwa-v${CACHE_VERSION}`;
const CACHE_STATIC = `${CACHE_NAME}-static`;
const CACHE_DYNAMIC = `${CACHE_NAME}-dynamic`;
const CACHE_API = `${CACHE_NAME}-api`;

// Critical assets for precaching (core app functionality)
const CRITICAL_ASSETS = [
    '/',
    '/static/offline.html',
    '/static/css/main.css',
    '/static/css/design-system/tokens.css',
    '/static/css/design-system/themes.css',
    '/static/css/design-system/components.css',
    '/static/css/design-system/utilities.css',
    '/static/css/design-system/accessibility.css',
    '/static/js/app.js',
    '/static/js/modules/offline-storage.js',
    '/static/manifest.json',
    '/static/icons/icon.svg'
];

// Optional assets (cached on demand)
const OPTIONAL_ASSETS = [
    'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+JP:wght@400;500;700&family=JetBrains+Mono:wght@400&display=swap'
];

// API endpoints to cache (v1 routes)
const API_ENDPOINTS = [
    '/api/v1/employees',
    '/api/v1/genzai',
    '/api/v1/ukeoi',
    '/api/v1/staff',
    '/api/v1/leave-requests',
    '/api/v1/fiscal/years',
    '/api/v1/system/db-status'
];

// Cache expiration times (milliseconds)
const CACHE_EXPIRATION = {
    api: 5 * 60 * 1000,        // 5 minutes for API data
    static: 24 * 60 * 60 * 1000, // 24 hours for static assets
    dynamic: 60 * 60 * 1000     // 1 hour for dynamic content
};

// Background sync tag
const SYNC_TAG = 'yukyu-background-sync';

// ==================== INSTALL EVENT ====================

self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker v' + CACHE_VERSION);

    event.waitUntil(
        caches.open(CACHE_STATIC)
            .then((cache) => {
                console.log('[SW] Caching critical assets...');
                return cache.addAll(CRITICAL_ASSETS);
            })
            .then(() => {
                // Cache optional assets without blocking installation
                return caches.open(CACHE_STATIC).then((cache) => {
                    return Promise.allSettled(
                        OPTIONAL_ASSETS.map(url =>
                            cache.add(url).catch(err => {
                                console.warn('[SW] Optional asset failed:', url, err.message);
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

// ==================== ACTIVATE EVENT ====================

self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker v' + CACHE_VERSION);

    const expectedCaches = [CACHE_STATIC, CACHE_DYNAMIC, CACHE_API];

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((cacheName) => {
                            // Delete old version caches
                            return cacheName.startsWith('yukyu-') &&
                                   !expectedCaches.includes(cacheName);
                        })
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

// ==================== FETCH STRATEGIES ====================

/**
 * Check if request is cacheable
 * @param {Request} request
 * @returns {boolean}
 */
function isCacheable(request) {
    const url = new URL(request.url);

    // Don't cache requests with timestamps or auth tokens
    if (url.searchParams.has('_t') ||
        url.searchParams.has('timestamp') ||
        url.searchParams.has('token')) {
        return false;
    }

    // Don't cache POST, PUT, DELETE requests
    if (request.method !== 'GET') {
        return false;
    }

    return true;
}

/**
 * Check if API cache is expired
 * @param {Response} response
 * @returns {boolean}
 */
function isApiCacheExpired(response) {
    if (!response) return true;

    const cachedTime = response.headers.get('sw-cache-time');
    if (!cachedTime) return true;

    const age = Date.now() - parseInt(cachedTime, 10);
    return age > CACHE_EXPIRATION.api;
}

/**
 * Clone response with cache timestamp
 * @param {Response} response
 * @returns {Promise<Response>}
 */
async function addCacheTimestamp(response) {
    const headers = new Headers(response.headers);
    headers.append('sw-cache-time', Date.now().toString());

    return new Response(await response.clone().blob(), {
        status: response.status,
        statusText: response.statusText,
        headers: headers
    });
}

/**
 * Network First Strategy - For API and HTML
 * Try network first, fallback to cache, then offline page
 */
async function networkFirst(request, cacheName) {
    try {
        const response = await fetch(request);

        // Cache successful responses
        if (response.ok && isCacheable(request)) {
            const cache = await caches.open(cacheName);
            const responseWithTimestamp = await addCacheTimestamp(response);
            cache.put(request, responseWithTimestamp);
        }

        return response;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', request.url);

        // Try cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            console.log('[SW] Serving from cache:', request.url);
            return cachedResponse;
        }

        // If it's a navigation request, show offline page
        if (request.mode === 'navigate') {
            console.log('[SW] Serving offline page');
            return caches.match('/static/offline.html');
        }

        throw error;
    }
}

/**
 * Cache First Strategy - For static assets
 * Try cache first, then network as fallback
 */
async function cacheFirst(request, cacheName) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        // Revalidate in background for fresh content
        fetchAndCache(request, cacheName).catch(() => {});
        return cachedResponse;
    }

    // Not in cache, fetch from network
    try {
        const response = await fetch(request);

        if (response.ok && isCacheable(request)) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        console.error('[SW] Cache first failed:', request.url, error);
        throw error;
    }
}

/**
 * Stale While Revalidate Strategy
 * Return cached version immediately, update cache in background
 */
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

/**
 * Fetch and cache in background
 */
async function fetchAndCache(request, cacheName) {
    const response = await fetch(request);

    if (response.ok) {
        const cache = await caches.open(cacheName);
        cache.put(request, response.clone());
    }

    return response;
}

// ==================== FETCH EVENT HANDLER ====================

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests (except for background sync)
    if (request.method !== 'GET') {
        // For POST requests to leave-requests, try background sync
        if (request.method === 'POST' && url.pathname === '/api/v1/leave-requests') {
            event.respondWith(handleOfflinePost(request));
        }
        return;
    }

    // Skip non-HTTP(S) requests
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // API requests - Network First with API cache
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request, CACHE_API));
        return;
    }

    // Static JS modules - Stale While Revalidate
    if (url.pathname.includes('/static/js/modules/')) {
        event.respondWith(staleWhileRevalidate(request, CACHE_STATIC));
        return;
    }

    // Static CSS/JS - Stale While Revalidate
    if (url.pathname.endsWith('.css') || url.pathname.endsWith('.js')) {
        event.respondWith(staleWhileRevalidate(request, CACHE_STATIC));
        return;
    }

    // Google Fonts - Stale While Revalidate
    if (url.hostname.includes('fonts.googleapis.com') ||
        url.hostname.includes('fonts.gstatic.com')) {
        event.respondWith(staleWhileRevalidate(request, CACHE_STATIC));
        return;
    }

    // CDN resources (Chart.js, GSAP, etc.) - Cache First
    if (url.hostname.includes('cdn.jsdelivr.net') ||
        url.hostname.includes('cdnjs.cloudflare.com')) {
        event.respondWith(cacheFirst(request, CACHE_STATIC));
        return;
    }

    // HTML/Navigation - Network First with offline fallback
    if (url.pathname === '/' ||
        request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(networkFirst(request, CACHE_DYNAMIC));
        return;
    }

    // Images/Icons - Cache First
    if (url.pathname.match(/\.(png|jpg|jpeg|svg|gif|webp|ico)$/)) {
        event.respondWith(cacheFirst(request, CACHE_STATIC));
        return;
    }

    // Default - Network First
    event.respondWith(networkFirst(request, CACHE_DYNAMIC));
});

// ==================== OFFLINE POST HANDLING ====================

/**
 * Handle POST requests when offline
 * Queue them for background sync
 */
async function handleOfflinePost(request) {
    try {
        // Try to send normally first
        const response = await fetch(request.clone());
        return response;
    } catch (error) {
        // Offline - queue for background sync
        console.log('[SW] Offline - queueing request for background sync');

        const requestData = await request.json();

        // Store in IndexedDB via message to client
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'QUEUE_REQUEST',
                data: requestData,
                url: request.url,
                method: request.method
            });
        });

        // Register for background sync
        if ('sync' in self.registration) {
            await self.registration.sync.register(SYNC_TAG);
        }

        // Return a "queued" response
        return new Response(JSON.stringify({
            status: 'queued',
            message: 'Request queued for background sync',
            timestamp: Date.now()
        }), {
            status: 202,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// ==================== BACKGROUND SYNC ====================

self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync triggered:', event.tag);

    if (event.tag === SYNC_TAG) {
        event.waitUntil(syncPendingRequests());
    }
});

/**
 * Sync all pending requests to server
 */
async function syncPendingRequests() {
    console.log('[SW] Syncing pending requests...');

    // Notify clients to sync their pending data
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
        client.postMessage({
            type: 'SYNC_PENDING'
        });
    });
}

// ==================== PUSH NOTIFICATIONS ====================

self.addEventListener('push', (event) => {
    console.log('[SW] Push notification received');

    const options = {
        body: event.data ? event.data.text() : 'New notification from YuKyuDATA',
        icon: '/static/icons/icon-192.svg',
        badge: '/static/icons/icon-72.svg',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            { action: 'view', title: 'View' },
            { action: 'dismiss', title: 'Dismiss' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('YuKyuDATA', options)
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'dismiss') {
        return;
    }

    event.waitUntil(
        clients.matchAll({ type: 'window' })
            .then(clientList => {
                // Focus existing window if available
                for (const client of clientList) {
                    if (client.url === '/' && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Open new window
                if (clients.openWindow) {
                    return clients.openWindow('/');
                }
            })
    );
});

// ==================== MESSAGE HANDLING ====================

self.addEventListener('message', (event) => {
    console.log('[SW] Message received:', event.data);

    const { type, data } = event.data;

    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;

        case 'CLEAR_CACHE':
            clearAllCaches().then(() => {
                event.source.postMessage({ type: 'CACHE_CLEARED' });
            });
            break;

        case 'GET_CACHE_STATS':
            getCacheStats().then(stats => {
                event.source.postMessage({ type: 'CACHE_STATS', data: stats });
            });
            break;

        case 'PRECACHE_API':
            precacheApiEndpoints().then(() => {
                event.source.postMessage({ type: 'API_PRECACHED' });
            });
            break;
    }
});

/**
 * Clear all caches
 */
async function clearAllCaches() {
    const cacheNames = await caches.keys();
    await Promise.all(
        cacheNames
            .filter(name => name.startsWith('yukyu-'))
            .map(name => caches.delete(name))
    );
    console.log('[SW] All caches cleared');
}

/**
 * Get cache statistics
 */
async function getCacheStats() {
    const stats = {
        version: CACHE_VERSION,
        caches: {}
    };

    const cacheNames = await caches.keys();

    for (const name of cacheNames) {
        if (name.startsWith('yukyu-')) {
            const cache = await caches.open(name);
            const keys = await cache.keys();
            stats.caches[name] = keys.length;
        }
    }

    return stats;
}

/**
 * Precache API endpoints for offline use
 */
async function precacheApiEndpoints() {
    const cache = await caches.open(CACHE_API);

    const promises = API_ENDPOINTS.map(async (endpoint) => {
        try {
            const response = await fetch(endpoint);
            if (response.ok) {
                const responseWithTimestamp = await addCacheTimestamp(response);
                await cache.put(endpoint, responseWithTimestamp);
                console.log('[SW] Precached:', endpoint);
            }
        } catch (error) {
            console.warn('[SW] Failed to precache:', endpoint, error.message);
        }
    });

    await Promise.allSettled(promises);
    console.log('[SW] API precaching complete');
}

// ==================== PERIODIC SYNC (if supported) ====================

self.addEventListener('periodicsync', (event) => {
    console.log('[SW] Periodic sync triggered:', event.tag);

    if (event.tag === 'yukyu-periodic-sync') {
        event.waitUntil(precacheApiEndpoints());
    }
});

console.log('[SW] Service Worker v' + CACHE_VERSION + ' loaded');
