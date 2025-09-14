FROM postgres:15

# 安裝 Python 和必要的套件
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-full \
    git \
    && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 建立虛擬環境
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# 複製 requirements.txt 和安裝 Python 套件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 複製 migration 檔案
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY models.py .
COPY database.py .
COPY init.sql .

# 複製初始化腳本
COPY init-db.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sh

# 設定環境變數
ENV PYTHONPATH=/app 