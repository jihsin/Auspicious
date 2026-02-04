# 建構階段
FROM node:20-alpine AS builder

WORKDIR /app

# 啟用 pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# 複製依賴配置
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

# 複製源碼並建構
COPY . .
RUN pnpm build

# 執行階段
FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production

# 建立非 root 使用者
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 複製建構產物
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 切換至非 root 使用者
USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
