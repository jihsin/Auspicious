# backend/app/services/notification.py
"""通知服務

支援 LINE Messaging API 發送通知。
用於 API 失效、系統異常等警報。
"""

import os
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional

# 台灣時區 (UTC+8)
TW_TIMEZONE = timezone(timedelta(hours=8))


# LINE Messaging API 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")
LINE_API_URL = "https://api.line.me/v2/bot/message/push"

# 通知冷卻時間（避免重複通知）
_last_notification_time: dict[str, datetime] = {}
NOTIFICATION_COOLDOWN = timedelta(hours=1)  # 同類型通知間隔至少 1 小時


def _can_send_notification(notification_type: str) -> bool:
    """檢查是否可以發送通知（避免重複）"""
    last_time = _last_notification_time.get(notification_type)
    if last_time is None:
        return True
    return datetime.now(TW_TIMEZONE) - last_time > NOTIFICATION_COOLDOWN


def _record_notification(notification_type: str):
    """記錄通知發送時間"""
    _last_notification_time[notification_type] = datetime.now(TW_TIMEZONE)


async def send_line_message(message: str) -> bool:
    """發送 LINE 訊息

    Args:
        message: 要發送的訊息內容

    Returns:
        是否發送成功
    """
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("LINE 通知未設定：缺少 TOKEN 或 USER_ID")
        return False

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }

    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message,
            }
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(LINE_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"LINE 通知發送成功")
                return True
            else:
                print(f"LINE 通知發送失敗: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"LINE 通知發送錯誤: {e}")
        return False


async def notify_api_key_expired(api_name: str, error_message: str) -> bool:
    """通知 API 密鑰失效

    Args:
        api_name: API 名稱（如 CWA、Gemini）
        error_message: 錯誤訊息

    Returns:
        是否發送成功
    """
    notification_type = f"api_expired_{api_name}"

    if not _can_send_notification(notification_type):
        print(f"通知冷卻中，跳過 {notification_type}")
        return False

    message = f"""🚨 API 密鑰失效警報

📛 API：{api_name}
⏰ 時間：{datetime.now(TW_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}
❌ 錯誤：{error_message}

請盡快更新 API 密鑰：
• CWA：https://opendata.cwa.gov.tw/user/authkey
• Gemini：https://aistudio.google.com/apikey

更新後需重新部署 Cloud Run。"""

    success = await send_line_message(message)
    if success:
        _record_notification(notification_type)
    return success


async def notify_system_error(error_type: str, error_message: str, details: Optional[str] = None) -> bool:
    """通知系統錯誤

    Args:
        error_type: 錯誤類型
        error_message: 錯誤訊息
        details: 詳細資訊（可選）

    Returns:
        是否發送成功
    """
    notification_type = f"system_error_{error_type}"

    if not _can_send_notification(notification_type):
        print(f"通知冷卻中，跳過 {notification_type}")
        return False

    message = f"""⚠️ 系統錯誤警報

📛 類型：{error_type}
⏰ 時間：{datetime.now(TW_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}
❌ 錯誤：{error_message}"""

    if details:
        message += f"\n📋 詳情：{details[:200]}"  # 限制長度

    success = await send_line_message(message)
    if success:
        _record_notification(notification_type)
    return success


async def notify_daily_summary(stats: dict) -> bool:
    """發送每日摘要（可選功能）

    Args:
        stats: 統計資料

    Returns:
        是否發送成功
    """
    message = f"""📊 好日子每日摘要

📅 日期：{datetime.now(TW_TIMEZONE).strftime('%Y-%m-%d')}
🌡️ 臺北即時：{stats.get('taipei_temp', 'N/A')}°C
📈 API 呼叫：{stats.get('api_calls', 0)} 次
✅ 系統狀態：正常"""

    return await send_line_message(message)
