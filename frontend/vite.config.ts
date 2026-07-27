import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import type { ProxyOptions } from "vite";

/** Proxy API calls to FastAPI, but let the React SPA handle browser navigations. */
function apiProxy(): ProxyOptions {
  return {
    target: "http://localhost:8000",
    bypass(req) {
      const url = req.url ?? "";
      // OAuth authorize/callback exchange must hit the API (full browser redirect).
      if (url.startsWith("/auth/github")) {
        return;
      }
      const accept = req.headers.accept ?? "";
      // Full page loads request HTML; fetch() from the app requests JSON.
      if (accept.includes("text/html")) {
        return "/index.html";
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/apis": apiProxy(),
      "/changes": apiProxy(),
      "/settings": apiProxy(),
      "/repos": apiProxy(),
      "/auth": apiProxy(),
      "/health": apiProxy(),
    },
  },
});
