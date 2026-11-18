import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
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
