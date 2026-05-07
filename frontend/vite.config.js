import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8010",
      "/assets": "http://127.0.0.1:8010",
      "/docs": "http://127.0.0.1:8010",
      "/openapi.json": "http://127.0.0.1:8010",
    },
  },
});
