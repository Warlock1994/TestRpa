"""NapCat 服务管理API"""
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# 存储 socketio 实例的引用
_sio = None


def set_napcat_sio(sio):
    """设置 socketio 实例"""
    global _sio
    _sio = sio


class NapCatStartRequest(BaseModel):
    qq_number: Optional[str] = ""


class NapCatConfigRequest(BaseModel):
    qq_number: str
    config: dict


@router.get("/napcat/status")
async def get_napcat_status():
    """获取 NapCat 服务状态"""
    from ..services.napcat_service import napcat_service
    status = napcat_service.get_status()
    qrcode_path = napcat_service.get_qrcode_path()
    status["qrcode_available"] = bool(qrcode_path)
    return status


@router.post("/napcat/start")
async def start_napcat(request: NapCatStartRequest):
    """启动 NapCat 服务"""
    from ..services.napcat_service import napcat_service
    
    def on_qrcode(qrcode_path: str):
        print(f"[NapCat API] 二维码已生成: {qrcode_path}")
        if _sio:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_sio.emit('napcat:qrcode', {'path': qrcode_path}))
                else:
                    loop.run_until_complete(_sio.emit('napcat:qrcode', {'path': qrcode_path}))
            except Exception as e:
                print(f"[NapCat API] 发送二维码事件失败: {e}")
    
    def on_login(qq_number: str):
        print(f"[NapCat API] 登录成功: {qq_number}")
        if _sio:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_sio.emit('napcat:login', {'qq_number': qq_number}))
                else:
                    loop.run_until_complete(_sio.emit('napcat:login', {'qq_number': qq_number}))
            except Exception as e:
                print(f"[NapCat API] 发送登录事件失败: {e}")
    
    return await napcat_service.start(request.qq_number, on_qrcode, on_login)


@router.get("/napcat/qrcode")
async def get_napcat_qrcode():
    """获取 NapCat 登录二维码"""
    from ..services.napcat_service import napcat_service
    
    qrcode_path = napcat_service.get_qrcode_path()
    if qrcode_path and Path(qrcode_path).exists():
        return FileResponse(path=qrcode_path, media_type="image/png", filename="qrcode.png")
    
    raise HTTPException(status_code=404, detail="二维码不存在，请先启动 NapCat 服务")


@router.post("/napcat/stop")
async def stop_napcat():
    """停止 NapCat 服务"""
    from ..services.napcat_service import napcat_service
    return napcat_service.stop()


@router.post("/napcat/refresh-qrcode")
async def refresh_napcat_qrcode():
    """刷新二维码 - 通过重启 NapCat 服务来生成新的二维码"""
    from ..services.napcat_service import napcat_service
    
    napcat_service.stop()
    await asyncio.sleep(1)
    
    qrcode_path = napcat_service.napcat_dir / "cache" / "qrcode.png"
    if qrcode_path.exists():
        try:
            qrcode_path.unlink()
        except:
            pass
    
    def on_qrcode(qrcode_path: str):
        print(f"[NapCat API] 新二维码已生成: {qrcode_path}")
        if _sio:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_sio.emit('napcat:qrcode', {'path': qrcode_path}))
                else:
                    loop.run_until_complete(_sio.emit('napcat:qrcode', {'path': qrcode_path}))
            except Exception as e:
                print(f"[NapCat API] 发送二维码事件失败: {e}")
    
    def on_login(qq_number: str):
        print(f"[NapCat API] 登录成功: {qq_number}")
        if _sio:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_sio.emit('napcat:login', {'qq_number': qq_number}))
                else:
                    loop.run_until_complete(_sio.emit('napcat:login', {'qq_number': qq_number}))
            except Exception as e:
                print(f"[NapCat API] 发送登录事件失败: {e}")
    
    result = await napcat_service.start("", on_qrcode, on_login)
    
    if result.get("success"):
        return {"success": True, "message": "二维码已刷新，请重新扫码"}
    else:
        return {"success": False, "error": result.get("error", "刷新失败")}


@router.post("/napcat/config")
async def update_napcat_config(request: NapCatConfigRequest):
    """更新 NapCat OneBot 配置"""
    from ..services.napcat_service import napcat_service
    return napcat_service.update_config(request.qq_number, request.config)


@router.get("/napcat/config/{qq_number}")
async def get_napcat_config(qq_number: str):
    """获取 NapCat OneBot 配置"""
    from ..services.napcat_service import napcat_service
    config = napcat_service.load_onebot_config(qq_number)
    if config:
        return {"success": True, "config": config}
    return {"success": False, "error": "配置不存在"}
