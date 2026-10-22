import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ["react-plotly.js/factory", "plotly.js/dist/plotly-basic.min.js"],
  },
  server: {
    host: "127.0.0.1",
    port: 5174,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  build: { chunkSizeWarningLimit: 5000 },
});
