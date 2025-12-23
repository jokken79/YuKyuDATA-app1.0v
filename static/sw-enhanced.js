/**
 * Enhanced Service Worker - PWA Features
 * Implementa caching offline, background sync y notificaciones
 */

const CACHE_NAME = 'yukyu-data-v2.0.1';
const STATIC_CACHE = 'yukyu-static-v2.0.1';
const API_CACHE = 'yukyu-api-v2.0.1';

// URLs estáticas para cachear
const STATIC_ASSETS = [
  '/',
  '/templates/index.html',
  '/static/css/main.css',
  '/static/css/modern-2025.css',
  '/static/css/design-system/tokens.css',
  '/static/css/design-system/components.css',
  '/static/css/design-system/themes.css',
  '/static/css/design-system/accessibility.css',
  '/static/css/responsive-enhancements.css',
  '/static/js/app.js',
  '/static/js/modules/utils.js',
  '/static/js/modules/theme-manager.js',
  '/static/js/modules/ui-manager.js',
  '/static/js/modules/data-service.js',
  '/static/js/modules/chart-manager.js',
  '/static/js/lazy-loader.js',
  '/static/js/error-boundary.js',
  '/static/icons/logo-premium.svg',
  '/static/icons/icon.svg'
];

// Endpoints de API para cachear estrategicamente
const API_CACHE_STRATEGIES = {
  // GET requests - cachear por 5 minutos
  cacheable: [
    '/api/employees',
    '/api/yukyu/kpi-stats',
    '/api/yukyu/monthly-summary',
    '/api/yukyu/by-employee-type',
    '/api/analytics/top10-active',
    '/api/factories'
  ],
  
  // POST requests - no cachear
  nonCacheable: [
    '/api/sync',
    '/api/sync-genzai',
    '/api/sync-ukeoi',
    '/api/leave-request',
    '/api/error-report'
  ]
};

// Instalación del Service Worker
self.addEventListener('install', (event) => {
  console.log('SW: Installing enhanced features...');
  
  event.waitUntil(
    (async () => {
      // Crear caches
      const staticCache = await caches.open(STATIC_CACHE);
      const apiCache = await caches.open(API_CACHE);
      
      // Cachear assets estáticos
      await staticCache.addAll(STATIC_ASSETS);
      
      // Precargar datos críticos
      await preloadCriticalData(apiCache);
      
      // Saltar waiting
      self.skipWaiting();
    })()
  );
});

// Activación del Service Worker
self.addEventListener('activate', (event) => {
  console.log('SW: Activating enhanced features...');
  
  event.waitUntil(
    (async () => {
      // Limpiar caches antiguos
      const cacheNames = await caches.keys();
      const deletions = cacheNames
        .filter(name => name !== STATIC_CACHE && name !== API_CACHE)
        .map(name => caches.delete(name));
      
      await Promise.all(deletions);
      
      // Tomar control
      self.clients.claim();
    })()
  );
});

// Interceptar requests
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Estrategia diferente para diferentes tipos de requests
  if (url.origin === location.origin) {
    if (url.pathname.startsWith('/api/')) {
      // API requests - Network First con Cache Fallback
      event.respondWith(handleAPIRequest(request));
    } else {
      // Static assets - Cache First con Network Fallback
      event.respondWith(handleStaticRequest(request));
    }
  } else {
    // External requests - Network Only
    event.respondWith(fetch(request));
  }
});

// Manejar requests de API
async function handleAPIRequest(request) {
  const cache = await caches.open(API_CACHE);
  const url = new URL(request.url);
  
  // Verificar si es cacheable
  const isCacheable = API_CACHE_STRATEGIES.cacheable.some(path => 
    url.pathname.startsWith(path)
  );
  
  if (!isCacheable || request.method !== 'GET') {
    // Requests no cacheables - network only
    try {
      const response = await fetch(request);
      
      // Cachear responses exitosas de GET
      if (response.ok && request.method === 'GET') {
        const responseClone = response.clone();
        await cache.put(request, responseClone);
      }
      
      return response;
    } catch (error) {
      // Intentar del cache si el network falla
      const cachedResponse = await cache.match(request);
      if (cachedResponse) {
        return cachedResponse;
      }
      
      throw error;
    }
  }
  
  // Requests cacheables - Network First
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const responseClone = networkResponse.clone();
      await cache.put(request, responseClone);
    }
    
    return networkResponse;
  } catch (error) {
    // Fallback al cache
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Offline fallback
    return new Response(
      JSON.stringify({ 
        error: 'Offline', 
        message: 'No hay conexión a internet' 
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Manejar requests estáticos
async function handleStaticRequest(request) {
  const cache = await caches.open(STATIC_CACHE);
  
  try {
    // Intentar del cache primero
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Si no está en cache, fetch y cachear
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const responseClone = networkResponse.clone();
      await cache.put(request, responseClone);
    }
    
    return networkResponse;
  } catch (error) {
    // Si el network falla, intentar del cache
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Offline fallback para HTML
    if (request.destination === 'document') {
      return caches.match('/templates/index.html');
    }
    
    throw error;
  }
}

// Precargar datos críticos
async function preloadCriticalData(apiCache) {
  try {
    const criticalEndpoints = [
      '/api/employees?enhanced=true&active_only=true',
      '/api/yukyu/kpi-stats/2024'
    ];
    
    const preloadPromises = criticalEndpoints.map(async (endpoint) => {
      try {
        const response = await fetch(endpoint);
        if (response.ok) {
          await apiCache.put(endpoint, response);
        }
      } catch (error) {
        console.warn(`Failed to preload ${endpoint}:`, error);
      }
    });
    
    await Promise.allSettled(preloadPromises);
  } catch (error) {
    console.warn('Critical data preload failed:', error);
  }
}

// Background Sync
self.addEventListener('sync', (event) => {
  console.log('SW: Background sync triggered:', event.tag);
  
  if (event.tag === 'sync-data') {
    event.waitUntil(syncPendingData());
  } else if (event.tag === 'sync-leave-requests') {
    event.waitUntil(syncLeaveRequests());
  }
});

// Sincronizar datos pendientes
async function syncPendingData() {
  try {
    // Obtener datos pendientes del IndexedDB
    const pendingData = await getPendingSyncData();
    
    for (const data of pendingData) {
      try {
        const response = await fetch('/api/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        
        if (response.ok) {
          await removePendingSyncData(data.id);
        }
      } catch (error) {
        console.warn('Failed to sync data:', error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Sincronizar solicitudes de vacaciones pendientes
async function syncLeaveRequests() {
  try {
    const pendingRequests = await getPendingLeaveRequests();
    
    for (const request of pendingRequests) {
      try {
        const response = await fetch('/api/leave-request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request.data)
        });
        
        if (response.ok) {
          await removePendingLeaveRequest(request.id);
          
          // Notificar al usuario
          await showNotification('Solicitud Enviada', 
            'Tu solicitud de vacaciones ha sido enviada correctamente');
        }
      } catch (error) {
        console.warn('Failed to sync leave request:', error);
      }
    }
  } catch (error) {
    console.error('Leave requests sync failed:', error);
  }
}

// Push Notifications
self.addEventListener('push', (event) => {
  console.log('SW: Push notification received');
  
  const options = {
    body: event.data.text(),
    icon: '/static/icons/icon.svg',
    badge: '/static/icons/icon.svg',
    vibrate: [200, 100, 200],
    data: {
      url: '/',
      timestamp: Date.now()
    },
    actions: [
      {
        action: 'open',
        title: 'Abrir Aplicación'
      },
      {
        action: 'dismiss',
        title: 'Descartar'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('YuKyuDATA', options)
  );
});

// Manejar clic en notificaciones
self.addEventListener('notificationclick', (event) => {
  console.log('SW: Notification clicked');
  
  event.notification.close();
  
  if (event.action === 'open' || !event.action) {
    event.waitUntil(
      clients.openWindow(event.notification.data.url || '/')
    );
  }
});

// Utils para IndexedDB (datos offline)
async function getPendingSyncData() {
  return new Promise((resolve) => {
    const request = indexedDB.open('yukyu-offline-db', 1);
    
    request.onerror = () => resolve([]);
    
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['pending-sync'], 'readonly');
      const store = transaction.objectStore('pending-sync');
      const getRequest = store.getAll();
      
      getRequest.onsuccess = () => resolve(getRequest.result || []);
      getRequest.onerror = () => resolve([]);
    };
    
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('pending-sync')) {
        db.createObjectStore('pending-sync', { keyPath: 'id' });
      }
    };
  });
}

async function removePendingSyncData(id) {
  return new Promise((resolve) => {
    const request = indexedDB.open('yukyu-offline-db', 1);
    
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['pending-sync'], 'readwrite');
      const store = transaction.objectStore('pending-sync');
      const deleteRequest = store.delete(id);
      
      deleteRequest.onsuccess = () => resolve();
      deleteRequest.onerror = () => resolve();
    };
  });
}

async function getPendingLeaveRequests() {
  // Similar implementación para solicitudes de vacaciones
  return [];
}

async function removePendingLeaveRequest(id) {
  // Similar implementación para eliminar solicitudes
  return Promise.resolve();
}

async function showNotification(title, body) {
  if ('Notification' in self && Notification.permission === 'granted') {
    await self.registration.showNotification(title, {
      body,
      icon: '/static/icons/icon.svg',
      badge: '/static/icons/icon.svg'
    });
  }
}

// Message handling
self.addEventListener('message', (event) => {
  console.log('SW: Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data && event.data.type === 'CACHE_API') {
    // Cachear manualmente endpoints específicos
    event.waitUntil(
      (async () => {
        const cache = await caches.open(API_CACHE);
        for (const url of event.data.urls) {
          try {
            const response = await fetch(url);
            if (response.ok) {
              await cache.put(url, response);
            }
          } catch (error) {
            console.warn(`Failed to cache ${url}:`, error);
          }
        }
      })()
    );
  }
});

// Periodic Background Sync (si está disponible)
if ('periodicSync' in self.registration) {
  self.registration.periodicSync.register('sync-data', {
    minInterval: 30 * 60 * 1000 // 30 minutos
  }).then(() => {
    console.log('SW: Periodic sync registered');
  }).catch(error => {
    console.warn('SW: Periodic sync registration failed:', error);
  });
}

console.log('SW: Enhanced Service Worker loaded');