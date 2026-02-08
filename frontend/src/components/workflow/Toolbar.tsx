import { useWorkflowStore } from '@/store/workflowStore'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useConfirm } from '@/components/ui/confirm-dialog'
import { workflowApi } from '@/services/api'
import { socketService } from '@/services/socket'
import { getBackendBaseUrl } from '@/services/config'
import { GlobalConfigDialog } from './GlobalConfigDialog'
import { DocumentationDialog } from './documentation'
import { AutoBrowserDialog } from './AutoBrowserDialog'
import { WorkflowHubDialog } from './WorkflowHubDialog'
import { LocalWorkflowDialog } from './LocalWorkflowDialog'
import { ScheduledTasksDialog } from '../scheduled-tasks/ScheduledTasksDialog'
import {
  Play,
  Square,
  Save,
  FolderOpen,
  Settings,
  BookOpen,
  Globe,
  Package,
  Code,
  Clock,
  EyeOff,
} from 'lucide-react'
import { useState, useEffect, useCallback, useRef } from 'react'

export function Toolbar() {
  const [workflowId, setWorkflowId] = useState<string | null>(null)
  const [showGlobalConfig, setShowGlobalConfig] = useState(false)
  const [showDocumentation, setShowDocumentation] = useState(false)
  const [showAutoBrowser, setShowAutoBrowser] = useState(false)
  const [showWorkflowHub, setShowWorkflowHub] = useState(false)
  const [showLocalWorkflow, setShowLocalWorkflow] = useState(false)
  const [showScheduledTasks, setShowScheduledTasks] = useState(false)
  const [defaultFolder, setDefaultFolder] = useState('')
  const { confirm, ConfirmDialog } = useConfirm()
  
  // 用于记录输入框聚焦时的初始名称
  const nameOnFocusRef = useRef<string>('')
  
  // 使用选择器确保配置更新时组件重新渲染
  const config = useGlobalConfigStore((state) => state.config)
  
  // 调试：监听配置变化
  useEffect(() => {
    console.log('[Toolbar] 配置已更新:', {
      autoCloseBrowser: config.browser?.autoCloseBrowser,
      fullscreen: config.browser?.fullscreen,
      type: config.browser?.type
    })
  }, [config.browser?.autoCloseBrowser, config.browser?.fullscreen, config.browser?.type])
  
  const name = useWorkflowStore((state) => state.name)
  const nodes = useWorkflowStore((state) => state.nodes)
  const edges = useWorkflowStore((state) => state.edges)
  const variables = useWorkflowStore((state) => state.variables)
  const hasUnsavedChanges = useWorkflowStore((state) => state.hasUnsavedChanges)
  const setWorkflowName = useWorkflowStore((state) => state.setWorkflowName)
  const setWorkflowNameWithHistory = useWorkflowStore((state) => state.setWorkflowNameWithHistory)
  const executionStatus = useWorkflowStore((state) => state.executionStatus)
  const exportWorkflow = useWorkflowStore((state) => state.exportWorkflow)
  const clearWorkflow = useWorkflowStore((state) => state.clearWorkflow)
  const addLog = useWorkflowStore((state) => state.addLog)
  const setExecutionStatus = useWorkflowStore((state) => state.setExecutionStatus)
  const clearLogs = useWorkflowStore((state) => state.clearLogs)
  const clearCollectedData = useWorkflowStore((state) => state.clearCollectedData)
  const setBottomPanelTab = useWorkflowStore((state) => state.setBottomPanelTab)
  const markAsSaved = useWorkflowStore((state) => state.markAsSaved)

  const isRunning = executionStatus === 'running'

  // 处理名称输入框聚焦 - 记录初始名称
  const handleNameFocus = useCallback(() => {
    nameOnFocusRef.current = name
  }, [name])

  // 处理名称输入框失焦 - 如果名称有变化则保存历史
  const handleNameBlur = useCallback(() => {
    if (nameOnFocusRef.current !== name) {
      // 名称有变化，使用 setWorkflowNameWithHistory 保存历史
      // 先恢复旧名称，再调用带历史的方法设置新名称
      const newName = name
      setWorkflowName(nameOnFocusRef.current)
      setWorkflowNameWithHistory(newName)
    }
  }, [name, setWorkflowName, setWorkflowNameWithHistory])

  // 获取默认文件夹
  useEffect(() => {
    const API_BASE = getBackendBaseUrl()
    fetch(`${API_BASE}/api/local-workflows/default-folder`)
      .then(res => res.json())
      .then(data => {
        if (data.folder) setDefaultFolder(data.folder)
      })
      .catch(console.error)
  }, [])

  // 通用执行函数
  const executeWorkflow = useCallback(async (headless: boolean) => {
    if (nodes.length === 0) {
      addLog({ level: 'warning', message: '工作流没有任何节点' })
      return
    }

    clearLogs()
    clearCollectedData()
    setBottomPanelTab('logs')  // 切换到日志栏
    addLog({ level: 'info', message: `正在准备执行工作流${headless ? '（无头模式）' : ''}...` })

    try {
      // 先创建或更新工作流
      let currentWorkflowId = workflowId

      if (!currentWorkflowId) {
        const createResult = await workflowApi.create({
          name,
          nodes: nodes.map(n => ({
            id: n.id,
            type: n.data.moduleType,
            position: n.position,
            data: n.data,
            style: n.style,
          })),
          edges: edges.map(e => ({
            id: e.id,
            source: e.source,
            target: e.target,
            sourceHandle: e.sourceHandle,
            targetHandle: e.targetHandle,
          })),
          variables: variables.map(v => ({
            name: v.name,
            value: v.value,
            type: v.type,
            scope: v.scope,
          })),
        })

        if (createResult.error) {
          addLog({ level: 'error', message: `创建工作流失败: ${createResult.error}` })
          return
        }

        currentWorkflowId = createResult.data!.id
        setWorkflowId(currentWorkflowId)
      } else {
        // 更新现有工作流
        await workflowApi.update(currentWorkflowId, {
          name,
          nodes: nodes.map(n => ({
            id: n.id,
            type: n.data.moduleType,
            position: n.position,
            data: n.data,
            style: n.style,
          })),
          edges: edges.map(e => ({
            id: e.id,
            source: e.source,
            target: e.target,
            sourceHandle: e.sourceHandle,
            targetHandle: e.targetHandle,
          })),
          variables: variables.map(v => ({
            name: v.name,
            value: v.value,
            type: v.type,
            scope: v.scope,
          })),
        })
      }

      // 执行工作流
      // 传递浏览器配置
      const browserConfig = config.browser ? {
        type: config.browser.type || 'msedge',
        executablePath: config.browser.executablePath || undefined,
        fullscreen: config.browser.fullscreen || false,
        autoCloseBrowser: config.browser.autoCloseBrowser
      } : undefined
      
      console.log('[Toolbar] 执行工作流，无头模式:', headless, '浏览器配置:', browserConfig)
      
      const executeResult = await workflowApi.execute(currentWorkflowId, { 
        headless,
        browserConfig 
      })
      
      if (executeResult.error) {
        addLog({ level: 'error', message: `执行失败: ${executeResult.error}` })
        return
      }

      setExecutionStatus('running')
      addLog({ level: 'info', message: `工作流开始执行${headless ? '（无头模式）' : ''}` })
    } catch (error) {
      addLog({ level: 'error', message: `执行异常: ${error}` })
    }
  }, [nodes, edges, variables, name, workflowId, addLog, clearLogs, clearCollectedData, setBottomPanelTab, setExecutionStatus, config.browser])

  // 普通运行（有头模式）
  const handleRun = useCallback(async () => {
    await executeWorkflow(false)
  }, [executeWorkflow])

  // 无头模式运行
  const handleRunHeadless = useCallback(async () => {
    await executeWorkflow(true)
  }, [executeWorkflow])

  const handleStop = useCallback(async () => {
    if (workflowId) {
      socketService.stopExecution(workflowId)
      await workflowApi.stop(workflowId)
    }
    setExecutionStatus('stopped')
    addLog({ level: 'warning', message: '工作流已停止' })
  }, [workflowId, setExecutionStatus, addLog])

  const handleSave = useCallback(async (skipConfirm = false) => {
    if (nodes.length === 0) {
      if (!skipConfirm) {
        addLog({ level: 'warning', message: '工作流没有任何节点，无法保存' })
      }
      return
    }

    const currentFolder = config.workflow?.localFolder || defaultFolder
    if (!currentFolder) {
      if (!skipConfirm) {
        addLog({ level: 'error', message: '未配置工作流保存路径' })
      }
      return
    }

    // 使用工作流名称作为文件名
    const filename = name || '未命名工作流'
    const workflowData = JSON.parse(exportWorkflow())

    try {
      // 如果不跳过确认，且用户开启了覆盖提示，先检查文件是否已存在
      const showOverwriteConfirm = config.workflow?.showOverwriteConfirm !== false
      console.log('[Toolbar] handleSave 调试:', {
        skipConfirm,
        showOverwriteConfirm,
        configValue: config.workflow?.showOverwriteConfirm,
        willCheckExists: !skipConfirm && showOverwriteConfirm
      })
      
      if (!skipConfirm && showOverwriteConfirm) {
        console.log('[Toolbar] 检查文件是否存在:', filename)
        const API_BASE = getBackendBaseUrl()
        const checkResponse = await fetch(`${API_BASE}/api/local-workflows/check-exists`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename,
            content: { _folder: currentFolder }
          })
        })
        const checkData = await checkResponse.json()
        console.log('[Toolbar] 文件检查结果:', checkData)

        // 如果文件已存在，询问用户是否覆盖
        if (checkData.exists) {
          console.log('[Toolbar] 文件已存在，弹出确认对话框')
          const shouldOverwrite = await confirm(
            `工作流 "${checkData.filename}" 已存在，是否覆盖？`,
            { type: 'warning', title: '文件已存在', confirmText: '覆盖', cancelText: '取消' }
          )
          
          console.log('[Toolbar] 用户选择:', shouldOverwrite ? '覆盖' : '取消')
          
          if (!shouldOverwrite) {
            addLog({ level: 'info', message: '已取消保存' })
            return
          }
        } else {
          console.log('[Toolbar] 文件不存在，直接保存')
        }
      }

      // 执行保存
      const API_BASE = getBackendBaseUrl()
      const response = await fetch(`${API_BASE}/api/local-workflows/save-to-folder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename,
          content: { ...workflowData, _folder: currentFolder }
        })
      })
      const data = await response.json()

      if (data.success) {
        if (!skipConfirm) {
          addLog({ level: 'success', message: `工作流已保存: ${data.filename}` })
        }
        markAsSaved()  // 标记为已保存
      } else {
        if (!skipConfirm) {
          addLog({ level: 'error', message: `保存失败: ${data.error}` })
        }
      }
    } catch (e) {
      if (!skipConfirm) {
        addLog({ level: 'error', message: `保存出错: ${e}` })
      }
    }
  }, [nodes.length, config.workflow?.localFolder, config.workflow?.showOverwriteConfirm, defaultFolder, name, exportWorkflow, addLog, confirm])

  const handleNewWorkflow = useCallback(() => {
    clearWorkflow()
    setWorkflowId(null)
    addLog({ level: 'info', message: '已创建新工作流' })
  }, [clearWorkflow, addLog])

  // 自动保存逻辑
  useEffect(() => {
    // 如果未开启自动保存，直接返回
    if (!config.workflow?.autoSave) return
    
    // 如果没有节点，不自动保存
    if (nodes.length === 0) return
    
    // 防抖：延迟2秒后自动保存
    const timer = setTimeout(() => {
      handleSave(true) // skipConfirm = true，不弹出覆盖提示
    }, 2000)
    
    return () => clearTimeout(timer)
  }, [nodes, edges, name, config.workflow?.autoSave, handleSave])

  // 快捷键监听（F5/Shift+F5 由后端全局热键处理，前端只拦截防止浏览器刷新）
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // F5 和 Shift+F5：只拦截，不执行任何操作（由后端全局热键处理）
      if (e.key === 'F5') {
        e.preventDefault()
        return
      }
      
      // 如果焦点在输入框中，不处理其他快捷键
      const target = e.target as HTMLElement
      const isInInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable
      if (isInInput) return
      
      // Ctrl+S 保存
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault()
        handleSave()
      }
      // Alt+N 新建
      if (e.altKey && e.key === 'n') {
        e.preventDefault()
        handleNewWorkflow()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleSave, handleNewWorkflow])
  
  // 页面关闭/刷新前检查未保存的更改
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      // 只有当有节点且有未保存的更改时才提示
      if (nodes.length > 0 && hasUnsavedChanges) {
        e.preventDefault()
        // 现代浏览器会显示标准提示，自定义消息可能不会显示
        e.returnValue = '工作流有未保存的更改，确定要离开吗？'
        return e.returnValue
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [nodes.length, hasUnsavedChanges])
  
  // 全局热键事件监听（后台热键触发）
  useEffect(() => {
    const handleHotkeyRun = () => {
      console.log('[Toolbar] 收到全局热键运行事件')
      if (!isRunning) {
        handleRun()
      }
    }
    
    const handleHotkeyStop = () => {
      console.log('[Toolbar] 收到全局热键停止事件')
      if (isRunning) {
        handleStop()
      }
    }
    
    window.addEventListener('hotkey:run', handleHotkeyRun)
    window.addEventListener('hotkey:stop', handleHotkeyStop)
    
    return () => {
      window.removeEventListener('hotkey:run', handleHotkeyRun)
      window.removeEventListener('hotkey:stop', handleHotkeyStop)
    }
  }, [isRunning, handleRun, handleStop])
  
  // 通知后端当前工作流ID（用于全局热键控制）
  useEffect(() => {
    // 使用一个固定的标识符，因为工作流可能还没有保存到后端
    socketService.setCurrentWorkflow('current')
  }, [])

  const handleOpen = () => {
    setShowLocalWorkflow(true)
  }

  // 导出为 Playwright Python 代码
  const handleExportPlaywright = useCallback(async () => {
    if (nodes.length === 0) {
      addLog({ level: 'warning', message: '工作流没有任何节点，无法导出' })
      return
    }

    try {
      // 先创建或更新工作流
      let currentWorkflowId = workflowId

      if (!currentWorkflowId) {
        const createResult = await workflowApi.create({
          name,
          nodes: nodes.map(n => ({
            id: n.id,
            type: n.data.moduleType,
            position: n.position,
            data: n.data,
            style: n.style,
          })),
          edges: edges.map(e => ({
            id: e.id,
            source: e.source,
            target: e.target,
            sourceHandle: e.sourceHandle,
            targetHandle: e.targetHandle,
          })),
          variables: variables.map(v => ({
            name: v.name,
            value: v.value,
            type: v.type,
            scope: v.scope,
          })),
        })

        if (createResult.error) {
          addLog({ level: 'error', message: `创建工作流失败: ${createResult.error}` })
          return
        }

        currentWorkflowId = createResult.data!.id
        setWorkflowId(currentWorkflowId)
      } else {
        // 更新现有工作流
        await workflowApi.update(currentWorkflowId, {
          name,
          nodes: nodes.map(n => ({
            id: n.id,
            type: n.data.moduleType,
            position: n.position,
            data: n.data,
            style: n.style,
          })),
          edges: edges.map(e => ({
            id: e.id,
            source: e.source,
            target: e.target,
            sourceHandle: e.sourceHandle,
            targetHandle: e.targetHandle,
          })),
          variables: variables.map(v => ({
            name: v.name,
            value: v.value,
            type: v.type,
            scope: v.scope,
          })),
        })
      }

      // 调用导出 API
      const API_BASE = getBackendBaseUrl()
      const response = await fetch(`${API_BASE}/api/workflows/${currentWorkflowId}/export-playwright`)
      const data = await response.json()

      if (data.code) {
        // 创建下载
        const blob = new Blob([data.code], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = data.filename || `${name.replace(/\s+/g, '_')}_playwright.py`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)

        addLog({ level: 'success', message: `已导出 Playwright 代码: ${data.filename}` })
      } else {
        addLog({ level: 'error', message: '导出失败: 未获取到代码' })
      }
    } catch (e) {
      addLog({ level: 'error', message: `导出出错: ${e}` })
    }
  }, [nodes, edges, variables, name, workflowId, addLog])

  const handleBrowserLog = (level: 'info' | 'success' | 'warning' | 'error', message: string) => {
    addLog({ level, message })
  }

  return (
    <header className="h-14 border-b bg-gradient-to-r from-blue-600 via-cyan-600 to-blue-600 bg-[length:200%_100%] animate-gradient flex items-center px-4 gap-4">
      {/* Logo/标题 */}
      <div className="flex items-center gap-2">
        <div className="p-1 rounded-lg bg-white/20 backdrop-blur-sm">
          <img src="/logo.png" alt="Logo" className="w-5 h-5" />
        </div>
        <span className="font-semibold text-lg text-white drop-shadow-sm">Web RPA</span>
      </div>

      {/* 分隔线 */}
      <div className="h-6 w-px bg-white/30" />

      {/* 工作流名称 */}
      <Input
        value={name}
        onChange={(e) => setWorkflowName(e.target.value)}
        onFocus={handleNameFocus}
        onBlur={handleNameBlur}
        className="w-48 h-8 bg-white/90 border-white/50"
        placeholder="工作流名称"
      />

      {/* 分隔线 */}
      <div className="h-6 w-px bg-white/30" />

      {/* 执行控制 */}
      <div className="flex items-center gap-2">
        {!isRunning ? (
          <>
            <Button 
              size="sm" 
              className="bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400 text-white border-0 
                transition-all duration-200 hover:scale-105 hover:shadow-lg hover:shadow-emerald-500/30
                active:scale-95" 
              onClick={handleRun}
            >
              <Play className="w-4 h-4 mr-1" />
              运行
              <span className="ml-1.5 text-[10px] opacity-70 font-normal">(F5)</span>
            </Button>
            <Button 
              size="sm" 
              className="bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-500 hover:to-slate-600 text-white border-0 
                transition-all duration-200 hover:scale-105 hover:shadow-lg hover:shadow-slate-500/30
                active:scale-95" 
              onClick={handleRunHeadless}
              title="无头模式运行（后台运行，不显示浏览器窗口）"
            >
              <EyeOff className="w-4 h-4 mr-1" />
              无头运行
            </Button>
          </>
        ) : (
          <Button 
            size="sm" 
            className="bg-gradient-to-r from-red-500 to-rose-500 hover:from-red-400 hover:to-rose-400 text-white border-0 
              transition-all duration-200 hover:scale-105 hover:shadow-lg hover:shadow-red-500/30
              active:scale-95 animate-pulse" 
            onClick={handleStop}
          >
            <Square className="w-4 h-4 mr-1" />
            停止
            <span className="ml-1.5 text-[10px] opacity-70 font-normal">(Shift+F5)</span>
          </Button>
        )}
      </div>

      {/* 分隔线 */}
      <div className="h-6 w-px bg-white/30" />

      {/* 文件操作 */}
      <div className="flex items-center gap-1">
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-blue-700 hover:bg-white hover:text-blue-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95" 
          onClick={() => {
            console.log('[Toolbar] 保存按钮被点击')
            handleSave()
          }}
        >
          <Save className="w-4 h-4 mr-1" />
          保存
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-blue-700 hover:bg-white hover:text-blue-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95" 
          onClick={handleOpen}
        >
          <FolderOpen className="w-4 h-4 mr-1" />
          打开
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-green-700 hover:bg-white hover:text-green-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95" 
          onClick={handleExportPlaywright}
        >
          <Code className="w-4 h-4 mr-1" />
          导出
        </Button>
      </div>

      {/* 右侧操作 */}
      <div className="ml-auto flex items-center gap-2">
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-purple-700 hover:bg-white hover:text-purple-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95" 
          onClick={() => setShowWorkflowHub(true)}
        >
          <Package className="w-4 h-4 mr-1" />
          工作流仓库
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="bg-white/90 border-white/50 text-orange-700 hover:bg-white hover:text-orange-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95"
          onClick={() => setShowScheduledTasks(true)}
        >
          <Clock className="w-4 h-4 mr-1" />
          计划任务
        </Button>

        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-cyan-700 hover:bg-white hover:text-cyan-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95" 
          onClick={() => setShowAutoBrowser(true)}
        >
          <Globe className="w-4 h-4 mr-1" />
          自动化浏览器
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-indigo-700 hover:bg-white hover:text-indigo-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95" 
          onClick={() => setShowDocumentation(true)}
        >
          <BookOpen className="w-4 h-4 mr-1" />
          教学文档
        </Button>
        <Button 
          variant="outline" 
          size="sm" 
          className="bg-white/90 border-white/50 text-gray-700 hover:bg-white hover:text-gray-800
            transition-all duration-200 hover:scale-105 hover:shadow-md active:scale-95" 
          onClick={() => setShowGlobalConfig(true)}
        >
          <Settings className="w-4 h-4 mr-1 transition-transform duration-300 hover:rotate-90" />
          全局配置
        </Button>
      </div>

      {/* 全局配置对话框 */}
      <GlobalConfigDialog isOpen={showGlobalConfig} onClose={() => setShowGlobalConfig(false)} />
      
      {/* 教学文档对话框 */}
      <DocumentationDialog isOpen={showDocumentation} onClose={() => setShowDocumentation(false)} />
      
      {/* 自动化浏览器对话框 */}
      <AutoBrowserDialog 
        isOpen={showAutoBrowser} 
        onClose={() => setShowAutoBrowser(false)} 
        onLog={handleBrowserLog}
      />
      
      {/* 工作流仓库对话框 */}
      <WorkflowHubDialog
        open={showWorkflowHub}
        onClose={() => setShowWorkflowHub(false)}
      />
      
      {/* 本地工作流对话框 */}
      <LocalWorkflowDialog
        isOpen={showLocalWorkflow}
        onClose={() => setShowLocalWorkflow(false)}
        onLog={(level, message) => addLog({ level, message })}
      />
      
      {/* 计划任务对话框 */}
      <ScheduledTasksDialog
        open={showScheduledTasks}
        onClose={() => setShowScheduledTasks(false)}
      />
      
      {/* 确认对话框 */}
      {ConfirmDialog}
    </header>
  )
}
