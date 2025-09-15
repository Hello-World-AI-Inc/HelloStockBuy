# 🚀 HelloStockBuy 開發工作流程

## 📋 概述

這個文檔描述了如何設置一個高效的開發環境，其中：
- **本地機器**: 只運行 Cursor 進行代碼編輯
- **測試服務器**: 運行 Docker 容器進行測試和開發

## 🏗️ 架構設置

```
┌─────────────────┐    ┌─────────────────┐
│   本地機器       │    │   測試服務器     │
│   (Cursor)      │    │   (Docker)      │
│                 │    │                 │
│   - 代碼編輯     │───►│   - 自動部署     │
│   - Git 提交     │    │   - Docker 運行  │
│   - 推送代碼     │    │   - 測試驗證     │
└─────────────────┘    └─────────────────┘
```

## 🛠️ 設置步驟

### 1. 測試服務器設置

在您的測試服務器上運行：

```bash
# 下載並運行設置腳本
curl -fsSL https://raw.githubusercontent.com/Hello-World-AI-Inc/helloStockBuy/main/setup-test-server.sh | bash
```

或者手動設置：

```bash
# 克隆項目
git clone git@github.com:Hello-World-AI-Inc/helloStockBuy.git
cd helloStockBuy

# 運行設置腳本
chmod +x setup-test-server.sh
./setup-test-server.sh
```

### 2. GitHub Secrets 設置

在 GitHub 倉庫設置中添加以下 Secrets：

- `TEST_SERVER_SSH_KEY`: 測試服務器的 SSH 私鑰
- `TEST_SERVER_USER`: 測試服務器用戶名 (通常是 `ubuntu`)
- `TEST_SERVER_HOST`: 測試服務器 IP 地址或域名

### 3. 本地開發環境

確保您的本地機器有：
- Git
- SSH 密鑰對 (用於 GitHub 和測試服務器)
- Cursor IDE

## 🔄 開發工作流程

### 自動部署 (推薦)

每次您推送代碼到 `main` 或 `develop` 分支時，GitHub Actions 會自動：

1. 拉取最新代碼
2. 停止現有容器
3. 構建新鏡像
4. 啟動服務
5. 執行健康檢查

### 手動部署

如果需要立即部署，可以運行：

```bash
# 部署到測試服務器
./deploy.sh test-server

# 或者部署到其他環境
./deploy.sh staging
```

### 本地開發流程

1. **編輯代碼**: 在 Cursor 中修改代碼
2. **提交更改**: 
   ```bash
   git add .
   git commit -m "描述您的更改"
   ```
3. **推送代碼**: 
   ```bash
   git push origin main
   ```
4. **自動部署**: GitHub Actions 自動部署到測試服務器
5. **測試驗證**: 訪問測試服務器 URL 驗證更改

## 🌐 服務訪問

部署完成後，您可以通過以下 URL 訪問服務：

- **前端**: `http://YOUR_SERVER_IP:3001`
- **後端 API**: `http://YOUR_SERVER_IP:8000`
- **API 文檔**: `http://YOUR_SERVER_IP:8000/docs`
- **健康檢查**: `http://YOUR_SERVER_IP:8000/health`

## 🔧 常用命令

### 測試服務器管理

```bash
# 檢查服務狀態
./health-check.sh

# 重啟服務
./restart.sh

# 查看日誌
docker-compose logs -f

# 進入容器
docker-compose exec frontend bash
docker-compose exec backend bash
```

### 本地開發

```bash
# 檢查 Git 狀態
git status

# 查看提交歷史
git log --oneline -10

# 切換分支
git checkout develop

# 合併分支
git merge develop
```

## 🚨 故障排除

### 常見問題

1. **部署失敗**
   - 檢查 GitHub Secrets 設置
   - 確認測試服務器 SSH 連接
   - 查看 GitHub Actions 日誌

2. **服務無法啟動**
   - 檢查 `.env` 文件配置
   - 確認端口沒有被佔用
   - 查看 Docker 容器日誌

3. **代碼同步問題**
   - 確認 Git 遠程倉庫設置
   - 檢查分支推送權限
   - 驗證 SSH 密鑰配置

### 日誌查看

```bash
# 查看所有服務日誌
docker-compose logs

# 查看特定服務日誌
docker-compose logs frontend
docker-compose logs backend
docker-compose logs db

# 實時查看日誌
docker-compose logs -f
```

## 📊 監控和維護

### 資源監控

```bash
# 查看 Docker 資源使用
docker stats

# 查看磁盤使用
df -h

# 查看內存使用
free -h
```

### 定期維護

```bash
# 清理未使用的 Docker 資源
docker system prune -f

# 更新系統包
sudo apt update && sudo apt upgrade -y

# 重啟服務器 (如果需要)
sudo reboot
```

## 🔐 安全建議

1. **SSH 密鑰**: 使用強密碼保護 SSH 私鑰
2. **防火牆**: 只開放必要的端口
3. **定期更新**: 保持系統和 Docker 鏡像更新
4. **備份**: 定期備份重要數據和配置
5. **監控**: 設置日誌監控和警報

## 📞 支持

如果遇到問題，請：

1. 檢查本文檔的故障排除部分
2. 查看 GitHub Issues
3. 聯繫開發團隊

---

**祝您開發愉快！** 🚀✨
