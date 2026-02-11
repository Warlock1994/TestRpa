import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useConfirm } from '@/components/ui/confirm-dialog'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import { useWorkflowStore } from '@/store/workflowStore'
import { X, FileJson, Trash2, RefreshCw, Search } from 'lucide-react'
import { getBackendBaseUrl } from '@/services/config'

interface LocalWorkflowDialogProps {
  isOpen: boolean
  onClose: () => void
  onLog: (level: 'info' | 'success' | 'warning' | 'error', message: string) => void
}

interface WorkflowInfo {
  filename: string
  name: string
  modifiedTime: string
  size: number
}

export function LocalWorkflowDialog({ isOpen, onClose, onLog }: LocalWorkflowDialogProps) {
  const { config } = useGlobalConfigStore()
  const importWorkflow = useWorkflowStore((state) => state.importWorkflow)
  const [workflows, setWorkflows] = useState<WorkflowInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [defaultFolder, setDefaultFolder] = useState('')
  const { confirm, ConfirmDialog } = useConfirm()

  const currentFolder = config.workflow?.localFolder || defaultFolder

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

  // 加载工作流列表
  const loadWorkflows = async () => {
    // 使用当前文件夹或默认文件夹
    const folder = config.workflow?.localFolder || defaultFolder || ''
    
    setLoading(true)
    try {
      const API_BASE = getBackendBaseUrl()
      const response = await fetch(`${API_BASE}/api/local-workflows/list`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder })
      })
      const data = await response.json()
      if (data.workflows) {
        setWorkflows(data.workflows)
      }
    } catch (e) {
      console.error('加载工作流列表失败:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      loadWorkflows()
    }
  }, [isOpen, defaultFolder, config.workflow?.localFolder])

  const handleOpen = async (workflow: WorkflowInfo) => {
    try {
      const API_BASE = getBackendBaseUrl()
      const response = await fetch(
        `${API_BASE}/api/local-workflows/load/${encodeURIComponent(workflow.filename)}?folder=${encodeURIComponent(currentFolder)}`
      )
      const data = await response.json()
      
      if (data.success && data.content) {
        const success = importWorkflow(JSON.stringify(data.content))
        if (success) {
          onLog('success', `已打开工作流: ${workflow.name}`)
          onClose()
        } else {
          onLog('error', '工作流格式无效')
        }
      } else {
        onLog('error', `打开失败: ${data.error}`)
      }
    } catch (e) {
      onLog('error', `打开工作流出错: ${e}`)
    }
  }

  const handleDelete = async (workflow: WorkflowInfo) => {
    const confirmed = await confirm(`确定要删除工作流 "${workflow.name}" 吗？`, {
      type: 'warning',
      title: '删除工作流'
    })
    
    if (confirmed) {
      try {
        const API_BASE = getBackendBaseUrl()
        const response = await fetch(
          `${API_BASE}/api/local-workflows/delete?filename=${encodeURIComponent(workflow.filename)}&folder=${encodeURIComponent(currentFolder)}`,
          { method: 'POST' }
        )
        const data = await response.json()
        
        if (data.success) {
          onLog('success', `已删除工作流: ${workflow.name}`)
          loadWorkflows()
        } else {
          onLog('error', `删除失败: ${data.error}`)
        }
      } catch (e) {
        onLog('error', `删除工作流出错: ${e}`)
      }
    }
  }

  const filteredWorkflows = workflows.filter(w =>
    w.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    w.filename.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white text-black border border-gray-200 rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden animate-scale-in">
        {/* 标题栏 */}
        <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-blue-50 via-cyan-50/50 to-blue-50">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
              <FileJson className="w-4 h-4 text-white" />
            </div>
            <h3 className="font-semibold text-gradient">打开本地工作流</h3>
          </div>
          <Button variant="ghost" size="icon" className="text-gray-600 hover:text-gray-900 hover:bg-white/50" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* 工具栏 */}
        <div className="p-3 border-b bg-gradient-to-r from-gray-50 to-blue-50/30 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="搜索工作流..."
              className="pl-9 bg-white border-gray-300"
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            className="border-gray-300 hover:bg-blue-50"
            onClick={loadWorkflows}
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>

        {/* 文件夹路径 */}
        <div className="px-4 py-2 bg-gradient-to-r from-gray-100 to-blue-50/50 text-xs text-gray-600 truncate">
          📁 {currentFolder || '加载中...'}
        </div>

        {/* 工作流列表 */}
        <div className="max-h-[400px] overflow-y-auto">
          {loading ? (
            <div className="p-8 text-center text-gray-500">加载中...</div>
          ) : filteredWorkflows.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              {searchTerm ? '没有找到匹配的工作流' : '文件夹中没有工作流文件'}
            </div>
          ) : (
            <div className="divide-y">
              {filteredWorkflows.map((workflow) => (
                <div
                  key={workflow.filename}
                  className="p-3 hover:bg-blue-50 cursor-pointer flex items-center gap-3 group"
                  onClick={() => handleOpen(workflow)}
                >
                  <FileJson className="w-8 h-8 text-blue-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 truncate">{workflow.name}</div>
                    <div className="text-xs text-gray-500 flex gap-3">
                      <span>{workflow.filename}</span>
                      <span>{workflow.modifiedTime}</span>
                      <span>{formatSize(workflow.size)}</span>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 hover:bg-red-50"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(workflow)
                    }}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 底部 */}
        <div className="p-3 border-t bg-gray-50 flex justify-between items-center">
          <span className="text-xs text-gray-500">
            共 {filteredWorkflows.length} 个工作流
          </span>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
        </div>
      </div>
      
      <ConfirmDialog />
    </div>
  )
}
