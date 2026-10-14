// Family tree app: the page always comes from the network when online (so updates show),
// images are kept on the device so the gallery also opens offline.
const CACHE = 'tree-v1';
self.addEventListener('install', e => { self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(['./', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png']))); });
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (u.origin !== location.origin) return;
  const isPage = r.mode === 'navigate' || u.pathname.endsWith('/') || u.pathname.endsWith('.html');
  if (isPage) {
    e.respondWith(fetch(r).then(res => {
      if (!u.search.includes('check=')) { const c = res.clone(); caches.open(CACHE).then(x => x.put(u.pathname, c)); }
      return res;
    }).catch(() => caches.match(u.pathname).then(m => m || caches.match('./'))));
    return;
  }
  e.respondWith(caches.match(r).then(m => m || fetch(r).then(res => {
    const c = res.clone(); caches.open(CACHE).then(x => x.put(r, c)); return res;
  })));
});
