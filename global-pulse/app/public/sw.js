/* Global Pulse — service worker PWA.
   App shell: cache-first. Datos del pulso: network-first con respaldo cache
   (offline muestra el ultimo pulso valido). */
const VERSION = 'gp-v1'
const SHELL = ['./', './index.html', './manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png']

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)))
  self.skipWaiting()
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url)
  if (e.request.method !== 'GET' || url.origin !== location.origin) return

  if (url.pathname.includes('/data/')) {
    // network-first: pulso fresco si hay red; si no, ultimo valido
    e.respondWith(
      fetch(e.request).then((res) => {
        const copy = res.clone()
        caches.open(VERSION).then((c) => c.put(e.request, copy))
        return res
      }).catch(() => caches.match(e.request))
    )
    return
  }
  // cache-first para el shell y assets con hash
  e.respondWith(
    caches.match(e.request).then((hit) => hit ||
      fetch(e.request).then((res) => {
        const copy = res.clone()
        caches.open(VERSION).then((c) => c.put(e.request, copy))
        return res
      }))
  )
})
