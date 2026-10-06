import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const configured = process.env.BACKEND_URL?.trim();
    if (process.env.VERCEL && !configured) {
      throw new Error("Set BACKEND_URL to the deployed FastAPI origin in Vercel before building.");
    }
    const backend = new URL(configured || "http://127.0.0.1:8000");
    if (!['http:', 'https:'].includes(backend.protocol) || backend.username || backend.password ||
        backend.pathname !== '/' || backend.search || backend.hash) {
      throw new Error("BACKEND_URL must be an HTTP(S) origin without credentials, a path, or a query.");
    }
    if (process.env.VERCEL && (backend.protocol !== 'https:' ||
        ['localhost', '127.0.0.1', '[::1]'].includes(backend.hostname))) {
      throw new Error("BACKEND_URL must be a public HTTPS origin when deploying to Vercel.");
    }
    return [{ source: "/api/:path*", destination: `${backend.origin}/api/:path*` }];
  },
};

export default nextConfig;
