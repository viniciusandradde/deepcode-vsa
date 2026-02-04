import withPWA from "next-pwa";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  typedRoutes: true,
  allowedDevOrigins: ["agente-ai.hospitalevangelico.com.br"],
  experimental: {
    serverActions: {
      allowedOrigins: ["localhost", "agente-ai.hospitalevangelico.com.br"],
    },
  },
  // Proxy para API backend - necessário quando acessado via domínio/proxy reverso
  async rewrites() {
    const backendUrl = process.env.API_BASE_URL || "http://backend:8000";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
  // Desabilitar cache em desenvolvimento para evitar problemas de módulos ausentes
  ...(process.env.NODE_ENV === "development" && {
    webpack: (config, { dev, isServer }) => {
      if (dev) {
        // Desabilitar cache do webpack em desenvolvimento
        config.cache = false;
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


