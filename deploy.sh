#!/bin/bash

# HelloStockBuy 自動部署腳本
# 用法: ./deploy.sh [server_name]

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
DEFAULT_SERVER="test-server"
SERVER_NAME=${1:-$DEFAULT_SERVER}

# 服務器配置 (可以根據需要修改)
case $SERVER_NAME in
  "test-server")
    SERVER_HOST="your-test-server.com"
    SERVER_USER="ubuntu"
    SERVER_PATH="/home/ubuntu/helloStockBuy"
    ;;
  "staging")
    SERVER_HOST="your-staging-server.com"
    SERVER_USER="ubuntu"
    SERVER_PATH="/home/ubuntu/helloStockBuy"
    ;;
  *)
    echo -e "${RED}❌ 未知的服務器: $SERVER_NAME${NC}"
    echo "可用的服務器: test-server, staging"
    exit 1
    ;;
esac

echo -e "${BLUE}🚀 開始部署到 $SERVER_NAME ($SERVER_HOST)${NC}"

# 檢查本地更改
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  檢測到未提交的更改，正在提交...${NC}"
    git add .
    git commit -m "Auto-deploy: $(date '+%Y-%m-%d %H:%M:%S')"
fi

# 推送到 GitHub
echo -e "${BLUE}📤 推送代碼到 GitHub...${NC}"
git push origin main

# 部署到遠程服務器
echo -e "${BLUE}🔄 部署到遠程服務器...${NC}"
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << EOF
    set -e
    echo "📁 進入項目目錄..."
    cd $SERVER_PATH
    
    echo "📥 拉取最新代碼..."
    git pull origin main
    
    echo "🛑 停止現有容器..."
    docker-compose down || true
    
    echo "📦 拉取最新鏡像..."
    docker-compose pull
    
    echo "🏗️  構建並啟動容器..."
    docker-compose up -d --build
    
    echo "🧹 清理未使用的 Docker 資源..."
    docker system prune -f
    
    echo "⏳ 等待服務啟動..."
    sleep 30
    
    echo "🔍 檢查服務狀態..."
    docker-compose ps
    
    echo "🌐 檢查前端服務..."
    curl -f http://localhost:3001/health || echo "前端健康檢查失敗"
    
    echo "🔧 檢查後端服務..."
    curl -f http://localhost:8000/health || echo "後端健康檢查失敗"
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 部署成功！${NC}"
    echo -e "${GREEN}🌐 前端: http://$SERVER_HOST:3001${NC}"
    echo -e "${GREEN}🔧 後端: http://$SERVER_HOST:8000${NC}"
    echo -e "${GREEN}📚 API 文檔: http://$SERVER_HOST:8000/docs${NC}"
else
    echo -e "${RED}❌ 部署失敗！請檢查錯誤信息。${NC}"
    exit 1
fi