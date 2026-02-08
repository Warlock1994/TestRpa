import { useEffect, useState } from 'react'
import { WorkflowEditor } from '@/components/workflow/WorkflowEditor'
import { InputPromptDialog } from '@/components/workflow/InputPromptDialog'
import { MusicPlayerContainer } from '@/components/workflow/MusicPlayerContainer'
import { VideoPlayerContainer } from '@/components/workflow/VideoPlayerContainer'
import { ImageViewerContainer } from '@/components/workflow/ImageViewerContainer'
import { UpdateDialog } from '@/components/workflow/UpdateDialog'
import { MouseCoordinateOverlay } from '@/components/workflow/MouseCoordinateOverlay'
import { socketService, updateSocketUrl } from '@/services/socket'
import { remoteService } from '@/services/remote'
import { dataAssetApi, imageAssetApi, updateApiBase } from '@/services/api'
import { setBackendPort } from '@/services/config'
import { useWorkflowStore } from '@/store/workflowStore'
import {
  CURRENT_VERSION,
  fetchLatestVersion,
  hasNewVersion,
} from '@/services/version'

function App() {
  const setDataAssets = useWorkflowStore((state) => state.setDataAssets)
  const setImageAssets = useWorkflowStore((state) => state.setImageAssets)
  
  const [updateInfo, setUpdateInfo] = useState<{
    show: boolean
    latestVersion: string
    downloadUrl: string
  }>({
    show: false,
    latestVersion: '',
    downloadUrl: '',
  })

  // 初始化：获取配置并加载已上传的Excel文件资源和图像资源
  useEffect(() => {
    const init = async () => {
      try {
        // 1. 先从配置文件读取后端端口
        let backendPort = 8000 // 默认端口
        
        try {
          const configResponse = await fetch('/WebRPAConfig.json')
          if (configResponse.ok) {
            const config = await configResponse.json()
            backendPort = config.backend?.port || 8000
            console.log('[Config] 从配置文件读取后端端口:', backendPort)
          }
        } catch (error) {
          console.warn('[Config] 无法读取配置文件，使用默认端口 8000')
        }
        
        // 2. 验证后端是否可访问
        const hostname = window.location.hostname
        const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1'
        
        try {
          const configUrl = isLocalhost
            ? `http://localhost:${backendPort}/api/config`
            : `http://${hostname}:${backendPort}/api/config`
          
          // 使用 AbortController 实现超时
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 2000) // 2秒超时
          
          const response = await fetch(configUrl, { 
            signal: controller.signal
          })
          
          clearTimeout(timeoutId)
          
          if (response.ok) {
            const config = await response.json()
            backendPort = config.backend?.port || backendPort
            console.log('[Config] 后端配置验证成功，端口:', backendPort)
          }
        } catch (error) {
          console.warn('[Config] 无法连接到后端，使用配置文件中的端口:', backendPort)
        }
        
        // 保存后端端口到 sessionStorage（使用配置服务）
        setBackendPort(backendPort)
        // 更新 API 基础地址和 Socket URL
        updateApiBase()
        updateSocketUrl()
        
        // 配置更新完成后，连接 WebSocket
        socketService.connect()
        
        // 3. 加载Excel资源
        const excelResult = await dataAssetApi.list()
        if (excelResult.data) {
          setDataAssets(excelResult.data)
        }
        
        // 4. 加载图像资源
        const imageResult = await imageAssetApi.list()
        if (imageResult.data) {
          setImageAssets(imageResult.data)
        }
      } catch (error) {
        console.error('初始化失败:', error)
      }
    }
    
    init()
    
    // 清理函数
    return () => {
      socketService.disconnect()
    }
  }, [setDataAssets, setImageAssets])

  // 拦截 F9 和 F10 快捷键，防止浏览器默认行为
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // F9 和 F10 是 WebRPA 的快捷键，阻止浏览器默认行为
      if (e.key === 'F9' || e.key === 'F10') {
        e.preventDefault()
        e.stopPropagation()
      }
    }
    
    // 使用 capture 阶段拦截，确保在其他处理器之前执行
    window.addEventListener('keydown', handleKeyDown, { capture: true })
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown, { capture: true })
    }
  }, [])

  // 页面关闭时清理远程协助会话
  useEffect(() => {
    const handleBeforeUnload = () => {
      const session = remoteService.getSession()
      if (session) {
        // 使用 sendBeacon 确保请求能发出
        const hubUrl = localStorage.getItem('workflow_hub_url') || 'https://hub.pmhs.top'
        const clientId = localStorage.getItem('workflow_hub_client_id')
        if (clientId) {
          navigator.sendBeacon(
            `${hubUrl}/api/remote/close`,
            JSON.stringify({ clientId })
          )
        }
      }
    }
    
    window.addEventListener('beforeunload', handleBeforeUnload)
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      // 组件卸载时清理远程协助
      remoteService.closeSession()
    }
  }, [])

  // 检查版本更新
  useEffect(() => {
    const checkUpdate = async () => {
      const versionInfo = await fetchLatestVersion()
      if (!versionInfo) return

      // 检查是否有新版本
      if (hasNewVersion(CURRENT_VERSION, versionInfo.version)) {
        setUpdateInfo({
          show: true,
          latestVersion: versionInfo.version,
          downloadUrl: versionInfo.downloadUrl,
        })
      }
    }

    // 延迟 1 秒检查，避免影响首屏加载
    const timer = setTimeout(checkUpdate, 1000)
    return () => clearTimeout(timer)
  }, [])

  const handleCloseUpdate = () => {
    setUpdateInfo(prev => ({ ...prev, show: false }))
  }

  const handleSkipUpdate = () => {
    setUpdateInfo(prev => ({ ...prev, show: false }))
  }

  return (
    <div className="h-screen w-screen overflow-hidden bg-background">
      <WorkflowEditor />
      <InputPromptDialog />
      <MusicPlayerContainer />
      <VideoPlayerContainer />
      <ImageViewerContainer />
      <UpdateDialog
        isOpen={updateInfo.show}
        currentVersion={CURRENT_VERSION}
        latestVersion={updateInfo.latestVersion}
        downloadUrl={updateInfo.downloadUrl}
        onClose={handleCloseUpdate}
        onSkip={handleSkipUpdate}
      />
      <MouseCoordinateOverlay />
    </div>
  )
}

export default App
