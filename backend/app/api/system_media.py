"""系统媒体相关API - 音频/视频/图片转换和缓存"""
import subprocess
import sys
import os
import hashlib
import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx

router = APIRouter()

# 缓存目录
audio_cache_dir = None
video_cache_dir = None
image_cache_dir = None
audio_cache = {}


def get_audio_cache_dir():
    """获取音频缓存目录"""
    global audio_cache_dir
    if audio_cache_dir is None:
        audio_cache_dir = Path(tempfile.gettempdir()) / "webrpa_audio_cache"
        audio_cache_dir.mkdir(exist_ok=True)
    return audio_cache_dir


def get_video_cache_dir():
    """获取视频缓存目录"""
    global video_cache_dir
    if video_cache_dir is None:
        video_cache_dir = Path(tempfile.gettempdir()) / "webrpa_video_cache"
        video_cache_dir.mkdir(exist_ok=True)
    return video_cache_dir


def get_image_cache_dir():
    """获取图片缓存目录"""
    global image_cache_dir
    if image_cache_dir is None:
        image_cache_dir = Path(tempfile.gettempdir()) / "webrpa_image_cache"
        image_cache_dir.mkdir(exist_ok=True)
    return image_cache_dir


def get_url_hash(url: str) -> str:
    """获取URL的哈希值"""
    return hashlib.md5(url.encode()).hexdigest()[:16]


class AudioConvertRequest(BaseModel):
    audioUrl: str


class VideoConvertRequest(BaseModel):
    videoUrl: str


class ImageConvertRequest(BaseModel):
    imageUrl: str


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
        
        if output_path.exists():
            return {"success": True, "audioPath": f"/api/system/audio/{url_hash}.mp3"}
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://music.163.com/",
            "Accept": "*/*",
        }
        
        async with httpx.AsyncClient(timeout=120, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            audio_data = response.content
        
        from urllib.parse import urlparse, unquote
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path).lower()
        
        supported_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.webm', '.opus', '.ape', '.wv']
        file_ext = '.mp3'
        for ext in supported_extensions:
            if path.endswith(ext):
                file_ext = ext
                break
        
        temp_input = cache_dir / f"{url_hash}_input{file_ext}"
        with open(temp_input, 'wb') as f:
            f.write(audio_data)
        
        if file_ext == '.mp3':
            temp_input.rename(output_path)
        else:
            ffmpeg = get_ffmpeg_path()
            cmd = [ffmpeg, '-i', str(temp_input), '-y', '-c:a', 'libmp3lame', '-q:a', '2', str(output_path)]
            
            result = subprocess.run(
                cmd, capture_output=True, timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            try:
                temp_input.unlink()
            except:
                pass
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                return {"success": False, "error": f"音频转换失败: {error_msg[:200]}"}
        
        return {"success": True, "audioPath": f"/api/system/audio/{url_hash}.mp3"}
        
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
    
    return FileResponse(path=str(file_path), media_type="audio/mpeg", filename=filename)


@router.get("/local-file")
async def get_local_file(path: str):
    """提供本地文件访问服务，用于视频/图片播放等"""
    import urllib.parse
    import mimetypes
    
    file_path = urllib.parse.unquote(path)
    file_path = Path(file_path)
    
    if not file_path.is_absolute():
        raise HTTPException(status_code=400, detail="必须使用绝对路径")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="路径不是文件")
    
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type is None:
        mime_type = "application/octet-stream"
    
    return FileResponse(path=str(file_path), media_type=mime_type, filename=file_path.name)


@router.post("/convert-video")
async def convert_video(request: VideoConvertRequest):
    """将视频转换为浏览器兼容的 H.264 格式"""
    from app.executors.base import get_ffmpeg_path, get_ffprobe_path
    
    video_url = request.videoUrl
    if not video_url:
        return {"success": False, "error": "视频路径不能为空"}
    
    try:
        cache_dir = get_video_cache_dir()
        is_local = False
        input_path = None
        temp_download = None
        
        if video_url.startswith(('http://', 'https://')):
            url_hash = get_url_hash(video_url)
            output_path = cache_dir / f"{url_hash}.mp4"
            
            if output_path.exists():
                return {"success": True, "videoPath": f"/api/system/video/{url_hash}.mp4"}
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "*/*"}
            
            async with httpx.AsyncClient(timeout=300, follow_redirects=True, headers=headers) as client:
                response = await client.get(video_url)
                response.raise_for_status()
                video_data = response.content
            
            temp_download = cache_dir / f"{url_hash}_input.tmp"
            with open(temp_download, 'wb') as f:
                f.write(video_data)
            input_path = str(temp_download)
        else:
            is_local = True
            input_path = video_url
            
            if not Path(input_path).exists():
                return {"success": False, "error": f"文件不存在: {input_path}"}
            
            url_hash = get_url_hash(input_path)
            output_path = cache_dir / f"{url_hash}.mp4"
            
            if output_path.exists():
                if output_path.stat().st_mtime >= Path(input_path).stat().st_mtime:
                    return {"success": True, "videoPath": f"/api/system/video/{url_hash}.mp4"}
        
        ffprobe = get_ffprobe_path()
        probe_cmd = [ffprobe, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name', '-of', 'default=noprint_wrappers=1:nokey=1', input_path]
        
        probe_result = subprocess.run(
            probe_cmd, capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        current_codec = probe_result.stdout.strip().lower()
        
        if current_codec == 'h264':
            if is_local:
                return {"success": True, "videoPath": f"/api/system/local-file?path={subprocess.list2cmdline([input_path])[1:-1]}", "needsConvert": False}
            else:
                import shutil
                shutil.copy(temp_download, output_path)
                if temp_download and temp_download.exists():
                    temp_download.unlink()
                return {"success": True, "videoPath": f"/api/system/video/{url_hash}.mp4"}
        
        ffmpeg = get_ffmpeg_path()
        cmd = [ffmpeg, '-y', '-i', input_path, '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(output_path)]
        
        result = subprocess.run(
            cmd, capture_output=True, timeout=600,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if temp_download and temp_download.exists():
            try:
                temp_download.unlink()
            except:
                pass
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            return {"success": False, "error": f"视频转码失败: {error_msg[-200:]}"}
        
        return {"success": True, "videoPath": f"/api/system/video/{url_hash}.mp4"}
        
    except httpx.HTTPError as e:
        return {"success": False, "error": f"下载视频失败: {str(e)}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "视频转码超时（超过10分钟）"}
    except Exception as e:
        return {"success": False, "error": f"处理视频失败: {str(e)}"}


@router.get("/video/{filename}")
async def get_video(filename: str):
    """获取转换后的视频文件"""
    cache_dir = get_video_cache_dir()
    file_path = cache_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    return FileResponse(path=str(file_path), media_type="video/mp4", filename=filename)


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
        
        if image_url.startswith(('http://', 'https://')):
            url_hash = get_url_hash(image_url)
            output_path = cache_dir / f"{url_hash}.png"
            
            if output_path.exists():
                return {"success": True, "imagePath": f"/api/system/image/{url_hash}.png"}
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "image/*,*/*"}
            
            async with httpx.AsyncClient(timeout=60, follow_redirects=True, headers=headers) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_data = response.content
            
            temp_download = cache_dir / f"{url_hash}_input.tmp"
            with open(temp_download, 'wb') as f:
                f.write(image_data)
            input_path = str(temp_download)
        else:
            is_local = True
            input_path = image_url
            
            if not Path(input_path).exists():
                return {"success": False, "error": f"文件不存在: {input_path}"}
            
            url_hash = get_url_hash(input_path)
            output_path = cache_dir / f"{url_hash}.png"
            
            if output_path.exists():
                if output_path.stat().st_mtime >= Path(input_path).stat().st_mtime:
                    return {"success": True, "imagePath": f"/api/system/image/{url_hash}.png"}
        
        ext = Path(input_path).suffix.lower()
        browser_supported = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico']
        
        if ext in browser_supported and is_local:
            return {"success": True, "imagePath": f"/api/system/local-file?path={subprocess.list2cmdline([input_path])[1:-1]}", "needsConvert": False}
        
        ffmpeg = get_ffmpeg_path()
        cmd = [ffmpeg, '-y', '-i', input_path, '-vframes', '1', str(output_path)]
        
        result = subprocess.run(
            cmd, capture_output=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if temp_download and temp_download.exists():
            try:
                temp_download.unlink()
            except:
                pass
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            return {"success": False, "error": f"图片转换失败: {error_msg[-200:]}"}
        
        return {"success": True, "imagePath": f"/api/system/image/{url_hash}.png"}
        
    except httpx.HTTPError as e:
        return {"success": False, "error": f"下载图片失败: {str(e)}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "图片转换超时"}
    except Exception as e:
        return {"success": False, "error": f"处理图片失败: {str(e)}"}


@router.get("/image/{filename}")
async def get_image(filename: str):
    """获取转换后的图片文件"""
    cache_dir = get_image_cache_dir()
    file_path = cache_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="图片文件不存在")
    
    ext = file_path.suffix.lower()
    mime_types = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp'}
    mime_type = mime_types.get(ext, 'image/png')
    
    return FileResponse(path=str(file_path), media_type=mime_type, filename=filename)
