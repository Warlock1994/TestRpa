import { useState, useEffect } from 'react'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import { getBackendBaseUrl } from '@/services/config'

export function MouseCoordinateOverlay() {
  const showMouseCoordinates = useGlobalConfigStore((state) => state.config.display?.showMouseCoordinates)
  const [isRunning, setIsRunning] = useState(false)

  // 启动/停止后端坐标显示服务
  useEffect(() => {
    const updateOverlay = async () => {
      try {
        const API_BASE = getBackendBaseUrl()
        if (showMouseCoordinates && !isRunning) {
          const response = await fetch(`${API_BASE}/api/system/coordinate-overlay/start`, { method: 'POST' })
          if (response.ok) {
            setIsRunning(true)
          }
        } else if (!showMouseCoordinates && isRunning) {
          const response = await fetch(`${API_BASE}/api/system/coordinate-overlay/stop`, { method: 'POST' })
          if (response.ok) {
            setIsRunning(false)
          }
        }
      } catch (error) {
        console.error('坐标显示服务错误:', error)
      }
    }
    
    updateOverlay()
    
    // 组件卸载时停止服务
    return () => {
      if (isRunning) {
        const API_BASE = getBackendBaseUrl()
        fetch(`${API_BASE}/api/system/coordinate-overlay/stop`, { method: 'POST' }).catch(() => {})
      }
    }
  }, [showMouseCoordinates, isRunning])

  // 不再在前端渲染任何内容，坐标显示由后端置顶窗口处理
  return null
}
