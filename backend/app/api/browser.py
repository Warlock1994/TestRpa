"""自动化浏览器API路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal

from app.services.browser_manager import (
    is_browser_open,
    start_browser,
    stop_browser,
    send_command,
    navigate,
    start_picker,
    stop_picker,
    get_selected_element,
    get_similar_elements,
    is_picker_active,
    get_user_data_dir,
)

router = APIRouter(prefix="/api/browser", tags=["browser"])


class BrowserConfig(BaseModel):
    type: Literal['msedge', 'chrome', 'chromium', 'firefox'] = 'msedge'
    executablePath: Optional[str] = None
    userDataDir: Optional[str] = None
    fullscreen: bool = False
    launchArgs: Optional[str] = None


class OpenBrowserRequest(BaseModel):
    url: str = "about:blank"
    browserConfig: Optional[BrowserConfig] = None


class NavigateRequest(BaseModel):
    url: str


@router.post("/open")
async def open_browser(request: OpenBrowserRequest = OpenBrowserRequest()):
    """打开自动化浏览器"""
    # 提取浏览器配置
    browser_type = 'msedge'
    executable_path = None
    user_data_dir = None
    fullscreen = False
    if request.browserConfig:
        browser_type = request.browserConfig.type
        executable_path = request.browserConfig.executablePath
        user_data_dir = request.browserConfig.userDataDir
        fullscreen = request.browserConfig.fullscreen
    
    if is_browser_open():
        # 已打开，导航到新URL
        if request.url != "about:blank":
            navigate(request.url)
        return {"message": "浏览器已打开", "status": "opened"}
    
    # 启动新进程
    success, error = start_browser(
        browser_type=browser_type, 
        executable_path=executable_path, 
        user_data_dir=user_data_dir,
        fullscreen=fullscreen
    )
    if success:
        if request.url != "about:blank":
            navigate(request.url)
        return {"message": "浏览器已打开", "status": "opened"}
    
    raise HTTPException(status_code=500, detail=f"打开浏览器失败: {error}")


@router.post("/close")
async def close_browser():
    """关闭自动化浏览器"""
    stop_browser()
    return {"message": "浏览器已关闭", "status": "closed"}


@router.get("/status")
async def get_browser_status():
    """获取浏览器状态"""
    is_open = is_browser_open()
    return {
        "status": "opened" if is_open else "closed",
        "isOpen": is_open,
        "pickerActive": is_picker_active()
    }


@router.post("/navigate")
async def navigate_to(request: NavigateRequest):
    """导航到指定URL"""
    result = navigate(request.url)
    if result.get("success"):
        return {"message": "导航成功", "url": request.url}
    raise HTTPException(status_code=500, detail=result.get("error", "导航失败"))


@router.post("/picker/start")
async def api_start_picker():
    """启动元素选择器"""
    result = start_picker()
    if result.get("success"):
        return {"message": "选择器已启动", "status": "active"}
    raise HTTPException(status_code=500, detail=result.get("error", "启动失败"))


@router.post("/picker/stop")
async def api_stop_picker():
    """停止元素选择器"""
    stop_picker()
    return {"message": "选择器已停止", "status": "inactive"}


@router.get("/picker/selected")
async def api_get_selected_element():
    """获取选中的单个元素"""
    result = get_selected_element()
    if result.get("success"):
        data = result.get("data")
        if data:
            return {"selected": True, "element": data}
        return {"selected": False, "element": None}
    raise HTTPException(status_code=400, detail=result.get("error", "获取失败"))


@router.get("/picker/similar")
async def api_get_similar_elements():
    """获取选中的相似元素"""
    result = get_similar_elements()
    if result.get("success"):
        data = result.get("data")
        if data:
            return {
                "selected": True,
                "similar": {
                    "pattern": data.get("pattern", ""),
                    "count": data.get("count", 0),
                    "indices": data.get("indices", []),
                    "minIndex": data.get("minIndex", 1),
                    "maxIndex": data.get("maxIndex", 1)
                }
            }
        return {"selected": False, "similar": None}
    raise HTTPException(status_code=400, detail=result.get("error", "获取失败"))
