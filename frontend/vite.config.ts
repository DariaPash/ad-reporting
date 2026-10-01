import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Бэкенд не настраивает CORS: фронтенд ходит относительными путями под /api,
// а same-origin обеспечивает прокси (здесь в dev, nginx.conf в Docker).
// Префикс /api обязателен: /reports — одновременно SPA-маршрут и эндпоинт бэкенда.
const API_PROXY_TARGET = process.env.VITE_API_PROXY_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: API_PROXY_TARGET,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
        // POST /reports может обращаться к внешним API Яндекса и ждать
        // асинхронный отчёт Директа — не резать долгий запрос таймаутом.
        timeout: 180_000,
        proxyTimeout: 180_000,
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
  },
});
