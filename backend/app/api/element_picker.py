"""元素选择器API路由 - 使用全局浏览器管理器"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.browser_manager import (
    is_browser_open,
    ensure_browser_open,
    navigate,
    start_picker,
    stop_picker,
    get_selected_element,
    get_similar_elements,
    is_picker_active,
)
from app.services.element_picker.selector import SelectorGenerator


router = APIRouter(prefix="/api/element-picker", tags=["element-picker"])


class StartPickerRequest(BaseModel):
    url: Optional[str] = None  # URL可选，为空时直接使用当前页面
    browserConfig: Optional[dict] = None  # 浏览器配置


@router.post("/start")
async def api_start_picker(request: StartPickerRequest):
    """启动元素选择器 - 使用全局浏览器，支持复用"""
    from app.services.browser_manager import (
        stop_browser, start_browser, find_page_by_url, switch_to_page
    )
    
    url = request.url.strip() if request.url else None
    browser_config = request.browserConfig or {}
    browser_type = browser_config.get('type', 'msedge')
    executable_path = browser_config.get('executablePath', '')
    fullscreen = browser_config.get('fullscreen', False)
    
    print(f"[ElementPicker] 启动请求，URL: {url or '(使用当前页面)'}, 浏览器: {browser_type}, 全屏: {fullscreen}")
    
    # 确保浏览器已打开（传递浏览器配置）
    if not ensure_browser_open(browser_type, executable_path if executable_path else None, fullscreen):
        raise HTTPException(status_code=500, detail="无法启动浏览器")
    
    # 如果提供了URL
    if url:
        # 先检查是否已有该URL的页面
        find_result = find_page_by_url(url)
        if find_result.get("success") and find_result.get("data", {}).get("found"):
            # 找到了已打开的页面，切换到该页面
            page_index = find_result["data"]["pageIndex"]
            switch_result = switch_to_page(page_index)
            if switch_result.get("success"):
                print(f"[ElementPicker] 切换到已打开的页面: {url}")
            else:
                # 切换失败，尝试导航
                nav_result = navigate(url)
                if not nav_result.get("success"):
                    raise HTTPException(status_code=500, detail=f"导航失败: {nav_result.get('error')}")
        else:
            # 没有找到，导航到目标URL
            nav_result = navigate(url)
            if not nav_result.get("success"):
                # 如果导航失败，可能是浏览器被关闭了，尝试重新启动
                print(f"[ElementPicker] 导航失败，尝试重新启动浏览器...")
                stop_browser()
                if not start_browser():
                    raise HTTPException(status_code=500, detail="无法重新启动浏览器")
                
                # 再次尝试导航
                nav_result = navigate(url)
                if not nav_result.get("success"):
                    raise HTTPException(status_code=500, detail=f"导航失败: {nav_result.get('error')}")
    # 如果没有提供URL，直接使用当前页面
    
    # 启动选择器
    result = start_picker()
    if result.get("success"):
        return {"message": "元素选择器已启动", "status": "active"}
    
    raise HTTPException(status_code=500, detail=result.get("error", "启动失败"))


@router.post("/stop")
async def api_stop_picker():
    """停止元素选择器"""
    stop_picker()
    return {"message": "元素选择器已停止", "status": "inactive"}


@router.get("/selected")
async def api_get_selected():
    """获取选中的元素"""
    if not is_browser_open():
        return {"selected": False, "active": False}
    
    result = get_selected_element()
    if result.get("success"):
        data = result.get("data")
        if data:
            # 优化选择器
            best_selector = SelectorGenerator.generate_selector(data) if hasattr(SelectorGenerator, 'generate_selector') else data.get('selector')
            return {
                "selected": True,
                "active": True,
                "element": {
                    "selector": best_selector,
                    "originalSelector": data.get('selector'),
                    "tagName": data.get('tagName', ''),
                    "text": data.get('text', ''),
                    "attributes": data.get('attributes', {}),
                    "rect": data.get('rect', {}),
                }
            }
        return {"selected": False, "active": is_picker_active()}
    
    return {"selected": False, "active": False}


@router.get("/similar")
async def api_get_similar():
    """获取相似元素"""
    if not is_browser_open():
        return {"selected": False, "active": False}
    
    result = get_similar_elements()
    if result.get("success"):
        data = result.get("data")
        if data:
            return {
                "selected": True,
                "active": True,
                "similar": {
                    "pattern": data.get('pattern', ''),
                    "count": data.get('count', 0),
                    "indices": data.get('indices', []),
                    "minIndex": data.get('minIndex', 1),
                    "maxIndex": data.get('maxIndex', 1),
                    "selector1": data.get('selector1', ''),
                    "selector2": data.get('selector2', ''),
                }
            }
        return {"selected": False, "active": is_picker_active()}
    
    return {"selected": False, "active": False}


@router.get("/status")
async def api_get_status():
    """获取选择器状态"""
    if is_picker_active():
        return {"status": "active"}
    return {"status": "inactive"}
