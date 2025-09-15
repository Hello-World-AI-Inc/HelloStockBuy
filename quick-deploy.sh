#!/bin/bash

# 快速部署腳本 - 用於 Cursor 中的快速部署
# 這個腳本會自動提交、推送並觸發部署

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 HelloStockBuy 快速部署${NC}"

# 檢查是否有未提交的更改
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  沒有檢測到更改，無需部署${NC}"
    exit 0
fi

# 顯示更改
echo -e "${BLUE}📋 檢測到以下更改:${NC}"
git status --short

# 自動提交
echo -e "${BLUE}💾 自動提交更改...${NC}"
git add .
git commit -m "Auto-deploy: $(date '+%Y-%m-%d %H:%M:%S') - $(git log -1 --pretty=format:'%s' | head -c 50)"

# 推送到 GitHub
echo -e "${BLUE}📤 推送到 GitHub...${NC}"
git push origin main

echo -e "${GREEN}✅ 代碼已推送！GitHub Actions 將自動部署到測試服務器${NC}"
echo -e "${BLUE}🔍 查看部署狀態: https://github.com/Hello-World-AI-Inc/helloStockBuy/actions${NC}"

# 等待一段時間後檢查部署狀態
echo -e "${YELLOW}⏳ 等待 30 秒後檢查部署狀態...${NC}"
sleep 30

# 檢查測試服務器狀態
TEST_SERVER_HOST="192.168.0.6"
echo -e "${BLUE}🔍 檢查測試服務器狀態...${NC}"
if curl -f -s http://$TEST_SERVER_HOST:8000/health > /dev/null; then
    echo -e "${GREEN}✅ 測試服務器運行正常${NC}"
    echo -e "${GREEN}🌐 前端: http://$TEST_SERVER_HOST:3001${NC}"
    echo -e "${GREEN}🔧 後端: http://$TEST_SERVER_HOST:8000${NC}"
    echo -e "${GREEN}📚 API 文檔: http://$TEST_SERVER_HOST:8000/docs${NC}"
else
    echo -e "${YELLOW}⚠️  測試服務器可能還在部署中，請稍後檢查${NC}"
    echo -e "${YELLOW}🌐 前端: http://$TEST_SERVER_HOST:3001${NC}"
    echo -e "${YELLOW}🔧 後端: http://$TEST_SERVER_HOST:8000${NC}"
fi
