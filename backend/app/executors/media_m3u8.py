"""媒体处理模块 - M3U8下载（使用 N_m3u8DL-RE）"""
import asyncio
import os
import re
import time as time_module
from pathlib import Path

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor, get_backend_root, get_ffmpeg_path
from .type_utils import to_int


def get_n_m3u8dl_path() -> str:
    """获取 N_m3u8DL-RE (m3u8.exe) 的路径"""
    m3u8_path = get_backend_root() / 'm3u8.exe'
    if m3u8_path.exists():
        return str(m3u8_path)
    n_m3u8dl_path = get_backend_root() / 'N_m3u8DL-RE.exe'
    if n_m3u8dl_path.exists():
        return str(n_m3u8dl_path)
    return ''


@register_executor
class DownloadM3U8Executor(ModuleExecutor):
    """M3U8视频下载模块执行器 - 使用 N_m3u8DL-RE"""
    
    @property
    def module_type(self) -> str:
        return "download_m3u8"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        m3u8_url = context.resolve_value(config.get('m3u8Url', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        output_filename = context.resolve_value(config.get('outputFilename', ''))
        result_variable = config.get('resultVariable', '')
        
        # HTTP 请求配置
        user_agent = context.resolve_value(config.get('userAgent', ''))
        referer = context.resolve_value(config.get('referer', ''))
        custom_headers = context.resolve_value(config.get('customHeaders', ''))
        timeout = to_int(config.get('timeout', 1800), 1800, context)
        
        # N_m3u8DL-RE 配置
        thread_count = to_int(config.get('threadCount', 8), 8, context)
        use_system_proxy = config.get('useSystemProxy', True)
        custom_proxy = context.resolve_value(config.get('customProxy', ''))
        decryption_key = context.resolve_value(config.get('decryptionKey', ''))
        auto_select = config.get('autoSelect', True)
        
        if not m3u8_url:
            return ModuleResult(success=False, error="M3U8链接不能为空")
        
        # 检查 N_m3u8DL-RE 是否存在
        n_m3u8dl_path = get_n_m3u8dl_path()
        if not n_m3u8dl_path:
            return ModuleResult(success=False, error="m3u8.exe 不存在，请将 N_m3u8DL-RE 放置在 backend 目录下并命名为 m3u8.exe")
        
        if not output_path:
            output_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        os.makedirs(output_path, exist_ok=True)
        
        if not output_filename:
            output_filename = f"m3u8_video_{int(time_module.time())}"
        
        # 移除扩展名（N_m3u8DL-RE 会自动添加）
        for ext in ['.mp4', '.ts', '.mkv']:
            if output_filename.endswith(ext):
                output_filename = output_filename[:-len(ext)]
                break
        
        print(f"[DEBUG] 开始下载 M3U8: {m3u8_url}")
        print(f"[DEBUG] 输出目录: {output_path}")
        print(f"[DEBUG] 输出文件名: {output_filename}")
        
        # 构建命令参数
        args = [
            n_m3u8dl_path,
            m3u8_url,
            '--save-dir', output_path,
            '--save-name', output_filename,
            '--thread-count', str(thread_count),
            '--del-after-done',
            '--no-log',
            '--ui-language', 'zh-CN',
            '--log-level', 'INFO',
            '-M', 'format=mp4',
        ]
        
        if auto_select:
            args.append('--auto-select')
        
        # HTTP 请求头
        if user_agent:
            args.extend(['-H', f'User-Agent: {user_agent}'])
        if referer:
            args.extend(['-H', f'Referer: {referer}'])
        if custom_headers:
            for line in custom_headers.strip().replace('|', '\n').split('\n'):
                line = line.strip()
                if line and ':' in line:
                    args.extend(['-H', line])
        
        # 代理设置
        if custom_proxy:
            args.extend(['--custom-proxy', custom_proxy])
        elif not use_system_proxy:
            args.extend(['--use-system-proxy', 'False'])
        
        # 解密密钥
        if decryption_key:
            args.extend(['--key', decryption_key])
        
        # FFmpeg 路径
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path and ffmpeg_path != 'ffmpeg':
            args.extend(['--ffmpeg-binary-path', ffmpeg_path])
        
        print(f"[DEBUG] N_m3u8DL-RE 命令: {' '.join(args)}")
        
        try:
            await context.send_progress("📥 开始下载 M3U8 视频...")
            
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                creationflags=0x08000000 if os.name == 'nt' else 0
            )
            
            output_lines = []
            last_progress_time = time_module.time()
            downloaded_size = ''
            download_speed = ''
            progress_percent = ''
            
            async def read_output():
                nonlocal last_progress_time, downloaded_size, download_speed, progress_percent
                while True:
                    try:
                        line = await asyncio.wait_for(process.stdout.readline(), timeout=5)
                        if not line:
                            break
                        
                        line_text = line.decode('utf-8', errors='ignore').strip()
                        if line_text:
                            output_lines.append(line_text)
                            print(f"[M3U8] {line_text}")
                            
                            # 解析进度信息
                            # 匹配百分比进度
                            percent_match = re.search(r'(\d+\.?\d*)%', line_text)
                            if percent_match:
                                progress_percent = percent_match.group(1)
                            
                            # 匹配下载速度 (如 1.5MB/s, 500KB/s)
                            speed_match = re.search(r'(\d+\.?\d*\s*[KMG]?B/s)', line_text, re.IGNORECASE)
                            if speed_match:
                                download_speed = speed_match.group(1)
                            
                            # 匹配已下载大小 (如 50.5MB, 1.2GB)
                            size_match = re.search(r'(\d+\.?\d*\s*[KMG]B)(?!\s*/s)', line_text, re.IGNORECASE)
                            if size_match:
                                downloaded_size = size_match.group(1)
                            
                            # 每2秒发送一次进度更新
                            current_time = time_module.time()
                            if current_time - last_progress_time >= 2:
                                # 构建进度消息
                                if progress_percent:
                                    msg_parts = [f"📥 下载进度: {progress_percent}%"]
                                    if downloaded_size:
                                        msg_parts.append(f"已下载: {downloaded_size}")
                                    if download_speed:
                                        msg_parts.append(f"速度: {download_speed}")
                                    await context.send_progress(" | ".join(msg_parts))
                                    last_progress_time = current_time
                                elif downloaded_size or download_speed:
                                    msg_parts = ["📥 下载中"]
                                    if downloaded_size:
                                        msg_parts.append(f"已下载: {downloaded_size}")
                                    if download_speed:
                                        msg_parts.append(f"速度: {download_speed}")
                                    await context.send_progress(" | ".join(msg_parts))
                                    last_progress_time = current_time
                                elif '混流' in line_text or 'mux' in line_text.lower():
                                    await context.send_progress("🔄 正在合并音视频...")
                                    last_progress_time = current_time
                                elif '完成' in line_text or 'done' in line_text.lower() or 'finish' in line_text.lower():
                                    await context.send_progress("✅ 下载完成，正在处理...")
                                    last_progress_time = current_time
                    except asyncio.TimeoutError:
                        # 超时时也发送当前状态
                        current_time = time_module.time()
                        if current_time - last_progress_time >= 5:
                            if progress_percent:
                                msg = f"📥 下载进度: {progress_percent}%"
                                if download_speed:
                                    msg += f" | 速度: {download_speed}"
                                await context.send_progress(msg)
                            else:
                                await context.send_progress("📥 下载中，请稍候...")
                            last_progress_time = current_time
                        continue
                    except Exception:
                        break
            
            try:
                await asyncio.wait_for(
                    asyncio.gather(read_output(), process.wait()),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ModuleResult(success=False, error=f"下载超时（{timeout}秒），请检查网络或增加超时时间")
            
            return_code = process.returncode
            output_text = '\n'.join(output_lines)
            
            if return_code != 0:
                error_lower = output_text.lower()
                
                # 解析更友好的错误信息
                if 'ssl connection could not be established' in error_lower:
                    return ModuleResult(success=False, error="SSL连接失败：无法建立安全连接，请检查网络或尝试使用代理")
                elif '10060' in output_text or 'connection attempt failed' in error_lower or '连接尝试失败' in output_text:
                    return ModuleResult(success=False, error="网络连接超时：无法连接到服务器，请检查网络连接或尝试使用代理")
                elif '10054' in output_text or 'connection reset' in error_lower:
                    return ModuleResult(success=False, error="连接被重置：服务器关闭了连接，可能需要设置 Referer 或链接已过期")
                elif '403' in output_text or 'forbidden' in error_lower:
                    return ModuleResult(success=False, error="访问被拒绝(403)：请检查 Referer 和 User-Agent 设置")
                elif '404' in output_text or 'not found' in error_lower:
                    return ModuleResult(success=False, error="资源不存在(404)：请检查链接是否正确")
                elif 'timeout' in error_lower or '超时' in output_text:
                    return ModuleResult(success=False, error="下载超时：请检查网络或增加超时时间")
                elif 'decrypt' in error_lower or '解密' in output_text:
                    return ModuleResult(success=False, error="解密失败：请提供正确的解密密钥")
                elif 'failed to execute action after' in error_lower or '重试' in output_text:
                    return ModuleResult(success=False, error="下载失败：多次重试后仍无法连接服务器，请检查网络或使用代理")
                else:
                    # 提取有意义的错误信息，过滤掉堆栈信息
                    meaningful_errors = []
                    for line in output_lines:
                        line_lower = line.lower()
                        # 跳过堆栈信息
                        if 'at system.' in line_lower or 'at n_m3u8dl' in line_lower or '--- end of' in line_lower:
                            continue
                        # 提取 WARN 和 ERROR 信息
                        if 'warn' in line_lower or 'error' in line_lower or '失败' in line or '错误' in line:
                            # 清理时间戳
                            clean_line = re.sub(r'^\d{2}:\d{2}:\d{2}\.\d+ (WARN|ERROR|INFO)\s*:\s*', '', line).strip()
                            if clean_line and len(clean_line) > 5:
                                meaningful_errors.append(clean_line)
                    
                    if meaningful_errors:
                        # 取最后几条有意义的错误
                        error_msg = meaningful_errors[-1] if len(meaningful_errors) == 1 else '\n'.join(meaningful_errors[-3:])
                        return ModuleResult(success=False, error=f"下载失败: {error_msg}")
                    else:
                        return ModuleResult(success=False, error="下载失败：未知错误，请查看日志获取详细信息")
            
            # 查找输出文件
            output_file = None
            for ext in ['.mp4', '.mkv', '.ts']:
                candidate = os.path.join(output_path, output_filename + ext)
                if os.path.exists(candidate):
                    output_file = candidate
                    break
            
            if not output_file:
                for f in os.listdir(output_path):
                    if f.startswith(output_filename) and any(f.endswith(ext) for ext in ['.mp4', '.mkv', '.ts']):
                        output_file = os.path.join(output_path, f)
                        break
            
            if not output_file or not os.path.exists(output_file):
                return ModuleResult(success=False, error="下载失败：输出文件不存在")
            
            file_size = os.path.getsize(output_file)
            if file_size == 0:
                os.remove(output_file)
                return ModuleResult(success=False, error="下载失败：输出文件为空")
            
            size_str = self._format_size(file_size)
            
            if result_variable:
                context.set_variable(result_variable, output_file)
            
            final_filename = os.path.basename(output_file)
            await context.send_progress(f"✅ 下载完成: {final_filename} ({size_str})")
            
            return ModuleResult(
                success=True,
                message=f"M3U8视频下载成功: {final_filename} ({size_str})",
                data={'output_path': output_file, 'file_size': file_size}
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"下载失败: {str(e)}")
    
    def _format_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
