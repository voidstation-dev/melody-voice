/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  // Ignore image optimization as we are exporting static HTML
  images: {
    unoptimized: true,
  },
  // Ensure we don't use trailing slashes to keep it simple for Tauri
  trailingSlash: false,
};

export default nextConfig;
