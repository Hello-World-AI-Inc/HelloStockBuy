# HelloStockBuy - 股票交易平台

一個整合多個新聞來源的即時股票市場數據和新聞聚合平台，具備 AI 情緒分析功能和股票數據管理。

## 功能特色

- 📈 **即時股票市場數據**（日線、分鐘線、技術指標）
- 📰 **多來源新聞聚合** (NewsAPI.org, Finnhub, Marketaux, FMP, Yahoo Finance)
- 🔄 **定期自動新聞更新**（後端自動排程，依配額限制分配）
- 🤖 **AI 情緒分析**（TextBlob + OpenAI GPT-3.5）
- 🎯 **智能情緒分數**（0-100）與信心度評估
- 📊 **股票圖表與技術指標**（支援多種時間週期）
- ⚙️ **調度器控制面板**（啟動/停止、手動抓取、配額監控）
- 🎯 **目標股票管理**（動態設定監控股票）
- 🐳 **Docker 容器化部署**
- 🎨 **現代化 Vue.js 前端界面**

## 🚀 最新功能

### 股票數據管理
- **日線數據**：開盤價、收盤價、最高價、最低價、成交量
- **分鐘線數據**：支援 1分鐘、5分鐘、15分鐘、30分鐘、60分鐘
- **技術指標**：MA、EMA、RSI、MACD、布林帶、KDJ
- **交易信號**：買入/賣出信號生成
- **圖表顯示**：互動式股票圖表，支援多種時間週期

### 調度器控制面板
- **狀態監控**：即時顯示調度器運行狀態
- **手動控制**：啟動/停止新聞抓取調度器
- **手動抓取**：即時觸發新聞抓取和情緒分析
- **配額監控**：顯示各新聞來源的配額使用狀況
- **新聞統計**：顯示已抓取新聞數量統計

## ⚙️ 環境變數配置

本專案使用兩個環境變數文件來管理配置：

### 1. 根目錄 `.env` 文件
全域設定，包含資料庫、AI API 和系統配置：

```bash
# =============================================================================
# HelloStockBuy - 全域環境變數設定
# =============================================================================

# 資料庫配置
POSTGRES_USER=hellostockbuy
POSTGRES_PASSWORD=hellostockbuy123
POSTGRES_DB=hellostockbuy_db
POSTGRES_HOST=db
POSTGRES_PORT=5432

# AI API 金鑰 (可選)
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Interactive Brokers 配置 (可選)
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1

# 系統配置
MARKET_DATA_SOURCE=yahoo
NEWS_FETCH_INTERVAL_HOURS=2

# 前端配置
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
HOST=0.0.0.0

# 開發模式
NODE_ENV=development
PYTHON_ENV=development
```

### 2. 後端 `backend/.env` 文件
後端專用設定，包含新聞 API 金鑰和配額限制：

```bash
# =============================================================================
# HelloStockBuy - 後端環境變數設定
# =============================================================================

# 資料庫配置 (從根目錄 .env 繼承)
POSTGRES_USER=hellostockbuy
POSTGRES_PASSWORD=hellostockbuy123
POSTGRES_DB=hellostockbuy_db
POSTGRES_HOST=db
POSTGRES_PORT=5432

# AI API 金鑰 (可選)
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Interactive Brokers 配置 (可選)
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1

# 系統配置
MARKET_DATA_SOURCE=yahoo
NEWS_FETCH_INTERVAL_HOURS=2

# =============================================================================
# 新聞 API 金鑰配置
# =============================================================================

# Yahoo Finance (免費，無需 API 金鑰)
# 使用 yfinance 模組，無需設定

# Finnhub API
FINNHUB_API_KEY=your_finnhub_api_key_here

# Marketaux API
MARKETAUX_API_KEY=your_marketaux_api_key_here

# FMP (Financial Modeling Prep) API
FMP_API_KEY=your_fmp_api_key_here

# NewsAPI.org
NEWSAPI_API_KEY=your_newsapi_key_here

# =============================================================================
# 配額限制配置
# =============================================================================

# Marketaux 配額限制
MARKETAUX_MAX_REQUEST_DAILY=100
MARKETAUX_MAX_NEWS_PER_REQUEST=3

# FMP 配額限制
FMP_MAX_REQUEST_DAILY=250
FMP_MAX_NEWS_PER_REQUEST=100

# NewsAPI.org 配額限制
NEWSAPI_MAX_REQUEST_DAILY=100
NEWSAPI_MAX_NEWS_PER_REQUEST=100

# Finnhub 配額限制 (免費版每日 60 次)
FINNHUB_MAX_REQUEST_DAILY=60
FINNHUB_MAX_NEWS_PER_REQUEST=10

# =============================================================================
# 調度器配置
# =============================================================================

# 新聞抓取間隔 (小時)
NEWS_FETCH_INTERVAL_HOURS=2

# 股票數據抓取間隔 (分鐘)
STOCK_DATA_FETCH_INTERVAL_MINUTES=15

# 技術指標計算間隔 (分鐘)
TECHNICAL_INDICATORS_INTERVAL_MINUTES=5

# =============================================================================
# 情緒分析配置
# =============================================================================

# OpenAI 模型設定
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=150
OPENAI_TEMPERATURE=0.3

# 情緒分析權重
TEXTBLOB_WEIGHT=0.3
OPENAI_WEIGHT=0.7

# =============================================================================
# 股票數據配置
# =============================================================================

# 預設目標股票
DEFAULT_TARGET_SYMBOLS=AAPL,GOOGL,MSFT,TSLA,AMZN,NVDA,META,BRK.A,UNH,JNJ

# 技術指標參數
RSI_PERIOD=14
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9
BOLLINGER_PERIOD=20
BOLLINGER_STD=2
MA_PERIODS=5,10,20,50,200

# 圖表配置
CHART_DEFAULT_PERIOD=1d
CHART_DEFAULT_INTERVAL=1m
CHART_MAX_POINTS=1000
```

### 環境變數說明

#### 必需配置
- **資料庫配置**：PostgreSQL 連接設定
- **新聞 API 金鑰**：至少需要一個新聞來源的 API 金鑰

#### 可選配置
- **AI API 金鑰**：用於進階情緒分析
- **Interactive Brokers**：用於實時交易
- **配額限制**：根據各 API 服務商的限制調整

#### 重要注意事項
1. **API 金鑰安全**：請將真實的 API 金鑰替換 `your_*_api_key_here`
2. **配額管理**：根據各服務商的免費/付費計劃調整配額限制
3. **資料庫密碼**：生產環境請使用強密碼
4. **Docker 環境**：所有服務都在 Docker 容器中運行

## ⏰ 後端自動新聞抓取與配額限制

- 後端服務會自動定期從多個新聞來源（Yahoo Finance、Finnhub、Marketaux、FMP、NewsAPI.org）抓取目標股票的最新新聞，並存入 PostgreSQL 資料庫。
- 抓取頻率與每次請求新聞數量，會根據 `backend/.env` 檔案中的配額限制自動分配。例如：
  - `MARKETAUX_MAX_REQUEST_DAILY=100`（每日最多 100 次）
  - `MARKETAUX_MAX_NEWS_PER_REQUEST=3`（每次最多 3 篇）
  - 其他來源亦有類似設定
- **Marketaux** 只會在美股交易時段自動抓取。
- 配額限制可依需求調整 `backend/.env`，重啟服務後自動生效。
- 前端只會從資料庫讀取新聞，不會直接呼叫外部 API。
- 可透過 `/news/scheduler/status` API 查詢目前配額使用狀況。

## 🤖 AI 情緒分析系統

### 功能特色
- **雙重分析**：結合 TextBlob 基本情緒分析與 OpenAI GPT-3.5 進階分析
- **智能評分**：0-100 分數系統，包含信心度評估
- **情緒標籤**：自動分類為 very_positive、positive、slightly_positive、neutral、slightly_negative、negative、very_negative
- **即時分析**：新聞抓取時自動進行情緒分析並存入資料庫

### 技術實現
- **TextBlob**：提供基本情緒極性分析（-1 到 1）
- **OpenAI GPT-3.5**：進階股票相關情緒分析，考慮股價影響、市場情緒等因素
- **加權平均**：結合兩種分析結果，提供更準確的情緒分數

### API 端點
- `GET /news/sentiment/{symbol}` - 查詢特定股票的情緒分析結果
- `GET /news/stats` - 查詢整體新聞統計，包含情緒分析統計

### 情緒分數說明
- **70-100**：非常正面 (very_positive)
- **60-69**：正面 (positive)  
- **45-59**：稍微正面 (slightly_positive)
- **40-44**：中性 (neutral)
- **30-39**：稍微負面 (slightly_negative)
- **20-29**：負面 (negative)
- **0-19**：非常負面 (very_negative)

## 系統需求

- Docker Desktop
- Git

## 快速開始

### 1. 克隆專案
```bash
git clone <repository-url>
cd helloStockBuy
```

### 2. 設定環境變數
複製並編輯環境變數檔案：

```bash
# 根目錄 .env（全域設定）
cp .env.example .env

# 後端 .env（新聞 API 與配額設定）
cp backend/.env.example backend/.env
```

**重要設定：**
- `backend/.env` 包含所有新聞 API 金鑰和配額限制
- 如需 OpenAI 情緒分析，請設定 `OPENAI_API_KEY`
- 配額限制可依需求調整

### 3. 啟動服務
```bash
docker compose up --build
```

### 4. 訪問應用
- 前端：http://localhost:3001
- 後端 API：http://localhost:8000
- API 文檔：http://localhost:8000/docs

## 主要 API 端點

### 新聞相關
- `GET /news/all/{symbol}` - 獲取所有來源的新聞
- `GET /news/sentiment/{symbol}` - 獲取情緒分析結果
- `GET /news/stats` - 獲取新聞統計
- `POST /news/fetch-and-store/{symbol}` - 手動觸發新聞抓取與情緒分析
- `GET /news/scheduler/status` - 查詢調度器狀態
- `POST /news/scheduler/start` - 啟動新聞調度器
- `POST /news/scheduler/stop` - 停止新聞調度器
- `GET /news/quota-status` - 查詢配額使用狀況

### 目標股票管理
- `GET /target-symbols` - 獲取目標股票清單
- `POST /target-symbols` - 設定目標股票清單

### 市場數據
- `GET /market-data/{symbol}` - 獲取股票市場數據
- `GET /market-data-source` - 獲取當前數據來源
- `GET /stock-data/{symbol}` - 獲取股票歷史數據
- `GET /stock-data/{symbol}/chart` - 獲取股票圖表數據
- `POST /stock-data/fetch/{symbol}` - 手動觸發股票數據抓取

## 前端功能說明

### 新聞管理區塊
- **調度器狀態**：顯示當前新聞抓取調度器狀態（Running/Stopped）
- **控制按鈕**：啟動/停止調度器、手動抓取新聞、清除新聞
- **配額狀態**：顯示各新聞來源的配額使用狀況
- **新聞統計**：顯示已抓取的新聞數量

### 股票圖表區塊
- **股票代碼輸入**：輸入要查看的股票代碼
- **時間週期選擇**：選擇日線或分鐘線數據
- **間隔選擇**：選擇數據間隔（1分鐘、5分鐘、15分鐘等）
- **圖表顯示**：互動式股票圖表，顯示價格、成交量、技術指標
- **交易信號**：顯示買入/賣出信號

### 目標股票管理
- **股票清單**：顯示當前監控的目標股票
- **動態更新**：新增或移除監控股票
- **新聞顯示**：顯示目標股票的最新新聞和情緒分析

## 開發指南

### 新增情緒分析來源
1. 在 `sentiment_analyzer.py` 中新增分析器
2. 在 `_combine_scores` 方法中整合新來源
3. 更新情緒標籤邏輯

### 調整情緒分析參數
- 修改 `_get_sentiment_label` 方法中的分數閾值
- 調整 OpenAI 提示詞以改善分析準確度
- 修改加權平均邏輯

### 新增股票數據來源
1. 在 `stock_data_service.py` 中新增數據來源
2. 更新 `fetch_daily_data` 和 `fetch_minute_data` 方法
3. 新增相應的技術指標計算

## 故障排除

### 常見問題
1. **情緒分析失敗**：檢查 OpenAI API 金鑰設定
2. **新聞抓取失敗**：檢查各新聞來源的 API 金鑰和配額
3. **配額限制**：調整 `backend/.env` 中的配額設定
4. **股票數據抓取失敗**：檢查 yfinance 模組是否正確安裝
5. **前端顯示問題**：檢查瀏覽器 Console 錯誤信息

### 依賴問題解決
```bash
# 如果遇到模組缺失問題，在 Docker 容器內安裝
docker exec -it hellostockbuy-backend-1 pip install textblob yfinance

# 重新構建容器
docker compose build backend
docker compose up -d backend
```

### 日誌查看
```bash
# 查看後端日誌
docker compose logs backend

# 查看前端日誌  
docker compose logs frontend

# 查看特定容器日誌
docker logs hellostockbuy-backend-1 --tail 50
```

## 項目結構

```
helloStockBuy/
├── .env                          # 全域環境變數
├── backend/
│   ├── .env                      # 後端環境變數
│   ├── main.py                   # FastAPI 主應用
│   ├── models.py                 # 資料庫模型
│   ├── news_scheduler.py         # 新聞調度器
│   ├── sentiment_analyzer.py     # 情緒分析服務
│   ├── stock_data_service.py     # 股票數據服務
│   ├── stock_data_scheduler.py   # 股票數據調度器
│   └── requirements.txt          # Python 依賴
├── frontend/
│   ├── pages/
│   │   └── index.vue            # 主頁面
│   ├── nuxt.config.ts           # Nuxt 配置
│   └── package.json             # Node.js 依賴
├── db/                          # 資料庫文件
├── docker-compose.yml           # Docker 配置
└── README.md                    # 項目文檔
```

## 授權

MIT License