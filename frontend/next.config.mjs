/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://13.235.91.181:8000/:path*",
      },
    ];
  },
};

export default nextConfig;