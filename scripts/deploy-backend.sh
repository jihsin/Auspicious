#!/bin/bash
# 部署後端到 Cloud Run

set -e

# 設定變數
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-asia-east1}"
SERVICE_NAME="auspicious-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "=== 好日子後端部署腳本 ==="
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"

# 切換到專案根目錄
cd "$(dirname "$0")/.."

# 步驟 1: 複製資料庫到 backend 目錄
echo ""
echo ">>> 步驟 1: 複製資料庫..."
cp data/auspicious.db backend/auspicious.db
echo "資料庫已複製到 backend/auspicious.db"

# 步驟 2: 建構 Docker image
echo ""
echo ">>> 步驟 2: 建構 Docker image..."
cd backend
docker build -t ${IMAGE_NAME}:latest .

# 清理複製的資料庫
rm -f auspicious.db
cd ..

# 步驟 3: 推送到 GCR
echo ""
echo ">>> 步驟 3: 推送 Docker image 到 GCR..."
docker push ${IMAGE_NAME}:latest

# 步驟 4: 部署到 Cloud Run
echo ""
echo ">>> 步驟 4: 部署到 Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "DEBUG=false"

# 取得服務 URL
echo ""
echo ">>> 部署完成！"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
echo "API URL: ${SERVICE_URL}"
echo ""
echo "請將此 URL 設定到 Vercel 的 NEXT_PUBLIC_API_URL 環境變數"
