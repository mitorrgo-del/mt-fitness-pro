const CACHE_NAME = 'mtfitness-v48';

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll([
        '/app/index.html',
        '/app/style.css',
        '/app/app.js',
        '/app/logo.jpg',
        '/app/manifest.json'
    ]))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== CACHE_NAME) return caches.delete(key);
      }));
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // Strategy: Network First, fallback to cache
  e.respondWith(
    fetch(e.request)
      .then((response) => {
        // Skip caching for API calls
        if(e.request.url.includes('/api/')) return response;
        const resClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(e.request, resClone));
        return response;
      })
      .catch(() => caches.match(e.request))
  );
});
