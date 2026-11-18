import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/health": "http://127.0.0.1:8000",
      "/upload": "http://127.0.0.1:8000",
      "/harmonize": "http://127.0.0.1:8000",
      "/validate": "http://127.0.0.1:8000",
      "/investigations": "http://127.0.0.1:8000",
      "/dsa": "http://127.0.0.1:8000",
      "/db": "http://127.0.0.1:8000",
      "/export": "http://127.0.0.1:8000",
      "/audit": "http://127.0.0.1:8000",
      "/review": "http://127.0.0.1:8000",
    },
  },
  optimizeDeps: {
    exclude: ["maplibre-gl"]
  },
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes("maplibre-gl")) {
            return "maplibre";
          }
          if (id.includes("react-force-graph-2d") || id.includes("d3-force")) {
            return "graph";
          }
          if (id.includes("lucide-react")) {
            return "lucide";
          }
          if (id.includes("node_modules/react/") || id.includes("node_modules/react-dom/")) {
            return "vendor";
          }
        }
      }
    }
  }
});
