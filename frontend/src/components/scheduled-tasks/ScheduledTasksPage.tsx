import { useEffect, useState } from 'react'
import { useScheduledTaskStore, type ScheduledTask } from '@/store/scheduledTaskStore'
import { Button } from '@/components/ui/button'
import { Plus, Play, Trash2, Edit, Clock, Zap, Power, BarChart3, FileText, X, Square } from 'lucide-react'
import { TaskCreateDialog } from './TaskCreateDialog'
import { TaskEditDialog } from './TaskEditDialog'
import { TaskLogsDialog } from './TaskLogsDialog'
import { StatisticsPanel } from './StatisticsPanel'
import { useConfirm } from '@/components/ui/confirm-dialog'

interface ScheduledTasksPageProps {
  onClose?: () => void
}

export function ScheduledTasksPage({ onClose }: ScheduledTasksPageProps = {}) {
  const {
    tasks,
    loading,
    fetchTasks,
    deleteTask,
    toggleTask,
    executeTask,
    stopTask,
    fetchStatistics
  } = useScheduledTaskStore()
  
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editingTask, setEditingTask] = useState<ScheduledTask | null>(null)
  const [logsTask, setLogsTask] = useState<ScheduledTask | null>(null)
  const [showStatistics, setShowStatistics] = useState(false)
  
  const { confirm, ConfirmDialog } = useConfirm()
  
  useEffect(() => {
    fetchTasks()
    fetchStatistics()
    
    // 每30秒刷新一次
    const interval = setInterval(() => {
      fetchTasks()
      fetchStatistics()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])
  
  const handleDelete = async (task: ScheduledTask) => {
    const confirmed = await confirm(
      `确定要删除任务"${task.name}"吗？此操作无法撤销。`,
      {
        title: '删除计划任务',
        confirmText: '删除',
        cancelText: '取消',
        type: 'warning'
      }
    )
    
    if (confirmed) {
      await deleteTask(task.id)
    }
  }
  
  const handleToggle = async (task: ScheduledTask) => {
    await toggleTask(task.id, !task.enabled)
  }
  
  const handleExecute = async (task: ScheduledTask) => {
    await executeTask(task.id)
  }
  
  const handleStop = async (task: ScheduledTask) => {
    const confirmed = await confirm(
      `确定要停止任务"${task.name}"的执行吗？`,
      {
        title: '停止任务',
        confirmText: '停止',
        cancelText: '取消',
        type: 'warning'
      }
    )
    
    if (confirmed) {
      await stopTask(task.id)
    }
  }
  
  const getTriggerTypeLabel = (type: string) => {
    switch (type) {
      case 'time': return '时间触发'
      case 'hotkey': return '热键触发'
      case 'startup': return '启动触发'
      default: return type
    }
  }
  
  const getTriggerDescription = (task: ScheduledTask) => {
    const trigger = task.trigger
    
    if (trigger.type === 'time') {
      switch (trigger.schedule_type) {
        case 'once':
          return `一次性 - ${trigger.start_date} ${trigger.start_time}`
        case 'daily':
          return `每天 ${trigger.daily_time}`
        case 'weekly':
          const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
          const dayLabels = trigger.weekly_days?.map(d => days[d]).join(', ')
          return `每周 ${dayLabels} ${trigger.weekly_time}`
        case 'monthly':
          return `每月 ${trigger.monthly_day}日 ${trigger.monthly_time}`
        case 'interval':
          return `每隔 ${trigger.interval_seconds}秒`
        default:
          return '时间触发'
      }
    } else if (trigger.type === 'hotkey') {
      return `热键: ${trigger.hotkey}`
    } else if (trigger.type === 'startup') {
      return `启动后 ${trigger.startup_delay || 0}秒`
    }
    
    return '-'
  }
  
  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }
  
  const getSuccessRate = (task: ScheduledTask) => {
    if (task.total_executions === 0) return 0
    return Math.round((task.success_executions / task.total_executions) * 100)
  }
  
  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* 头部 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">计划任务</h1>
            <p className="text-sm text-gray-500 mt-1">
              管理定时任务、热键触发和启动任务
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setShowStatistics(true)}
              className="gap-2"
            >
              <BarChart3 className="w-4 h-4" />
              统计信息
            </Button>
            <Button
              onClick={() => setCreateDialogOpen(true)}
              className="gap-2"
            >
              <Plus className="w-4 h-4" />
              创建任务
            </Button>
            {onClose && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </Button>
            )}
          </div>
        </div>
      </div>
      
      {/* 任务列表 */}
      <div className="flex-1 overflow-auto p-6">
        {loading && tasks.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-500">加载中...</div>
          </div>
        ) : tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <Clock className="w-16 h-16 mb-4 text-gray-300" />
            <p className="text-lg font-medium">还没有计划任务</p>
            <p className="text-sm mt-2">点击"创建任务"开始添加</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {tasks.map(task => (
              <div
                key={task.id}
                className={`bg-white rounded-lg border-2 p-4 transition-all ${
                  task.enabled
                    ? 'border-blue-200 hover:border-blue-300'
                    : 'border-gray-200 hover:border-gray-300 opacity-60'
                }`}
              >
                {/* 任务头部 */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900 truncate">
                        {task.name}
                      </h3>
                      {task.is_running && (
                        <span className="flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                          <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                          执行中
                        </span>
                      )}
                    </div>
                    {task.description && (
                      <p className="text-sm text-gray-500 line-clamp-2">
                        {task.description}
                      </p>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggle(task)}
                    className={`ml-2 ${task.enabled ? 'text-green-600' : 'text-gray-400'}`}
                  >
                    <Power className="w-4 h-4" />
                  </Button>
                </div>
                
                {/* 工作流信息 */}
                <div className="mb-3 p-2 bg-gray-50 rounded text-sm">
                  <div className="text-gray-600">
                    工作流: <span className="text-gray-900 font-medium">{task.workflow_name || task.workflow_id}</span>
                  </div>
                </div>
                
                {/* 触发器信息 */}
                <div className="mb-3 space-y-1">
                  <div className="flex items-center gap-2 text-sm">
                    {task.trigger.type === 'time' && <Clock className="w-4 h-4 text-blue-500" />}
                    {task.trigger.type === 'hotkey' && <Zap className="w-4 h-4 text-yellow-500" />}
                    {task.trigger.type === 'startup' && <Power className="w-4 h-4 text-green-500" />}
                    <span className="text-gray-600">{getTriggerTypeLabel(task.trigger.type)}</span>
                  </div>
                  <div className="text-sm text-gray-700 pl-6">
                    {getTriggerDescription(task)}
                  </div>
                  {task.next_execution_time && (
                    <div className="text-xs text-gray-500 pl-6">
                      下次执行: {formatDateTime(task.next_execution_time)}
                    </div>
                  )}
                </div>
                
                {/* 执行统计 */}
                <div className="mb-3 grid grid-cols-3 gap-2 text-center text-sm">
                  <div className="p-2 bg-gray-50 rounded">
                    <div className="text-gray-600 text-xs">总执行</div>
                    <div className="font-semibold text-gray-900">{task.total_executions}</div>
                  </div>
                  <div className="p-2 bg-green-50 rounded">
                    <div className="text-green-600 text-xs">成功</div>
                    <div className="font-semibold text-green-700">{task.success_executions}</div>
                  </div>
                  <div className="p-2 bg-red-50 rounded">
                    <div className="text-red-600 text-xs">失败</div>
                    <div className="font-semibold text-red-700">{task.failed_executions}</div>
                  </div>
                </div>
                
                {/* 成功率 */}
                {task.total_executions > 0 && (
                  <div className="mb-3">
                    <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                      <span>成功率</span>
                      <span className="font-medium">{getSuccessRate(task)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full transition-all"
                        style={{ width: `${getSuccessRate(task)}%` }}
                      />
                    </div>
                  </div>
                )}
                
                {/* 最后执行 */}
                {task.last_execution_time && (
                  <div className="mb-3 text-xs text-gray-500">
                    <div className="flex items-center justify-between">
                      <span>最后执行:</span>
                      <span className={`font-medium ${
                        task.last_execution_status === 'success' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {task.last_execution_status === 'success' ? '成功' : '失败'}
                      </span>
                    </div>
                    <div className="text-gray-400 mt-0.5">
                      {formatDateTime(task.last_execution_time)}
                    </div>
                  </div>
                )}
                
                {/* 操作按钮 */}
                <div className="flex gap-2 pt-3 border-t border-gray-100">
                  {task.is_running ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleStop(task)}
                      className="flex-1 gap-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Square className="w-3 h-3" />
                      停止
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleExecute(task)}
                      disabled={!task.enabled}
                      className="flex-1 gap-1"
                    >
                      <Play className="w-3 h-3" />
                      执行
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setLogsTask(task)}
                    className="flex-1 gap-1"
                  >
                    <FileText className="w-3 h-3" />
                    日志
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setEditingTask(task)}
                    className="gap-1"
                  >
                    <Edit className="w-3 h-3" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(task)}
                    className="gap-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* 对话框 */}
      <TaskCreateDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
      />
      
      {editingTask && (
        <TaskEditDialog
          task={editingTask}
          open={true}
          onClose={() => setEditingTask(null)}
        />
      )}
      
      {logsTask && (
        <TaskLogsDialog
          task={logsTask}
          open={true}
          onClose={() => setLogsTask(null)}
        />
      )}
      
      {showStatistics && (
        <StatisticsPanel
          open={true}
          onClose={() => setShowStatistics(false)}
        />
      )}
      
      {/* 确认对话框 */}
      <ConfirmDialog />
    </div>
  )
}
