"""高级模块执行器 - advanced_mouse"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float, parse_search_region
import asyncio
import ctypes
import os
import re
import time


@register_executor
class RealMouseScrollExecutor(ModuleExecutor):
    """真实鼠标滚动模块执行器 - 使用 SendInput API 实现真正的硬件级滚轮模拟"""

    @property
    def module_type(self) -> str:
        return "real_mouse_scroll"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        direction = context.resolve_value(config.get("direction", "down"))  # 支持变量引用
        scroll_amount = to_int(config.get("scrollAmount", 3), 3, context)  # 滚动格数
        scroll_count = to_int(config.get("scrollCount", 1), 1, context)  # 滚动次数
        scroll_interval = to_int(config.get("scrollInterval", 100), 100, context)  # 滚动间隔(毫秒)

        try:
            import ctypes
            from ctypes import wintypes
            
            # SendInput 结构体定义
            INPUT_MOUSE = 0
            MOUSEEVENTF_WHEEL = 0x0800
            WHEEL_DELTA = 120  # 一格滚轮的标准值
            
            class MOUSEINPUT(ctypes.Structure):
                _fields_ = [
                    ("dx", wintypes.LONG),
                    ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
                ]
            
            class INPUT(ctypes.Structure):
                _fields_ = [
                    ("type", wintypes.DWORD),
                    ("mi", MOUSEINPUT)
                ]
            
            # 计算滚动量（向上为正，向下为负）
            delta = WHEEL_DELTA * scroll_amount
            if direction == "down":
                delta = -delta
            
            # 执行滚动
            for i in range(scroll_count):
                # 构建 INPUT 结构
                inp = INPUT()
                inp.type = INPUT_MOUSE
                inp.mi.dx = 0
                inp.mi.dy = 0
                inp.mi.mouseData = delta & 0xFFFFFFFF  # 转为无符号
                inp.mi.dwFlags = MOUSEEVENTF_WHEEL
                inp.mi.time = 0
                inp.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
                
                # 使用 SendInput 发送滚轮事件
                ctypes.windll.user32.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(INPUT))
                
                if i < scroll_count - 1 and scroll_interval > 0:
                    await asyncio.sleep(scroll_interval / 1000)
            
            direction_text = "向下" if direction == "down" else "向上"
            return ModuleResult(
                success=True, 
                message=f"已{direction_text}滚动 {scroll_count} 次，每次 {scroll_amount} 格"
            )

        except ImportError:
            return ModuleResult(success=False, error="此功能仅支持 Windows 系统")
        except Exception as e:
            return ModuleResult(success=False, error=f"真实鼠标滚动失败: {str(e)}")

@register_executor
class RealMouseClickExecutor(ModuleExecutor):
    """真实鼠标点击模块执行器 - 使用 SendInput API 实现真正的硬件级鼠标点击"""

    @property
    def module_type(self) -> str:
        return "real_mouse_click"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import ctypes
        from ctypes import wintypes

        x = context.resolve_value(config.get("x", ""))
        y = context.resolve_value(config.get("y", ""))
        button = context.resolve_value(config.get("button", "left"))  # 支持变量引用
        click_type = context.resolve_value(config.get("clickType", "single"))  # single/double/hold
        hold_duration = to_int(config.get("holdDuration", 1000), 1000, context)  # 长按时长(毫秒)

        if not x or not y:
            return ModuleResult(success=False, error="X和Y坐标不能为空")

        try:
            x = int(x)
            y = int(y)
        except ValueError:
            return ModuleResult(success=False, error="坐标必须是数字")

        try:
            # 设置 DPI 感知，确保坐标准确
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except:
                    pass
            
            user32 = ctypes.windll.user32
            
            # SendInput 结构体定义
            INPUT_MOUSE = 0
            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            MOUSEEVENTF_RIGHTDOWN = 0x0008
            MOUSEEVENTF_RIGHTUP = 0x0010
            MOUSEEVENTF_MIDDLEDOWN = 0x0020
            MOUSEEVENTF_MIDDLEUP = 0x0040
            
            class MOUSEINPUT(ctypes.Structure):
                _fields_ = [
                    ("dx", wintypes.LONG),
                    ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
                ]
            
            class INPUT(ctypes.Structure):
                _fields_ = [
                    ("type", wintypes.DWORD),
                    ("mi", MOUSEINPUT)
                ]

            # 根据按键类型选择事件
            if button == "left":
                down_event = MOUSEEVENTF_LEFTDOWN
                up_event = MOUSEEVENTF_LEFTUP
            elif button == "right":
                down_event = MOUSEEVENTF_RIGHTDOWN
                up_event = MOUSEEVENTF_RIGHTUP
            else:  # middle
                down_event = MOUSEEVENTF_MIDDLEDOWN
                up_event = MOUSEEVENTF_MIDDLEUP

            button_text = {"left": "左键", "right": "右键", "middle": "中键"}[button]
            
            # 使用 SetCursorPos 直接移动鼠标（不需要坐标转换，更精确）
            def move_mouse(px, py):
                user32.SetCursorPos(int(px), int(py))
            
            # 发送鼠标按键事件
            def send_mouse_event(event_flag):
                inp = INPUT()
                inp.type = INPUT_MOUSE
                inp.mi.dx = 0
                inp.mi.dy = 0
                inp.mi.mouseData = 0
                inp.mi.dwFlags = event_flag
                inp.mi.time = 0
                inp.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
                user32.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(INPUT))

            if click_type == "hold":
                # 长按模式
                move_mouse(x, y)
                await asyncio.sleep(0.02)
                send_mouse_event(down_event)
                await asyncio.sleep(hold_duration / 1000)
                send_mouse_event(up_event)
                
                return ModuleResult(
                    success=True, 
                    message=f"已在 ({x}, {y}) 执行{button_text}长按 {hold_duration}ms"
                )
            else:
                # 单击或双击模式
                click_count = 2 if click_type == "double" else 1
                move_mouse(x, y)
                await asyncio.sleep(0.02)
                
                for _ in range(click_count):
                    send_mouse_event(down_event)
                    await asyncio.sleep(0.05)
                    send_mouse_event(up_event)
                    if click_type == "double":
                        await asyncio.sleep(0.1)

                click_text = "双击" if click_type == "double" else "单击"
                return ModuleResult(
                    success=True, 
                    message=f"已在 ({x}, {y}) 执行{button_text}{click_text}"
                )

        except Exception as e:
            return ModuleResult(success=False, error=f"鼠标点击失败: {str(e)}")

@register_executor
class RealMouseMoveExecutor(ModuleExecutor):
    """真实鼠标移动模块执行器 - 使用 SetCursorPos 实现精确的鼠标移动"""

    @property
    def module_type(self) -> str:
        return "real_mouse_move"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import ctypes

        x = context.resolve_value(config.get("x", ""))
        y = context.resolve_value(config.get("y", ""))
        duration = to_int(config.get("duration", 0), 0, context)

        if not x or not y:
            return ModuleResult(success=False, error="X和Y坐标不能为空")

        try:
            target_x = int(x)
            target_y = int(y)
        except ValueError:
            return ModuleResult(success=False, error="坐标必须是数字")

        try:
            # 设置 DPI 感知，确保坐标准确
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except:
                    pass
            
            user32 = ctypes.windll.user32

            if duration > 0:
                # 平滑移动
                class POINT(ctypes.Structure):
                    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
                
                pt = POINT()
                user32.GetCursorPos(ctypes.byref(pt))
                start_x, start_y = pt.x, pt.y

                steps = max(10, duration // 10)
                for i in range(steps + 1):
                    progress = i / steps
                    current_x = int(start_x + (target_x - start_x) * progress)
                    current_y = int(start_y + (target_y - start_y) * progress)
                    user32.SetCursorPos(current_x, current_y)
                    await asyncio.sleep(duration / 1000 / steps)
            else:
                # 瞬间移动
                user32.SetCursorPos(target_x, target_y)

            return ModuleResult(
                success=True, 
                message=f"鼠标已移动到 ({target_x}, {target_y})"
            )

        except Exception as e:
            return ModuleResult(success=False, error=f"鼠标移动失败: {str(e)}")

@register_executor
class RealMouseDragExecutor(ModuleExecutor):
    """真实鼠标拖拽模块执行器 - 使用 SetCursorPos + SendInput 实现精确的鼠标拖拽"""

    @property
    def module_type(self) -> str:
        return "real_mouse_drag"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import ctypes
        from ctypes import wintypes

        # 获取起点和终点坐标
        start_x = context.resolve_value(config.get("startX", ""))
        start_y = context.resolve_value(config.get("startY", ""))
        end_x = context.resolve_value(config.get("endX", ""))
        end_y = context.resolve_value(config.get("endY", ""))
        button = context.resolve_value(config.get("button", "left"))  # 支持变量引用
        duration = to_int(config.get("duration", 500), 500, context)  # 拖拽时长，默认500ms

        # 验证坐标
        if not start_x or not start_y:
            return ModuleResult(success=False, error="起点坐标不能为空")
        if not end_x or not end_y:
            return ModuleResult(success=False, error="终点坐标不能为空")

        try:
            start_x = int(start_x)
            start_y = int(start_y)
            end_x = int(end_x)
            end_y = int(end_y)
        except ValueError:
            return ModuleResult(success=False, error="坐标必须是数字")

        try:
            # 设置 DPI 感知，确保坐标准确
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except:
                    pass
            
            user32 = ctypes.windll.user32
            
            # SendInput 结构体定义
            INPUT_MOUSE = 0
            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            MOUSEEVENTF_RIGHTDOWN = 0x0008
            MOUSEEVENTF_RIGHTUP = 0x0010
            MOUSEEVENTF_MIDDLEDOWN = 0x0020
            MOUSEEVENTF_MIDDLEUP = 0x0040
            
            class MOUSEINPUT(ctypes.Structure):
                _fields_ = [
                    ("dx", wintypes.LONG),
                    ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
                ]
            
            class INPUT(ctypes.Structure):
                _fields_ = [
                    ("type", wintypes.DWORD),
                    ("mi", MOUSEINPUT)
                ]

            # 根据按键类型选择事件
            if button == "left":
                down_event = MOUSEEVENTF_LEFTDOWN
                up_event = MOUSEEVENTF_LEFTUP
            elif button == "right":
                down_event = MOUSEEVENTF_RIGHTDOWN
                up_event = MOUSEEVENTF_RIGHTUP
            else:  # middle
                down_event = MOUSEEVENTF_MIDDLEDOWN
                up_event = MOUSEEVENTF_MIDDLEUP
            
            # 发送鼠标按键事件
            def send_mouse_event(event_flag):
                inp = INPUT()
                inp.type = INPUT_MOUSE
                inp.mi.dx = 0
                inp.mi.dy = 0
                inp.mi.mouseData = 0
                inp.mi.dwFlags = event_flag
                inp.mi.time = 0
                inp.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
                user32.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(INPUT))

            # 1. 移动到起点
            user32.SetCursorPos(start_x, start_y)
            await asyncio.sleep(0.05)
            
            # 2. 按下鼠标
            send_mouse_event(down_event)
            await asyncio.sleep(0.05)

            # 3. 平滑拖拽到终点
            steps = max(10, duration // 20)  # 至少10步，每步约20ms
            for i in range(1, steps + 1):
                progress = i / steps
                current_x = int(start_x + (end_x - start_x) * progress)
                current_y = int(start_y + (end_y - start_y) * progress)
                user32.SetCursorPos(current_x, current_y)
                await asyncio.sleep(duration / 1000 / steps)

            # 4. 释放鼠标
            await asyncio.sleep(0.05)
            send_mouse_event(up_event)

            button_text = {"left": "左键", "right": "右键", "middle": "中键"}[button]
            return ModuleResult(
                success=True, 
                message=f"已使用{button_text}从 ({start_x}, {start_y}) 拖拽到 ({end_x}, {end_y})"
            )

        except Exception as e:
            return ModuleResult(success=False, error=f"鼠标拖拽失败: {str(e)}")

@register_executor
class GetMousePositionExecutor(ModuleExecutor):
    """获取鼠标位置模块执行器"""

    @property
    def module_type(self) -> str:
        return "get_mouse_position"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import ctypes

        variable_name_x = config.get("variableNameX", "")
        variable_name_y = config.get("variableNameY", "")

        if not variable_name_x and not variable_name_y:
            return ModuleResult(success=False, error="至少需要指定一个变量名")

        try:
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))

            if variable_name_x:
                context.set_variable(variable_name_x, pt.x)
            if variable_name_y:
                context.set_variable(variable_name_y, pt.y)

            return ModuleResult(
                success=True, 
                message=f"鼠标位置: ({pt.x}, {pt.y})",
                data={"x": pt.x, "y": pt.y}
            )

        except Exception as e:
            return ModuleResult(success=False, error=f"获取鼠标位置失败: {str(e)}")