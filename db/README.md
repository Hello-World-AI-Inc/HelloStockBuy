# 資料庫容器

這個目錄包含自定義的 PostgreSQL 容器，會在啟動時自動執行資料庫 migration。

## 功能

- 基於 PostgreSQL 15
- 自動安裝 Python 和 Alembic
- 容器啟動時自動執行資料庫 migration
- 無需手動執行 SQL 腳本

## 檔案結構

```
db/
├── Dockerfile          # 自定義 PostgreSQL 容器
├── requirements.txt    # Python 套件需求
├── init-db.sh         # 初始化腳本
├── models.py          # SQLAlchemy 模型
├── database.py        # 資料庫連接設定
├── alembic/           # Alembic migration 檔案
├── alembic.ini        # Alembic 設定
├── data/              # PostgreSQL 資料檔案 (gitignored)
└── README.md          # 本檔案
```

## 使用方式

1. 確保環境變數已設定（在專案根目錄的 .env 檔案）
2. 執行 `docker compose up -d`
3. 資料庫會自動建立所有必要的資料表

## 環境變數

需要以下環境變數：
- `POSTGRES_USER`: 資料庫使用者名稱
- `POSTGRES_PASSWORD`: 資料庫密碼
- `POSTGRES_DB`: 資料庫名稱

## 注意事項

- 首次啟動時會自動執行 migration
- 資料檔案會保存在 `./db/data/` 目錄
- 如果資料庫已存在，不會重複執行 migration 