import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { phoneApi, imageAssetApi } from '@/services/api'
import { getBackendBaseUrl } from '@/services/config'
import { useWorkflowStore } from '@/store/workflowStore'
import { Camera, Crop, Save, X, Loader2, AlertCircle } from 'lucide-react'

interface PhoneScreenshotCropperProps {
  open: boolean
  onClose: () => void
  deviceId: string
}

interface CropArea {
  startX: number
  startY: number
  endX: number
  endY: number
}

export function PhoneScreenshotCropper({ open, onClose, deviceId }: PhoneScreenshotCropperProps) {
  const [screenshot, setScreenshot] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [cropArea, setCropArea] = useState<CropArea | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [templateName, setTemplateName] = useState('')
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)
  const { setBottomPanelTab } = useWorkflowStore()

  // 截取手机屏幕
  const captureScreenshot = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)
    setScreenshot(null)
    setCropArea(null)
    
    try {
      const result = await phoneApi.screenshot(deviceId)
      if (result.error) {
        setError(result.error)
      } else if (result.data?.path) {
        // 构建截图URL
        const API_BASE = getBackendBaseUrl()
        const timestamp = Date.now()
        setScreenshot(`${API_BASE}/api/phone/screenshot/file?device_id=${deviceId}&t=${timestamp}`)
        
        // 生成默认文件名
        const now = new Date()
        const defaultName = `template_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`
        setTemplateName(defaultName)
      }
    } catch (err) {
      setError('截图失败: ' + String(err))
    } finally {
      setLoading(false)
    }
  }

  // 鼠标按下开始框选
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !imageRef.current) return
    
    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const scaleX = imageRef.current.naturalWidth / rect.width
    const scaleY = imageRef.current.naturalHeight / rect.height
    
    const x = (e.clientX - rect.left) * scaleX
    const y = (e.clientY - rect.top) * scaleY
    
    setCropArea({ startX: x, startY: y, endX: x, endY: y })
    setIsDragging(true)
  }

  // 鼠标移动更新框选区域
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging || !cropArea || !canvasRef.current || !imageRef.current) return
    
    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const scaleX = imageRef.current.naturalWidth / rect.width
    const scaleY = imageRef.current.naturalHeight / rect.height
    
    const x = (e.clientX - rect.left) * scaleX
    const y = (e.clientY - rect.top) * scaleY
    
    setCropArea({ ...cropArea, endX: x, endY: y })
  }

  // 鼠标松开完成框选
  const handleMouseUp = () => {
    setIsDragging(false)
  }

  // 绘制截图和裁剪框
  useEffect(() => {
    if (!canvasRef.current || !imageRef.current || !screenshot) return
    
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    const img = imageRef.current
    
    // 等待图片加载完成
    const drawImage = () => {
      if (!img.complete || img.naturalWidth === 0) {
        return
      }
      
      // 设置canvas尺寸为图片原始尺寸
      canvas.width = img.naturalWidth
      canvas.height = img.naturalHeight
      
      // 清空画布
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      // 绘制图片
      ctx.drawImage(img, 0, 0)
      
      // 绘制裁剪框
      if (cropArea) {
        const x = Math.min(cropArea.startX, cropArea.endX)
        const y = Math.min(cropArea.startY, cropArea.endY)
        const width = Math.abs(cropArea.endX - cropArea.startX)
        const height = Math.abs(cropArea.endY - cropArea.startY)
        
        // 半透明遮罩
        ctx.fillStyle = 'rgba(0, 0, 0, 0.5)'
        ctx.fillRect(0, 0, canvas.width, canvas.height)
        
        // 清除选中区域
        ctx.clearRect(x, y, width, height)
        ctx.drawImage(img, x, y, width, height, x, y, width, height)
        
        // 绘制边框
        ctx.strokeStyle = '#10b981'
        ctx.lineWidth = 3
        ctx.strokeRect(x, y, width, height)
        
        // 绘制尺寸信息
        ctx.fillStyle = '#10b981'
        ctx.font = 'bold 16px sans-serif'
        const sizeText = `${Math.round(width)} × ${Math.round(height)}`
        const textWidth = ctx.measureText(sizeText).width
        ctx.fillRect(x, y - 25, textWidth + 10, 25)
        ctx.fillStyle = 'white'
        ctx.fillText(sizeText, x + 5, y - 7)
      }
    }
    
    // 如果图片已加载，直接绘制
    if (img.complete && img.naturalWidth > 0) {
      drawImage()
    } else {
      // 否则等待加载完成
      img.onload = drawImage
    }
  }, [screenshot, cropArea])

  // 保存裁剪的模板
  const saveCroppedTemplate = async () => {
    if (!cropArea || !templateName.trim()) {
      setError('请框选区域并输入图像名称')
      return
    }
    
    const x = Math.min(cropArea.startX, cropArea.endX)
    const y = Math.min(cropArea.startY, cropArea.endY)
    const width = Math.abs(cropArea.endX - cropArea.startX)
    const height = Math.abs(cropArea.endY - cropArea.startY)
    
    if (width < 10 || height < 10) {
      setError('裁剪区域太小，最小尺寸为 10x10')
      return
    }
    
    setSaving(true)
    setError(null)
    setSuccess(null)
    
    try {
      const result = await phoneApi.captureTemplate(
        deviceId,
        Math.round(x),
        Math.round(y),
        Math.round(width),
        Math.round(height),
        templateName.trim()
      )
      
      if (result.error) {
        const errorMsg = typeof result.error === 'string' 
          ? result.error 
          : JSON.stringify(result.error)
        setError(errorMsg)
      } else if (result.data?.asset) {
        // 重新加载图像资源列表以确保同步
        try {
          const assetsResult = await imageAssetApi.list()
          if (assetsResult.data) {
            useWorkflowStore.getState().setImageAssets(assetsResult.data)
            
            // 自动切换到图像资源标签页
            setBottomPanelTab('images')
          }
        } catch (err) {
          console.error('刷新图像资源列表失败:', err)
        }
        
        // 显示成功提示
        const successMsg = `✅ 模板"${templateName.trim()}"已保存至图像资源！您可以继续截取其他模板，或关闭对话框。`
        setSuccess(successMsg)
        
        // 清空输入框，但保留选区，方便用户继续框选其他区域
        setTemplateName('')
        
        // 5秒后自动隐藏成功提示
        setTimeout(() => {
          setSuccess(null)
        }, 5000)
      }
    } catch (err) {
      const errorMsg = '保存失败: ' + String(err)
      console.error(errorMsg, err)
      setError(errorMsg)
    } finally {
      setSaving(false)
    }
  }

  // 对话框打开时自动截图
  useEffect(() => {
    if (open && deviceId) {
      captureScreenshot()
    }
  }, [open, deviceId])

  if (!open) return null

  return (
    <div 
      className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 animate-fade-in"
      onClick={onClose}
    >
      <div 
        className="bg-white text-black border border-gray-200 rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 标题栏 */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-emerald-50 to-green-50">
          <div className="flex items-center gap-2">
            <Crop className="w-6 h-6 text-emerald-600" />
            <h2 className="text-xl font-semibold text-gray-900">截图并裁剪模板</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 内容区域 */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {/* 说明 */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <div className="flex gap-3">
              <Camera className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-blue-900 mb-1">使用说明</h3>
                <p className="text-sm text-blue-700">
                  1. 点击"重新截图"按钮截取当前手机屏幕<br />
                  2. 在截图上按住鼠标左键拖动框选需要的区域<br />
                  3. 输入图像名称并点击"保存至图像资源"<br />
                  4. 图像将自动保存到底栏的图像资源中
                </p>
              </div>
            </div>
          </div>

          {/* 成功信息 */}
          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4 animate-in fade-in slide-in-from-top-2 duration-300">
              <div className="flex gap-3">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-sm text-green-700 flex-1">{success}</p>
              </div>
            </div>
          )}

          {/* 错误信息 */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <div className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}

          {/* 截图区域 */}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="w-12 h-12 text-emerald-600 animate-spin mb-4" />
              <p className="text-gray-600">正在截取手机屏幕...</p>
            </div>
          ) : screenshot ? (
            <div className="space-y-4">
              {/* 截图显示 */}
              <div className="relative border-2 border-gray-300 rounded-lg overflow-hidden bg-gray-100">
                <img
                  ref={imageRef}
                  src={screenshot}
                  alt="手机截图"
                  crossOrigin="anonymous"
                  className="hidden"
                  onLoad={() => {
                    console.log('图片加载成功')
                    // 触发重绘
                    if (canvasRef.current && imageRef.current) {
                      const canvas = canvasRef.current
                      const ctx = canvas.getContext('2d')
                      const img = imageRef.current
                      if (ctx && img.complete && img.naturalWidth > 0) {
                        canvas.width = img.naturalWidth
                        canvas.height = img.naturalHeight
                        ctx.drawImage(img, 0, 0)
                      }
                    }
                  }}
                  onError={(e) => {
                    console.error('图片加载失败:', e)
                    setError('图片加载失败，请重试')
                  }}
                />
                <canvas
                  ref={canvasRef}
                  className="w-full h-auto cursor-crosshair"
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onMouseLeave={handleMouseUp}
                />
              </div>

              {/* 操作区域 */}
              <div className="flex items-end gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    图像名称
                  </label>
                  <Input
                    value={templateName}
                    onChange={(e) => setTemplateName(e.target.value)}
                    placeholder="输入图像名称"
                    className="w-full"
                  />
                </div>
                <Button
                  variant="outline"
                  onClick={captureScreenshot}
                  disabled={loading}
                >
                  <Camera className="w-4 h-4 mr-2" />
                  重新截图
                </Button>
                <Button
                  onClick={saveCroppedTemplate}
                  disabled={!cropArea || !templateName.trim() || saving}
                  className="bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400"
                >
                  {saving ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      保存中...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      保存至图像资源
                    </>
                  )}
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-20">
              <Camera className="w-16 h-16 text-gray-400 mb-4" />
              <p className="text-gray-600 mb-4">点击下方按钮开始截图</p>
              <Button
                onClick={captureScreenshot}
                className="bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400"
              >
                <Camera className="w-4 h-4 mr-2" />
                截取手机屏幕
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
