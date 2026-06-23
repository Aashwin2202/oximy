import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy forwards /api to the backend so the app can call relative URLs.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND ?? "http://localhost:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
});
