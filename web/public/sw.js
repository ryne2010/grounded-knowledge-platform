const SW_VERSION = "gkp-sw-v2";
const SHELL_CACHE = `${SW_VERSION}-shell`;
const STATIC_CACHE = `${SW_VERSION}-static`;
const API_CACHE = `${SW_VERSION}-api`;

const SHELL_URLS = ["/", "/index.html", "/manifest.webmanifest"];
const CACHEABLE_API_PATHS = new Set(["/api/meta", "/api/docs", "/api/stats"]);

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_URLS)).then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => ![SHELL_CACHE, STATIC_CACHE, API_CACHE].includes(key))
          .map((key) => caches.delete(key)),
      ),
    ).then(() => self.clients.claim()),
  );
});

function staleWhileRevalidate(request) {
  return caches.open(STATIC_CACHE).then((cache) =>
    cache.match(request).then((cached) => {
      const network = fetch(request)
        .then((response) => {
          if (response && response.ok) {
            cache.put(request, response.clone());
          }
          return response;
        })
        .catch(() => {
          if (cached) return cached;
          return Promise.reject(new Error("offline and static asset not cached"));
        });
      return cached || network;
    }),
  );
}

function networkFirstApi(request) {
  return caches.open(API_CACHE).then((cache) =>
    fetch(request)
      .then((response) => {
        if (response && response.ok) {
          cache.put(request, response.clone());
        }
        return response;
      })
      .catch(() =>
        cache.match(request).then((cached) => {
          if (cached) return cached;
          return Promise.reject(new Error("offline and api response not cached"));
        }),
      ),
  );
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/api/query")) {
    // Never cache query answers by default.
    event.respondWith(fetch(request));
    return;
  }

  if (url.pathname.startsWith("/api/")) {
    // Keep API caching minimal and safe-by-default.
    // Do not persist sensitive/private endpoints in offline cache.
    if (CACHEABLE_API_PATHS.has(url.pathname)) {
      event.respondWith(networkFirstApi(request));
    } else {
      event.respondWith(fetch(request));
    }
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() =>
        caches.open(SHELL_CACHE).then((cache) => cache.match("/index.html")),
      ),
    );
    return;
  }

  event.respondWith(staleWhileRevalidate(request));
});
