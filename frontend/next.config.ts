import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 生產環境使用 standalone 模式以減少 Docker 映像大小
  output: "standalone",
};

export default nextConfig;
