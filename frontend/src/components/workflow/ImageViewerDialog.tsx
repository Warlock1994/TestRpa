import { useState, useEffect, useRef, useCallback } from 'react'
import { X, ZoomIn, ZoomOut, RotateCw, Download, Maximize, Minimize } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ImageViewerDialogProps {
  imageUrl: string
  requestId: string
  autoClose: boolean
  displayTime: number // 毫秒，0表示不自动关闭
  onClose: (success: boolean, error?: string) => void
}

export function ImageViewerDialog({ imageUrl, autoClose, displayTime, onClose }: ImageViewerDialogProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [loadingMessage, setLoadingMessage] = useState('加载中...')
  const [error, setError] = useState<string | null>(null)
  const [scale, setScale] = useState(1)
  const [rotation, setRotation] = useState(0)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [actualImageUrl, setActualImageUrl] = useState('')
  const [isConverting, setIsConverting] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const retryCountRef = useRef(0)

  // 将本地文件路径转换为后端 API URL
  const getInitialUrl = useCallback((url: string) => {
    console.log('[ImageViewer] 原始 URL:', url)
    if (url.match(/^[A-Za-z]:[\\\/]/)) {
      // Windows 绝对路径，通过后端 API 访问
      const apiUrl = `http://localhost:8000/api/system/local-file?path=${encodeURIComponent(url)}`
      console.log('[ImageViewer] 转换为 API URL:', apiUrl)
      return apiUrl
    } else if (url.startsWith('/') && !url.startsWith('//')) {
      // Unix 绝对路径
      const apiUrl = `http://localhost:8000/api/system/local-file?path=${encodeURIComponent(url)}`
      console.log('[ImageViewer] 转换为 API URL:', apiUrl)
      return apiUrl
    }
    return url
  }, [])

  // 转换图片格式（使用后端 FFmpeg）
  const convertImage = useCallback(async (url: string): Promise<string | null> => {
    setIsConverting(true)
    setLoadingMessage('正在转换图片格式...')
    
    try {
      const response = await fetch('http://localhost:8000/api/system/convert-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ imageUrl: url })
      })
      
      const result = await response.json()
      
      if (result.success) {
        return `http://localhost:8000${result.imagePath}`
      } else {
        console.error('[ImageViewer] 转换失败:', result.error)
        return null
      }
    } catch (err) {
      console.error('[ImageViewer] 转换请求失败:', err)
      return null
    } finally {
      setIsConverting(false)
    }
  }, [])

  // 初始化图片 URL
  useEffect(() => {
    const initialUrl = getInitialUrl(imageUrl)
    setActualImageUrl(initialUrl)
  }, [imageUrl, getInitialUrl])

  // 自动关闭计时器
  useEffect(() => {
    if (autoClose && displayTime > 0 && !isLoading && !error) {
      timerRef.current = setTimeout(() => {
        onClose(true)
      }, displayTime)
    }
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [autoClose, displayTime, isLoading, error, onClose])

  // 监听全屏变化
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  // 图片加载
  const handleImageLoad = () => {
    setIsLoading(false)
  }

  const handleImageError = async () => {
    console.error('[ImageViewer] 图片加载失败:', actualImageUrl)
    
    // 如果是第一次失败，尝试用 FFmpeg 转换
    if (retryCountRef.current === 0) {
      retryCountRef.current++
      console.log('[ImageViewer] 尝试使用 FFmpeg 转换...')
      
      const convertedUrl = await convertImage(imageUrl)
      if (convertedUrl) {
        console.log('[ImageViewer] 转换成功，使用新 URL:', convertedUrl)
        setActualImageUrl(convertedUrl)
        setLoadingMessage('加载转换后的图片...')
        return
      }
    }
    
    setError('图片加载失败，格式可能不支持')
    setIsLoading(false)
  }

  // 缩放
  const zoomIn = () => setScale(s => Math.min(s + 0.25, 5))
  const zoomOut = () => setScale(s => Math.max(s - 0.25, 0.25))
  const resetZoom = () => setScale(1)

  // 旋转
  const rotate = () => setRotation(r => (r + 90) % 360)

  // 全屏
  const toggleFullscreen = () => {
    if (!containerRef.current) return
    if (isFullscreen) {
      document.exitFullscreen()
    } else {
      containerRef.current.requestFullscreen()
    }
  }

  // 下载图片
  const downloadImage = () => {
    const link = document.createElement('a')
    link.href = actualImageUrl
    link.download = getFileName()
    link.click()
  }

  // 关闭
  const handleClose = () => {
    onClose(true)
  }

  // 从URL提取文件名
  const getFileName = () => {
    try {
      const url = new URL(imageUrl)
      const path = decodeURIComponent(url.pathname)
      const fileName = path.split('/').pop() || '图片'
      return fileName.length > 40 ? fileName.substring(0, 37) + '...' : fileName
    } catch {
      return '图片查看'
    }
  }

  // 鼠标滚轮缩放
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    if (e.deltaY < 0) {
      zoomIn()
    } else {
      zoomOut()
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in">
      <div 
        ref={containerRef}
        className="bg-white text-black border border-gray-200 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-scale-in"
      >
        {/* 头部 */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-lg">🖼️</span>
            <span className="font-semibold text-gray-900 truncate max-w-[400px]">{getFileName()}</span>
            {autoClose && displayTime > 0 && !isLoading && !error && (
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                {(displayTime / 1000).toFixed(0)}秒后自动关闭
              </span>
            )}
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            onClick={handleClose}
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* 图片区域 */}
        <div 
          className="flex-1 overflow-auto bg-gray-100 flex items-center justify-center min-h-[300px]"
          onWheel={handleWheel}
        >
          {error ? (
            <div className="text-center text-red-500 py-8">
              <span className="text-4xl mb-2 block">😢</span>
              {error}
            </div>
          ) : isLoading ? (
            <div className="text-center text-gray-500 py-8">
              <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
              <div>{loadingMessage}</div>
              {isConverting && (
                <div className="text-xs text-gray-400 mt-1">使用 FFmpeg 转换中...</div>
              )}
            </div>
          ) : null}
          <img
            ref={imageRef}
            src={actualImageUrl}
            alt="查看图片"
            onLoad={handleImageLoad}
            onError={handleImageError}
            className={`max-w-full max-h-full object-contain transition-transform duration-200 ${isLoading || error ? 'hidden' : ''}`}
            style={{
              transform: `scale(${scale}) rotate(${rotation}deg)`,
            }}
            draggable={false}
          />
        </div>

        {/* 工具栏 */}
        <div className="flex items-center justify-center gap-2 px-4 py-3 border-t border-gray-200 bg-gray-50 shrink-0">
          <Button
            variant="ghost"
            size="sm"
            className="text-gray-600 hover:text-gray-900 hover:bg-gray-200"
            onClick={zoomOut}
            title="缩小"
          >
            <ZoomOut className="w-4 h-4 mr-1" />
            缩小
          </Button>
          <button
            className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-200 rounded"
            onClick={resetZoom}
            title="重置缩放"
          >
            {Math.round(scale * 100)}%
          </button>
          <Button
            variant="ghost"
            size="sm"
            className="text-gray-600 hover:text-gray-900 hover:bg-gray-200"
            onClick={zoomIn}
            title="放大"
          >
            <ZoomIn className="w-4 h-4 mr-1" />
            放大
          </Button>
          <div className="w-px h-6 bg-gray-300 mx-2" />
          <Button
            variant="ghost"
            size="sm"
            className="text-gray-600 hover:text-gray-900 hover:bg-gray-200"
            onClick={rotate}
            title="旋转90°"
          >
            <RotateCw className="w-4 h-4 mr-1" />
            旋转
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-gray-600 hover:text-gray-900 hover:bg-gray-200"
            onClick={toggleFullscreen}
            title={isFullscreen ? '退出全屏' : '全屏'}
          >
            {isFullscreen ? <Minimize className="w-4 h-4 mr-1" /> : <Maximize className="w-4 h-4 mr-1" />}
            {isFullscreen ? '退出' : '全屏'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-gray-600 hover:text-gray-900 hover:bg-gray-200"
            onClick={downloadImage}
            title="下载图片"
          >
            <Download className="w-4 h-4 mr-1" />
            下载
          </Button>
        </div>
      </div>
    </div>
  )
}

// 全局状态管理 - 使用 window 对象存储以确保跨模块共享
declare global {
  interface Window {
    __imageViewerCallback?: ((props: ImageViewerDialogProps | null) => void) | null
  }
}

export function setImageViewerCallback(callback: (props: ImageViewerDialogProps | null) => void) {
  window.__imageViewerCallback = callback
}

export function showImageViewer(props: Omit<ImageViewerDialogProps, 'onClose'>, onClose: (success: boolean, error?: string) => void) {
  if (window.__imageViewerCallback) {
    window.__imageViewerCallback({
      ...props,
      onClose: (success, error) => {
        window.__imageViewerCallback?.(null)
        onClose(success, error)
      }
    })
  }
}

export function hideImageViewer() {
  console.log('[ImageViewer] hideImageViewer called')
  if (window.__imageViewerCallback) {
    window.__imageViewerCallback(null)
  }
}
