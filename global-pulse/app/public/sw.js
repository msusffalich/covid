/* Global Pulse — service worker PWA.

   Navegacion (index.html): network-first. Assets con hash y iconos:
   cache-first. Datos del pulso: network-first con respaldo cache
   (offline muestra el ultimo pulso valido).

   POR QUE index.html NO VA CACHE-FIRST (roto el 2026-08-12):
   el index referencia los bundles por nombre con hash. Al reconstruir la app
   el hash cambia y el bundle viejo DESAPARECE del servidor. Un dispositivo con
   el index antiguo en cache pedia un .js que ya devolvia 404, no cargaba nada
   y se quedaba en blanco — de forma permanente, porque `activate` solo purga
   cachés cuya clave difiere de VERSION, y VERSION estaba escrita a mano.
   El HTML de entrada tiene que venir siempre de la red cuando la haya. */
const VERSION = 'gp-v2'
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

/** Red primero, cache como respaldo. Para lo que caduca: datos y HTML. */
function redPrimero(peticion) {
  return fetch(peticion).then((res) => {
    const copia = res.clone()
    caches.open(VERSION).then((c) => c.put(peticion, copia))
    return res
  }).catch(() => caches.match(peticion).then((hit) => hit || caches.match('./index.html')))
}

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url)
  if (e.request.method !== 'GET' || url.origin !== location.origin) return

  // El documento de entrada: siempre fresco si hay red. Cubre tanto la
  // navegacion (modo standalone de la PWA) como la peticion directa del HTML.
  if (e.request.mode === 'navigate' ||
      url.pathname === '/' ||
      url.pathname.endsWith('/index.html')) {
    e.respondWith(redPrimero(e.request))
    return
  }

  if (url.pathname.includes('/data/')) {
    e.respondWith(redPrimero(e.request))
    return
  }

  // cache-first solo para lo inmutable: assets con hash en el nombre e iconos
  e.respondWith(
    caches.match(e.request).then((hit) => hit ||
      fetch(e.request).then((res) => {
        const copy = res.clone()
        caches.open(VERSION).then((c) => c.put(e.request, copy))
        return res
      }))
  )
})
