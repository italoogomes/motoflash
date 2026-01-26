/**
 * Firebase Messaging Service Worker
 *
 * Este Service Worker recebe notificacoes push do Firebase Cloud Messaging
 * mesmo quando o app esta em background ou fechado.
 */

// Importa os scripts do Firebase
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// Configuracao do Firebase (mesma do app)
const firebaseConfig = {
    apiKey: "AIzaSyAiSSKyuApZdCauW40rWkz5V-0F0IiKyuk",
    authDomain: "motoflash-80f6a.firebaseapp.com",
    projectId: "motoflash-80f6a",
    storageBucket: "motoflash-80f6a.firebasestorage.app",
    messagingSenderId: "567462227460",
    appId: "1:567462227460:web:9349a2e8425fb358398f51",
    measurementId: "G-VP0RCMV9D2"
};

// Inicializa o Firebase
firebase.initializeApp(firebaseConfig);

// Obtem instancia do Messaging
const messaging = firebase.messaging();

// Handler para mensagens em background
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] Mensagem em background recebida:', payload);

    // Extrai dados da notificacao (tenta varios caminhos)
    const notificationTitle = payload.notification?.title
        || payload.data?.title
        || 'Novo Lote de Entregas!';

    const notificationBody = payload.notification?.body
        || payload.data?.body
        || 'Voce recebeu novas entregas. Abra o app para ver.';

    const notificationOptions = {
        body: notificationBody,
        icon: '/icons/icon-192.png',
        badge: '/icons/icon-72.png',
        tag: payload.data?.type || 'motoflash-notification',
        vibrate: [200, 100, 200, 100, 200],
        data: payload.data || {},
        requireInteraction: true
    };

    // Mostra a notificacao
    return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handler para clique na notificacao
self.addEventListener('notificationclick', (event) => {
    console.log('[firebase-messaging-sw.js] Notificacao clicada:', event);

    event.notification.close();

    // Abre o app ou foca na janela existente
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Se ja tem uma janela aberta, foca nela
                for (const client of clientList) {
                    if (client.url.includes('/motoboy') && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Se nao tem janela aberta, abre uma nova
                if (clients.openWindow) {
                    return clients.openWindow('/motoboy');
                }
            })
    );
});

// Handler para push (fallback)
self.addEventListener('push', (event) => {
    console.log('[firebase-messaging-sw.js] Push recebido:', event);

    if (event.data) {
        try {
            const data = event.data.json();
            console.log('[firebase-messaging-sw.js] Dados do push:', data);
        } catch (e) {
            console.log('[firebase-messaging-sw.js] Dados do push (texto):', event.data.text());
        }
    }
});

console.log('[firebase-messaging-sw.js] Service Worker carregado');
