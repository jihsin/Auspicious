# 多階段建構 - 建構階段
FROM python:3.11-slim as builder

WORKDIR /app

# 安裝 poetry 和 export plugin
RUN pip install poetry poetry-plugin-export

COPY pyproject.toml poetry.lock* ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# 執行階段
FROM python:3.11-slim

WORKDIR /app

# 複製依賴清單並安裝
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY app ./app

# 建立資料目錄
RUN mkdir -p /app/data

# 複製資料庫
COPY auspicious.db /app/data/auspicious.db

# 設定環境變數
ENV DATABASE_URL=sqlite:////app/data/auspicious.db
ENV DEBUG=false

# Cloud Run 使用 PORT 環境變數
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
