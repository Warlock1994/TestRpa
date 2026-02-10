import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { phoneApi } from '@/services/api'
import { Smartphone, RefreshCw, Monitor, AlertCircle, CheckCircle, Loader2, X, Crop } from 'lucide-react'
import { PhoneScreenshotCropper } from './PhoneScreenshotCropper'

interface PhoneMirrorDialogProps {
  open: boolean
  onClose: () => void
}

interface Device {
  id: string
  model: string
  status: string
}

export function PhoneMirrorDialog({ open, onClose }: PhoneMirrorDialogProps) {
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mirrorStatus, setMirrorStatus] = useState<{
    running: boolean
    device_id: string | null
  }>({ running: false, device_id: null })
  const [refreshing, setRefreshing] = useState(false)
  const [showCropper, setShowCropper] = useState(false)
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('')

  // 加载设备列表
  const loadDevices = async () => {
    setRefreshing(true)
    setError(null)
    try {
      const result = await phoneApi.getDevices()
      if (result.error) {
        setError(result.error)
        setDevices([])
      } else {
        setDevices(result.data?.devices || [])
      }
    } catch (err) {
      setError('获取设备列表失败')
      setDevices([])
    } finally {
      setRefreshing(false)
    }
  }

  // 加载镜像状态
  const loadMirrorStatus = async () => {
    try {
      const result = await phoneApi.getMirrorStatus()
      if (result.data?.status) {
        setMirrorStatus(result.data.status)
      }
    } catch (err) {
      console.error('获取镜像状态失败:', err)
    }
  }

  // 启动镜像
  const startMirror = async (deviceId: string) => {
    setLoading(true)
    setError(null)
    try {
      const result = await phoneApi.startMirror(deviceId, 1920, '8M')
      if (result.error) {
        // 显示详细的错误信息
        setError(result.error)
      } else {
        // 启动成功，更新状态
        await loadMirrorStatus()
      }
    } catch (err) {
      setError('启动镜像失败')
    } finally {
      setLoading(false)
    }
  }

  // 停止镜像
  const stopMirror = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await phoneApi.stopMirror()
      if (result.error) {
        setError(result.error)
      } else {
        await loadMirrorStatus()
      }
    } catch (err) {
      setError('停止镜像失败')
    } finally {
      setLoading(false)
    }
  }

  // 对话框打开时加载数据
  useEffect(() => {
    if (open) {
      loadDevices()
      loadMirrorStatus()
    }
  }, [open])

  if (!open) return null

  return (
    <>
      <div 
        className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in"
        onClick={onClose}
      >
      <div 
        className="bg-white text-black border border-gray-200 rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 标题栏 */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-emerald-50 to-green-50">
          <div className="flex items-center gap-2">
            <Smartphone className="w-6 h-6 text-emerald-600" />
            <h2 className="text-xl font-semibold text-gray-900">手机屏幕镜像</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 内容区域 */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-80px)]">
          <div className="space-y-6">
          {/* 说明 */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex gap-3">
              <Monitor className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-blue-900 mb-1">功能说明</h3>
                <p className="text-sm text-blue-700">
                  启动手机屏幕镜像后，您可以在电脑上查看和操作手机屏幕。
                  镜像窗口会自动置顶显示，方便您同时使用电脑和手机。
                </p>
              </div>
            </div>
          </div>

          {/* 镜像状态 */}
          {mirrorStatus.running && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <div>
                    <h3 className="font-semibold text-green-900">镜像运行中</h3>
                    <p className="text-sm text-green-700">
                      设备: {mirrorStatus.device_id || '未知'}
                    </p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={stopMirror}
                  disabled={loading}
                  className="border-red-300 text-red-700 hover:bg-red-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                      停止中...
                    </>
                  ) : (
                    '停止镜像'
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* 错误信息 */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-red-900 mb-2">连接失败</h3>
                  <pre className="text-sm text-red-700 whitespace-pre-wrap font-mono bg-red-100 p-3 rounded">
                    {error}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* 设备列表 */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">已连接的设备</h3>
              <Button
                variant="outline"
                size="sm"
                onClick={loadDevices}
                disabled={refreshing}
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
                刷新
              </Button>
            </div>

            {devices.length === 0 ? (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <Smartphone className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-2">未检测到设备</p>
                <p className="text-sm text-gray-500">
                  请确保手机已通过 USB 连接并开启了 USB 调试
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {devices.map((device) => (
                  <div
                    key={device.id}
                    className="bg-white border border-gray-200 rounded-lg p-4 hover:border-emerald-300 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                          <Smartphone className="w-5 h-5 text-emerald-600" />
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-900">{device.model || device.id}</h4>
                          <p className="text-sm text-gray-500">
                            {device.id} • {device.status}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          onClick={() => {
                            setSelectedDeviceId(device.id)
                            setShowCropper(true)
                          }}
                          className="border-orange-300 text-orange-700 hover:bg-orange-50"
                        >
                          <Crop className="w-4 h-4 mr-1" />
                          截图裁剪
                        </Button>
                        <Button
                          onClick={() => startMirror(device.id)}
                          disabled={loading || mirrorStatus.running}
                          className="bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400"
                        >
                          {loading ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                              启动中...
                            </>
                          ) : (
                            <>
                              <Monitor className="w-4 h-4 mr-1" />
                              启动镜像
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          </div>
        </div>
      </div>
      </div>

      {/* 截图裁剪对话框 */}
      <PhoneScreenshotCropper
        open={showCropper}
        onClose={() => setShowCropper(false)}
        deviceId={selectedDeviceId}
      />
    </>
  )
}
