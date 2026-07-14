// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  routeRules: {
    "/api/**": { proxy: "http://localhost:8000/**" },
  },

  compatibilityDate: "2026-01-01",
  devtools: { enabled: true },
  ssr: false,

  css: ["~/assets/css/main.css"],

  app: {
    head: {
      title: "Warehouse Storage",
      meta: [
        {
          name: "viewport",
          content: "width=device-width, initial-scale=1, maximum-scale=1",
        },
        {
          name: "description",
          content: "Barcode-driven warehouse inventory & withdrawal tracker",
        },
      ],
    },
  },

  runtimeConfig: {
    public: {
      // Base URL the BROWSER uses to reach the API. Overridable via the
      // NUXT_PUBLIC_API_BASE env var (set in docker-compose.yml).
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8000",
    },
  },

  nitro: {
    // Bind Nuxt's production server to all interfaces so it's reachable
    // from outside the Docker container.
    experimental: {
      wasm: false,
    },
  },
});
