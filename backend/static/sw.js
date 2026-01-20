// MotoFlash Service Worker v1.0
const CACHE_NAME = 'motoflash-v1';
const OFFLINE_URL = '/motoboy';

// Arquivos para cache inicial
const PRECACHE_ASSETS = [
  '/motoboy',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  'https://cdn.tailwindcss.com',
  'https://unpkg.com/react@18/umd/react.production.min.js',
  'https://unpkg.com/react-dom@18/umd/react-dom.production.min.js',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
];

// Instalação - cache dos arquivos essenciais
self.addEventListener('install', (event) => {
  console.log('📦 Service Worker: Instalando...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('📦 Service Worker: Cacheando arquivos');
        return cache.addAll(PRECACHE_ASSETS);
      })
      .then(() => {
        console.log('✅ Service Worker: Instalado com sucesso!');
        return self.skipWaiting();
      })
      .catch((err) => {
        console.error('❌ Service Worker: Erro ao instalar', err);
      })
  );
});

// Ativação - limpa caches antigos
self.addEventListener('activate', (event) => {
  console.log('🚀 Service Worker: Ativando...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('🗑️ Service Worker: Removendo cache antigo:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('✅ Service Worker: Ativado!');
        return self.clients.claim();
      })
  );
});

// Intercepta requisições - estratégia Network First com fallback para cache
self.addEventListener('fetch', (event) => {
  // Ignora requisições que não são GET
  if (event.request.method !== 'GET') return;
  
  // Ignora requisições para API (sempre precisa de rede)
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/api') || 
      url.pathname.startsWith('/orders') || 
      url.pathname.startsWith('/couriers') ||
      url.pathname.startsWith('/dispatch')) {
    return;
  }
  
  event.respondWith(
    // Tenta buscar da rede primeiro
    fetch(event.request)
      .then((response) => {
        // Se deu certo, salva no cache e retorna
        if (response.ok) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseClone);
            });
        }
        return response;
      })
      .catch(() => {
        // Se falhou (offline), busca do cache
        return caches.match(event.request)
          .then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Se não tem no cache e é navegação, mostra página offline
            if (event.request.mode === 'navigate') {
              return caches.match(OFFLINE_URL);
            }
            // Retorna resposta de erro genérica
            return new Response('Offline', {
              status: 503,
              statusText: 'Service Unavailable'
            });
          });
      })
  );
});

// Recebe mensagens do app
self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
  }
});

// Push Notifications (preparado para o próximo card!)
self.addEventListener('push', (event) => {
  console.log('🔔 Push recebido:', event);
  
  let data = { title: 'MotoFlash', body: 'Nova notificação' };
  
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }
  
  const options = {
    body: data.body,
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-96.png',
    vibrate: [200, 100, 200],
    tag: data.tag || 'motoflash-notification',
    renotify: true,
    data: data.data || {},
    actions: data.actions || [
      { action: 'open', title: '📱 Abrir App' },
      { action: 'close', title: '✕ Fechar' }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Clique na notificação
self.addEventListener('notificationclick', (event) => {
  console.log('🖱️ Notificação clicada:', event.action);
  
  event.notification.close();
  
  if (event.action === 'close') return;
  
  // Abre ou foca no app
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Se já tem uma janela aberta, foca nela
        for (const client of clientList) {
          if (client.url.includes('/motoboy') && 'focus' in client) {
            return client.focus();
          }
        }
        // Se não, abre nova janela
        if (clients.openWindow) {
          return clients.openWindow('/motoboy');
        }
      })
  );
});

console.log('🏍️ MotoFlash Service Worker carregado!');
