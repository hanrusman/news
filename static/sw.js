const CACHE_NAME = 'newsdeck-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/manifest.json',
    '/static/images/icon-192.png',
    '/static/images/icon-512.png'
    // Add other static assets like CSS/JS here if they were local files
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

self.addEventListener('fetch', (event) => {
    // Network-first strategy for HTML pages (we want fresh news)
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => {
                return caches.match('/'); // Fallback to cached dashboard if offline
            })
        );
        return;
    }

    // Stale-while-revalidate for static assets
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            const fetchPromise = fetch(event.request).then((networkResponse) => {
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, networkResponse.clone());
                });
                return networkResponse;
            });
            return cachedResponse || fetchPromise;
        })
    );
});
