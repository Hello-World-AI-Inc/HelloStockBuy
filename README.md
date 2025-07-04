# HelloStockBuy - 股票交易平台

一個整合多個新聞來源的即時股票市場數據和新聞聚合平台。

## 功能特色

- 📈 即時股票市場數據
- 📰 多來源新聞聚合 (NewsAPI.org, Finnhub, Marketaux, FMP)
- 🔄 定期自動新聞更新
- 🐳 Docker 容器化部署
- 🎨 現代化 Vue.js 前端界面

## 系統需求

- Docker Desktop
- Git

## 快速開始

### 1. 克隆專案
```bash
git clone <your-github-repo-url>
cd helloStockBuy
```

### 2. 設定環境變數
複製環境變數範本並填入你的 API 金鑰：

```bash
# 複製範本檔案
cp .env.example .env

# 編輯 .env 檔案，填入你的 API 金鑰
nano .env  # 或使用你喜歡的編輯器
```

**必需的 API 金鑰**（至少需要其中兩個才能正常運作）：
- `FINNHUB_API_KEY` - 免費註冊 [finnhub.io](https://finnhub.io/)
- `NEWSAPI_API_KEY` - 免費註冊 [newsapi.org](https://newsapi.org/)

**可選的 API 金鑰**：
- `MARKETAUX_API_KEY` - 付費服務 [marketaux.com](https://marketaux.com/)
- `FMP_API_KEY` - 付費服務 [financialmodelingprep.com](https://financialmodelingprep.com/)

### 3. 取得 API 金鑰

點擊上面的連結註冊並取得免費的 API 金鑰。系統會自動跳過無法使用的付費服務。

### 4. 啟動服務
```bash
# 啟動所有服務
docker compose up

# 或只啟動後端
docker compose up backend

# 或只啟動前端
docker compose up frontend
```

### 5. 存取應用程式
- 前端: http://localhost:3000
- 後端 API: http://localhost:8000
- API 文檔: http://localhost:8000/docs

## API 端點

### 市場數據
- `GET /market-data/{symbol}` - 取得股票市場數據

### 新聞
- `GET /news/all/{symbol}` - 取得所有來源的新聞
- `GET /news/finnhub/{symbol}` - 只取得 Finnhub 新聞
- `GET /news/newsapi/{symbol}` - 只取得 NewsAPI 新聞

## 專案結構

```
helloStockBuy/
├── backend/                 # FastAPI 後端
│   ├── main.py             # 主應用程式
│   ├── market_data.py      # 市場數據和新聞來源
│   ├── models.py           # 資料庫模型
│   ├── requirements.txt    # Python 依賴
│   └── Dockerfile         # 後端容器設定
├── frontend/               # Nuxt.js 前端
│   ├── pages/             # 頁面組件
│   ├── package.json       # Node.js 依賴
│   └── Dockerfile         # 前端容器設定
├── db/                    # 資料庫資料
├── docker-compose.yml     # Docker 編排
└── .env                   # 環境變數
```

## 開發指南

### 重建容器
```bash
# 重建後端
docker compose build backend

# 重建前端
docker compose build frontend

# 重建所有服務
docker compose build
```

### 查看日誌
```bash
# 查看後端日誌
docker compose logs backend

# 查看前端日誌
docker compose logs frontend

# 即時追蹤日誌
docker compose logs -f backend
```

### 停止服務
```bash
docker compose down
```

## 故障排除

### 常見問題

1. **API 金鑰錯誤**
   - 確認 `.env` 檔案中的 API 金鑰正確
   - 檢查 API 金鑰是否有效且未過期

2. **容器無法啟動**
   - 確認 Docker Desktop 正在運行
   - 檢查端口是否被佔用

3. **新聞來源無法使用**
   - 系統會自動跳過無法使用的來源
   - 檢查日誌了解具體錯誤原因

### 日誌位置
- 後端日誌: `docker compose logs backend`
- 前端日誌: `docker compose logs frontend`

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 授權

MIT License