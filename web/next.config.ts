import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1", "localhost", "192.168.1.87"],
  async headers() {
    return [
      {
        source: "/sw.js",
        headers: [
          {
            key: "Content-Type",
            value: "application/javascript; charset=utf-8",
          },
          {
            key: "Cache-Control",
            value: "public, max-age=0, must-revalidate",
          },
        ],
      },
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "i.ytimg.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "i1.ytimg.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "i2.ytimg.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "i3.ytimg.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "i4.ytimg.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "img.youtube.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "image-cdn-ak.spotifycdn.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "yt3.googleusercontent.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "yt3.ggpht.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "f4.bcbits.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "i1.sndcdn.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "scontent.fna.fbcdn.net",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "scontent.xx.fbcdn.net",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "lookaside.fbsbx.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "linktr.ee",
        pathname: "/**",
      },
    ],
  },
};

export default nextConfig;
