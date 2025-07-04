# 使用 Node 20 alpine 版（體積細）
FROM node:20

# 設定工作目錄
WORKDIR /app

# 先複製 lock file（有助 Docker cache）
COPY pnpm-lock.yaml ./

# 複製其他項目檔案
COPY . .

# 啟用 pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# 安裝所有依賴（包括 devDependencies）
RUN pnpm install --frozen-lockfile --store-dir=.pnpm-store

# 開放 port
EXPOSE 3000

# 啟動 Nuxt
CMD ["pnpm", "dev"] 