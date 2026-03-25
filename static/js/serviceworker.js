const CACHE_NAME = 'rentora-v1';
const STATIC_ASSETS = [
    '/',
    '/cars/',
    '/dashboard/',
    '/booking/',
    '/static/css/styles.css', // Assuming there's a main CSS
    '/static/js/main.js',     // Assuming there's a main JS
    '/static/images/icon-192.png',
    '/static/images/icon-512.png',
    '/offline/'
];

// Install Event
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log('Opened cache');
            return cache.addAll(STATIC_ASSETS);
        })
    );
});

// Activate Event
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== CACHE_NAME) {
                        console.log('Clearing old cache');
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
});

// Fetch Event
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            // Return from cache if found
            if (response) {
                return response;
            }

            // Otherwise fetch from network
            return fetch(event.request).catch(() => {
                // If network fails, show offline page for navigation requests
                if (event.request.mode === 'navigate') {
                    return caches.match('/offline/');
                }
            });
        })
    );
});

// Background Sync for Forms
self.addEventListener('sync', event => {
    if (event.tag === 'sync-booking-form') {
        console.log('Syncing booking form...');
        // Implement actual sync logic if needed
    }
});

// Push Notification Handling
self.addEventListener('push', event => {
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/images/icon-192.png',
        badge: '/static/images/icon-192.png',
        data: {
            url: data.url || '/dashboard/'
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification Click Event
self.addEventListener('notificationclick', event => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
