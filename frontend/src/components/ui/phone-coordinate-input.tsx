import { useState, useEffect, useRef } from 'react'
import { Smartphone, Loader2, X, Play } from 'lucide-react'
import { VariableInput } from './variable-input'
import { Button } from './button'
import { cn } from '@/lib/utils'
import { phoneApi } from '@/services/api'

interface PhoneCoordinateInputProps {
  xValue: string
  yValue: string
  onXChange: (value: string) => void
  onYChange: (value: string) => void
  xPlaceholder?: string
  yPlaceholder?: string
  className?: string
}

export function PhoneCoordinateInput({
  xValue,
  yValue,
  onXChange,
  onYChange,
  xPlaceholder = '手机屏幕X坐标',
  yPlaceholder = '手机屏幕Y坐标',
  className,
}: PhoneCoordinateInputProps) {
  const [isPicking, setIsPicking] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [statusText, setStatusText] = useState('')
  const [deviceId, setDeviceId] = useState<string | null>(null)
  const pollingIntervalRef = useRef<number | null>(null)

  // 检查设备
  const checkDevice = async () => {
    try {
      const result = await phoneApi.getDevices()
      if (result.data?.devices && result.data.devices.length > 0) {
        setDeviceId(result.data.devices[0].id)
        return result.data.devices[0].id
      }
      return null
    } catch {
      return null
    }
  }

  useEffect(() => {
    checkDevice()
  }, [])

  // 轮询坐标
  const startPolling = () => {
    if (pollingIntervalRef.current) return

    let lastCoord: { x: number; y: number } | null = null

    pollingIntervalRef.current = window.setInterval(async () => {
      try {
        const statusResult = await phoneApi.getMirrorStatus()
        if (statusResult.data?.status && !statusResult.data.status.running) {
          handleStop()
          return
        }

        const result = await phoneApi.getPickedCoordinate()
        if (result.data?.picked && result.data.x !== undefined && result.data.y !== undefined) {
          const currentCoord = { x: result.data.x, y: result.data.y }
          
          if (!lastCoord || lastCoord.x !== currentCoord.x || lastCoord.y !== currentCoord.y) {
            onXChange(String(currentCoord.x))
            onYChange(String(currentCoord.y))
            setStatusText(`✅ 已获取坐标: (${currentCoord.x}, ${currentCoord.y})`)
            setTimeout(() => {
              if (isPicking) {
                setStatusText('✅ 运行中，按住 Ctrl+左键 获取坐标')
              }
            }, 2000)
            
            lastCoord = currentCoord
          }
        }
      } catch (error) {
        console.error('Failed to get coordinate:', error)
      }
    }, 200)
  }

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
  }

  useEffect(() => {
    return () => stopPolling()
  }, [])

  const handlePick = async () => {
    if (isPicking) return
    
    setIsPicking(true)
    setStatusText('正在检查设备...')
    
    const currentDeviceId = await checkDevice()
    
    if (!currentDeviceId) {
      setStatusText('❌ 未检测到设备，请先连接手机')
      setTimeout(() => setStatusText(''), 3000)
      setIsPicking(false)
      return
    }
    
    setStatusText('正在启动镜像窗口...')
    
    try {
      const result = await phoneApi.startCoordinatePicker(currentDeviceId, 1920, '8M')
      
      if (!result.data?.success) {
        setStatusText(`❌ 启动失败: ${result.data?.error || result.error || '未知错误'}`)
        setTimeout(() => setStatusText(''), 3000)
        setIsPicking(false)
        return
      }
      
      setStatusText('✅ 已启动！按住 Ctrl+左键 获取坐标')
      startPolling()
      
    } catch (error) {
      console.error('Failed to start:', error)
      setStatusText('❌ 启动失败')
      setTimeout(() => setStatusText(''), 2000)
      setIsPicking(false)
    }
  }

  const handleStop = async () => {
    try {
      stopPolling()
      await phoneApi.stopCoordinatePicker()
      setStatusText('')
      setIsPicking(false)
    } catch (error) {
      console.error('Failed to stop:', error)
      setStatusText('')
      setIsPicking(false)
    }
  }

  const handleTest = async () => {
    const x = parseInt(xValue)
    const y = parseInt(yValue)
    
    if (isNaN(x) || isNaN(y)) {
      setStatusText('❌ 请先输入有效的坐标')
      setTimeout(() => setStatusText(''), 2000)
      return
    }
    
    if (!deviceId) {
      setStatusText('❌ 未检测到设备')
      setTimeout(() => setStatusText(''), 2000)
      return
    }
    
    setIsTesting(true)
    setStatusText(`正在测试坐标 (${x}, ${y})...`)
    
    try {
      const result = await phoneApi.testCoordinate(x, y, deviceId)
      
      if (result.data?.success) {
        setStatusText(`✅ 已在手机上点击坐标 (${x}, ${y})`)
      } else {
        setStatusText(`❌ 测试失败: ${result.data?.error || result.error || '未知错误'}`)
      }
      setTimeout(() => setStatusText(''), 3000)
    } catch (error) {
      console.error('Failed to test:', error)
      setStatusText('❌ 测试失败')
      setTimeout(() => setStatusText(''), 2000)
    } finally {
      setIsTesting(false)
    }
  }

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center gap-2">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground w-6">X:</span>
            <VariableInput
              value={xValue}
              onChange={onXChange}
              placeholder={xPlaceholder}
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground w-6">Y:</span>
            <VariableInput
              value={yValue}
              onChange={onYChange}
              placeholder={yPlaceholder}
            />
          </div>
        </div>
        <div className="flex flex-col gap-1">
          {!isPicking ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handlePick}
              className="h-8 px-3 flex items-center justify-center gap-1"
              title="启动镜像窗口，按住 Ctrl+左键 获取坐标"
            >
              <Smartphone className="h-3 w-3" />
              <span className="text-xs whitespace-nowrap">拾取</span>
            </Button>
          ) : (
            <Button
              type="button"
              variant="destructive"
              size="sm"
              onClick={handleStop}
              className="h-8 px-3 flex items-center justify-center gap-1"
              title="关闭坐标选择器"
            >
              <X className="h-3 w-3" />
              <span className="text-xs whitespace-nowrap">关闭</span>
            </Button>
          )}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleTest}
            disabled={isTesting || !xValue || !yValue || !deviceId}
            className="h-8 px-3 flex items-center justify-center gap-1"
            title="在手机上测试当前坐标"
          >
            {isTesting ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin" />
                <span className="text-xs whitespace-nowrap">测试中</span>
              </>
            ) : (
              <>
                <Play className="h-3 w-3" />
                <span className="text-xs whitespace-nowrap">测试</span>
              </>
            )}
          </Button>
        </div>
      </div>
      {statusText ? (
        <p className={cn(
          'text-xs',
          statusText.includes('✅') ? 'text-green-600' : 
          statusText.includes('❌') ? 'text-red-600' : 
          'text-blue-600'
        )}>
          {statusText}
        </p>
      ) : (
        <p className="text-xs text-muted-foreground">
          点击「拾取」启动镜像窗口，按住 Ctrl+左键 获取坐标。点击「测试」验证坐标。
        </p>
      )}
    </div>
  )
}
