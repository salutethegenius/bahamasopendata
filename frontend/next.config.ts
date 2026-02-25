import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "bahamasopendata.com",
        pathname: "/_next/static/media/**",
      },
    ],
  },
};

export default nextConfig;
