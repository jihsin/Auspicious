# 好日子 App 後端服務

歷史氣象統計與節氣分析 API 服務。

## 技術棧

- Python 3.11+
- FastAPI
- SQLAlchemy
- Pandas/NumPy

## 開發

```bash
# 安裝依賴
poetry install

# 啟動開發伺服器
poetry run uvicorn app.main:app --reload --port 8000

# 執行測試
poetry run pytest
```

## API 端點

- `GET /health` - 健康檢查
