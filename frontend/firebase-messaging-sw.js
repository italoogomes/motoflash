// Firebase Messaging Service Worker
// Este arquivo PRECISA ter esse nome e ficar na raiz do site

importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js');

// Configuração do Firebase (mesma do frontend)
firebase.initializeApp({
  apiKey: "AIzaSyAiSSKyuApZdCauW40rWkz5V-0F0IiKyuk",
  authDomain: "motoflash-80f6a.firebaseapp.com",
  projectId: "motoflash-80f6a",
  storageBucket: "motoflash-80f6a.firebasestorage.app",
  messagingSenderId: "567462227460",
  appId: "1:567462227460:web:9349a2e8425fb358398f51"
});

const messaging = firebase.messaging();

// Recebe mensagens em segundo plano
messaging.onBackgroundMessage((payload) => {
  console.log('📩 Push recebido em background:', payload);
  
  const notificationTitle = payload.notification?.title || '🏍️ MotoFlash';
  const notificationOptions = {
    body: payload.notification?.body || 'Nova notificação',
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-96.png',
    tag: 'motoflash-notification',
    renotify: true,
    vibrate: [200, 100, 200],
    data: payload.data || {}
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Quando clica na notificação
self.addEventListener('notificationclick', (event) => {
  console.log('🔔 Notificação clicada:', event);
  
  event.notification.close();
  
  // Abre ou foca na aba do motoboy
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Procura se já tem uma aba aberta
        for (const client of clientList) {
          if (client.url.includes('/motoboy') && 'focus' in client) {
            return client.focus();
          }
        }
        // Se não tem, abre uma nova
        if (clients.openWindow) {
          return clients.openWindow('/motoboy');
        }
      })
  );
});
