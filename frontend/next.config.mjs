/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Static export: the app is a client-side SPA that talks to the backend API,
  // so it deploys as plain static files (ideal for Cloudflare Pages — no adapter
  // or edge runtime needed). `next build` emits the site into `out/`.
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
