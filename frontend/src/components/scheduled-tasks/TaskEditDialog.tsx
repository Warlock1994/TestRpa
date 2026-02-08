import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { useScheduledTaskStore, type ScheduledTask, type ScheduledTaskTrigger } from '@/store/scheduledTaskStore'
import { localWorkflowApi } from '@/services/api'
import { Clock, Zap, Power, Repeat, X, Play, Square } from 'lucide-react'
import { useConfirm } from '@/components/ui/confirm-dialog'

interface TaskEditDialogProps {
  task: ScheduledTask
  open: boolean
  onClose: () => void
}

export function TaskEditDialog({ task, open, onClose }: TaskEditDialogProps) {
  const { updateTask, executeTask, stopTask, fetchTasks } = useScheduledTaskStore()
  const { confirm, ConfirmDialog } = useConfirm()
  
  // 当前任务状态（用于实时更新）
  const [currentTask, setCurrentTask] = useState(task)
  
  // 基本信息
  const [name, setName] = useState(task.name)
  const [description, setDescription] = useState(task.description || '')
  const [workflowId, setWorkflowId] = useState(task.workflow_id)
  const [workflowName, setWorkflowName] = useState(task.workflow_name || '')
  
  // 工作流列表
  const [workflows, setWorkflows] = useState<any[]>([])
  const [loadingWorkflows, setLoadingWorkflows] = useState(false)
  
  // 触发器类型
  const [triggerType, setTriggerType] = useState<'time' | 'hotkey' | 'startup'>(task.trigger.type)
  
  // 时间触发器配置
  const [scheduleType, setScheduleType] = useState<'once' | 'daily' | 'weekly' | 'monthly' | 'interval'>(
    task.trigger.schedule_type || 'daily'
  )
  const [startDate, setStartDate] = useState(task.trigger.start_date || '')
  const [startTime, setStartTime] = useState(task.trigger.start_time || '08:00:00')
  const [endDate, setEndDate] = useState(task.trigger.end_date || '')
  const [dailyTime, setDailyTime] = useState(task.trigger.daily_time || '08:00:00')
  const [weeklyDays, setWeeklyDays] = useState<number[]>(task.trigger.weekly_days || [1])
  const [weeklyTime, setWeeklyTime] = useState(task.trigger.weekly_time || '08:00:00')
  const [monthlyDay, setMonthlyDay] = useState(task.trigger.monthly_day || 1)
  const [monthlyTime, setMonthlyTime] = useState(task.trigger.monthly_time || '08:00:00')
  const [intervalSeconds, setIntervalSeconds] = useState(task.trigger.interval_seconds || 300)
  
  // 重复执行配置
  const [repeatEnabled, setRepeatEnabled] = useState(task.trigger.repeat_enabled || false)
  const [repeatCount, setRepeatCount] = useState<number | null>(task.trigger.repeat_count || null)
  const [repeatInterval, setRepeatInterval] = useState(task.trigger.repeat_interval || 60)
  
  // 热键触发器配置
  const [hotkey, setHotkey] = useState(task.trigger.hotkey || '')
  const [recordingHotkey, setRecordingHotkey] = useState(false)
  
  // 启动触发器配置
  const [startupDelay, setStartupDelay] = useState(task.trigger.startup_delay || 0)
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  // 加载工作流列表
  useEffect(() => {
    if (open) {
      loadWorkflows()
      // 定时刷新任务状态
      const interval = setInterval(async () => {
        await refreshTaskStatus()
      }, 1000) // 每秒刷新一次
      
      return () => clearInterval(interval)
    }
  }, [open])
  
  // 刷新任务状态
  const refreshTaskStatus = async () => {
    try {
      await fetchTasks()
      // 从 store 中获取最新的任务状态
      const tasks = useScheduledTaskStore.getState().tasks
      const updatedTask = tasks.find(t => t.id === task.id)
      if (updatedTask) {
        setCurrentTask(updatedTask)
      }
    } catch (error) {
      console.error('刷新任务状态失败:', error)
    }
  }
  
  const loadWorkflows = async () => {
    setLoadingWorkflows(true)
    try {
      // 先获取默认文件夹
      const folderResponse = await localWorkflowApi.getDefaultFolder()
      if (folderResponse.data?.folder) {
        // 然后列出该文件夹中的工作流
        const listResponse = await localWorkflowApi.list(folderResponse.data.folder)
        if (listResponse.data?.workflows) {
          setWorkflows(listResponse.data.workflows)
        }
      }
    } catch (error) {
      console.error('加载工作流失败:', error)
    } finally {
      setLoadingWorkflows(false)
    }
  }
  
  const handleWorkflowChange = (filename: string) => {
    setWorkflowId(filename)
    const workflow = workflows.find(w => w.filename === filename)
    if (workflow) {
      setWorkflowName(workflow.name)
    }
  }
  
  const handleWeeklyDayToggle = (day: number) => {
    if (weeklyDays.includes(day)) {
      setWeeklyDays(weeklyDays.filter(d => d !== day))
    } else {
      setWeeklyDays([...weeklyDays, day].sort())
    }
  }
  
  const handleHotkeyRecord = () => {
    setRecordingHotkey(true)
    setHotkey('按下热键...')
    
    const handleKeyDown = (e: KeyboardEvent) => {
      e.preventDefault()
      e.stopPropagation()
      
      const keys: string[] = []
      
      // 修饰键
      if (e.ctrlKey) keys.push('ctrl')
      if (e.altKey) keys.push('alt')
      if (e.shiftKey) keys.push('shift')
      if (e.metaKey) keys.push('cmd')
      
      // 主键映射 - 支持更多按键
      const keyMap: Record<string, string> = {
        // 功能键
        'F1': 'f1', 'F2': 'f2', 'F3': 'f3', 'F4': 'f4',
        'F5': 'f5', 'F6': 'f6', 'F7': 'f7', 'F8': 'f8',
        'F9': 'f9', 'F10': 'f10', 'F11': 'f11', 'F12': 'f12',
        // 特殊键
        'Escape': 'esc', 'Tab': 'tab', 'CapsLock': 'capslock',
        'Enter': 'enter', 'Backspace': 'backspace', 'Delete': 'delete',
        'Insert': 'insert', 'Home': 'home', 'End': 'end',
        'PageUp': 'pageup', 'PageDown': 'pagedown',
        'ArrowUp': 'up', 'ArrowDown': 'down', 'ArrowLeft': 'left', 'ArrowRight': 'right',
        'Space': 'space',
        // 数字键盘
        'NumLock': 'numlock',
        // 符号键
        '`': 'grave', '~': 'grave',
        '-': 'minus', '_': 'minus',
        '=': 'equal', '+': 'equal',
        '[': 'bracketleft', '{': 'bracketleft',
        ']': 'bracketright', '}': 'bracketright',
        '\\': 'backslash', '|': 'backslash',
        ';': 'semicolon', ':': 'semicolon',
        "'": 'quote', '"': 'quote',
        ',': 'comma', '<': 'comma',
        '.': 'period', '>': 'period',
        '/': 'slash', '?': 'slash',
      }
      
      // 获取主键
      let mainKey = ''
      if (e.key && !['Control', 'Alt', 'Shift', 'Meta'].includes(e.key)) {
        // 使用keyMap映射,如果没有映射则使用原始key
        mainKey = keyMap[e.key] || e.key.toLowerCase()
        
        // 如果是单个字母或数字,直接使用
        if (/^[a-z0-9]$/i.test(e.key)) {
          mainKey = e.key.toLowerCase()
        }
      }
      
      // 添加主键
      if (mainKey) {
        keys.push(mainKey)
      }
      
      // 至少需要一个键(可以是单键或组合键)
      if (keys.length > 0) {
        const hotkeyStr = keys.join('+')
        setHotkey(hotkeyStr)
        setRecordingHotkey(false)
        window.removeEventListener('keydown', handleKeyDown)
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    
    setTimeout(() => {
      if (recordingHotkey) {
        setRecordingHotkey(false)
        setHotkey('')
        window.removeEventListener('keydown', handleKeyDown)
      }
    }, 10000)
  }
  
  const buildTrigger = (): ScheduledTaskTrigger => {
    const trigger: ScheduledTaskTrigger = {
      type: triggerType,
      repeat_enabled: repeatEnabled,
      repeat_count: repeatEnabled ? repeatCount : undefined,
      repeat_interval: repeatEnabled ? repeatInterval : undefined,
    }
    
    if (triggerType === 'time') {
      trigger.schedule_type = scheduleType
      
      switch (scheduleType) {
        case 'once':
          trigger.start_date = startDate
          trigger.start_time = startTime
          trigger.end_date = endDate || undefined
          break
        case 'daily':
          trigger.daily_time = dailyTime
          break
        case 'weekly':
          trigger.weekly_days = weeklyDays
          trigger.weekly_time = weeklyTime
          break
        case 'monthly':
          trigger.monthly_day = monthlyDay
          trigger.monthly_time = monthlyTime
          break
        case 'interval':
          trigger.interval_seconds = intervalSeconds
          break
      }
    } else if (triggerType === 'hotkey') {
      trigger.hotkey = hotkey
    } else if (triggerType === 'startup') {
      trigger.startup_delay = startupDelay
    }
    
    return trigger
  }
  
  const validate = (): string | null => {
    if (!name.trim()) return '请输入任务名称'
    if (!workflowId) return '请选择工作流'
    
    if (triggerType === 'time') {
      if (scheduleType === 'once') {
        if (!startDate) return '请选择开始日期'
        if (!startTime) return '请选择开始时间'
      } else if (scheduleType === 'weekly') {
        if (weeklyDays.length === 0) return '请至少选择一个星期'
      } else if (scheduleType === 'interval') {
        if (intervalSeconds <= 0) return '间隔秒数必须大于0'
      }
    } else if (triggerType === 'hotkey') {
      if (!hotkey) return '请设置热键'
    }
    
    if (repeatEnabled) {
      if (repeatCount !== null && repeatCount <= 0) return '重复次数必须大于0'
      if (repeatInterval <= 0) return '重复间隔必须大于0'
    }
    
    return null
  }
  
  // 执行任务
  const handleExecute = async () => {
    try {
      await executeTask(currentTask.id)
      await refreshTaskStatus()
    } catch (error) {
      console.error('执行任务失败:', error)
    }
  }
  
  // 停止任务
  const handleStop = async () => {
    const confirmed = await confirm(
      `确定要停止任务"${currentTask.name}"的执行吗？`,
      {
        title: '停止任务',
        confirmText: '停止',
        cancelText: '取消',
        type: 'warning'
      }
    )
    
    if (confirmed) {
      try {
        await stopTask(currentTask.id)
        await refreshTaskStatus()
      } catch (error) {
        console.error('停止任务失败:', error)
      }
    }
  }
  
  const handleSubmit = async () => {
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }
    
    setLoading(true)
    setError('')
    
    try {
      await updateTask(task.id, {
        name: name.trim(),
        description: description.trim() || undefined,
        workflow_id: workflowId,
        workflow_name: workflowName,
        trigger: buildTrigger(),
      })
      
      onClose()
    } catch (error: any) {
      setError(error.message || '更新任务失败')
    } finally {
      setLoading(false)
    }
  }
  
  const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  
  if (!open) return null
  
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col animate-scale-in" onClick={(e) => e.stopPropagation()}>
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">编辑计划任务</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* 内容 */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* 基本信息 */}
          <div className="space-y-2">
            <Label htmlFor="name">任务名称 *</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="输入任务名称"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="description">任务描述</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="输入任务描述（可选）"
              rows={2}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="workflow">关联工作流 *</Label>
            <Select value={workflowId || ''} onValueChange={handleWorkflowChange}>
              <SelectTrigger>
                <SelectValue placeholder={loadingWorkflows ? "加载中..." : "选择工作流"} />
              </SelectTrigger>
              <SelectContent>
                {workflows.length === 0 ? (
                  <div className="px-2 py-1.5 text-sm text-gray-500">暂无工作流</div>
                ) : (
                  workflows.map(workflow => (
                    <SelectItem key={workflow.filename} value={workflow.filename}>
                      {workflow.name}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
          
          {/* 触发器类型 */}
          <div className="space-y-2">
            <Label>触发器类型 *</Label>
            <div className="grid grid-cols-3 gap-2">
              <Button
                type="button"
                variant={triggerType === 'time' ? 'default' : 'outline'}
                onClick={() => setTriggerType('time')}
                className="gap-2"
              >
                <Clock className="w-4 h-4" />
                时间触发
              </Button>
              <Button
                type="button"
                variant={triggerType === 'hotkey' ? 'default' : 'outline'}
                onClick={() => setTriggerType('hotkey')}
                className="gap-2"
              >
                <Zap className="w-4 h-4" />
                热键触发
              </Button>
              <Button
                type="button"
                variant={triggerType === 'startup' ? 'default' : 'outline'}
                onClick={() => setTriggerType('startup')}
                className="gap-2"
              >
                <Power className="w-4 h-4" />
                启动触发
              </Button>
            </div>
          </div>
          
          {/* 时间触发器配置 */}
          {triggerType === 'time' && (
            <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
              <div className="space-y-2">
                <Label>调度类型</Label>
                <Select value={scheduleType} onValueChange={(v: any) => setScheduleType(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem key="once" value="once">一次性执行</SelectItem>
                    <SelectItem key="daily" value="daily">每日执行</SelectItem>
                    <SelectItem key="weekly" value="weekly">每周执行</SelectItem>
                    <SelectItem key="monthly" value="monthly">每月执行</SelectItem>
                    <SelectItem key="interval" value="interval">间隔执行</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {scheduleType === 'once' && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>开始日期</Label>
                      <Input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>开始时间</Label>
                      <Input
                        type="time"
                        step="1"
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>结束日期（可选）</Label>
                    <Input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                    />
                  </div>
                </>
              )}
              
              {scheduleType === 'daily' && (
                <div className="space-y-2">
                  <Label>执行时间</Label>
                  <Input
                    type="time"
                    step="1"
                    value={dailyTime}
                    onChange={(e) => setDailyTime(e.target.value)}
                  />
                </div>
              )}
              
              {scheduleType === 'weekly' && (
                <>
                  <div className="space-y-2">
                    <Label>选择星期</Label>
                    <div className="grid grid-cols-7 gap-2">
                      {weekDays.map((day, index) => (
                        <Button
                          key={index}
                          type="button"
                          variant={weeklyDays.includes(index) ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => handleWeeklyDayToggle(index)}
                        >
                          {day}
                        </Button>
                      ))}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>执行时间</Label>
                    <Input
                      type="time"
                      step="1"
                      value={weeklyTime}
                      onChange={(e) => setWeeklyTime(e.target.value)}
                    />
                  </div>
                </>
              )}
              
              {scheduleType === 'monthly' && (
                <>
                  <div className="space-y-2">
                    <Label>每月第几天</Label>
                    <Input
                      type="number"
                      min="1"
                      max="31"
                      value={monthlyDay}
                      onChange={(e) => setMonthlyDay(parseInt(e.target.value) || 1)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>执行时间</Label>
                    <Input
                      type="time"
                      step="1"
                      value={monthlyTime}
                      onChange={(e) => setMonthlyTime(e.target.value)}
                    />
                  </div>
                </>
              )}
              
              {scheduleType === 'interval' && (
                <div className="space-y-2">
                  <Label>间隔秒数</Label>
                  <Input
                    type="number"
                    min="1"
                    value={intervalSeconds}
                    onChange={(e) => setIntervalSeconds(parseInt(e.target.value) || 300)}
                  />
                  <p className="text-xs text-gray-500">
                    {intervalSeconds >= 60 ? `约 ${Math.round(intervalSeconds / 60)} 分钟` : `${intervalSeconds} 秒`}
                  </p>
                </div>
              )}
            </div>
          )}
          
          {/* 热键触发器配置 */}
          {triggerType === 'hotkey' && (
            <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
              <div className="space-y-2">
                <Label>热键设置</Label>
                <div className="flex gap-2">
                  <Input
                    value={hotkey}
                    onChange={(e) => setHotkey(e.target.value)}
                    placeholder="例如: ctrl+shift+f1"
                    readOnly={recordingHotkey}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleHotkeyRecord}
                    disabled={recordingHotkey}
                  >
                    {recordingHotkey ? '录制中...' : '录制'}
                  </Button>
                </div>
                <p className="text-xs text-gray-500">
                  点击"录制"按钮后按下热键，或手动输入（如：ctrl+shift+f1）
                </p>
              </div>
            </div>
          )}
          
          {/* 启动触发器配置 */}
          {triggerType === 'startup' && (
            <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
              <div className="space-y-2">
                <Label>启动延迟（秒）</Label>
                <Input
                  type="number"
                  min="0"
                  value={startupDelay}
                  onChange={(e) => setStartupDelay(parseInt(e.target.value) || 0)}
                />
                <p className="text-xs text-gray-500">
                  WebRPA启动后延迟多少秒执行任务
                </p>
              </div>
            </div>
          )}
          
          {/* 重复执行配置 */}
          <div className="space-y-4 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Repeat className="w-4 h-4 text-blue-600" />
                <Label htmlFor="repeat-enabled" className="cursor-pointer">
                  启用重复执行
                </Label>
              </div>
              <Switch
                id="repeat-enabled"
                checked={repeatEnabled}
                onCheckedChange={setRepeatEnabled}
              />
            </div>
            
            {repeatEnabled && (
              <div className="space-y-4 pt-2">
                <div className="space-y-2">
                  <Label>重复次数</Label>
                  <Input
                    type="number"
                    min="1"
                    value={repeatCount || ''}
                    onChange={(e) => setRepeatCount(e.target.value ? parseInt(e.target.value) : null)}
                    placeholder="留空表示无限重复"
                  />
                  <p className="text-xs text-gray-500">
                    留空表示无限重复，直到手动停止
                  </p>
                </div>
                
                <div className="space-y-2">
                  <Label>重复间隔（秒）</Label>
                  <Input
                    type="number"
                    min="1"
                    value={repeatInterval}
                    onChange={(e) => setRepeatInterval(parseInt(e.target.value) || 60)}
                  />
                  <p className="text-xs text-gray-500">
                    每次执行完成后等待多少秒再次执行
                  </p>
                </div>
              </div>
            )}
          </div>
          
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-600">
              {error}
            </div>
          )}
        </div>
        
        {/* 底部按钮 */}
        <div className="flex items-center justify-between gap-3 p-6 border-t border-gray-200 bg-gray-50">
          {/* 左侧：执行/停止按钮 */}
          <div>
            {currentTask.is_running ? (
              <Button
                variant="outline"
                onClick={handleStop}
                className="gap-1 text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Square className="w-4 h-4" />
                停止
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={handleExecute}
                disabled={!currentTask.enabled}
                className="gap-1"
              >
                <Play className="w-4 h-4" />
                立即执行
              </Button>
            )}
          </div>
          
          {/* 右侧：取消和保存按钮 */}
          <div className="flex gap-3">
            <Button variant="outline" onClick={onClose} disabled={loading}>
              取消
            </Button>
            <Button onClick={handleSubmit} disabled={loading}>
              {loading ? '保存中...' : '保存更改'}
            </Button>
          </div>
        </div>
        
        {/* 确认对话框 */}
        <ConfirmDialog />
      </div>
    </div>
  )
}
