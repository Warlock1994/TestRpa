import { io, Socket } from 'socket.io-client'
import { useWorkflowStore } from '@/store/workflowStore'
import type { LogLevel } from '@/types'
import { getBackendBaseUrl } from './config'

// 动态获取 Socket 连接地址
function getSocketUrl(): string {
  return getBackendBaseUrl()
}

let SOCKET_URL = getSocketUrl()

// 更新 Socket 连接地址（当获取到配置后调用）
export function updateSocketUrl() {
  SOCKET_URL = getSocketUrl()
}

// 输入弹窗回调
type InputPromptCallback = (data: {
  requestId: string
  variableName: string
  title: string
  message: string
  defaultValue: string
  inputMode: 'single' | 'list'
}) => void

// 浏览器被占用错误回调
type BrowserBusyCallback = () => void

// 浏览器意外关闭回调
type BrowserClosedCallback = () => void

// 全局音频播放器（用于管理播放状态）
let currentAudio: HTMLAudioElement | null = null

// 数据行批量处理缓冲区 - 已移除，不再使用
// let dataRowBuffer: Record<string, unknown>[] = []
// let dataRowFlushTimer: ReturnType<typeof setTimeout> | null = null
// const DATA_ROW_FLUSH_INTERVAL = 16
// const DATA_ROW_BATCH_SIZE = 50

// 是否正在执行中（用于控制是否接收实时数据行）
let isExecuting = false

class SocketService {
  private socket: Socket | null = null
  private connected = false
  private inputPromptCallback: InputPromptCallback | null = null
  private browserBusyCallback: BrowserBusyCallback | null = null
  private browserClosedCallback: BrowserClosedCallback | null = null

  // 设置输入弹窗回调
  setInputPromptCallback(callback: InputPromptCallback | null) {
    this.inputPromptCallback = callback
  }

  // 设置浏览器被占用错误回调
  setBrowserBusyCallback(callback: BrowserBusyCallback | null) {
    this.browserBusyCallback = callback
  }

  // 设置浏览器意外关闭回调
  setBrowserClosedCallback(callback: BrowserClosedCallback | null) {
    this.browserClosedCallback = callback
  }

  // 发送输入结果
  sendInputResult(requestId: string, value: string | null) {
    if (this.socket?.connected) {
      this.socket.emit('input_prompt_result', { requestId, value })
    }
  }

  // 发送语音合成结果
  sendTTSResult(requestId: string, success: boolean) {
    if (this.socket?.connected) {
      this.socket.emit('tts_result', { requestId, success })
    }
  }

  // 发送JS脚本执行结果
  sendJsScriptResult(requestId: string, success: boolean, result?: unknown, error?: string) {
    if (this.socket?.connected) {
      this.socket.emit('js_script_result', { requestId, success, result, error })
    }
  }

  // 发送音乐播放结果
  sendPlayMusicResult(requestId: string, success: boolean, error?: string) {
    if (this.socket?.connected) {
      this.socket.emit('play_music_result', { requestId, success, error })
    }
  }

  // 发送视频播放结果
  sendPlayVideoResult(requestId: string, success: boolean, error?: string) {
    if (this.socket?.connected) {
      this.socket.emit('play_video_result', { requestId, success, error })
    }
  }

  // 发送图片查看结果
  sendViewImageResult(requestId: string, success: boolean, error?: string) {
    if (this.socket?.connected) {
      this.socket.emit('view_image_result', { requestId, success, error })
    }
  }

  // 播放音乐 - 显示播放器弹窗
  private playMusic(data: {
    requestId: string
    audioUrl: string
    waitForEnd: boolean
  }) {
    try {
      // 停止之前的音频
      if (currentAudio) {
        currentAudio.pause()
        currentAudio = null
      }

      // 使用播放器弹窗
      import('@/components/workflow/MusicPlayerDialog').then(({ showMusicPlayer }) => {
        showMusicPlayer(
          {
            audioUrl: data.audioUrl,
            requestId: data.requestId,
            waitForEnd: data.waitForEnd
          },
          (success, error) => {
            this.sendPlayMusicResult(data.requestId, success, error)
          }
        )
      }).catch(err => {
        // 如果导入失败，回退到简单播放
        console.error('加载播放器失败，使用简单播放:', err)
        this.playMusicSimple(data)
      })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err)
      this.sendPlayMusicResult(data.requestId, false, errorMsg)
    }
  }

  // 简单播放（备用方案）
  private playMusicSimple(data: {
    requestId: string
    audioUrl: string
    waitForEnd: boolean
  }) {
    try {
      const audio = new Audio(data.audioUrl)
      currentAudio = audio

      if (data.waitForEnd) {
        audio.onended = () => {
          this.sendPlayMusicResult(data.requestId, true)
          currentAudio = null
        }
        audio.onerror = () => {
          this.sendPlayMusicResult(data.requestId, false, '音频加载或播放失败')
          currentAudio = null
        }
        audio.play().catch((err) => {
          this.sendPlayMusicResult(data.requestId, false, err.message)
          currentAudio = null
        })
      } else {
        audio.play().catch((err) => {
          console.error('播放音乐失败:', err)
        })
        this.sendPlayMusicResult(data.requestId, true)
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err)
      this.sendPlayMusicResult(data.requestId, false, errorMsg)
    }
  }

  // 播放视频 - 显示播放器弹窗
  private playVideo(data: {
    requestId: string
    videoUrl: string
    waitForEnd: boolean
  }) {
    try {
      import('@/components/workflow/VideoPlayerDialog').then(({ showVideoPlayer }) => {
        showVideoPlayer(
          {
            videoUrl: data.videoUrl,
            requestId: data.requestId,
            waitForEnd: data.waitForEnd
          },
          (success, error) => {
            this.sendPlayVideoResult(data.requestId, success, error)
          }
        )
      }).catch(err => {
        const errorMsg = err instanceof Error ? err.message : String(err)
        this.sendPlayVideoResult(data.requestId, false, `加载播放器失败: ${errorMsg}`)
      })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err)
      this.sendPlayVideoResult(data.requestId, false, errorMsg)
    }
  }

  // 查看图片 - 显示图片查看器弹窗
  private viewImage(data: {
    requestId: string
    imageUrl: string
    autoClose: boolean
    displayTime: number
  }) {
    try {
      import('@/components/workflow/ImageViewerDialog').then(({ showImageViewer }) => {
        showImageViewer(
          {
            imageUrl: data.imageUrl,
            requestId: data.requestId,
            autoClose: data.autoClose,
            displayTime: data.displayTime
          },
          (success, error) => {
            this.sendViewImageResult(data.requestId, success, error)
          }
        )
      }).catch(err => {
        const errorMsg = err instanceof Error ? err.message : String(err)
        this.sendViewImageResult(data.requestId, false, `加载图片查看器失败: ${errorMsg}`)
      })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err)
      this.sendViewImageResult(data.requestId, false, errorMsg)
    }
  }

  // 执行语音合成
  private executeTTS(data: {
    requestId: string
    text: string
    lang: string
    rate: number
    pitch: number
    volume: number
  }) {
    try {
      const utterance = new SpeechSynthesisUtterance(data.text)
      utterance.lang = data.lang
      utterance.rate = data.rate
      utterance.pitch = data.pitch
      utterance.volume = data.volume

      utterance.onend = () => {
        this.sendTTSResult(data.requestId, true)
      }

      utterance.onerror = () => {
        this.sendTTSResult(data.requestId, false)
      }

      // 取消之前的语音
      window.speechSynthesis.cancel()
      window.speechSynthesis.speak(utterance)
    } catch {
      this.sendTTSResult(data.requestId, false)
    }
  }

  // 执行JS脚本
  private executeJsScript(data: {
    requestId: string
    code: string
    variables: Record<string, unknown>
  }) {
    try {
      // 创建一个包含用户代码的函数
      // 用户代码中应该定义 main(vars) 函数
      const wrappedCode = `
        ${data.code}
        
        // 调用 main 函数并返回结果
        if (typeof main === 'function') {
          return main(vars);
        } else {
          throw new Error('未找到 main 函数，请确保代码中定义了 main(vars) 函数');
        }
      `
      
      // 使用 Function 构造器创建函数，传入 vars 参数
      // eslint-disable-next-line @typescript-eslint/no-implied-eval
      const fn = new Function('vars', wrappedCode)
      const result = fn(data.variables)
      
      this.sendJsScriptResult(data.requestId, true, result)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      this.sendJsScriptResult(data.requestId, false, undefined, errorMessage)
    }
  }

  connect() {
    if (this.socket?.connected) {
      return
    }

    // 如果已有socket实例，先清理
    if (this.socket) {
      this.socket.removeAllListeners()
      this.socket.disconnect()
      this.socket = null
    }

    this.socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      timeout: 120000,  // 连接超时 120秒
    })

    this.socket.on('connect', () => {
      console.log('Socket connected')
      this.connected = true
      
      // 连接后同步 verboseLog 状态到后端
      const verboseLog = useWorkflowStore.getState().verboseLog
      this.socket?.emit('set_verbose_log', { enabled: verboseLog })
      
      // 连接后设置当前工作流ID（用于全局热键控制）
      this.socket?.emit('set_current_workflow', { workflowId: 'current' })
      
      // 重连后，如果之前是 running 状态，重置为 pending
      // 因为可能错过了 completed 事件
      const currentStatus = useWorkflowStore.getState().executionStatus
      if (currentStatus === 'running') {
        console.log('[Socket] 重连后检测到 running 状态，重置为 completed')
        useWorkflowStore.getState().setExecutionStatus('completed')
        isExecuting = false
      }
    })

    this.socket.on('disconnect', (reason) => {
      console.log('Socket disconnected, reason:', reason)
      this.connected = false
      
      // 如果是执行中断开，标记需要在重连后检查状态
      if (isExecuting) {
        console.log('[Socket] 执行中断开连接，将在重连后重置状态')
      }
    })

    // 执行开始
    this.socket.on('execution:started', (data: { workflowId: string }) => {
      console.log('Execution started:', data.workflowId)
      isExecuting = true
      useWorkflowStore.getState().setExecutionStatus('running')
      // 清空之前的数据
      useWorkflowStore.getState().clearCollectedData()
      // ❌ 不要清空变量列表！变量应该保留，由后端的 variable_update 事件更新
      // useWorkflowStore.setState({ variables: [] })
    })

    // 日志消息 - 🔥 完全实时显示，立即添加，不使用任何批处理！
    this.socket.on('execution:log', (data: {
      workflowId: string
      log: {
        id: string
        timestamp: string
        level: LogLevel
        nodeId?: string
        message: string
        duration?: number
        isUserLog?: boolean  // 是否是用户打印的日志（打印日志模块）
        isSystemLog?: boolean  // 是否是系统日志（流程开始/结束等）
      }
    }) => {
      console.log('[Socket] 🔥 收到日志:', data.log.message, '| level:', data.log.level, '| isUserLog:', data.log.isUserLog, '| isSystemLog:', data.log.isSystemLog)
      const verboseLog = useWorkflowStore.getState().verboseLog
      console.log('[Socket] verboseLog 状态:', verboseLog)
      const log = data.log
      
      // 检测浏览器相关错误
      if (log.level === 'error' && log.message) {
        // 浏览器被关闭的模式（运行中用户手动关闭浏览器）- 只在执行中才触发
        const browserClosedPatterns = [
          'Target page, context or browser has been closed',
          'browser has been closed',
          'Browser closed',
          'Page closed',
        ]
        
        // 浏览器启动失败/被占用的模式（启动时出错）
        const browserStartFailedPatterns = [
          'launch_persistent_context',
          '无法启动持久化浏览器',
          '浏览器数据目录被占用',
          'user-data-dir',
          '浏览器启动后立即关闭',
          '打开浏览器失败',
          '浏览器启动超时',
        ]
        
        const isBrowserClosed = browserClosedPatterns.some(pattern => 
          log.message.includes(pattern)
        )
        const isBrowserStartFailed = browserStartFailedPatterns.some(pattern => 
          log.message.includes(pattern)
        )
        
        // 如果是运行中浏览器被关闭（不是启动失败），触发浏览器关闭回调
        if (isBrowserClosed && !isBrowserStartFailed && isExecuting && this.browserClosedCallback) {
          this.browserClosedCallback()
        }
        // 启动时浏览器启动失败/被占用才弹窗提示
        else if (isBrowserStartFailed && this.browserBusyCallback) {
          this.browserBusyCallback()
        }
      }
      
      // 简洁日志模式下，显示：用户日志、系统日志、错误日志
      if (!verboseLog && !log.isUserLog && !log.isSystemLog && log.level !== 'error') {
        console.log('[Socket] ❌ 日志被过滤（简洁模式）')
        return
      }
      
      console.log('[Socket] ✅ 日志通过过滤，准备添加到 store')
      
      // 🔥 立即添加日志，完全实时，不使用任何批处理或延迟！
      useWorkflowStore.getState().addLog({
        level: log.level,
        message: log.message,
        nodeId: log.nodeId,
        duration: log.duration,
      })
      
      console.log('[Socket] ✅ 日志已添加到 store')
    })

    // 输入弹窗请求
    this.socket.on('execution:input_prompt', (data: {
      requestId: string
      variableName: string
      title: string
      message: string
      defaultValue: string
      inputMode?: 'single' | 'list'
    }) => {
      if (this.inputPromptCallback) {
        this.inputPromptCallback({
          ...data,
          inputMode: data.inputMode || 'single'
        })
      }
    })

    // 语音合成请求
    this.socket.on('execution:tts_request', (data: {
      requestId: string
      text: string
      lang: string
      rate: number
      pitch: number
      volume: number
    }) => {
      this.executeTTS(data)
    })

    // JS脚本执行请求
    this.socket.on('execution:js_script', (data: {
      requestId: string
      code: string
      variables: Record<string, unknown>
    }) => {
      this.executeJsScript(data)
    })

    // 播放音乐请求
    this.socket.on('execution:play_music', (data: {
      requestId: string
      audioUrl: string
      waitForEnd: boolean
    }) => {
      this.playMusic(data)
    })

    // 播放视频请求
    this.socket.on('execution:play_video', (data: {
      requestId: string
      videoUrl: string
      waitForEnd: boolean
    }) => {
      this.playVideo(data)
    })

    // 查看图片请求
    this.socket.on('execution:view_image', (data: {
      requestId: string
      imageUrl: string
      autoClose: boolean
      displayTime: number
    }) => {
      this.viewImage(data)
    })

    // 执行完成
    this.socket.on('execution:completed', (data: {
      workflowId: string
      result: {
        status: string
        executedNodes: number
        failedNodes: number
        dataFile?: string
      }
      collectedData?: Record<string, unknown>[]
    }) => {
      console.log('[Socket] 🔥 收到 execution:completed 事件 - 后端执行完成！', data)
      
      // 🔥 停止接收实时数据行
      isExecuting = false
      
      const status = data.result.status as 'completed' | 'failed' | 'stopped'
      console.log('[Socket] 🔥 立即设置执行状态为:', status)
      
      // 🔥 立即更新所有状态
      const store = useWorkflowStore.getState()
      store.setExecutionStatus(status)
      
      // 🔥 处理收集的数据（如果有）
      if (data.collectedData && data.collectedData.length > 0) {
        console.log('[Socket] 收到收集的数据:', data.collectedData.length, '条')
        store.setCollectedData(data.collectedData)
      }
      
      // 🔥 触发全局事件，通知所有组件执行已完成
      window.dispatchEvent(new CustomEvent('execution:completed', { 
        detail: { status, executedNodes: data.result.executedNodes, failedNodes: data.result.failedNodes } 
      }))
      
      // 🔥 停止所有音频播放
      this.stopAllAudio()
      
      // 🔥 添加完成日志
      store.addLog({
        level: status === 'completed' ? 'success' : 'error',
        message: `🎉 执行${status === 'completed' ? '完成' : '失败'}，共执行 ${data.result.executedNodes} 个节点，失败 ${data.result.failedNodes} 个`,
      })
      
      console.log('[Socket] 🔥 前端状态已全部更新完成！')
    })

    // 数据行收集 - 实时显示
    this.socket.on('execution:data_row', (data: {
      workflowId: string
      row: Record<string, unknown>
    }) => {
      if (!isExecuting) return
      
      console.log('[Socket] 收到数据行:', data.row)
      const store = useWorkflowStore.getState()
      store.addDataRow(data.row)
    })

    // 执行停止
    this.socket.on('execution:stopped', (_data: { workflowId: string }) => {
      isExecuting = false  // 停止接收实时数据行
      // 停止所有音频播放
      this.stopAllAudio()
      useWorkflowStore.getState().setExecutionStatus('stopped')
    })
    
    // 热键触发运行工作流
    this.socket.on('hotkey:run_workflow', (_data: { workflowId: string }) => {
      console.log('[Hotkey] 收到运行工作流请求')
      // 触发全局事件，让 Toolbar 组件处理
      window.dispatchEvent(new CustomEvent('hotkey:run'))
    })
    
    // 热键触发停止工作流
    this.socket.on('hotkey:stop_workflow', (_data: { workflowId: string }) => {
      console.log('[Hotkey] 收到停止工作流请求')
      window.dispatchEvent(new CustomEvent('hotkey:stop'))
    })
    
    // 热键提示没有活动工作流
    this.socket.on('hotkey:no_workflow', () => {
      console.log('[Hotkey] 没有活动的工作流')
    })
    
    // 热键触发开始录制宏 (F9)
    this.socket.on('hotkey:macro_start', () => {
      console.log('[Hotkey] 收到开始录制宏请求')
      window.dispatchEvent(new CustomEvent('hotkey:macro_start'))
    })
    
    // 热键触发停止录制宏 (F10)
    this.socket.on('hotkey:macro_stop', () => {
      console.log('[Hotkey] 收到停止录制宏请求')
      window.dispatchEvent(new CustomEvent('hotkey:macro_stop'))
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.removeAllListeners()
      this.socket.disconnect()
      this.socket = null
      this.connected = false
    }
    isExecuting = false
  }

  isConnected() {
    return this.connected
  }

  // 停止所有音频/视频播放
  private stopAllAudio() {
    if (currentAudio) {
      currentAudio.pause()
      currentAudio.currentTime = 0
      currentAudio = null
    }
    // 同时停止语音合成
    window.speechSynthesis.cancel()
    // 关闭音乐播放器弹窗
    import('@/components/workflow/MusicPlayerDialog').then(({ hideMusicPlayer }) => {
      hideMusicPlayer()
    }).catch(() => {})
    // 关闭视频播放器弹窗
    import('@/components/workflow/VideoPlayerDialog').then(({ hideVideoPlayer }) => {
      hideVideoPlayer()
    }).catch(() => {})
    // 关闭图片查看器弹窗
    import('@/components/workflow/ImageViewerDialog').then(({ hideImageViewer }) => {
      hideImageViewer()
    }).catch(() => {})
  }

  // 发送停止执行请求
  stopExecution(workflowId: string) {
    // 停止所有音频
    this.stopAllAudio()
    if (this.socket?.connected) {
      this.socket.emit('execution_stop', { workflowId })
    }
  }

  // 设置详细日志开关状态（同步到后端）
  setVerboseLog(enabled: boolean) {
    if (this.socket?.connected) {
      this.socket.emit('set_verbose_log', { enabled })
    }
  }
  
  // 设置当前活动的工作流ID（用于全局热键控制）
  setCurrentWorkflow(workflowId: string | null) {
    if (this.socket?.connected) {
      this.socket.emit('set_current_workflow', { workflowId })
    }
  }
}

export const socketService = new SocketService()
