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
    },
  },

  nitro: {
    experimental: {
      wasm: false,
    },
  },
});
