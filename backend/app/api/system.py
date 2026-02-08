"""系统相关API路由"""
import subprocess
import sys
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import json

router = APIRouter(prefix="/api/system", tags=["system"])

# 鼠标坐标拾取器进程
mouse_picker_process = None


class OpenUrlRequest(BaseModel):
    url: str


@router.post("/open-url")
async def open_url(request: OpenUrlRequest):
    """使用系统默认浏览器打开URL"""
    import webbrowser
    try:
        webbrowser.open(request.url)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


class FolderSelectRequest(BaseModel):
    title: Optional[str] = "选择文件夹"
    initialDir: Optional[str] = None


class FileSelectRequest(BaseModel):
    title: Optional[str] = "选择文件"
    initialDir: Optional[str] = None
    fileTypes: Optional[list[tuple[str, str]]] = None  # [("Excel文件", "*.xlsx"), ...]


def select_folder_windows(title: str, initial_dir: str = None) -> str:
    """使用现代 Windows 资源管理器风格的文件夹选择对话框（和文件选择对话框一样的样式）"""
    import tempfile
    import os
    
    # 创建临时 C# 脚本
    cs_code = '''
using System;
using System.Runtime.InteropServices;

[ComImport, Guid("DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7")]
class FileOpenDialogCOM { }

[ComImport, Guid("42f85136-db7e-439c-85f1-e4075d135fc8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IFileOpenDialog {
    [PreserveSig] int Show(IntPtr hwndOwner);
    void SetFileTypes();
    void SetFileTypeIndex();
    void GetFileTypeIndex();
    void Advise();
    void Unadvise();
    void SetOptions(uint fos);
    void GetOptions();
    void SetDefaultFolder();
    void SetFolder(IShellItem psi);
    void GetFolder();
    void GetCurrentSelection();
    void SetFileName();
    void GetFileName();
    void SetTitle([MarshalAs(UnmanagedType.LPWStr)] string pszTitle);
    void SetOkButtonLabel();
    void SetFileNameLabel();
    void GetResult(out IShellItem ppsi);
}

[ComImport, Guid("43826D1E-E718-42EE-BC55-A1E261C37BFE"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IShellItem {
    void BindToHandler();
    void GetParent();
    void GetDisplayName(uint sigdnName, out IntPtr ppszName);
    void GetAttributes();
    void Compare();
}

public class FolderPicker {
    [DllImport("user32.dll")]
    static extern IntPtr GetForegroundWindow();
    
    [DllImport("user32.dll")]
    static extern bool SetForegroundWindow(IntPtr hWnd);
    
    [DllImport("user32.dll")]
    static extern IntPtr GetDesktopWindow();

    public static string Show(string title) {
        IFileOpenDialog dialog = (IFileOpenDialog)new FileOpenDialogCOM();
        dialog.SetOptions(0x20 | 0x40);
        dialog.SetTitle(title);
        
        // 获取当前前台窗口句柄，让对话框显示在最前面
        IntPtr hwnd = GetForegroundWindow();
        if (hwnd == IntPtr.Zero) {
            hwnd = GetDesktopWindow();
        }
        
        if (dialog.Show(hwnd) == 0) {
            IShellItem result;
            dialog.GetResult(out result);
            IntPtr pszPath;
            result.GetDisplayName(0x80058000, out pszPath);
            string path = Marshal.PtrToStringUni(pszPath);
            Marshal.FreeCoTaskMem(pszPath);
            return path;
        }
        return null;
    }
}
'''
    
    ps_script = f'''
$code = @"
{cs_code}
"@

try {{
    Add-Type -TypeDefinition $code -ErrorAction Stop
    $result = [FolderPicker]::Show("{title}")
    if ($result) {{
        Write-Output $result
    }}
}} catch {{
    Add-Type -AssemblyName System.Windows.Forms
    $fb = New-Object System.Windows.Forms.FolderBrowserDialog
    $fb.Description = "{title}"
    $fb.ShowNewFolderButton = $true
    if ($fb.ShowDialog() -eq 'OK') {{
        Write-Output $fb.SelectedPath
    }}
}}
'''
    
    # 写入临时 ps1 文件（使用 UTF-8 BOM 编码以支持中文）
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.ps1', delete=False) as f:
        # UTF-8 BOM + 内容
        f.write(b'\xef\xbb\xbf')
        f.write(ps_script.encode('utf-8'))
        ps_file = f.name
    
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return result.stdout.strip()
    finally:
        os.unlink(ps_file)


def select_file_windows(title: str, initial_dir: str = None, file_filter: str = None) -> str:
    """使用 PowerShell 打开文件选择对话框"""
    import tempfile
    import os
    
    # 使用 COM 接口实现现代风格的文件选择对话框
    # 注意：类名使用 File 前缀以区分文件夹选择器
    cs_code = '''
using System;
using System.Runtime.InteropServices;

[ComImport, Guid("DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7")]
class FileOpenDialogCOM2 { }

[ComImport, Guid("42f85136-db7e-439c-85f1-e4075d135fc8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IFileOpenDialog2 {
    [PreserveSig] int Show(IntPtr hwndOwner);
    void SetFileTypes(uint cFileTypes, IntPtr rgFilterSpec);
    void SetFileTypeIndex(uint iFileType);
    void GetFileTypeIndex();
    void Advise();
    void Unadvise();
    void SetOptions(uint fos);
    void GetOptions();
    void SetDefaultFolder();
    void SetFolder(IShellItem2 psi);
    void GetFolder();
    void GetCurrentSelection();
    void SetFileName([MarshalAs(UnmanagedType.LPWStr)] string pszName);
    void GetFileName();
    void SetTitle([MarshalAs(UnmanagedType.LPWStr)] string pszTitle);
    void SetOkButtonLabel();
    void SetFileNameLabel();
    void GetResult(out IShellItem2 ppsi);
}

[ComImport, Guid("43826D1E-E718-42EE-BC55-A1E261C37BFE"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IShellItem2 {
    void BindToHandler();
    void GetParent();
    void GetDisplayName(uint sigdnName, out IntPtr ppszName);
    void GetAttributes();
    void Compare();
}

public class FilePicker {
    [DllImport("user32.dll")]
    static extern IntPtr GetForegroundWindow();
    
    [DllImport("user32.dll")]
    static extern IntPtr GetDesktopWindow();

    public static string Show(string title) {
        IFileOpenDialog2 dialog = (IFileOpenDialog2)new FileOpenDialogCOM2();
        // 不设置 FOS_PICKFOLDERS (0x20)，只设置 FOS_FORCEFILESYSTEM (0x40)
        dialog.SetOptions(0x40);
        dialog.SetTitle(title);
        
        IntPtr hwnd = GetForegroundWindow();
        if (hwnd == IntPtr.Zero) {
            hwnd = GetDesktopWindow();
        }
        
        if (dialog.Show(hwnd) == 0) {
            IShellItem2 result;
            dialog.GetResult(out result);
            IntPtr pszPath;
            result.GetDisplayName(0x80058000, out pszPath);
            string path = Marshal.PtrToStringUni(pszPath);
            Marshal.FreeCoTaskMem(pszPath);
            return path;
        }
        return null;
    }
}
'''
    
    ps_script = f'''
$code = @"
{cs_code}
"@

try {{
    Add-Type -TypeDefinition $code -ErrorAction Stop
    $result = [FilePicker]::Show("{title}")
    if ($result) {{
        Write-Output $result
    }}
}} catch {{
    # 回退到传统对话框
    Add-Type -AssemblyName System.Windows.Forms
    $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
    $openFileDialog.Title = "{title}"
    {f'$openFileDialog.InitialDirectory = "{initial_dir}"' if initial_dir else ''}
    {f'$openFileDialog.Filter = "{file_filter}"' if file_filter else ''}
    if ($openFileDialog.ShowDialog() -eq 'OK') {{
        Write-Output $openFileDialog.FileName
    }}
}}
'''
    
    # 写入临时 ps1 文件（使用 UTF-8 BOM 编码以支持中文）
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.ps1', delete=False) as f:
        f.write(b'\xef\xbb\xbf')
        f.write(ps_script.encode('utf-8'))
        ps_file = f.name
    
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return result.stdout.strip()
    finally:
        os.unlink(ps_file)


@router.post("/select-folder")
async def select_folder(request: FolderSelectRequest):
    """打开文件夹选择对话框"""
    try:
        folder_path = select_folder_windows(
            title=request.title or "选择文件夹",
            initial_dir=request.initialDir
        )
        
        if folder_path:
            return {"success": True, "path": folder_path}
        else:
            return {"success": False, "path": None, "message": "用户取消选择"}
    
    except Exception as e:
        return {"success": False, "path": None, "error": str(e)}


@router.post("/select-file")
async def select_file(request: FileSelectRequest):
    """打开文件选择对话框"""
    try:
        # 转换文件类型过滤器格式
        file_filter = None
        if request.fileTypes:
            # 转换为 Windows 格式: "Excel文件|*.xlsx|所有文件|*.*"
            filter_parts = []
            for desc, pattern in request.fileTypes:
                filter_parts.append(f"{desc}|{pattern}")
            file_filter = "|".join(filter_parts)
        
        file_path = select_file_windows(
            title=request.title or "选择文件",
            initial_dir=request.initialDir,
            file_filter=file_filter
        )
        
        if file_path:
            return {"success": True, "path": file_path}
        else:
            return {"success": False, "path": None, "message": "用户取消选择"}
    
    except Exception as e:
        return {"success": False, "path": None, "error": str(e)}


@router.post("/pick-mouse-position")
async def pick_mouse_position():
    """启动鼠标坐标拾取器，返回用户点击的屏幕坐标"""
    global mouse_picker_process
    
    try:
        # 如果已有进程在运行，先终止
        if mouse_picker_process and mouse_picker_process.poll() is None:
            mouse_picker_process.terminate()
            mouse_picker_process = None
        
        # 获取 Python 解释器路径
        python_path = Path(__file__).parent.parent.parent.parent / "Python313" / "python.exe"
        if not python_path.exists():
            python_path = sys.executable
        
        # 获取拾取器脚本路径
        picker_script = Path(__file__).parent.parent / "services" / "mouse_picker" / "picker_process.py"
        
        # 启动拾取器进程
        mouse_picker_process = subprocess.Popen(
            [str(python_path), str(picker_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        # 等待进程启动
        result = {"success": False, "x": None, "y": None, "cancelled": False}
        
        # 读取输出，等待坐标
        while True:
            line = mouse_picker_process.stdout.readline()
            if not line:
                break
            
            try:
                data = json.loads(line.decode('utf-8').strip())
                
                if data.get("status") == "started":
                    continue
                elif data.get("status") == "ready":
                    continue
                elif data.get("type") == "position":
                    pos = data.get("data", {})
                    result = {
                        "success": True,
                        "x": pos.get("x"),
                        "y": pos.get("y"),
                        "button": pos.get("button")
                    }
                    break
                elif data.get("type") == "cancelled":
                    result = {"success": False, "cancelled": True, "x": None, "y": None}
                    break
                elif data.get("status") == "closed":
                    break
                elif data.get("error"):
                    result = {"success": False, "error": data.get("error")}
                    break
            except json.JSONDecodeError:
                continue
        
        # 确保进程已结束
        if mouse_picker_process.poll() is None:
            mouse_picker_process.terminate()
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/get-current-mouse-position")
async def get_current_mouse_position():
    """获取当前鼠标位置（不需要点击）"""
    try:
        import ctypes
        
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        
        return {
            "success": True,
            "x": pt.x,
            "y": pt.y
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 音频文件缓存
import tempfile
import os
import hashlib
import httpx

audio_cache_dir = None
audio_cache = {}  # url_hash -> file_path


def get_audio_cache_dir():
    """获取音频缓存目录"""
    global audio_cache_dir
    if audio_cache_dir is None:
        audio_cache_dir = Path(tempfile.gettempdir()) / "webrpa_audio_cache"
        audio_cache_dir.mkdir(exist_ok=True)
    return audio_cache_dir


def get_url_hash(url: str) -> str:
    """获取URL的哈希值"""
    return hashlib.md5(url.encode()).hexdigest()[:16]


class AudioConvertRequest(BaseModel):
    audioUrl: str


@router.post("/convert-audio")
async def convert_audio(request: AudioConvertRequest):
    """下载并转换音频为MP3格式，返回可播放的URL"""
    from app.executors.base import get_ffmpeg_path
    
    audio_url = request.audioUrl
    if not audio_url:
        return {"success": False, "error": "音频URL不能为空"}
    
    try:
        url = audio_url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        url_hash = get_url_hash(url)
        cache_dir = get_audio_cache_dir()
        output_path = cache_dir / f"{url_hash}.mp3"
        
        # 检查缓存
        if output_path.exists():
            return {
                "success": True,
                "audioPath": f"/api/system/audio/{url_hash}.mp3"
            }
        
        # 下载音频
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://music.163.com/",
            "Accept": "*/*",
        }
        
        async with httpx.AsyncClient(timeout=120, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            audio_data = response.content
        
        # 从URL中提取文件扩展名
        from urllib.parse import urlparse, unquote
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path).lower()
        
        # 支持的音频格式
        supported_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.webm', '.opus', '.ape', '.wv']
        file_ext = '.mp3'
        for ext in supported_extensions:
            if path.endswith(ext):
                file_ext = ext
                break
        
        # 保存原始文件
        temp_input = cache_dir / f"{url_hash}_input{file_ext}"
        with open(temp_input, 'wb') as f:
            f.write(audio_data)
        
        # 如果已经是MP3，直接重命名
        if file_ext == '.mp3':
            temp_input.rename(output_path)
        else:
            # 使用ffmpeg转换为MP3
            ffmpeg = get_ffmpeg_path()
            cmd = [
                ffmpeg, '-i', str(temp_input), '-y',
                '-c:a', 'libmp3lame', '-q:a', '2',
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 清理临时输入文件
            try:
                temp_input.unlink()
            except:
                pass
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                return {"success": False, "error": f"音频转换失败: {error_msg[:200]}"}
        
        return {
            "success": True,
            "audioPath": f"/api/system/audio/{url_hash}.mp3"
        }
        
    except httpx.HTTPError as e:
        return {"success": False, "error": f"下载音频失败: {str(e)}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "音频转换超时"}
    except Exception as e:
        return {"success": False, "error": f"处理音频失败: {str(e)}"}


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """获取转换后的音频文件"""
    cache_dir = get_audio_cache_dir()
    file_path = cache_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="音频文件不存在")
    
    return FileResponse(
        path=str(file_path),
        media_type="audio/mpeg",
        filename=filename
    )


@router.get("/local-file")
async def get_local_file(path: str):
    """提供本地文件访问服务，用于视频/图片播放等"""
    import urllib.parse
    import mimetypes
    
    # URL 解码路径
    file_path = urllib.parse.unquote(path)
    
    # 安全检查：确保路径是绝对路径
    file_path = Path(file_path)
    if not file_path.is_absolute():
        raise HTTPException(status_code=400, detail="必须使用绝对路径")
    
    # 检查文件是否存在
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="路径不是文件")
    
    # 获取 MIME 类型
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type is None:
        mime_type = "application/octet-stream"
    
    # 返回文件
    return FileResponse(
        path=str(file_path),
        media_type=mime_type,
        filename=file_path.name
    )


# 视频缓存目录
video_cache_dir = None


def get_video_cache_dir():
    """获取视频缓存目录"""
    global video_cache_dir
    if video_cache_dir is None:
        video_cache_dir = Path(tempfile.gettempdir()) / "webrpa_video_cache"
        video_cache_dir.mkdir(exist_ok=True)
    return video_cache_dir


class VideoConvertRequest(BaseModel):
    videoUrl: str  # 可以是本地路径或网络URL


@router.post("/convert-video")
async def convert_video(request: VideoConvertRequest):
    """将视频转换为浏览器兼容的 H.264 格式，返回可播放的URL"""
    from app.executors.base import get_ffmpeg_path, get_ffprobe_path
    
    video_url = request.videoUrl
    if not video_url:
        return {"success": False, "error": "视频路径不能为空"}
    
    try:
        cache_dir = get_video_cache_dir()
        is_local = False
        input_path = None
        temp_download = None
        
        # 判断是本地文件还是网络URL
        if video_url.startswith(('http://', 'https://')):
            # 网络URL - 需要下载
            url_hash = get_url_hash(video_url)
            output_path = cache_dir / f"{url_hash}.mp4"
            
            # 检查缓存
            if output_path.exists():
                return {
                    "success": True,
                    "videoPath": f"/api/system/video/{url_hash}.mp4"
                }
            
            # 下载视频
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "*/*",
            }
            
            async with httpx.AsyncClient(timeout=300, follow_redirects=True, headers=headers) as client:
                response = await client.get(video_url)
                response.raise_for_status()
                video_data = response.content
            
            # 保存临时文件
            temp_download = cache_dir / f"{url_hash}_input.tmp"
            with open(temp_download, 'wb') as f:
                f.write(video_data)
            input_path = str(temp_download)
            
        else:
            # 本地文件
            is_local = True
            input_path = video_url
            
            if not Path(input_path).exists():
                return {"success": False, "error": f"文件不存在: {input_path}"}
            
            # 使用文件路径的哈希作为缓存键
            url_hash = get_url_hash(input_path)
            output_path = cache_dir / f"{url_hash}.mp4"
            
            # 检查缓存
            if output_path.exists():
                # 检查源文件是否更新
                if output_path.stat().st_mtime >= Path(input_path).stat().st_mtime:
                    return {
                        "success": True,
                        "videoPath": f"/api/system/video/{url_hash}.mp4"
                    }
        
        # 使用 ffprobe 检查视频编码
        ffprobe = get_ffprobe_path()
        probe_cmd = [
            ffprobe, '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_path
        ]
        
        probe_result = subprocess.run(
            probe_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        current_codec = probe_result.stdout.strip().lower()
        print(f"[DEBUG] 视频编码: {current_codec}")
        
        # 如果已经是 H.264，直接复制（对于网络视频）或返回原路径（对于本地视频）
        if current_codec == 'h264':
            if is_local:
                # 本地 H.264 视频，直接返回本地文件路径
                return {
                    "success": True,
                    "videoPath": f"/api/system/local-file?path={subprocess.list2cmdline([input_path])[1:-1]}",
                    "needsConvert": False
                }
            else:
                # 网络 H.264 视频，复制到缓存
                import shutil
                shutil.copy(temp_download, output_path)
                if temp_download and temp_download.exists():
                    temp_download.unlink()
                return {
                    "success": True,
                    "videoPath": f"/api/system/video/{url_hash}.mp4"
                }
        
        # 需要转码 - 使用 FFmpeg 转换为 H.264
        ffmpeg = get_ffmpeg_path()
        cmd = [
            ffmpeg, '-y',
            '-i', input_path,
            '-c:v', 'libx264',      # H.264 编码
            '-preset', 'fast',       # 快速编码
            '-crf', '23',            # 质量（越小越好，23是默认值）
            '-c:a', 'aac',           # AAC 音频
            '-b:a', '128k',          # 音频比特率
            '-movflags', '+faststart',  # 支持流式播放
            str(output_path)
        ]
        
        print(f"[DEBUG] 视频转码命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=600,  # 10分钟超时
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        # 清理临时下载文件
        if temp_download and temp_download.exists():
            try:
                temp_download.unlink()
            except:
                pass
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            print(f"[DEBUG] 视频转码失败: {error_msg[-500:]}")
            return {"success": False, "error": f"视频转码失败: {error_msg[-200:]}"}
        
        return {
            "success": True,
            "videoPath": f"/api/system/video/{url_hash}.mp4"
        }
        
    except httpx.HTTPError as e:
        return {"success": False, "error": f"下载视频失败: {str(e)}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "视频转码超时（超过10分钟）"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"处理视频失败: {str(e)}"}


@router.get("/video/{filename}")
async def get_video(filename: str):
    """获取转换后的视频文件"""
    cache_dir = get_video_cache_dir()
    file_path = cache_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=filename
    )


# 图片缓存目录
image_cache_dir = None


def get_image_cache_dir():
    """获取图片缓存目录"""
    global image_cache_dir
    if image_cache_dir is None:
        image_cache_dir = Path(tempfile.gettempdir()) / "webrpa_image_cache"
        image_cache_dir.mkdir(exist_ok=True)
    return image_cache_dir


class ImageConvertRequest(BaseModel):
    imageUrl: str  # 可以是本地路径或网络URL


@router.post("/convert-image")
async def convert_image(request: ImageConvertRequest):
    """将图片转换为浏览器兼容的 PNG/JPEG 格式"""
    from app.executors.base import get_ffmpeg_path
    
    image_url = request.imageUrl
    if not image_url:
        return {"success": False, "error": "图片路径不能为空"}
    
    try:
        cache_dir = get_image_cache_dir()
        is_local = False
        input_path = None
        temp_download = None
        
        # 判断是本地文件还是网络URL
        if image_url.startswith(('http://', 'https://')):
            # 网络URL - 需要下载
            url_hash = get_url_hash(image_url)
            output_path = cache_dir / f"{url_hash}.png"
            
            # 检查缓存
            if output_path.exists():
                return {
                    "success": True,
                    "imagePath": f"/api/system/image/{url_hash}.png"
                }
            
            # 下载图片
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "image/*,*/*",
            }
            
            async with httpx.AsyncClient(timeout=60, follow_redirects=True, headers=headers) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_data = response.content
            
            # 保存临时文件
            temp_download = cache_dir / f"{url_hash}_input.tmp"
            with open(temp_download, 'wb') as f:
                f.write(image_data)
            input_path = str(temp_download)
            
        else:
            # 本地文件
            is_local = True
            input_path = image_url
            
            if not Path(input_path).exists():
                return {"success": False, "error": f"文件不存在: {input_path}"}
            
            # 使用文件路径的哈希作为缓存键
            url_hash = get_url_hash(input_path)
            output_path = cache_dir / f"{url_hash}.png"
            
            # 检查缓存（如果源文件没有更新）
            if output_path.exists():
                if output_path.stat().st_mtime >= Path(input_path).stat().st_mtime:
                    return {
                        "success": True,
                        "imagePath": f"/api/system/image/{url_hash}.png"
                    }
        
        # 检查是否是浏览器原生支持的格式
        ext = Path(input_path).suffix.lower()
        browser_supported = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico']
        
        if ext in browser_supported and is_local:
            # 浏览器支持的格式，直接返回本地文件
            return {
                "success": True,
                "imagePath": f"/api/system/local-file?path={subprocess.list2cmdline([input_path])[1:-1]}",
                "needsConvert": False
            }
        
        # 使用 FFmpeg 转换为 PNG（支持几乎所有图片格式）
        ffmpeg = get_ffmpeg_path()
        cmd = [
            ffmpeg, '-y',
            '-i', input_path,
            '-vframes', '1',  # 只取第一帧（对于动图）
            str(output_path)
        ]
        
        print(f"[DEBUG] 图片转换命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        # 清理临时下载文件
        if temp_download and temp_download.exists():
            try:
                temp_download.unlink()
            except:
                pass
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            print(f"[DEBUG] 图片转换失败: {error_msg[-500:]}")
            return {"success": False, "error": f"图片转换失败: {error_msg[-200:]}"}
        
        return {
            "success": True,
            "imagePath": f"/api/system/image/{url_hash}.png"
        }
        
    except httpx.HTTPError as e:
        return {"success": False, "error": f"下载图片失败: {str(e)}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "图片转换超时"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"处理图片失败: {str(e)}"}


@router.get("/image/{filename}")
async def get_image(filename: str):
    """获取转换后的图片文件"""
    cache_dir = get_image_cache_dir()
    file_path = cache_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="图片文件不存在")
    
    # 根据扩展名确定 MIME 类型
    ext = file_path.suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    mime_type = mime_types.get(ext, 'image/png')
    
    return FileResponse(
        path=str(file_path),
        media_type=mime_type,
        filename=filename
    )


# ============ 宏录制器 API ============

# 全局录制状态
macro_recording_state = {
    "is_recording": False,
    "actions": [],
    "start_time": 0,
    "options": {},
    "mouse_listener": None,
    "keyboard_listener": None,
    "last_move_time": 0,
    "hotkey_listener": None,  # 全局快捷键监听器
    "pending_start": False,   # 等待开始录制（快捷键触发）
    "pending_stop": False,    # 等待停止录制（快捷键触发）
}


class MacroStartRequest(BaseModel):
    recordMouseMove: bool = True
    recordMouseClick: bool = True
    recordKeyboard: bool = True
    recordScroll: bool = True
    mouseMoveInterval: int = 16  # 鼠标移动采样间隔(ms)，默认16ms约60fps


@router.post("/macro/start")
async def start_macro_recording(request: MacroStartRequest):
    """开始宏录制 - 使用 pynput 库安全监听，使用 Windows API 获取精确坐标"""
    import time
    import ctypes
    
    global macro_recording_state
    
    if macro_recording_state["is_recording"]:
        return {"success": False, "error": "已经在录制中"}
    
    try:
        from pynput import mouse, keyboard
    except ImportError:
        return {"success": False, "error": "pynput 库未安装，请运行: pip install pynput"}
    
    # 设置进程为 DPI 感知，确保获取真实物理像素坐标
    try:
        # Windows 8.1+ 使用 SetProcessDpiAwareness
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except:
        try:
            # Windows Vista/7/8 使用 SetProcessDPIAware
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass
    
    # 定义 POINT 结构体用于获取真实鼠标坐标
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
    # 获取真实鼠标坐标的函数（使用 Windows API，不受 DPI 缩放影响）
    def get_real_cursor_pos():
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
    
    macro_recording_state["is_recording"] = True
    macro_recording_state["actions"] = []
    macro_recording_state["start_time"] = time.time() * 1000  # 毫秒
    macro_recording_state["last_move_time"] = 0
    macro_recording_state["pending_start"] = False
    macro_recording_state["pending_stop"] = False
    macro_recording_state["options"] = {
        "recordMouseMove": request.recordMouseMove,
        "recordMouseClick": request.recordMouseClick,
        "recordKeyboard": request.recordKeyboard,
        "recordScroll": request.recordScroll,
        "mouseMoveInterval": request.mouseMoveInterval,
    }
    
    options = macro_recording_state["options"]
    
    def get_time():
        return int(time.time() * 1000 - macro_recording_state["start_time"])
    
    # 鼠标移动回调 - 使用 Windows API 获取真实坐标
    def on_mouse_move(x, y):
        if not macro_recording_state["is_recording"]:
            return False  # 停止监听
        if not options["recordMouseMove"]:
            return True
        
        current_time = get_time()
        if current_time - macro_recording_state["last_move_time"] >= options["mouseMoveInterval"]:
            macro_recording_state["last_move_time"] = current_time
            # 使用 Windows API 获取真实坐标，而不是 pynput 传入的坐标
            real_x, real_y = get_real_cursor_pos()
            macro_recording_state["actions"].append({
                "type": "mouse_move",
                "time": current_time,
                "x": real_x,
                "y": real_y,
            })
        return True
    
    # 鼠标点击回调 - 使用 Windows API 获取真实坐标
    def on_mouse_click(x, y, button, pressed):
        if not macro_recording_state["is_recording"]:
            return False
        if not options["recordMouseClick"]:
            return True
        
        button_name = "left"
        if button == mouse.Button.right:
            button_name = "right"
        elif button == mouse.Button.middle:
            button_name = "middle"
        
        # 使用 Windows API 获取真实坐标
        real_x, real_y = get_real_cursor_pos()
        macro_recording_state["actions"].append({
            "type": "mouse_click",
            "time": get_time(),
            "x": real_x,
            "y": real_y,
            "button": button_name,
            "pressed": pressed,
        })
        return True
    
    # 鼠标滚轮回调 - 使用 Windows API 获取真实坐标
    def on_mouse_scroll(x, y, dx, dy):
        if not macro_recording_state["is_recording"]:
            return False
        if not options["recordScroll"]:
            return True
        
        # dy > 0 向上滚动，dy < 0 向下滚动
        delta = int(dy * 120)  # 转换为 Windows 滚轮单位
        # 使用 Windows API 获取真实坐标
        real_x, real_y = get_real_cursor_pos()
        macro_recording_state["actions"].append({
            "type": "mouse_scroll",
            "time": get_time(),
            "x": real_x,
            "y": real_y,
            "delta": delta,
        })
        return True
    
    # 键盘按下回调
    def on_key_press(key):
        if not macro_recording_state["is_recording"]:
            return False
        if not options["recordKeyboard"]:
            return True
        
        # 获取虚拟键码
        try:
            if hasattr(key, 'vk'):
                vk_code = key.vk
            elif hasattr(key, 'value'):
                vk_code = key.value.vk
            else:
                # 尝试从字符获取
                vk_code = ord(key.char.upper()) if hasattr(key, 'char') and key.char else 0
        except:
            vk_code = 0
        
        # 忽略 F9(0x78) 和 F10(0x79) 快捷键，这些用于控制录制
        if vk_code in (0x78, 0x79):  # VK_F9, VK_F10
            return True
        
        if vk_code > 0:
            macro_recording_state["actions"].append({
                "type": "key_press",
                "time": get_time(),
                "keyCode": vk_code,
                "pressed": True,
            })
        return True
    
    # 键盘释放回调
    def on_key_release(key):
        if not macro_recording_state["is_recording"]:
            return False
        if not options["recordKeyboard"]:
            return True
        
        try:
            if hasattr(key, 'vk'):
                vk_code = key.vk
            elif hasattr(key, 'value'):
                vk_code = key.value.vk
            else:
                vk_code = ord(key.char.upper()) if hasattr(key, 'char') and key.char else 0
        except:
            vk_code = 0
        
        # 忽略 F9(0x78) 和 F10(0x79) 快捷键
        if vk_code in (0x78, 0x79):  # VK_F9, VK_F10
            return True
        
        if vk_code > 0:
            macro_recording_state["actions"].append({
                "type": "key_press",
                "time": get_time(),
                "keyCode": vk_code,
                "pressed": False,
            })
        return True
    
    # 启动监听器
    mouse_listener = mouse.Listener(
        on_move=on_mouse_move,
        on_click=on_mouse_click,
        on_scroll=on_mouse_scroll
    )
    keyboard_listener = keyboard.Listener(
        on_press=on_key_press,
        on_release=on_key_release
    )
    
    mouse_listener.start()
    keyboard_listener.start()
    
    macro_recording_state["mouse_listener"] = mouse_listener
    macro_recording_state["keyboard_listener"] = keyboard_listener
    
    return {"success": True, "message": "录制已开始"}


@router.post("/macro/stop")
async def stop_macro_recording():
    """停止宏录制"""
    global macro_recording_state
    
    if not macro_recording_state["is_recording"]:
        return {"success": False, "error": "没有正在进行的录制"}
    
    macro_recording_state["is_recording"] = False
    
    # 停止监听器
    if macro_recording_state["mouse_listener"]:
        macro_recording_state["mouse_listener"].stop()
        macro_recording_state["mouse_listener"] = None
    
    if macro_recording_state["keyboard_listener"]:
        macro_recording_state["keyboard_listener"].stop()
        macro_recording_state["keyboard_listener"] = None
    
    actions = macro_recording_state["actions"]
    
    return {
        "success": True,
        "actions": actions,
        "count": len(actions)
    }


@router.get("/macro/data")
async def get_macro_data():
    """获取当前录制的数据和快捷键触发状态"""
    global macro_recording_state
    
    # 检查是否有快捷键触发的状态变化
    pending_start = macro_recording_state.get("pending_start", False)
    pending_stop = macro_recording_state.get("pending_stop", False)
    
    # 重置 pending 状态
    if pending_start:
        macro_recording_state["pending_start"] = False
    if pending_stop:
        macro_recording_state["pending_stop"] = False
    
    return {
        "success": True,
        "isRecording": macro_recording_state["is_recording"],
        "actions": macro_recording_state["actions"],
        "count": len(macro_recording_state["actions"]),
        "pendingStart": pending_start,  # 快捷键触发开始
        "pendingStop": pending_stop,    # 快捷键触发停止
    }


@router.post("/macro/hotkey/start")
async def start_macro_hotkey_listener():
    """启动全局快捷键监听器（F9开始录制，F10停止录制）"""
    global macro_recording_state
    
    # 如果已有监听器在运行，先停止
    if macro_recording_state.get("hotkey_listener"):
        try:
            macro_recording_state["hotkey_listener"].stop()
        except:
            pass
        macro_recording_state["hotkey_listener"] = None
    
    try:
        from pynput import keyboard
    except ImportError:
        return {"success": False, "error": "pynput 库未安装"}
    
    def on_hotkey_press(key):
        """全局快捷键处理"""
        try:
            # 获取虚拟键码
            if hasattr(key, 'vk'):
                vk_code = key.vk
            elif hasattr(key, 'value'):
                vk_code = key.value.vk
            else:
                return True
            
            # F9 (0x78) - 开始录制
            if vk_code == 0x78:
                if not macro_recording_state["is_recording"]:
                    macro_recording_state["pending_start"] = True
            # F10 (0x79) - 停止录制
            elif vk_code == 0x79:
                if macro_recording_state["is_recording"]:
                    macro_recording_state["pending_stop"] = True
        except:
            pass
        return True
    
    # 启动全局快捷键监听器
    hotkey_listener = keyboard.Listener(on_press=on_hotkey_press)
    hotkey_listener.start()
    
    macro_recording_state["hotkey_listener"] = hotkey_listener
    
    return {"success": True, "message": "全局快捷键监听已启动 (F9开始, F10停止)"}


@router.post("/macro/hotkey/stop")
async def stop_macro_hotkey_listener():
    """停止全局快捷键监听器"""
    global macro_recording_state
    
    if macro_recording_state.get("hotkey_listener"):
        try:
            macro_recording_state["hotkey_listener"].stop()
        except:
            pass
        macro_recording_state["hotkey_listener"] = None
    
    return {"success": True, "message": "全局快捷键监听已停止"}


@router.get("/mouse-position")
async def get_mouse_position():
    """获取当前鼠标位置"""
    import ctypes
    
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    
    return {
        "success": True,
        "x": pt.x,
        "y": pt.y
    }


# ==================== NapCat 服务管理 ====================

class NapCatStartRequest(BaseModel):
    qq_number: Optional[str] = ""


class NapCatConfigRequest(BaseModel):
    qq_number: str
    config: dict


# 存储 socketio 实例的引用
_sio = None

def set_napcat_sio(sio):
    """设置 socketio 实例"""
    global _sio
    _sio = sio


@router.get("/napcat/status")
async def get_napcat_status():
    """获取 NapCat 服务状态"""
    from ..services.napcat_service import napcat_service
    status = napcat_service.get_status()
    # 添加二维码路径
    qrcode_path = napcat_service.get_qrcode_path()
    if qrcode_path:
        status["qrcode_available"] = True
    else:
        status["qrcode_available"] = False
    return status


@router.post("/napcat/start")
async def start_napcat(request: NapCatStartRequest):
    """启动 NapCat 服务"""
    from ..services.napcat_service import napcat_service
    
    def on_qrcode(qrcode_path: str):
        """二维码生成回调"""
        print(f"[NapCat API] 二维码已生成: {qrcode_path}")
        if _sio:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_sio.emit('napcat:qrcode', {'path': qrcode_path}))
                else:
                    loop.run_until_complete(_sio.emit('napcat:qrcode', {'path': qrcode_path}))
            except Exception as e:
                print(f"[NapCat API] 发送二维码事件失败: {e}")
    
    def on_login(qq_number: str):
        """登录成功回调"""
        print(f"[NapCat API] 登录成功: {qq_number}")
        if _sio:
            import asyncio
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
        return FileResponse(
            path=qrcode_path,
            media_type="image/png",
            filename="qrcode.png"
        )
    
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
    import asyncio
    
    # 先停止服务
    napcat_service.stop()
    
    # 等待一下确保进程完全停止
    await asyncio.sleep(1)
    
    # 删除旧的二维码文件
    qrcode_path = napcat_service.napcat_dir / "cache" / "qrcode.png"
    if qrcode_path.exists():
        try:
            qrcode_path.unlink()
        except:
            pass
    
    # 重新启动服务（不指定 QQ 号，使用扫码登录）
    def on_qrcode(qrcode_path: str):
        print(f"[NapCat API] 新二维码已生成: {qrcode_path}")
        if _sio:
            import asyncio
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
            import asyncio
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


# 鼠标坐标实时显示服务
_mouse_tracker_running = False
_mouse_tracker_task = None


@router.get("/mouse-position")
async def get_mouse_position():
    """获取当前鼠标位置"""
    import ctypes
    
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    
    return {"x": pt.x, "y": pt.y}


@router.post("/mouse-tracker/start")
async def start_mouse_tracker():
    """启动鼠标坐标追踪（通过WebSocket推送）"""
    global _mouse_tracker_running
    _mouse_tracker_running = True
    return {"success": True, "message": "鼠标追踪已启动"}


@router.post("/mouse-tracker/stop")
async def stop_mouse_tracker():
    """停止鼠标坐标追踪"""
    global _mouse_tracker_running
    _mouse_tracker_running = False
    return {"success": True, "message": "鼠标追踪已停止"}


@router.get("/mouse-tracker/status")
async def get_mouse_tracker_status():
    """获取鼠标追踪状态"""
    return {"running": _mouse_tracker_running}


# ==================== 鼠标坐标实时显示 ====================

@router.post("/coordinate-overlay/start")
async def start_coordinate_overlay():
    """启动鼠标坐标实时显示（置顶窗口）"""
    from app.services.coordinate_overlay import start_coordinate_overlay
    return start_coordinate_overlay()


@router.post("/coordinate-overlay/stop")
async def stop_coordinate_overlay():
    """停止鼠标坐标实时显示"""
    from app.services.coordinate_overlay import stop_coordinate_overlay
    return stop_coordinate_overlay()


@router.get("/coordinate-overlay/status")
async def get_coordinate_overlay_status():
    """获取坐标显示状态"""
    from app.services.coordinate_overlay import is_overlay_running
    return {"running": is_overlay_running()}
