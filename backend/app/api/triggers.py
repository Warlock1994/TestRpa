"""触发器API路由"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.services.trigger_manager import trigger_manager


router = APIRouter(prefix="/api/triggers", tags=["triggers"])


class WebhookTriggerRequest(BaseModel):
    """Webhook触发请求"""
    data: Optional[Dict[str, Any]] = None


@router.post("/webhook/{webhook_id}")
@router.get("/webhook/{webhook_id}")
@router.put("/webhook/{webhook_id}")
@router.delete("/webhook/{webhook_id}")
async def trigger_webhook(webhook_id: str, request: Request):
    """
    触发Webhook
    支持GET/POST/PUT/DELETE方法
    """
    method = request.method

    # 获取请求数据
    try:
        if method in ['POST', 'PUT']:
            body = await request.json()
        else:
            body = dict(request.query_params)
    except:
        body = {}

    # 获取请求头
    headers = dict(request.headers)

    # 构建触发数据
    trigger_data = {
        'method': method,
        'headers': headers,
        'body': body,
        'query': dict(request.query_params),
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }

    # 触发Webhook
    success = trigger_manager.trigger_webhook(webhook_id, method, trigger_data)

    if not success:
        raise HTTPException(status_code=404, detail="Webhook不存在或HTTP方法不匹配")

    return {
        "success": True,
        "message": "Webhook已触发",
        "webhookId": webhook_id,
        "method": method
    }


@router.get("/webhooks")
async def list_webhooks():
    """获取所有已注册的Webhook"""
    from app.utils.config import get_backend_url
    
    webhooks = []
    for webhook_id, data in trigger_manager.webhooks.items():
        webhooks.append({
            'webhookId': webhook_id,
            'method': data['method'],
            'url': f"{get_backend_url()}/api/triggers/webhook/{webhook_id}"
        })
    return {"webhooks": webhooks}


@router.get("/hotkeys")
async def list_hotkeys():
    """获取所有已注册的热键"""
    hotkeys = []
    for trigger_id, data in trigger_manager.hotkeys.items():
        hotkeys.append({
            'triggerId': trigger_id,
            'hotkey': data['original'],
            'normalized': data['hotkey']
        })
    return {"hotkeys": hotkeys}


@router.get("/file-watchers")
async def list_file_watchers():
    """获取所有已注册的文件监控"""
    watchers = []
    for watcher_id, data in trigger_manager.file_watchers.items():
        watchers.append({
            'watcherId': watcher_id,
            'path': data['path'],
            'type': data['type'],
            'pattern': data['pattern']
        })
    return {"watchers": watchers}


@router.get("/email-monitors")
async def list_email_monitors():
    """获取所有已注册的邮件监控"""
    monitors = []
    for monitor_id, data in trigger_manager.email_monitors.items():
        monitors.append({
            'monitorId': monitor_id,
            'server': data['server'],
            'account': data['account'],
            'fromFilter': data['from_filter'],
            'subjectFilter': data['subject_filter']
        })
    return {"monitors": monitors}
