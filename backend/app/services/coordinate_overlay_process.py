"""鼠标坐标实时显示 - 独立进程脚本 (现代化UI)"""
import ctypes
import os
import sys

# Win32 类型
HWND = ctypes.c_void_p
HDC = ctypes.c_void_p
HINSTANCE = ctypes.c_void_p
HICON = ctypes.c_void_p
HCURSOR = ctypes.c_void_p
HBRUSH = ctypes.c_void_p
HFONT = ctypes.c_void_p
HPEN = ctypes.c_void_p
HRGN = ctypes.c_void_p
LPCWSTR = ctypes.c_wchar_p
WPARAM = ctypes.c_ulonglong
LPARAM = ctypes.c_longlong
BOOL = ctypes.c_int
UINT = ctypes.c_uint
LONG = ctypes.c_long
DWORD = ctypes.c_ulong

# 常量
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_LAYERED = 0x00080000
WS_POPUP = 0x80000000
WM_DESTROY = 0x0002
WM_PAINT = 0x000F
WM_TIMER = 0x0113
DT_LEFT = 0x0000
DT_VCENTER = 0x0004
DT_SINGLELINE = 0x0020
SW_SHOW = 5
LWA_ALPHA = 0x00000002
PS_SOLID = 0

# 颜色定义 (BGR 格式)
COLOR_BG = 0x302520           # 深色背景
COLOR_BORDER = 0x785030       # 边框色
COLOR_ACCENT = 0xE8A030       # 强调色 (亮蓝)
COLOR_TEXT_LABEL = 0xB0B0B0   # 标签文字
COLOR_TEXT_VALUE = 0xFFFFFF   # 数值文字
COLOR_TRANSPARENT = 0xFF00FF  # 透明色键 (品红)


class POINT(ctypes.Structure):
    _fields_ = [("x", LONG), ("y", LONG)]


class RECT(ctypes.Structure):
    _fields_ = [("left", LONG), ("top", LONG), ("right", LONG), ("bottom", LONG)]


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", HDC),
        ("fErase", BOOL),
        ("rcPaint", RECT),
        ("fRestore", BOOL),
        ("fIncUpdate", BOOL),
        ("rgbReserved", ctypes.c_byte * 32)
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", HWND),
        ("message", UINT),
        ("wParam", WPARAM),
        ("lParam", LPARAM),
        ("time", DWORD),
        ("pt", POINT)
    ]


WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, HWND, UINT, WPARAM, LPARAM)


class WNDCLASSEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", UINT),
        ("style", UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", HINSTANCE),
        ("hIcon", HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", HBRUSH),
        ("lpszMenuName", LPCWSTR),
        ("lpszClassName", LPCWSTR),
        ("hIconSm", HICON)
    ]


# 全局
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

current_x = 0
current_y = 0
g_hwnd = None
g_font_label = None
g_font_value = None
g_font_title = None
g_parent_pid = None

# 窗口尺寸
WIN_WIDTH = 180
WIN_HEIGHT = 85
CORNER_RADIUS = 12


def get_cursor_pos():
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def is_parent_alive():
    """检查父进程是否还活着"""
    if g_parent_pid is None:
        return True
    try:
        # 尝试打开父进程
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, g_parent_pid)
        if handle:
            # 检查进程是否还在运行
            exit_code = ctypes.c_ulong()
            kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            kernel32.CloseHandle(handle)
            return exit_code.value == 259  # STILL_ACTIVE
        return False
    except:
        return False


def draw_crosshair_icon(hdc, x, y, size, color):
    """绘制十字准星图标"""
    pen = gdi32.CreatePen(PS_SOLID, 2, color)
    old_pen = gdi32.SelectObject(hdc, pen)
    
    half = size // 2
    gdi32.MoveToEx(hdc, x - half, y, None)
    gdi32.LineTo(hdc, x + half + 1, y)
    gdi32.MoveToEx(hdc, x, y - half, None)
    gdi32.LineTo(hdc, x, y + half + 1)
    
    gdi32.SelectObject(hdc, old_pen)
    gdi32.DeleteObject(pen)
    
    # 中心点
    brush = gdi32.CreateSolidBrush(color)
    old_brush = gdi32.SelectObject(hdc, brush)
    gdi32.Ellipse(hdc, x - 3, y - 3, x + 4, y + 4)
    gdi32.SelectObject(hdc, old_brush)
    gdi32.DeleteObject(brush)


def wnd_proc(hwnd, msg, wparam, lparam):
    global current_x, current_y, g_font_label, g_font_value, g_font_title
    
    if msg == WM_PAINT:
        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
        
        rect = RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        
        # 用透明色填充背景
        trans_brush = gdi32.CreateSolidBrush(COLOR_TRANSPARENT)
        user32.FillRect(hdc, ctypes.byref(rect), trans_brush)
        gdi32.DeleteObject(trans_brush)
        
        # 绘制圆角矩形背景
        brush = gdi32.CreateSolidBrush(COLOR_BG)
        pen = gdi32.CreatePen(PS_SOLID, 2, COLOR_BORDER)
        old_brush = gdi32.SelectObject(hdc, brush)
        old_pen = gdi32.SelectObject(hdc, pen)
        gdi32.RoundRect(hdc, 1, 1, rect.right - 1, rect.bottom - 1, CORNER_RADIUS * 2, CORNER_RADIUS * 2)
        gdi32.SelectObject(hdc, old_brush)
        gdi32.SelectObject(hdc, old_pen)
        gdi32.DeleteObject(brush)
        gdi32.DeleteObject(pen)
        
        # 顶部强调线
        pen = gdi32.CreatePen(PS_SOLID, 3, COLOR_ACCENT)
        old_pen = gdi32.SelectObject(hdc, pen)
        gdi32.MoveToEx(hdc, 12, 4, None)
        gdi32.LineTo(hdc, rect.right - 12, 4)
        gdi32.SelectObject(hdc, old_pen)
        gdi32.DeleteObject(pen)
        
        # 创建字体
        if not g_font_title:
            g_font_title = gdi32.CreateFontW(15, 0, 0, 0, 600, 0, 0, 0, 1, 0, 0, 0, 0, "Microsoft YaHei UI")
        if not g_font_label:
            g_font_label = gdi32.CreateFontW(14, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 0, 0, "Microsoft YaHei UI")
        if not g_font_value:
            g_font_value = gdi32.CreateFontW(20, 0, 0, 0, 700, 0, 0, 0, 1, 0, 0, 0, 0, "Consolas")
        
        gdi32.SetBkMode(hdc, 1)  # TRANSPARENT
        
        # 十字准星图标
        draw_crosshair_icon(hdc, 24, 45, 18, COLOR_ACCENT)
        
        # 标题
        old_font = gdi32.SelectObject(hdc, g_font_title)
        gdi32.SetTextColor(hdc, COLOR_ACCENT)
        title_rect = RECT(48, 10, rect.right - 10, 28)
        user32.DrawTextW(hdc, "WebRPA 坐标", -1, ctypes.byref(title_rect), DT_LEFT | DT_SINGLELINE)
        
        # X 坐标
        gdi32.SelectObject(hdc, g_font_label)
        gdi32.SetTextColor(hdc, COLOR_TEXT_LABEL)
        x_label_rect = RECT(48, 32, 68, 50)
        user32.DrawTextW(hdc, "X", -1, ctypes.byref(x_label_rect), DT_LEFT | DT_SINGLELINE)
        
        gdi32.SelectObject(hdc, g_font_value)
        gdi32.SetTextColor(hdc, COLOR_TEXT_VALUE)
        x_value_rect = RECT(65, 30, 130, 52)
        user32.DrawTextW(hdc, str(current_x), -1, ctypes.byref(x_value_rect), DT_LEFT | DT_SINGLELINE)
        
        # Y 坐标
        gdi32.SelectObject(hdc, g_font_label)
        gdi32.SetTextColor(hdc, COLOR_TEXT_LABEL)
        y_label_rect = RECT(48, 54, 68, 72)
        user32.DrawTextW(hdc, "Y", -1, ctypes.byref(y_label_rect), DT_LEFT | DT_SINGLELINE)
        
        gdi32.SelectObject(hdc, g_font_value)
        gdi32.SetTextColor(hdc, COLOR_TEXT_VALUE)
        y_value_rect = RECT(65, 52, 130, 74)
        user32.DrawTextW(hdc, str(current_y), -1, ctypes.byref(y_value_rect), DT_LEFT | DT_SINGLELINE)
        
        # 分隔线
        pen = gdi32.CreatePen(PS_SOLID, 1, COLOR_BORDER)
        old_pen = gdi32.SelectObject(hdc, pen)
        gdi32.MoveToEx(hdc, 135, 30, None)
        gdi32.LineTo(hdc, 135, 72)
        gdi32.SelectObject(hdc, old_pen)
        gdi32.DeleteObject(pen)
        
        # 屏幕区域
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
        
        h_pos = "左" if current_x < screen_w // 3 else ("右" if current_x > screen_w * 2 // 3 else "中")
        v_pos = "上" if current_y < screen_h // 3 else ("下" if current_y > screen_h * 2 // 3 else "中")
        
        gdi32.SelectObject(hdc, g_font_label)
        gdi32.SetTextColor(hdc, COLOR_ACCENT)
        pos_rect = RECT(142, 42, 175, 62)
        user32.DrawTextW(hdc, f"{v_pos}{h_pos}", -1, ctypes.byref(pos_rect), DT_LEFT | DT_SINGLELINE)
        
        gdi32.SelectObject(hdc, old_font)
        user32.EndPaint(hwnd, ctypes.byref(ps))
        return 0
        
    elif msg == WM_TIMER:
        # 检查父进程
        if not is_parent_alive():
            user32.PostMessageW(hwnd, WM_DESTROY, 0, 0)
            return 0
        
        current_x, current_y = get_cursor_pos()
        
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
        
        new_x = current_x + 25
        new_y = current_y + 25
        
        if new_x + WIN_WIDTH > screen_w:
            new_x = current_x - WIN_WIDTH - 15
        if new_y + WIN_HEIGHT > screen_h:
            new_y = current_y - WIN_HEIGHT - 15
        
        user32.MoveWindow(hwnd, new_x, new_y, WIN_WIDTH, WIN_HEIGHT, False)
        user32.InvalidateRect(hwnd, None, True)
        return 0
        
    elif msg == WM_DESTROY:
        if g_font_label:
            gdi32.DeleteObject(g_font_label)
        if g_font_value:
            gdi32.DeleteObject(g_font_value)
        if g_font_title:
            gdi32.DeleteObject(g_font_title)
        user32.PostQuitMessage(0)
        return 0
    
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def main():
    global g_hwnd, g_parent_pid
    
    # 获取父进程 PID
    if len(sys.argv) > 1:
        try:
            g_parent_pid = int(sys.argv[1])
        except:
            pass
    
    # DPI 感知
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        pass
    
    wnd_proc_cb = WNDPROC(wnd_proc)
    hInstance = kernel32.GetModuleHandleW(None)
    class_name = "WebRPACoordOverlay"
    
    # 创建透明色画刷
    trans_brush = gdi32.CreateSolidBrush(COLOR_TRANSPARENT)
    
    wc = WNDCLASSEX()
    wc.cbSize = ctypes.sizeof(WNDCLASSEX)
    wc.lpfnWndProc = wnd_proc_cb
    wc.hInstance = hInstance
    wc.hCursor = user32.LoadCursorW(None, 32512)
    wc.hbrBackground = trans_brush
    wc.lpszClassName = class_name
    
    if not user32.RegisterClassExW(ctypes.byref(wc)):
        return
    
    g_hwnd = user32.CreateWindowExW(
        WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_LAYERED,
        class_name, "WebRPA坐标", WS_POPUP,
        100, 100, WIN_WIDTH, WIN_HEIGHT,
        None, None, hInstance, None
    )
    
    if not g_hwnd:
        return
    
    # 设置透明色键和透明度
    LWA_COLORKEY = 0x00000001
    user32.SetLayeredWindowAttributes(g_hwnd, COLOR_TRANSPARENT, 245, LWA_COLORKEY | LWA_ALPHA)
    
    # 设置圆角区域
    rgn = gdi32.CreateRoundRectRgn(0, 0, WIN_WIDTH + 1, WIN_HEIGHT + 1, CORNER_RADIUS * 2, CORNER_RADIUS * 2)
    user32.SetWindowRgn(g_hwnd, rgn, True)
    
    user32.ShowWindow(g_hwnd, SW_SHOW)
    user32.SetTimer(g_hwnd, 1, 30, None)
    
    msg = MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))
    
    user32.UnregisterClassW(class_name, hInstance)
    gdi32.DeleteObject(trans_brush)


if __name__ == "__main__":
    main()
