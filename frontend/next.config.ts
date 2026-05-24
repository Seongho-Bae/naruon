import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  experimental: {
    // @ts-expect-error: Next.js 15 types don't include allowedDevOrigins but Turbopack uses it
    allowedDevOrigins: ['127.0.0.1', 'localhost', '169.254.23.164'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
