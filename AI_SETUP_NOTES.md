# 🤖 AI 助手設置說明

## 📋 項目配置摘要

### 🏗️ 開發環境設置
- **本地機器**: 只運行 Cursor 進行代碼編輯
- **測試服務器**: `192.168.0.6` (root 用戶)
- **項目路徑**: `/root/helloStockBuy`

### 🐳 Docker 服務配置
- **前端**: http://192.168.0.6:3001
- **後端**: http://192.168.0.6:8000
- **API 文檔**: http://192.168.0.6:8000/docs
- **數據庫**: PostgreSQL on port 5432

### 🚀 部署工作流程
1. 在 Cursor 中編輯代碼
2. 運行 `./quick-deploy.sh`
3. 自動提交、推送並部署到測試服務器
4. 在測試服務器上測試更改

### 🔧 常用命令
```bash
# 快速部署
./quick-deploy.sh

# 檢查服務狀態
ssh root@192.168.0.6 "cd /root/helloStockBuy && docker-compose ps"

# 查看日誌
ssh root@192.168.0.6 "cd /root/helloStockBuy && docker-compose logs"

# 重啟服務
ssh root@192.168.0.6 "cd /root/helloStockBuy && docker-compose restart"
```

### ⚙️ 環境變量配置
- `FINNHUB_API_KEY=demo_key_12345` (至少 10 個字符)
- `NEWS_FETCH_INTERVAL_HOURS=2`
- 環境變量文件位置: `./backend/.env` 和 `./.env`

### 🚨 故障排除
- **端口 8000 被佔用**: 殺死 docker-proxy 進程
- **後端無法啟動**: 檢查環境變量配置
- **API 密鑰驗證失敗**: 確保密鑰長度至少 10 個字符

### 📝 給下一個 AI 助手的說明
1. 這個項目使用遠程開發設置
2. 本地機器只用於代碼編輯
3. 所有 Docker 服務運行在測試服務器 192.168.0.6 上
4. 使用 `./quick-deploy.sh` 進行自動部署
5. 測試服務器運行前端在端口 3001，後端在端口 8000
6. SSH 訪問: `ssh root@192.168.0.6`
7. 服務器上的項目路徑: `/root/helloStockBuy`
8. 部署後總是檢查服務狀態
9. 環境變量已配置用於演示/測試

---
**最後更新**: 2025-09-15
**配置狀態**: ✅ 已設置並測試
