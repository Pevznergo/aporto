/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://74.208.193.3:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
