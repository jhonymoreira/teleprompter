// Gerado pelo build.py. Versão muda sempre que o app muda.
const CACHE = 'teleprompter-e44f6c92e6';
const FILES = ['./', 'index.html', 'fonts.css', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png', 'fonts/AtkinsonHyperlegible-400.woff2', 'fonts/AtkinsonHyperlegible-700.woff2', 'fonts/Figtree-400.woff2', 'fonts/Figtree-500.woff2', 'fonts/Figtree-600.woff2', 'fonts/Figtree-700.woff2', 'fonts/JetBrainsMono-500.woff2'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

// Com internet: busca a versão nova (até 3 s). Sem internet: usa a guardada.
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  e.respondWith(
    timeout(fetch(req), 3000)
      .then(res => {
        if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
        return res;
      })
      .catch(() => caches.match(req, { ignoreSearch: true })
        .then(hit => hit || (req.mode === 'navigate' ? caches.match('index.html') : Response.error())))
  );
});

function timeout(p, ms) {
  return new Promise((ok, fail) => {
    const t = setTimeout(() => fail(new Error('timeout')), ms);
    p.then(r => { clearTimeout(t); ok(r); }, err => { clearTimeout(t); fail(err); });
  });
}
