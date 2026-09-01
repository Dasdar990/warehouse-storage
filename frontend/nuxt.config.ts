// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from "@tailwindcss/vite";

export default defineNuxtConfig({
  vite: {
    plugins: [tailwindcss()],
  },

  routeRules: {
    // Inside Docker, the frontend must talk to "backend", not "localhost"
    "/api/**": {
      proxy:
        process.env.NODE_ENV === "development"
          ? "http://backend:8000/**"
          : "http://localhost:8000/**",
    },
  },

  compatibilityDate: "2026-01-01",
  devtools: { enabled: true },
  ssr: true,

  css: ["~/assets/css/main.css"],

  app: {
    baseURL: "/warehouse-storage-frontend/",
    head: {
      title: "Industrial Engineering Warehouse",
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
      // If the browser makes the calls, use the host's public IP/localhost.
      // If the server makes them (even with ssr: false), point to the right fallback.
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8000",
      // The NFC bridge (nfc-bridge/bridge.py) always runs on the same
      // machine as the browser showing the login page -- the kiosk the
      // PN7150 dongle is plugged into -- regardless of where the backend
      // itself is hosted, so this defaults to localhost independently of
      // apiBase.
      nfcBridgeUrl: process.env.NUXT_PUBLIC_NFC_BRIDGE_URL || "ws://localhost:8765",
    },
  },

  nitro: {
    experimental: {
      wasm: false,
    },
  },
});
