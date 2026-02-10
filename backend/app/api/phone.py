"""手机设备管理API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
from ..services.adb_manager import get_adb_manager
from ..services.scrcpy_manager import get_scrcpy_manager
from ..services.phone_coordinate_picker import get_coordinate_picker

router = APIRouter(prefix="/api/phone", tags=["phone"])


class ConnectWifiRequest(BaseModel):
    ip_address: str
    port: int = 5555


class StartCoordinatePickerRequest(BaseModel):
    device_id: str
    max_size: int = 1920
    bit_rate: str = '8M'


@router.get("/devices")
async def get_devices():
    """获取已连接的设备列表"""
    try:
        adb = get_adb_manager()
        # 先启动ADB服务器
        adb.start_server()
        devices = adb.get_devices()
        return {"success": True, "devices": devices}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/device/info")
async def get_device_info(device_id: Optional[str] = None):
    """获取设备详细信息"""
    try:
        adb = get_adb_manager()
        info = adb.get_device_info(device_id)
        return {"success": True, "info": info}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/connect/wifi")
async def connect_wifi(request: ConnectWifiRequest):
    """通过WiFi连接设备"""
    try:
        adb = get_adb_manager()
        success, error = adb.connect_wifi(request.ip_address, request.port)
        if not success:
            return {"success": False, "error": error}
        return {"success": True, "message": "WiFi连接成功"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/mirror/status")
async def get_mirror_status():
    """获取镜像状态"""
    try:
        scrcpy = get_scrcpy_manager()
        status = scrcpy.get_status()
        return {"success": True, "status": status}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/mirror/start")
async def start_mirror(request: StartCoordinatePickerRequest):
    """启动手机镜像（普通Scrcpy镜像，可以正常操作手机）"""
    try:
        scrcpy = get_scrcpy_manager()
        
        # 检查是否已经在运行
        if scrcpy.is_running():
            return {"success": False, "error": "镜像已在运行中"}
        
        # 获取手机实际分辨率
        adb = get_adb_manager()
        device_info = adb.get_device_info(request.device_id)
        
        if device_info.get('current_resolution'):
            # 使用当前实际分辨率（已考虑屏幕方向）
            resolution = device_info['current_resolution']
            width, height = map(int, resolution.split('x'))
            print(f"[API] 手机当前分辨率: {width}x{height}（方向: {'横屏' if device_info.get('is_landscape') == 'true' else '竖屏'}）")
        elif device_info.get('resolution'):
            # 解析物理分辨率 "1080x2400"
            resolution = device_info['resolution']
            width, height = map(int, resolution.split('x'))
            print(f"[API] 手机物理分辨率: {width}x{height}（未获取到屏幕方向）")
        else:
            print(f"[API] 警告: 无法获取手机分辨率，使用原始分辨率（不缩放）")
        
        # 启动镜像窗口（正常模式，可以操作）
        # max_size=0 表示不限制，使用手机原始分辨率
        success, error = scrcpy.start_mirror(
            device_id=request.device_id,
            max_size=0,
            bit_rate=request.bit_rate,
            window_title="手机屏幕镜像",
            always_on_top=True,
            no_control=False,  # 允许控制
            stay_awake=True    # 保持屏幕常亮
        )
        
        if not success:
            return {"success": False, "error": error}
        
        return {"success": True, "message": "镜像已启动"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/mirror/stop")
async def stop_mirror():
    """停止手机镜像"""
    try:
        scrcpy = get_scrcpy_manager()
        success, error = scrcpy.stop_mirror()
        if not success:
            return {"success": False, "error": error}
        
        return {"success": True, "message": "镜像已停止"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/coordinate-picker/start")
async def start_coordinate_picker(request: StartCoordinatePickerRequest):
    """启动坐标选择器 - 最终方案"""
    try:
        scrcpy = get_scrcpy_manager()
        adb = get_adb_manager()
        
        # 获取手机分辨率（使用物理分辨率，坐标选择器会自动处理方向）
        device_info = adb.get_device_info(request.device_id)
        
        if device_info.get('resolution'):
            resolution = device_info['resolution']
            phone_width, phone_height = map(int, resolution.split('x'))
        else:
            # 默认分辨率
            phone_width = 1080
            phone_height = 2400
        
        # 如果已经在运行，只启动监听
        if scrcpy.is_running():
            picker = get_coordinate_picker()
            picker.set_phone_resolution(phone_width, phone_height)
            picker.start()
            
            # 查找并置顶窗口
            _focus_scrcpy_window()
            
            return {"success": True, "message": "坐标选择器已启动"}
        
        # 启动镜像窗口（max_size=0 使用原始分辨率）
        success, error = scrcpy.start_mirror(
            device_id=request.device_id,
            max_size=0,
            bit_rate=request.bit_rate,
            window_title="手机坐标选择器",
            always_on_top=True,
            no_control=True,  # 禁用控制
            stay_awake=False
        )
        
        if not success:
            return {"success": False, "error": error}
        
        # 等待窗口创建
        import asyncio
        await asyncio.sleep(1.5)
        
        # 查找并置顶窗口
        _focus_scrcpy_window()
        
        # 启动监听
        picker = get_coordinate_picker()
        picker.set_phone_resolution(phone_width, phone_height)
        picker.start()
        
        return {"success": True, "message": "坐标选择器已启动"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _focus_scrcpy_window():
    """查找并置顶 Scrcpy 窗口"""
    try:
        import win32gui
        import win32con
        import time
        
        # 重试最多 5 次，每次等待 0.5 秒
        for attempt in range(5):
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if "手机" in title or "坐标选择器" in title:
                        windows.append(hwnd)
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                hwnd = windows[0]
                try:
                    # 置顶窗口
                    win32gui.SetWindowPos(
                        hwnd,
                        win32con.HWND_TOPMOST,
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
                    )
                    
                    # 激活窗口（聚焦）
                    # 使用 ShowWindow 先显示窗口
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    
                    # 然后尝试设置为前台窗口
                    try:
                        win32gui.SetForegroundWindow(hwnd)
                        print(f"[API] ✅ 已置顶并聚焦 Scrcpy 窗口")
                    except:
                        # 如果 SetForegroundWindow 失败，使用备用方法
                        # 通过模拟 Alt 键来绕过 Windows 的前台窗口限制
                        import win32api
                        import win32con as wcon
                        
                        # 按下 Alt 键
                        win32api.keybd_event(wcon.VK_MENU, 0, 0, 0)
                        # 设置前台窗口
                        win32gui.SetForegroundWindow(hwnd)
                        # 释放 Alt 键
                        win32api.keybd_event(wcon.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                        print(f"[API] ✅ 已置顶并聚焦 Scrcpy 窗口（使用备用方法）")
                    
                    return  # 成功，退出函数
                except Exception as e:
                    print(f"[API] ⚠️ 第 {attempt + 1} 次尝试置顶窗口失败: {e}")
                    if attempt < 4:  # 如果不是最后一次尝试
                        time.sleep(0.5)  # 等待 0.5 秒后重试
                    continue
            else:
                # 没找到窗口，等待后重试
                if attempt < 4:
                    time.sleep(0.5)
        
        print(f"[API] ⚠️ 未找到 Scrcpy 窗口或置顶失败")
    except Exception as e:
        print(f"[API] ⚠️ 置顶窗口异常: {e}")


@router.post("/coordinate-picker/test")
async def test_coordinate(x: int, y: int, device_id: Optional[str] = None):
    """测试坐标（通过ADB在手机上执行点击）"""
    try:
        adb = get_adb_manager()
        
        # 临时启用触摸显示，让用户能看到点击位置
        adb.enable_show_touches(True, device_id)
        
        # 执行点击
        success, error = adb.tap(x, y, device_id)
        if not success:
            return {"success": False, "error": error}
        
        # 等待一小段时间让用户看到触摸效果
        import asyncio
        await asyncio.sleep(0.5)
        
        # 禁用触摸显示
        adb.enable_show_touches(False, device_id)
        
        return {"success": True, "message": f"已在手机上点击坐标 ({x}, {y})"}
    except Exception as e:
        return {"success": False, "error": str(e)}


class ShowTouchesRequest(BaseModel):
    """显示触摸操作请求"""
    enable: bool
    device_id: Optional[str] = None


@router.post("/settings/show-touches")
async def set_show_touches(request: ShowTouchesRequest):
    """启用/禁用显示触摸操作（开发者选项）
    
    启用后，手机屏幕上会显示触摸点的圆圈标记
    """
    try:
        adb = get_adb_manager()
        success, error = adb.enable_show_touches(request.enable, request.device_id)
        if not success:
            return {"success": False, "error": error}
        
        action = "已启用" if request.enable else "已禁用"
        return {"success": True, "message": f"{action}触摸显示"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/settings/pointer-location")
async def set_pointer_location(request: ShowTouchesRequest):
    """启用/禁用指针位置（开发者选项）
    
    启用后，屏幕顶部会显示触摸坐标信息
    """
    try:
        adb = get_adb_manager()
        success, error = adb.enable_pointer_location(request.enable, request.device_id)
        if not success:
            return {"success": False, "error": error}
        
        action = "已启用" if request.enable else "已禁用"
        return {"success": True, "message": f"{action}指针位置显示"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/coordinate-picker/stop")
async def stop_coordinate_picker():
    """停止坐标选择器"""
    try:
        # 停止坐标监听
        picker = get_coordinate_picker()
        picker.stop()
        
        # 停止镜像窗口
        scrcpy = get_scrcpy_manager()
        success, error = scrcpy.stop_mirror()
        if not success:
            return {"success": False, "error": error}
        
        return {"success": True, "message": "坐标选择器已停止"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/coordinate-picker/coordinate")
async def get_picked_coordinate():
    """获取已选择的坐标"""
    try:
        picker = get_coordinate_picker()
        coord = picker.get_picked_coordinate()
        
        if coord:
            return {"success": True, "x": coord[0], "y": coord[1], "picked": True}
        else:
            return {"success": True, "picked": False}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/screenshot")
async def get_screenshot(device_id: Optional[str] = None):
    """截取手机屏幕"""
    try:
        import tempfile
        adb = get_adb_manager()
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            screenshot_path = tmp_file.name
        
        # 截取屏幕
        success, error = adb.screenshot(screenshot_path, device_id)
        if not success:
            return {"success": False, "error": error}
        
        return {"success": True, "path": screenshot_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/screenshot/file")
async def get_screenshot_file(device_id: Optional[str] = None):
    """获取手机截图文件"""
    from fastapi.responses import FileResponse
    import tempfile
    
    try:
        adb = get_adb_manager()
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            screenshot_path = tmp_file.name
        
        # 截取屏幕
        success, error = adb.screenshot(screenshot_path, device_id)
        if not success:
            raise HTTPException(status_code=500, detail=error)
        
        return FileResponse(
            screenshot_path,
            media_type="image/png",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CaptureTemplateRequest(BaseModel):
    device_id: str
    x: int
    y: int
    width: int
    height: int
    save_name: Optional[str] = None


class CalibrateRequest(BaseModel):
    window_points: List[List[int]]  # [[x1,y1], [x2,y2], ...]
    phone_points: List[List[int]]   # [[x1,y1], [x2,y2], ...]


@router.post("/coordinate-picker/calibrate")
async def calibrate_coordinate_picker(request: CalibrateRequest):
    """校准坐标映射
    
    需要提供至少2个对应点:
    - window_points: 窗口坐标列表
    - phone_points: 对应的手机实际坐标列表
    """
    try:
        picker = get_coordinate_picker()
        
        # 转换为元组列表
        window_points = [tuple(p) for p in request.window_points]
        phone_points = [tuple(p) for p in request.phone_points]
        
        success = picker.calibrate(window_points, phone_points)
        
        if success:
            return {"success": True, "message": "坐标映射校准成功"}
        else:
            return {"success": False, "error": "校准失败，请检查输入数据"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/coordinate-picker/calibration-status")
async def get_calibration_status():
    """获取校准状态"""
    try:
        picker = get_coordinate_picker()
        return {
            "success": True,
            "is_calibrated": picker.is_calibrated,
            "calibration_data": picker.calibration_data if picker.is_calibrated else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class QuickCalibrateRequest(BaseModel):
    """快速校准请求"""
    window_x: int  # 用户在窗口上点击的X坐标
    window_y: int  # 用户在窗口上点击的Y坐标
    actual_phone_x: int  # 手机上实际点击的X坐标
    actual_phone_y: int  # 手机上实际点击的Y坐标
    window_width: Optional[int] = None  # 窗口宽度（可选，如果未提供则使用已保存的）
    window_height: Optional[int] = None  # 窗口高度（可选，如果未提供则使用已保存的）
    phone_width: Optional[int] = None  # 手机宽度（可选，如果未提供则使用已保存的）
    phone_height: Optional[int] = None  # 手机高度（可选，如果未提供则使用已保存的）


@router.post("/coordinate-picker/quick-calibrate")
async def quick_calibrate(request: QuickCalibrateRequest):
    """快速校准 - 只需一个点即可校准
    
    用户在窗口上点击一个位置，然后告诉我们手机上实际点击的位置
    我们会根据这个点来调整坐标映射
    """
    try:
        picker = get_coordinate_picker()
        
        # 如果提供了窗口尺寸和手机分辨率，则更新
        if request.window_width and request.window_height:
            picker.window_width = request.window_width
            picker.window_height = request.window_height
        
        if request.phone_width and request.phone_height:
            picker.phone_width = request.phone_width
            picker.phone_height = request.phone_height
        
        # 确保有窗口尺寸和手机分辨率
        if not picker.window_width or not picker.window_height:
            return {"success": False, "error": "未获取窗口尺寸，请提供 window_width 和 window_height"}
        
        if not picker.phone_width or not picker.phone_height:
            return {"success": False, "error": "未设置手机分辨率，请提供 phone_width 和 phone_height"}
        
        # 使用单点偏移校准
        success = picker.calibrate_with_offset(
            request.window_x,
            request.window_y,
            request.actual_phone_x,
            request.actual_phone_y
        )
        
        if success:
            return {
                "success": True,
                "message": "快速校准成功",
                "calibration_data": picker.calibration_data
            }
        else:
            return {"success": False, "error": "校准失败"}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@router.post("/coordinate-picker/start-two-click-calibrate")
async def start_two_click_calibrate():
    """开始两次点击校准
    
    用户需要：
    1. 在窗口上点击一个位置（红点）
    2. 点击「测试」按钮，观察手机上实际点击的位置（绿点）
    3. 在窗口上点击绿点的位置
    
    系统会自动计算偏移并校准
    """
    try:
        picker = get_coordinate_picker()
        
        # 确保坐标选择器正在运行
        if not picker.is_active:
            return {"success": False, "error": "坐标选择器未启动"}
        
        # 确保有窗口句柄
        if not picker.scrcpy_hwnd:
            picker.scrcpy_hwnd = picker.find_scrcpy_window()
            if not picker.scrcpy_hwnd:
                return {"success": False, "error": "未找到 Scrcpy 窗口"}
        
        # 确保有手机分辨率
        if not picker.phone_width or not picker.phone_height:
            return {"success": False, "error": "未设置手机分辨率"}
        
        # 启动两次点击校准
        picker.start_two_click_calibration()
        
        return {
            "success": True,
            "message": "已开始两次点击校准，请按照提示操作",
            "step": 1,
            "instruction": "第1步: 请在窗口上点击一个位置（红点）"
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@router.post("/coordinate-picker/cancel-calibrate")
async def cancel_calibrate():
    """取消校准"""
    try:
        picker = get_coordinate_picker()
        picker.cancel_calibration()
        return {"success": True, "message": "已取消校准"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/coordinate-picker/calibration-step")
async def get_calibration_step():
    """获取当前校准步骤"""
    try:
        picker = get_coordinate_picker()
        
        if not picker.calibration_mode:
            return {
                "success": True,
                "in_calibration": False,
                "step": 0
            }
        
        if not picker.calibration_first_window_coord:
            return {
                "success": True,
                "in_calibration": True,
                "step": 1,
                "instruction": "第1步: 请在窗口上点击一个位置（红点）"
            }
        else:
            return {
                "success": True,
                "in_calibration": True,
                "step": 2,
                "first_coord": picker.calibration_first_window_coord,
                "instruction": "第2步: 点击「测试」按钮，观察手机上实际点击的位置（绿点）\n第3步: 在窗口上点击绿点的位置"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/coordinate-picker/auto-calibrate")
async def auto_calibrate_coordinate_picker(device_id: str):
    """自动校准坐标映射
    
    通过在手机屏幕的多个位置点击并获取实际触摸坐标来建立准确的映射关系
    """
    try:
        import asyncio
        import time
        
        picker = get_coordinate_picker()
        adb = get_adb_manager()
        
        # 确保坐标选择器正在运行
        if not picker.is_active:
            return {"success": False, "error": "坐标选择器未启动"}
        
        # 确保有窗口句柄
        if not picker.scrcpy_hwnd:
            picker.scrcpy_hwnd = picker.find_scrcpy_window()
            if not picker.scrcpy_hwnd:
                return {"success": False, "error": "未找到 Scrcpy 窗口"}
        
        # 确保有手机分辨率
        if not picker.phone_width or not picker.phone_height:
            return {"success": False, "error": "未设置手机分辨率"}
        
        print(f"[AutoCalibrate] 开始自动校准...")
        print(f"[AutoCalibrate] 手机分辨率: {picker.phone_width}x{picker.phone_height}")
        
        # 定义校准点（手机坐标）：四个角 + 中心
        calibration_points_phone = [
            (50, 50),  # 左上角（留一点边距）
            (picker.phone_width - 50, 50),  # 右上角
            (50, picker.phone_height - 50),  # 左下角
            (picker.phone_width - 50, picker.phone_height - 50),  # 右下角
            (picker.phone_width // 2, picker.phone_height // 2),  # 中心
        ]
        
        window_points = []
        phone_points = []
        
        # 临时禁用正常的坐标选择回调
        original_callback = picker.callback
        picker.callback = None
        
        # 对每个校准点进行测试
        for i, (phone_x, phone_y) in enumerate(calibration_points_phone):
            print(f"[AutoCalibrate] 校准点 {i+1}/5: 手机坐标 ({phone_x}, {phone_y})")
            
            # 在手机上点击这个位置
            success, error = adb.tap(phone_x, phone_y, device_id)
            if not success:
                picker.callback = original_callback
                return {"success": False, "error": f"在手机上点击失败: {error}"}
            
            # 等待一小段时间，让用户看到点击效果
            time.sleep(0.3)
            
            # 获取当前鼠标在窗口中的位置
            # 这里我们需要用户把鼠标移动到刚才点击的位置
            # 但这样不太实际，所以我们换一个思路：
            # 让用户在窗口上点击，然后我们在手机上也点击同样的位置，比较结果
        
        # 恢复回调
        picker.callback = original_callback
        
        # 上面的方法不太可行，我们需要换一个思路
        # 让用户手动点击窗口上的几个位置，然后告诉我们手机上实际点击的位置
        
        return {
            "success": False,
            "error": "自动校准功能需要用户交互，请使用快速校准接口"
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


class ManualCalibrateRequest(BaseModel):
    """手动校准请求"""
    device_id: str


@router.post("/coordinate-picker/start-manual-calibrate")
async def start_manual_calibrate(request: ManualCalibrateRequest):
    """开始手动校准流程
    
    返回需要用户点击的窗口位置列表
    """
    try:
        picker = get_coordinate_picker()
        
        # 确保坐标选择器正在运行
        if not picker.is_active:
            return {"success": False, "error": "坐标选择器未启动"}
        
        # 确保有窗口句柄和尺寸
        if not picker.scrcpy_hwnd:
            picker.scrcpy_hwnd = picker.find_scrcpy_window()
            if not picker.scrcpy_hwnd:
                return {"success": False, "error": "未找到 Scrcpy 窗口"}
        
        # 获取窗口尺寸
        if not picker.window_width or not picker.window_height:
            # 尝试获取窗口尺寸
            try:
                client_rect = win32gui.GetClientRect(picker.scrcpy_hwnd)
                picker.window_width = client_rect[2]
                picker.window_height = client_rect[3]
            except:
                return {"success": False, "error": "无法获取窗口尺寸"}
        
        # 确保有手机分辨率
        if not picker.phone_width or not picker.phone_height:
            return {"success": False, "error": "未设置手机分辨率"}
        
        # 定义校准点（窗口坐标）：四个角 + 中心
        margin = 50  # 边距
        calibration_points_window = [
            (margin, margin),  # 左上角
            (picker.window_width - margin, margin),  # 右上角
            (margin, picker.window_height - margin),  # 左下角
            (picker.window_width - margin, picker.window_height - margin),  # 右下角
            (picker.window_width // 2, picker.window_height // 2),  # 中心
        ]
        
        return {
            "success": True,
            "message": "请依次点击窗口上的以下位置，并记录手机上实际点击的坐标",
            "calibration_points": [
                {"index": i, "window_x": x, "window_y": y}
                for i, (x, y) in enumerate(calibration_points_window)
            ],
            "window_size": {
                "width": picker.window_width,
                "height": picker.window_height
            },
            "phone_size": {
                "width": picker.phone_width,
                "height": picker.phone_height
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


class SubmitCalibrationDataRequest(BaseModel):
    """提交校准数据请求"""
    window_x: int
    window_y: int
    device_id: str


@router.post("/coordinate-picker/get-actual-coordinate")
async def get_actual_coordinate(request: SubmitCalibrationDataRequest):
    """获取窗口坐标对应的实际手机坐标
    
    用户在窗口上点击一个位置，我们在手机上也点击，然后通过 getevent 获取实际坐标
    """
    try:
        import subprocess
        import re
        import time
        
        picker = get_coordinate_picker()
        adb = get_adb_manager()
        
        # 确保有窗口句柄
        if not picker.scrcpy_hwnd:
            picker.scrcpy_hwnd = picker.find_scrcpy_window()
            if not picker.scrcpy_hwnd:
                return {"success": False, "error": "未找到 Scrcpy 窗口"}
        
        # 将窗口坐标转换为手机坐标（使用当前的转换逻辑）
        # 先模拟屏幕坐标
        point = win32gui.ClientToScreen(picker.scrcpy_hwnd, (request.window_x, request.window_y))
        screen_x, screen_y = point
        
        # 转换为手机坐标
        phone_coord = picker.get_window_coordinate(picker.scrcpy_hwnd, screen_x, screen_y)
        if not phone_coord:
            return {"success": False, "error": "无法转换坐标"}
        
        estimated_x, estimated_y = phone_coord
        
        # 在手机上点击这个位置
        success, error = adb.tap(estimated_x, estimated_y, request.device_id)
        if not success:
            return {"success": False, "error": f"在手机上点击失败: {error}"}
        
        # 等待点击完成
        time.sleep(0.2)
        
        # 通过 getevent 获取实际触摸坐标
        # 这个方法比较复杂，需要解析 getevent 的输出
        # 暂时返回估算的坐标，让用户手动确认
        
        return {
            "success": True,
            "window_x": request.window_x,
            "window_y": request.window_y,
            "estimated_phone_x": estimated_x,
            "estimated_phone_y": estimated_y,
            "message": "已在手机上点击，请观察实际点击位置并手动输入实际坐标"
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@router.post("/screenshot/capture-template")
async def capture_template_from_screenshot(request: CaptureTemplateRequest):
    """从手机截图中截取指定区域作为模板图像"""
    try:
        import cv2
        import numpy as np
        import tempfile
        import uuid
        from datetime import datetime
        
        adb = get_adb_manager()
        
        # 创建临时目录保存截图
        with tempfile.TemporaryDirectory() as temp_dir:
            screenshot_path = os.path.join(temp_dir, 'phone_screenshot.png')
            
            # 截取手机屏幕
            success, error = adb.screenshot(screenshot_path, request.device_id)
            if not success:
                return {"success": False, "error": f"截取手机屏幕失败: {error}"}
            
            # 读取截图
            screen = cv2.imread(screenshot_path)
            if screen is None:
                return {"success": False, "error": "无法读取手机截图"}
            
            screen_h, screen_w = screen.shape[:2]
            
            # 验证坐标和尺寸
            if request.x < 0 or request.y < 0 or request.x + request.width > screen_w or request.y + request.height > screen_h:
                return {
                    "success": False,
                    "error": f"截取区域超出屏幕范围（屏幕: {screen_w}x{screen_h}，请求: {request.x},{request.y},{request.width}x{request.height}）"
                }
            
            if request.width < 10 or request.height < 10:
                return {"success": False, "error": "截取区域太小，最小尺寸为 10x10"}
            
            # 截取指定区域
            template = screen[request.y:request.y+request.height, request.x:request.x+request.width]
            
            # 生成文件名
            save_name = request.save_name
            if not save_name:
                save_name = f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 保存到图像资源目录
            from ..api.image_assets import IMAGE_UPLOAD_DIR, image_assets
            
            file_id = str(uuid.uuid4())
            saved_name = f"{file_id}.png"
            file_path = os.path.join(IMAGE_UPLOAD_DIR, saved_name)
            
            # 保存图像
            cv2.imencode('.png', template)[1].tofile(file_path)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 存储元数据
            asset = {
                'id': file_id,
                'name': saved_name,
                'originalName': f"{save_name}.png",
                'size': file_size,
                'uploadedAt': datetime.now().isoformat(),
                'path': file_path,
                'folder': '',
                'extension': '.png',
            }
            image_assets[file_id] = asset
            
            return {
                "success": True,
                "message": f"已截取模板图像 ({request.width}x{request.height})",
                "asset": {
                    'id': asset['id'],
                    'name': asset['name'],
                    'originalName': asset['originalName'],
                    'size': asset['size'],
                    'uploadedAt': asset['uploadedAt'],
                    'folder': asset['folder'],
                    'extension': asset['extension'],
                    'path': asset['path']
                }
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}
