#!/bin/bash

# 測試服務器設置腳本
# 在遠程服務器上運行此腳本來設置 HelloStockBuy

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 設置 HelloStockBuy 測試服務器...${NC}"

# 更新系統
echo -e "${YELLOW}📦 更新系統包...${NC}"
sudo apt update && sudo apt upgrade -y

# 安裝 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}🐳 安裝 Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo -e "${GREEN}✅ Docker 已安裝${NC}"
fi

# 安裝 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}🐳 安裝 Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo -e "${GREEN}✅ Docker Compose 已安裝${NC}"
fi

# 安裝 Git
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}📥 安裝 Git...${NC}"
    sudo apt install git -y
else
    echo -e "${GREEN}✅ Git 已安裝${NC}"
fi

# 創建項目目錄
PROJECT_DIR="/home/$USER/helloStockBuy"
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}📁 創建項目目錄...${NC}"
    mkdir -p $PROJECT_DIR
    cd $PROJECT_DIR
    
    # 克隆項目 (需要先設置 GitHub SSH key)
    echo -e "${YELLOW}📥 克隆項目...${NC}"
    git clone git@github.com:Hello-World-AI-Inc/helloStockBuy.git .
else
    echo -e "${GREEN}✅ 項目目錄已存在${NC}"
    cd $PROJECT_DIR
fi

# 創建環境變量文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚙️  創建環境變量文件...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  請編輯 .env 文件設置您的配置${NC}"
fi

# 設置防火牆 (可選)
echo -e "${YELLOW}🔥 設置防火牆規則...${NC}"
sudo ufw allow 22    # SSH
sudo ufw allow 3001  # Frontend
sudo ufw allow 8000  # Backend
sudo ufw allow 5432  # PostgreSQL (如果需要外部訪問)
sudo ufw --force enable

# 創建健康檢查腳本
cat > health-check.sh << 'EOF'
#!/bin/bash
echo "🔍 檢查 HelloStockBuy 服務狀態..."

# 檢查 Docker 容器
echo "📦 Docker 容器狀態:"
docker-compose ps

# 檢查前端
echo "🌐 前端健康檢查:"
curl -f http://localhost:3001/health || echo "❌ 前端服務異常"

# 檢查後端
echo "🔧 後端健康檢查:"
curl -f http://localhost:8000/health || echo "❌ 後端服務異常"

# 檢查數據庫
echo "🗄️  數據庫連接:"
docker-compose exec -T db pg_isready -U postgres || echo "❌ 數據庫連接異常"
EOF

chmod +x health-check.sh

# 創建重啟腳本
cat > restart.sh << 'EOF'
#!/bin/bash
echo "🔄 重啟 HelloStockBuy 服務..."
docker-compose down
docker-compose up -d --build
echo "✅ 服務已重啟"
EOF

chmod +x restart.sh

echo -e "${GREEN}✅ 測試服務器設置完成！${NC}"
echo -e "${BLUE}📋 下一步:${NC}"
echo -e "1. 編輯 .env 文件設置您的配置"
echo -e "2. 運行: docker-compose up -d"
echo -e "3. 檢查狀態: ./health-check.sh"
echo -e "4. 重啟服務: ./restart.sh"
echo -e ""
echo -e "${GREEN}🌐 服務將在以下端口運行:${NC}"
echo -e "- 前端: http://$(curl -s ifconfig.me):3001"
echo -e "- 後端: http://$(curl -s ifconfig.me):8000"
echo -e "- API 文檔: http://$(curl -s ifconfig.me):8000/docs"
