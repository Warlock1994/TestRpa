import { useState, useEffect, useRef } from 'react'
import { X, Globe, MousePointer, Copy, Check, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { UrlInput } from '@/components/ui/url-input'
import { browserApi } from '@/services/api'
import { useGlobalConfigStore } from '@/store/globalConfigStore'

interface AutoBrowserDialogProps {
  isOpen: boolean
  onClose: () => void
  onLog: (level: 'info' | 'success' | 'warning' | 'error', message: string) => void
}

export function AutoBrowserDialog({ isOpen, onClose, onLog }: AutoBrowserDialogProps) {
  const [browserOpen, setBrowserOpen] = useState(false)
  const [pickerActive, setPickerActive] = useState(false)
  const [loading, setLoading] = useState(false)
  const [url, setUrl] = useState('')
  const [copied, setCopied] = useState(false)
  const [lastSelector, setLastSelector] = useState('')
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const { config } = useGlobalConfigStore()

  // 检查浏览器状态
  const checkStatus = async () => {
    try {
      const result = await browserApi.getStatus()
      if (result.data) {
        setBrowserOpen(result.data.isOpen)
        setPickerActive(result.data.pickerActive)
      }
    } catch {
      setBrowserOpen(false)
      setPickerActive(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      checkStatus()
    }
  }, [isOpen])

  // 轮询检查选择结果
  useEffect(() => {
    if (pickerActive) {
      pollingRef.current = setInterval(async () => {
        // 检查单元素选择
        const singleResult = await browserApi.getSelectedElement()
        if (singleResult.data?.selected && singleResult.data.element) {
          const selector = singleResult.data.element.selector
          setLastSelector(selector)
          onLog('success', `已选择元素: ${selector}`)
        }

        // 检查相似元素选择
        const similarResult = await browserApi.getSimilarElements()
        if (similarResult.data?.selected && similarResult.data.similar) {
          const pattern = similarResult.data.similar.pattern
          const count = similarResult.data.similar.count
          setLastSelector(pattern)
          onLog('success', `已选择 ${count} 个相似元素: ${pattern}`)
        }
      }, 500)
    } else {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [pickerActive, onLog])

  const copyToClipboard = async (text: string) => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text)
      } else {
        const textArea = document.createElement('textarea')
        textArea.value = text
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand('copy')
        textArea.remove()
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      onLog('success', '已复制到剪贴板')
    } catch {
      onLog('error', '复制失败')
    }
  }

  const handleOpenBrowser = async () => {
    setLoading(true)
    try {
      // 传递浏览器配置
      const browserConfig = config.browser ? {
        type: config.browser.type || 'msedge',
        executablePath: config.browser.executablePath || undefined,
        userDataDir: config.browser.userDataDir || undefined,
        fullscreen: config.browser.fullscreen || false
      } : undefined
      
      const result = await browserApi.open(url || undefined, browserConfig)
      if (result.error) {
        onLog('error', `打开浏览器失败: ${result.error}`)
      } else {
        setBrowserOpen(true)
        const browserName = config.browser?.type === 'chrome' ? 'Chrome' : 
                           config.browser?.type === 'firefox' ? 'Firefox' :
                           config.browser?.type === 'chromium' ? 'Chromium' : 'Edge'
        onLog('success', `自动化浏览器(${browserName})已打开，登录状态将自动保存`)
      }
    } catch (error) {
      onLog('error', `打开浏览器异常: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  const handleCloseBrowser = async () => {
    setLoading(true)
    try {
      await browserApi.close()
      setBrowserOpen(false)
      setPickerActive(false)
      onLog('info', '浏览器已关闭')
    } catch (error) {
      onLog('error', `关闭浏览器失败: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  const handleNavigate = async () => {
    if (!url) return
    try {
      const result = await browserApi.navigate(url)
      if (result.error) {
        onLog('error', `导航失败: ${result.error}`)
      } else {
        onLog('info', `已导航到: ${url}`)
      }
    } catch (error) {
      onLog('error', `导航异常: ${error}`)
    }
  }



  const handleStartPicker = async () => {
    try {
      const result = await browserApi.startPicker()
      if (result.error) {
        onLog('error', `启动选择器失败: ${result.error}`)
      } else {
        setPickerActive(true)
        onLog('info', '元素选择器已启动 - Ctrl+点击选择单个元素，Alt+点击选择相似元素')
      }
    } catch (error) {
      onLog('error', `启动选择器异常: ${error}`)
    }
  }

  const handleStopPicker = async () => {
    try {
      await browserApi.stopPicker()
      setPickerActive(false)
      onLog('info', '元素选择器已停止')
    } catch {
      setPickerActive(false)
    }
  }

  if (!isOpen) return null

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 animate-fade-in"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-xl shadow-2xl w-[500px] max-h-[90vh] flex flex-col overflow-hidden animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between px-4 py-3 border-b bg-gradient-to-r from-cyan-50 via-blue-50/50 to-cyan-50 flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-500">
              <Globe className="w-4 h-4 text-white" />
            </div>
            <h3 className="font-medium text-gradient">自动化浏览器</h3>
            {browserOpen && (
              <span className="px-2 py-0.5 text-xs bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 rounded-full border border-green-200/50">
                已打开
              </span>
            )}
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-white/50 rounded-md transition-colors">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* 内容 - 添加滚动条 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* 说明 */}
          <div className="p-3 bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200/50 rounded-xl text-sm text-blue-800">
            <p className="font-medium mb-1">功能说明：</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>在此浏览器中登录的账号，运行工作流时会自动保持登录状态</li>
              <li>支持元素选择器，选中后自动复制选择器到剪贴板</li>
              <li>相似元素选择会自动使用 {'{index}'} 变量替换变化部分</li>
              <li className="font-medium text-cyan-700">
                💡 按 <kbd className="px-1.5 py-0.5 bg-cyan-100 border border-cyan-300 rounded text-[10px] font-mono">Alt+X</kbd> 可使用高级元素选择器（推荐）
              </li>
            </ul>
          </div>

          {/* URL 输入 - 仅在浏览器打开后显示 */}
          {browserOpen && (
            <>
              {/* Alt+X 快捷键提示 */}
              <div className="p-3 bg-gradient-to-r from-orange-50 via-amber-50 to-yellow-50 border border-orange-200/50 rounded-xl">
                <div className="flex items-start gap-2">
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center">
                    <span className="text-white text-lg">✨</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-purple-900 mb-1">高级元素选择器</p>
                    <p className="text-xs text-purple-700 mb-2">
                      在浏览器中按 <kbd className="px-2 py-1 bg-white border-2 border-purple-300 rounded shadow-sm text-xs font-bold text-purple-700">Alt+X</kbd> 激活智能元素定位助手
                    </p>
                    <div className="flex flex-wrap gap-1 text-[10px] text-purple-600">
                      <span className="px-1.5 py-0.5 bg-purple-100 rounded">🎯 智能选择器生成</span>
                      <span className="px-1.5 py-0.5 bg-purple-100 rounded">📋 批量收集管理</span>
                      <span className="px-1.5 py-0.5 bg-purple-100 rounded">🎨 可拖拽面板</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">导航到网址</label>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <UrlInput
                      value={url}
                      onChange={setUrl}
                      placeholder="https://example.com"
                    />
                  </div>
                  <Button variant="outline" size="sm" className="border-blue-200 text-blue-600 hover:bg-blue-50" onClick={handleNavigate} disabled={!url}>
                    跳转
                  </Button>
                </div>
              </div>
            </>
          )}

          {/* 浏览器控制 */}
          <div className="flex gap-2">
            {!browserOpen ? (
              <Button onClick={handleOpenBrowser} disabled={loading} className="flex-1 bg-green-600 hover:bg-green-700 text-white">
                <Globe className="w-4 h-4 mr-2" />
                {loading ? '打开中...' : '打开浏览器'}
              </Button>
            ) : (
              <>
                <Button variant="outline" className="flex-1 border-red-200 text-red-600 hover:bg-red-50" onClick={handleCloseBrowser} disabled={loading}>
                  关闭浏览器
                </Button>
                <Button variant="outline" className="border-gray-200 text-gray-600 hover:bg-gray-50" onClick={checkStatus}>
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </>
            )}
          </div>

          {/* 元素选择器 */}
          {browserOpen && (
            <div className="space-y-3 pt-2 border-t">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">元素选择器</span>
                {pickerActive ? (
                  <Button variant="destructive" size="sm" onClick={handleStopPicker}>
                    停止选择
                  </Button>
                ) : (
                  <Button size="sm" className="bg-cyan-600 hover:bg-cyan-700 text-white" onClick={handleStartPicker}>
                    <MousePointer className="w-4 h-4 mr-1" />
                    启动选择器
                  </Button>
                )}
              </div>

              {pickerActive && (
                <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg text-sm">
                  <p className="font-medium text-orange-800 mb-2">选择器已激活</p>
                  <ul className="text-xs text-orange-700 space-y-1">
                    <li>• <kbd className="px-1 bg-orange-100 rounded">Ctrl</kbd> + 点击：选择单个元素</li>
                    <li>• 按住 <kbd className="px-1 bg-orange-100 rounded">Alt</kbd> 依次点击两个相似元素，自动识别并选择所有相似元素</li>
                    <li>• 按 <kbd className="px-1 bg-orange-100 rounded">Esc</kbd> 取消相似元素选择</li>
                  </ul>
                </div>
              )}

              {/* 最近复制的选择器 */}
              {lastSelector && (
                <div className="space-y-1">
                  <label className="text-xs text-gray-500">最近复制的选择器：</label>
                  <div className="flex items-center gap-2 p-2 bg-gray-50 rounded border">
                    <code className="flex-1 text-xs text-blue-600 truncate" title={lastSelector}>
                      {lastSelector}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={() => copyToClipboard(lastSelector)}
                    >
                      {copied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 底部 */}
        <div className="px-4 py-3 border-t bg-gray-50 rounded-b-lg flex justify-end flex-shrink-0">
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
        </div>
      </div>
    </div>
  )
}
