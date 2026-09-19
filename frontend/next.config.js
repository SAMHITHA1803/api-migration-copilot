/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://YOUR_EC2_PUBLIC_IP:8000/:path*",
      },
    ];
  },
};

module.exports = nextConfig;