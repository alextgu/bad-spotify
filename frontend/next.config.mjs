/** @type {import('next').NextConfig} */
const nextConfig = {
  // The site is static on purpose: it reads a recorded session file, so there
  // is no backend to host, no API keys in the browser, and nothing that can
  // fail live in front of judges.
  //
  // Uncomment to export a plain folder of HTML you can drop on any static host
  // (GitHub Pages, Netlify, Vercel, a USB stick):
  //   output: "export",
};

export default nextConfig;
