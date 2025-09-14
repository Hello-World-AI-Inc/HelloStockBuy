#!/bin/bash
set -e

echo "等待 PostgreSQL 啟動..."
# 等待 PostgreSQL 完全啟動
until pg_isready -U $POSTGRES_USER -d $POSTGRES_DB; do
  echo "等待 PostgreSQL 啟動..."
  sleep 2
done

echo "PostgreSQL 已啟動，開始執行 migration..."

# 設定資料庫連接字串
export SQLALCHEMY_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@127.0.0.1:5432/$POSTGRES_DB"

# 執行 Alembic migration
cd /app
alembic upgrade head

# 匯入初始資料
echo "匯入初始 SQL 資料..."
psql -U $POSTGRES_USER -d $POSTGRES_DB -f /app/init.sql

echo "資料庫 migration 與初始資料匯入完成！" 