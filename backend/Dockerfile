# 多階段建構 - 建構階段
FROM python:3.11-slim as builder

WORKDIR /app
RUN pip install poetry

COPY pyproject.toml poetry.lock* ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# 執行階段
FROM python:3.11-slim

WORKDIR /app

# 複製依賴清單並安裝
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
