import type { NextConfig } from "next";
import withPWAInit from "@ducanh2912/next-pwa";

const withPWA = withPWAInit({
  dest: "public",
  cacheOnFrontEndNav: true,
  aggressiveFrontEndNavCaching: true,
  reloadOnOnline: true,
  disable: process.env.NODE_ENV === "development",
  workboxOptions: {
    disableDevLogs: true,
  },
});

const nextConfig: NextConfig = {
  // 生產環境使用 standalone 模式以減少 Docker 映像大小
  output: "standalone",
  // 添加空的 turbopack 配置以支援 PWA webpack 插件
  turbopack: {},
};

export default withPWA(nextConfig);
