import withPWA from "next-pwa";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  typedRoutes: true,
  experimental: {
    serverActions: {
      allowedOrigins: ["localhost", "agente-ai.hospitalevangelico.com.br"],
    },
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


