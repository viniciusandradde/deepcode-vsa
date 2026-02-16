import withPWA from "next-pwa";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  typedRoutes: true,
  experimental: {
    allowedDevOrigins: [
      "localhost:3000",
      "localhost:3001",
      "agente-ai.hospitalevangelico.com.br",
      "https://agente-ai.hospitalevangelico.com.br",
      "http://agente-ai.hospitalevangelico.com.br",
    ],
    serverActions: {
      allowedOrigins: [
        "localhost:3000",
        "localhost:3001",
        "agente-ai.hospitalevangelico.com.br",
        "https://agente-ai.hospitalevangelico.com.br",
      ],
    },
  },
  // Security headers
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
  // Proxy para API backend
  async rewrites() {
    const backendUrl = process.env.API_BASE_URL || "http://backend:8000";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
  // Desabilitar cache em desenvolvimento para evitar problemas de modulos ausentes
  ...(process.env.NODE_ENV === "development" && {
    webpack: (config, { dev, isServer }) => {
      if (dev && !isServer) {
        config.cache = false;
        // Fix HMR WebSocket connection issues when behind a proxy
        if (config.devServer) {
          config.devServer.client = {
            ...config.devServer.client,
            webSocketURL: "wss://agente-ai.hospitalevangelico.com.br/_next/webpack-hmr",
          };
        }
      }
      return config;
    },
  }),
};

export default withPWA({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development",
})(nextConfig);
