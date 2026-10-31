"""Monta o site do teleprompter (GitHub Pages) a partir de ../teleprompter.html.

O teleprompter.html é a fonte única: é o mesmo arquivo publicado no Claude.
Aqui ele ganha o <head> de app (ícone, tela cheia, funciona sem internet),
as fontes locais e um service worker com versão nova a cada mudança.

Uso:  python3 build.py
"""
import hashlib
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "teleprompter.html"

HEAD = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Teleprompter">
<meta name="theme-color" content="#0f1114">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="stylesheet" href="fonts.css">
<style>
:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
body { margin: 0; }
img { max-width: 100%; }
[hidden] { display: none !important; }
</style>
<script>
if ('serviceWorker' in navigator) addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
</script>
"""

SW = """// Gerado pelo build.py. Versão muda sempre que o app muda.
const CACHE = 'teleprompter-__VERSION__';
const FILES = ['./', 'index.html', 'fonts.css', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png', __FONTS__];

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
"""


def main():
    src = SRC.read_text(encoding="utf-8")
    top, body = src.split('<main id="setup">', 1)
    # no Claude as fontes vêm do Google; aqui ficam no próprio site
    top = re.sub(r'<link rel="(preconnect|stylesheet)" href="https://fonts\.[^"]+"[^>]*>\n', "", top)
    top = re.sub(r'<meta name="claude:[^>]+>\n', "", top)
    html = HEAD + top + "</head>\n<body>\n<main id=\"setup\">" + body + "\n</body>\n</html>\n"
    (HERE / "index.html").write_text(html, encoding="utf-8")

    fonts = sorted(p.name for p in (HERE / "fonts").glob("*.woff2"))
    version = hashlib.sha1((html + "".join(fonts)).encode()).hexdigest()[:10]
    sw = SW.replace("__VERSION__", version).replace("__FONTS__", ", ".join(f"'fonts/{f}'" for f in fonts))
    (HERE / "sw.js").write_text(sw, encoding="utf-8")
    print("index.html e sw.js gerados, versão", version)


if __name__ == "__main__":
    main()
