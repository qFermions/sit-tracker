/* Sit Tracker service worker — versioned cache-first offline support.
   Bump SW_VERSION whenever sit-tracker-v2.html changes so clients pick up the update. */
const SW_VERSION = "v4.3.0";
const CACHE = "sit-tracker-" + SW_VERSION;
const ASSETS = [
  "./sit-tracker-v2.html",
  "./manifest.json",
  "./abhinna-practice-manual.md",
  "./abhinna-6-roadmap.md",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./icons/apple-touch-icon.png"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k.startsWith("sit-tracker-") && k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// The app posts {type:'SKIP_WAITING'} when the user chooses to apply an update.
self.addEventListener("message", e => {
  if (e.data && e.data.type === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return; // never intercept external calls (e.g. AI provider)
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then(hit =>
      hit ||
      fetch(e.request).then(resp => {
        if (resp.ok) {
          const copy = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy));
        }
        return resp;
      })
    ).catch(() => caches.match("./sit-tracker-v2.html"))
  );
});
