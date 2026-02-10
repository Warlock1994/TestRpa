"""ADB 管理器 - 封装 Android Debug Bridge 命令"""
import subprocess
import json
import re
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Tuple


class ADBManager:
    """ADB 管理器类"""
    
    def __init__(self, adb_path: Optional[str] = None):
        """初始化 ADB 管理器
        
        Args:
            adb_path: ADB 可执行文件路径，如果为 None 则使用项目内置的 ADB
        """
        if adb_path:
            self.adb_path = adb_path
        else:
            # 使用项目内置的 ADB
            project_root = Path(__file__).parent.parent.parent
            self.adb_path = str(project_root / "scrcpy" / "adb.exe")
        
        if not os.path.exists(self.adb_path):
            raise FileNotFoundError(f"ADB 可执行文件不存在: {self.adb_path}")
        
        print(f"[ADBManager] 使用 ADB 路径: {self.adb_path}")
    
    def auto_connect_device(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """自动连接设备（如果有设备则返回，没有则尝试启动 ADB 服务器）
        
        Returns:
            (成功与否, 设备ID, 错误信息)
        """
        try:
            # 1. 先尝试获取已连接的设备
            devices = self.get_devices()
            
            if devices:
                # 有设备已连接
                device_id = devices[0]['id']
                print(f"[ADBManager] ✅ 找到已连接的设备: {device_id}")
                return True, device_id, None
            
            # 2. 没有设备，尝试启动 ADB 服务器
            print("[ADBManager] 未找到设备，正在启动 ADB 服务器...")
            success, error = self.start_server()
            if not success:
                error_msg = self._format_connection_error("启动 ADB 服务器失败", error)
                return False, None, error_msg
            
            # 3. 等待一下，再次检查设备
            time.sleep(2)
            devices = self.get_devices()
            
            if devices:
                device_id = devices[0]['id']
                print(f"[ADBManager] ✅ 找到已连接的设备: {device_id}")
                return True, device_id, None
            
            # 4. 还是没有设备，返回详细的错误信息
            error_msg = self._format_connection_error("未检测到设备", None)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = self._format_connection_error("自动连接设备异常", str(e))
            return False, None, error_msg
    
    def _format_connection_error(self, error_type: str, detail: Optional[str]) -> str:
        """格式化连接错误信息
        
        Args:
            error_type: 错误类型
            detail: 错误详情
            
        Returns:
            格式化的错误信息
        """
        error_msg = f"\n{'='*60}\n"
        error_msg += f"❌ 手机设备连接失败: {error_type}\n"
        error_msg += f"{'='*60}\n\n"
        
        if detail:
            error_msg += f"📋 错误详情:\n{detail}\n\n"
        
        error_msg += "💡 可能的原因和解决方案:\n\n"
        error_msg += "1️⃣ 手机未通过 USB 连接到电脑\n"
        error_msg += "   ✅ 解决方案: 使用 USB 数据线将手机连接到电脑\n\n"
        
        error_msg += "2️⃣ 手机未开启 USB 调试模式\n"
        error_msg += "   ✅ 解决方案:\n"
        error_msg += "      a. 进入手机「设置」→「关于手机」\n"
        error_msg += "      b. 连续点击「版本号」7次，开启开发者模式\n"
        error_msg += "      c. 返回「设置」→「开发者选项」\n"
        error_msg += "      d. 开启「USB 调试」选项\n\n"
        
        error_msg += "3️⃣ 手机未授权 USB 调试\n"
        error_msg += "   ✅ 解决方案:\n"
        error_msg += "      a. 重新插拔 USB 数据线\n"
        error_msg += "      b. 手机屏幕会弹出「允许 USB 调试」对话框\n"
        error_msg += "      c. 勾选「始终允许使用这台计算机进行调试」\n"
        error_msg += "      d. 点击「允许」按钮\n\n"
        
        error_msg += "4️⃣ USB 驱动未安装或异常\n"
        error_msg += "   ✅ 解决方案:\n"
        error_msg += "      a. 打开「设备管理器」检查是否有黄色感叹号\n"
        error_msg += "      b. 如有异常，右键选择「更新驱动程序」\n"
        error_msg += "      c. 或访问手机厂商官网下载对应的 USB 驱动\n\n"
        
        error_msg += "5️⃣ ADB 服务异常\n"
        error_msg += "   ✅ 解决方案:\n"
        error_msg += "      a. 关闭其他可能占用 ADB 的程序（如手机助手、模拟器等）\n"
        error_msg += "      b. 重启 WebRPA 服务\n\n"
        
        error_msg += "6️⃣ 使用的是充电线而非数据线\n"
        error_msg += "   ✅ 解决方案: 更换为支持数据传输的 USB 数据线\n\n"
        
        error_msg += f"{'='*60}\n"
        error_msg += "📖 详细文档: 请查看项目 README.md 中的「手机自动化」章节\n"
        error_msg += f"{'='*60}\n"
        
        return error_msg
    
    def _run_command(self, args: List[str], timeout: int = 30, check: bool = True) -> Tuple[bool, str, str]:
        """执行 ADB 命令
        
        Args:
            args: 命令参数列表
            timeout: 超时时间（秒）
            check: 是否检查返回码
            
        Returns:
            (成功与否, 标准输出, 标准错误)
        """
        try:
            cmd = [self.adb_path] + args
            print(f"[ADBManager] 执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            
            success = result.returncode == 0 if check else True
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"命令执行超时（{timeout}秒）"
        except Exception as e:
            return False, "", str(e)
    
    def start_server(self) -> Tuple[bool, str]:
        """启动 ADB 服务器
        
        Returns:
            (成功与否, 错误信息)
        """
        success, stdout, stderr = self._run_command(['start-server'])
        if not success:
            return False, f"启动 ADB 服务器失败: {stderr}"
        return True, ""
    
    def kill_server(self) -> Tuple[bool, str]:
        """停止 ADB 服务器
        
        Returns:
            (成功与否, 错误信息)
        """
        success, stdout, stderr = self._run_command(['kill-server'])
        if not success:
            return False, f"停止 ADB 服务器失败: {stderr}"
        return True, ""
    
    def get_devices(self) -> List[Dict[str, str]]:
        """获取已连接的设备列表
        
        Returns:
            设备列表，每个设备包含 id, status, model, product 等信息
        """
        success, stdout, stderr = self._run_command(['devices', '-l'])
        if not success:
            print(f"[ADBManager] 获取设备列表失败: {stderr}")
            return []
        
        devices = []
        lines = stdout.strip().split('\n')
        
        # 跳过第一行 "List of devices attached"
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            # 解析设备信息
            # 格式: device_id    device    model:xxx product:xxx device:xxx transport_id:xxx
            parts = line.split()
            if len(parts) < 2:
                continue
            
            device_id = parts[0]
            status = parts[1]
            
            device_info = {
                'id': device_id,
                'status': status,
                'model': '',
                'product': '',
                'device': '',
                'transport_id': ''
            }
            
            # 解析额外信息
            for part in parts[2:]:
                if ':' in part:
                    key, value = part.split(':', 1)
                    if key in device_info:
                        device_info[key] = value
            
            devices.append(device_info)
        
        return devices
    
    def get_device_info(self, device_id: Optional[str] = None) -> Dict[str, str]:
        """获取设备详细信息
        
        Args:
            device_id: 设备 ID，如果为 None 则使用第一个设备
            
        Returns:
            设备信息字典
        """
        device_args = ['-s', device_id] if device_id else []
        
        info = {
            'id': device_id or '',
            'model': '',
            'brand': '',
            'android_version': '',
            'sdk_version': '',
            'resolution': '',
            'density': '',
            'battery_level': '',
            'battery_status': '',
            'wifi_status': '',
            'ip_address': ''
        }
        
        # 获取设备型号
        success, stdout, _ = self._run_command(device_args + ['shell', 'getprop', 'ro.product.model'])
        if success:
            info['model'] = stdout.strip()
        
        # 获取品牌
        success, stdout, _ = self._run_command(device_args + ['shell', 'getprop', 'ro.product.brand'])
        if success:
            info['brand'] = stdout.strip()
        
        # 获取 Android 版本
        success, stdout, _ = self._run_command(device_args + ['shell', 'getprop', 'ro.build.version.release'])
        if success:
            info['android_version'] = stdout.strip()
        
        # 获取 SDK 版本
        success, stdout, _ = self._run_command(device_args + ['shell', 'getprop', 'ro.build.version.sdk'])
        if success:
            info['sdk_version'] = stdout.strip()
        
        # 获取屏幕分辨率
        success, stdout, _ = self._run_command(device_args + ['shell', 'wm', 'size'])
        if success:
            match = re.search(r'Physical size: (\d+x\d+)', stdout)
            if match:
                info['resolution'] = match.group(1)
        
        # 获取屏幕方向（0=竖屏, 1=横屏左, 2=倒置竖屏, 3=横屏右）
        success, stdout, _ = self._run_command(device_args + ['shell', 'dumpsys', 'input'])
        if success:
            # 查找 SurfaceOrientation
            match = re.search(r'SurfaceOrientation:\s*(\d+)', stdout)
            if match:
                orientation = int(match.group(1))
                info['orientation'] = str(orientation)
                # 0 或 2 = 竖屏, 1 或 3 = 横屏
                info['is_landscape'] = 'true' if orientation in [1, 3] else 'false'
            else:
                # 如果找不到，尝试另一种方法
                info['orientation'] = '0'
                info['is_landscape'] = 'false'
        
        # 获取当前实际显示分辨率（考虑旋转）
        # 如果是横屏，实际显示的宽高会交换
        if info.get('resolution') and info.get('is_landscape') == 'true':
            resolution_parts = info['resolution'].split('x')
            if len(resolution_parts) == 2:
                width, height = resolution_parts
                # 横屏时，宽度应该大于高度
                # 如果物理分辨率是竖屏格式（高>宽），则交换
                if int(width) < int(height):
                    # 交换宽高
                    info['current_resolution'] = f"{height}x{width}"
                    print(f"[ADBManager] 横屏设备，交换分辨率: {info['resolution']} -> {info['current_resolution']}")
                else:
                    info['current_resolution'] = info['resolution']
            else:
                info['current_resolution'] = info['resolution']
        else:
            info['current_resolution'] = info.get('resolution', '')
        
        # 获取屏幕密度
        success, stdout, _ = self._run_command(device_args + ['shell', 'wm', 'density'])
        if success:
            match = re.search(r'Physical density: (\d+)', stdout)
            if match:
                info['density'] = match.group(1)
        
        # 获取电池信息
        success, stdout, _ = self._run_command(device_args + ['shell', 'dumpsys', 'battery'])
        if success:
            # 解析电量
            match = re.search(r'level: (\d+)', stdout)
            if match:
                info['battery_level'] = match.group(1)
            
            # 解析充电状态
            match = re.search(r'status: (\d+)', stdout)
            if match:
                status_code = int(match.group(1))
                status_map = {
                    1: '未知',
                    2: '充电中',
                    3: '放电中',
                    4: '未充电',
                    5: '已充满'
                }
                info['battery_status'] = status_map.get(status_code, '未知')
        
        # 获取 WiFi 状态
        success, stdout, _ = self._run_command(device_args + ['shell', 'dumpsys', 'wifi'])
        if success:
            if 'Wi-Fi is enabled' in stdout:
                info['wifi_status'] = '已开启'
            else:
                info['wifi_status'] = '已关闭'
        
        # 获取 IP 地址
        success, stdout, _ = self._run_command(device_args + ['shell', 'ip', 'addr', 'show', 'wlan0'])
        if success:
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', stdout)
            if match:
                info['ip_address'] = match.group(1)
        
        return info
    
    def tap(self, x: int, y: int, device_id: Optional[str] = None, show_marker: bool = False) -> Tuple[bool, str]:
        """点击屏幕坐标
        
        Args:
            x: X 坐标
            y: Y 坐标
            device_id: 设备 ID
            show_marker: 是否显示标记（通过短暂显示通知）
            
        Returns:
            (成功与否, 错误信息)
        """
        device_args = ['-s', device_id] if device_id else []
        
        # 如果需要显示标记，先发送一个通知
        if show_marker:
            # 使用 am broadcast 发送一个简单的通知来标记位置
            # 这会在屏幕上短暂显示一个提示
            marker_text = f"点击: ({x}, {y})"
            self._run_command(
                device_args + ['shell', 'am', 'broadcast', '-a', 'android.intent.action.SHOW_TEXT', 
                              '--es', 'text', marker_text]
            )
        
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'input', 'tap', str(x), str(y)]
        )
        if not success:
            return False, f"点击失败: {stderr}"
        return True, ""
    
    def enable_show_touches(self, enable: bool = True, device_id: Optional[str] = None) -> Tuple[bool, str]:
        """启用/禁用显示触摸操作（开发者选项）
        
        Args:
            enable: True=启用, False=禁用
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        device_args = ['-s', device_id] if device_id else []
        value = '1' if enable else '0'
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'settings', 'put', 'system', 'show_touches', value]
        )
        if not success:
            return False, f"设置失败: {stderr}"
        return True, ""
    
    def enable_pointer_location(self, enable: bool = True, device_id: Optional[str] = None) -> Tuple[bool, str]:
        """启用/禁用指针位置（开发者选项）
        
        Args:
            enable: True=启用, False=禁用
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        device_args = ['-s', device_id] if device_id else []
        value = '1' if enable else '0'
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'settings', 'put', 'system', 'pointer_location', value]
        )
        if not success:
            return False, f"设置失败: {stderr}"
        return True, ""
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300, 
              device_id: Optional[str] = None) -> Tuple[bool, str]:
        """滑动屏幕
        
        Args:
            x1: 起点 X 坐标
            y1: 起点 Y 坐标
            x2: 终点 X 坐标
            y2: 终点 Y 坐标
            duration: 滑动时长（毫秒）
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        device_args = ['-s', device_id] if device_id else []
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'input', 'swipe', str(x1), str(y1), str(x2), str(y2), str(duration)]
        )
        if not success:
            return False, f"滑动失败: {stderr}"
        return True, ""
    
    def long_press(self, x: int, y: int, duration: int = 1000, 
                   device_id: Optional[str] = None) -> Tuple[bool, str]:
        """长按屏幕坐标
        
        Args:
            x: X 坐标
            y: Y 坐标
            duration: 长按时长（毫秒）
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        # 使用 swipe 命令，从 (x,y) 滑动到 (x+1,y+1)，这样可以更好地模拟长按
        # 因为完全相同的坐标可能被识别为点击
        return self.swipe(x, y, x + 1, y + 1, duration, device_id)
    
    def input_text(self, text: str, device_id: Optional[str] = None) -> Tuple[bool, str]:
        """输入文本
        
        Args:
            text: 要输入的文本
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        device_args = ['-s', device_id] if device_id else []
        
        # 检查文本是否包含中文
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
        
        if has_chinese:
            # 对于中文，使用 IME 输入法
            # 先尝试使用 am broadcast 方法（需要 ADBKeyboard）
            try:
                escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$')
                
                # 尝试使用 ADBKeyboard
                success, stdout, stderr = self._run_command(
                    device_args + ['shell', 'am', 'broadcast', '-a', 'ADB_INPUT_TEXT', '--es', 'msg', escaped_text],
                    check=False
                )
                
                # 检查是否成功（ADBKeyboard 会返回特定的输出）
                if 'Broadcast completed' in stdout or 'result=0' in stdout:
                    return True, ""
                
                # 如果 ADBKeyboard 不可用，返回错误并提示
                return False, (
                    f"❌ 无法输入中文文本\n\n"
                    f"💡 解决方案：\n"
                    f"1. 在手机上安装 ADBKeyboard 应用\n"
                    f"2. 下载地址: https://github.com/senzhk/ADBKeyBoard/releases\n"
                    f"3. 安装后在手机设置中启用 ADBKeyboard 输入法\n"
                    f"4. 将 ADBKeyboard 设置为默认输入法\n\n"
                    f"或者：\n"
                    f"- 使用「📱 点击」模块先点击输入框\n"
                    f"- 然后手动在手机上输入文本"
                )
                
            except Exception as e:
                return False, f"输入中文失败: {str(e)}"
        else:
            # 纯英文、数字和符号，使用传统方法
            # 转义特殊字符
            text_escaped = text.replace(' ', '%s')
            text_escaped = text_escaped.replace('&', '\\&')
            text_escaped = text_escaped.replace('(', '\\(')
            text_escaped = text_escaped.replace(')', '\\)')
            text_escaped = text_escaped.replace('<', '\\<')
            text_escaped = text_escaped.replace('>', '\\>')
            text_escaped = text_escaped.replace('|', '\\|')
            text_escaped = text_escaped.replace(';', '\\;')
            text_escaped = text_escaped.replace('`', '\\`')
            text_escaped = text_escaped.replace('$', '\\$')
            text_escaped = text_escaped.replace('\\', '\\\\')
            
            success, stdout, stderr = self._run_command(
                device_args + ['shell', 'input', 'text', text_escaped]
            )
            if not success:
                return False, f"输入文本失败: {stderr}"
            return True, ""
    
    def press_key(self, keycode: str, device_id: Optional[str] = None) -> Tuple[bool, str]:
        """按下按键
        
        Args:
            keycode: 按键代码（如 KEYCODE_HOME, KEYCODE_BACK 等）
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        device_args = ['-s', device_id] if device_id else []
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'input', 'keyevent', keycode]
        )
        if not success:
            return False, f"按键失败: {stderr}"
        return True, ""
    
    def screenshot(self, save_path: str, device_id: Optional[str] = None) -> Tuple[bool, str]:
        """截取屏幕
        
        Args:
            save_path: 保存路径
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        device_args = ['-s', device_id] if device_id else []
        
        # 先截图到设备
        temp_path = '/sdcard/screenshot_temp.png'
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'screencap', '-p', temp_path]
        )
        if not success:
            return False, f"截图失败: {stderr}"
        
        # 拉取到本地
        success, stdout, stderr = self._run_command(
            device_args + ['pull', temp_path, save_path]
        )
        if not success:
            return False, f"拉取截图失败: {stderr}"
        
        # 删除设备上的临时文件
        self._run_command(device_args + ['shell', 'rm', temp_path], check=False)
        
        return True, ""
    
    def install_apk(self, apk_path: str, device_id: Optional[str] = None) -> Tuple[bool, str]:
        """安装 APK
        
        Args:
            apk_path: APK 文件路径
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        if not os.path.exists(apk_path):
            return False, f"APK 文件不存在: {apk_path}"
        
        device_args = ['-s', device_id] if device_id else []
        success, stdout, stderr = self._run_command(
            device_args + ['install', '-r', apk_path],
            timeout=120  # 安装可能需要较长时间
        )
        if not success:
            return False, f"安装失败: {stderr}"
        
        if 'Success' not in stdout:
            return False, f"安装失败: {stdout}"
        
        return True, ""
    
    def uninstall_app(self, package_name: str, device_id: Optional[str] = None) -> Tuple[bool, str]:
        """卸载应用
        
        Args:
            package_name: 应用包名
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        device_args = ['-s', device_id] if device_id else []
        success, stdout, stderr = self._run_command(
            device_args + ['uninstall', package_name]
        )
        if not success:
            return False, f"卸载失败: {stderr}"
        
        if 'Success' not in stdout:
            return False, f"卸载失败: {stdout}"
        
        return True, ""
    
    def start_app(self, package_name: str, activity: Optional[str] = None, 
                  device_id: Optional[str] = None) -> Tuple[bool, str]:
        """启动应用
        
        Args:
            package_name: 应用包名
            activity: Activity 名称（可选）
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        device_args = ['-s', device_id] if device_id else []
        
        if activity:
            component = f"{package_name}/{activity}"
        else:
            # 尝试获取主 Activity
            success, stdout, stderr = self._run_command(
                device_args + ['shell', 'cmd', 'package', 'resolve-activity', '--brief', package_name]
            )
            if success and stdout.strip():
                component = stdout.strip().split('\n')[-1]
            else:
                # 使用 monkey 命令启动
                success, stdout, stderr = self._run_command(
                    device_args + ['shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1']
                )
                if not success:
                    return False, f"启动应用失败: {stderr}"
                return True, ""
        
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'am', 'start', '-n', component]
        )
        if not success:
            return False, f"启动应用失败: {stderr}"
        
        return True, ""
    
    def stop_app(self, package_name: str, device_id: Optional[str] = None) -> Tuple[bool, str]:
        """停止应用
        
        Args:
            package_name: 应用包名
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        device_args = ['-s', device_id] if device_id else []
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'am', 'force-stop', package_name]
        )
        if not success:
            return False, f"停止应用失败: {stderr}"
        return True, ""
    
    def clear_app_data(self, package_name: str, device_id: Optional[str] = None) -> Tuple[bool, str]:
        """清除应用数据
        
        Args:
            package_name: 应用包名
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        device_args = ['-s', device_id] if device_id else []
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'pm', 'clear', package_name]
        )
        if not success:
            return False, f"清除数据失败: {stderr}"
        
        if 'Success' not in stdout:
            return False, f"清除数据失败: {stdout}"
        
        return True, ""
    
    def get_installed_packages(self, device_id: Optional[str] = None) -> List[str]:
        """获取已安装的应用列表
        
        Args:
            device_id: 设备 ID
            
        Returns:
            应用包名列表
        """
        device_args = ['-s', device_id] if device_id else []
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'pm', 'list', 'packages']
        )
        if not success:
            print(f"[ADBManager] 获取应用列表失败: {stderr}")
            return []
        
        packages = []
        for line in stdout.strip().split('\n'):
            if line.startswith('package:'):
                packages.append(line.replace('package:', '').strip())
        
        return packages
    
    def push_file(self, local_path: str, remote_path: str, 
                  device_id: Optional[str] = None) -> Tuple[bool, str]:
        """推送文件到设备
        
        Args:
            local_path: 本地文件路径
            remote_path: 设备文件路径
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        if not os.path.exists(local_path):
            return False, f"本地文件不存在: {local_path}"
        
        device_args = ['-s', device_id] if device_id else []
        success, stdout, stderr = self._run_command(
            device_args + ['push', local_path, remote_path],
            timeout=120
        )
        if not success:
            return False, f"推送文件失败: {stderr}"
        
        return True, ""
    
    def pull_file(self, remote_path: str, local_path: str, 
                  device_id: Optional[str] = None) -> Tuple[bool, str]:
        """从设备拉取文件
        
        Args:
            remote_path: 设备文件路径
            local_path: 本地文件路径
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        device_args = ['-s', device_id] if device_id else []
        success, stdout, stderr = self._run_command(
            device_args + ['pull', remote_path, local_path],
            timeout=120
        )
        if not success:
            return False, f"拉取文件失败: {stderr}"
        
        return True, ""
    
    def list_files(self, remote_path: str, device_id: Optional[str] = None) -> List[Dict[str, str]]:
        """列出设备目录内容
        
        Args:
            remote_path: 设备目录路径
            device_id: 设备 ID
            
        Returns:
            文件列表
        """
        device_args = ['-s', device_id] if device_id else []
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'ls', '-la', remote_path]
        )
        if not success:
            print(f"[ADBManager] 列出目录失败: {stderr}")
            return []
        
        files = []
        for line in stdout.strip().split('\n'):
            # 跳过总计行
            if line.startswith('total'):
                continue
            
            parts = line.split()
            if len(parts) >= 8:
                files.append({
                    'permissions': parts[0],
                    'size': parts[4],
                    'date': f"{parts[5]} {parts[6]}",
                    'name': ' '.join(parts[7:])
                })
        
        return files
    
    def connect_wifi(self, ip_address: str, port: int = 5555) -> Tuple[bool, str]:
        """通过 WiFi 连接设备
        
        Args:
            ip_address: 设备 IP 地址
            port: 端口号（默认 5555）
            
        Returns:
            (成功与否, 错误信息)
        """
        # 先通过 USB 启用 TCP/IP 模式
        success, stdout, stderr = self._run_command(['tcpip', str(port)])
        if not success:
            return False, f"启用 TCP/IP 模式失败: {stderr}"
        
        # 等待设备重启 ADB
        time.sleep(2)
        
        # 连接设备
        success, stdout, stderr = self._run_command(['connect', f"{ip_address}:{port}"])
        if not success:
            return False, f"连接失败: {stderr}"
        
        if 'connected' not in stdout.lower():
            return False, f"连接失败: {stdout}"
        
        return True, ""
    
    def disconnect_wifi(self, ip_address: str, port: int = 5555) -> Tuple[bool, str]:
        """断开 WiFi 连接
        
        Args:
            ip_address: 设备 IP 地址
            port: 端口号（默认 5555）
            
        Returns:
            (成功与否, 错误信息)
        """
        success, stdout, stderr = self._run_command(['disconnect', f"{ip_address}:{port}"])
        if not success:
            return False, f"断开连接失败: {stderr}"
        
        return True, ""
    
    def set_volume(self, volume: int, stream_type: str = 'music', device_id: Optional[str] = None) -> Tuple[bool, str]:
        """设置音量
        
        Args:
            volume: 音量值（0-15）
            stream_type: 音频流类型（music, ring, alarm, notification, system）
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        import logging
        import time
        logger = logging.getLogger(__name__)
        
        # 限制音量范围
        volume = max(0, min(15, volume))
        
        device_args = ['-s', device_id] if device_id else []
        
        logger.info(f"[SetVolume] 开始设置音量: volume={volume}, stream_type={stream_type}")
        
        # 使用按键模拟设置音量（最通用的方法）
        # 先获取当前音量
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'dumpsys', 'audio']
        )
        
        if not success:
            logger.error(f"[SetVolume] ❌ 无法获取当前音量: {stderr}")
            return False, f"无法获取当前音量: {stderr}"
        
        # 解析当前音量（从 dumpsys audio 输出中提取）
        current_volume = -1
        stream_name_map = {
            'music': 'STREAM_MUSIC',
            'ring': 'STREAM_RING',
            'alarm': 'STREAM_ALARM',
            'notification': 'STREAM_NOTIFICATION',
            'system': 'STREAM_SYSTEM'
        }
        stream_name = stream_name_map.get(stream_type, 'STREAM_MUSIC')
        
        logger.info(f"[SetVolume] 解析 dumpsys audio 输出，查找 {stream_name}")
        
        # 查找音量信息
        for line in stdout.split('\n'):
            if stream_name in line:
                # 查找 mIndexCurrent 或类似的音量指示器
                if 'mIndexCurrent' in line or 'Current' in line:
                    try:
                        # 尝试多种解析方式
                        # 格式1: "mIndexCurrent: 10"
                        if ':' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                value_str = parts[1].strip().split()[0]
                                current_volume = int(value_str)
                                logger.info(f"[SetVolume] 找到当前音量: {current_volume} (从格式1)")
                                break
                    except Exception as e:
                        logger.warning(f"[SetVolume] 解析音量失败: {e}, line={line}")
        
        # 如果无法解析当前音量，先将音量降到最低，然后再升到目标值
        if current_volume == -1:
            logger.warning(f"[SetVolume] 无法解析当前音量，将先降到最低再升到目标值")
            # 按15次音量减键，确保降到最低
            for i in range(15):
                self._run_command(device_args + ['shell', 'input', 'keyevent', 'KEYCODE_VOLUME_DOWN'])
                time.sleep(0.05)
            current_volume = 0
            logger.info(f"[SetVolume] 已将音量降到最低")
        
        logger.info(f"[SetVolume] 当前音量: {current_volume}, 目标音量: {volume}")
        
        # 计算需要按多少次音量键
        volume_diff = volume - current_volume
        
        if volume_diff == 0:
            logger.info(f"[SetVolume] ✅ 音量已经是目标值，无需调整")
            return True, ""
        
        # 使用音量键调整
        keycode = 'KEYCODE_VOLUME_UP' if volume_diff > 0 else 'KEYCODE_VOLUME_DOWN'
        press_count = abs(volume_diff)
        
        logger.info(f"[SetVolume] 需要按 {press_count} 次 {keycode}")
        
        for i in range(press_count):
            success, stdout, stderr = self._run_command(
                device_args + ['shell', 'input', 'keyevent', keycode]
            )
            if not success:
                logger.error(f"[SetVolume] ❌ 第 {i+1} 次按键失败: {stderr}")
                return False, f"模拟按键失败: {stderr}"
            logger.info(f"[SetVolume] 第 {i+1}/{press_count} 次按键成功")
            # 短暂延迟，确保按键生效
            time.sleep(0.15)
        
        logger.info(f"[SetVolume] ✅ 使用按键模拟设置音量完成")
        return True, ""
    
    def _get_stream_id(self, stream_type: str) -> int:
        """获取音频流 ID"""
        stream_map = {
            'music': 3,      # STREAM_MUSIC
            'ring': 2,       # STREAM_RING
            'alarm': 4,      # STREAM_ALARM
            'notification': 5,  # STREAM_NOTIFICATION
            'system': 1      # STREAM_SYSTEM
        }
        return stream_map.get(stream_type, 3)
    
    def set_brightness(self, brightness: int, device_id: Optional[str] = None) -> Tuple[bool, str]:
        """设置屏幕亮度
        
        Args:
            brightness: 亮度值（0-255）
            device_id: 设备 ID
            
        Returns:
            (成功与否, 错误信息)
        """
        # 限制亮度范围
        brightness = max(0, min(255, brightness))
        
        device_args = ['-s', device_id] if device_id else []
        
        # 设置亮度需要两步：
        # 1. 关闭自动亮度
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'settings', 'put', 'system', 'screen_brightness_mode', '0']
        )
        
        if not success:
            return False, f"关闭自动亮度失败: {stderr}"
        
        # 2. 设置亮度值
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'settings', 'put', 'system', 'screen_brightness', str(brightness)]
        )
        
        if not success:
            return False, f"设置亮度失败: {stderr}"
        
        return True, ""

    
    def get_app_list_with_names(self, device_id: Optional[str] = None) -> Dict[str, str]:
        """获取应用列表及其名称（应用名 -> 包名的映射）
        
        Args:
            device_id: 设备 ID
            
        Returns:
            应用名称到包名的映射字典
        """
        device_args = ['-s', device_id] if device_id else []
        
        print(f"[ADBManager] 开始获取应用列表...")
        
        # 获取所有第三方应用包名（排除系统应用，速度更快）
        success, stdout, stderr = self._run_command(
            device_args + ['shell', 'pm', 'list', 'packages', '-3'],
            timeout=30
        )
        
        if not success:
            print(f"[ADBManager] 获取应用列表失败: {stderr}")
            return {}
        
        packages = []
        for line in stdout.strip().split('\n'):
            if line.startswith('package:'):
                package = line.replace('package:', '').strip()
                if package:
                    packages.append(package)
        
        print(f"[ADBManager] 找到 {len(packages)} 个第三方应用")
        
        # 使用包名映射作为应用名（简化版本，速度快）
        # 常见应用的中文名映射
        common_apps = {
            'com.tencent.mm': '微信',
            'com.tencent.mobileqq': 'QQ',
            'com.taobao.taobao': '淘宝',
            'com.jingdong.app.mall': '京东',
            'com.xunmeng.pinduoduo': '拼多多',
            'com.eg.android.AlipayGphone': '支付宝',
            'tv.danmaku.bili': '哔哩哔哩',
            'com.ss.android.ugc.aweme': '抖音',
            'com.smile.gifmaker': '快手',
            'com.netease.cloudmusic': '网易云音乐',
            'com.tencent.karaoke': '全民K歌',
            'com.baidu.BaiduMap': '百度地图',
            'com.autonavi.minimap': '高德地图',
            'com.tencent.mtt': 'QQ浏览器',
            'com.UCMobile': 'UC浏览器',
            'com.baidu.searchbox': '百度',
            'com.sina.weibo': '微博',
            'com.zhihu.android': '知乎',
            'com.tencent.qqlive': '腾讯视频',
            'com.youku.phone': '优酷',
            'com.iqiyi.i18n': '爱奇艺',
            'com.tencent.qqmusic': 'QQ音乐',
            'com.kugou.android': '酷狗音乐',
            'com.kuwo.kwmusic': '酷我音乐',
            'com.tencent.wework': '企业微信',
            'com.alibaba.android.rimet': '钉钉',
            'com.ss.android.lark': '飞书',
            'com.tencent.tim': 'TIM',
            'com.chaoxing.mobile': '学习通',
            'com.yiban.app': '易班',
        }
        
        app_map = {}
        for package in packages:
            # 优先使用常见应用映射
            if package in common_apps:
                app_name = common_apps[package]
            else:
                # 使用包名的最后一部分作为应用名
                app_name = package.split('.')[-1]
            
            app_map[app_name] = package
        
        print(f"[ADBManager] 完成！共获取 {len(app_map)} 个应用")
        return app_map
    
    def find_package_by_name(self, app_name: str, device_id: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str], List[tuple]]:
        """通过应用名称查找包名
        
        Args:
            app_name: 应用名称
            device_id: 设备 ID
            
        Returns:
            (成功与否, 包名, 错误信息, 所有匹配项列表)
        """
        print(f"[ADBManager] 查找应用: {app_name}")
        
        # 获取应用列表
        app_map = self.get_app_list_with_names(device_id)
        
        if not app_map:
            return False, None, "无法获取应用列表", []
        
        # 精确匹配
        if app_name in app_map:
            package = app_map[app_name]
            print(f"[ADBManager] 精确匹配: {app_name} -> {package}")
            return True, package, None, [(app_name, package)]
        
        # 模糊匹配
        matches = []
        app_name_lower = app_name.lower()
        for name, package in app_map.items():
            if app_name_lower in name.lower() or name.lower() in app_name_lower:
                matches.append((name, package))
        
        if len(matches) == 0:
            return False, None, f"未找到名称包含 '{app_name}' 的应用", []
        elif len(matches) == 1:
            name, package = matches[0]
            print(f"[ADBManager] 模糊匹配: {app_name} -> {name} ({package})")
            return True, package, None, matches
        else:
            # 多个匹配
            match_list = '\n'.join([f"  - {name} ({pkg})" for name, pkg in matches])
            error = f"找到 {len(matches)} 个匹配的应用:\n{match_list}\n\n请使用包名精确指定要启动的应用"
            return False, None, error, matches


# 全局 ADB 管理器实例
_adb_manager: Optional[ADBManager] = None


def get_adb_manager() -> ADBManager:
    """获取全局 ADB 管理器实例"""
    global _adb_manager
    if _adb_manager is None:
        _adb_manager = ADBManager()
    return _adb_manager
