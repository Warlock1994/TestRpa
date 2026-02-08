import { useCallback, useRef, useEffect, useState, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  SelectionMode,
  type ReactFlowInstance,
  type Node,
  type Edge,
  type OnSelectionChangeParams,
  type Connection,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Keyboard, ChevronDown, ChevronUp, FileJson, AlertTriangle, Boxes } from 'lucide-react'

import { useWorkflowStore, type NodeData } from '@/store/workflowStore'
import { ModuleNode } from './ModuleNode'
import { QuickModulePicker } from './QuickModulePicker'
import { getAllAvailableModules } from './ModuleSidebar'
import { useModuleStatsStore } from '@/store/moduleStatsStore'
import { GroupNode } from './GroupNode'
import { SubflowHeaderNode } from './SubflowHeaderNode'
import { NoteNode } from './NoteNode'
import { ModuleSidebar } from './ModuleSidebar'
import { ConfigPanel } from './ConfigPanel'
import { LogPanel } from './LogPanel'
import { Toolbar } from './Toolbar'
import { RemoteCursor } from './RemoteCursor'
import { socketService } from '@/services/socket'
import { remoteService } from '@/services/remote'
import type { ModuleType } from '@/types'

// 模块计数组件
function ModuleCount() {
  const nodes = useWorkflowStore((state) => state.nodes)
  
  // 计算模块数量（排除 group、note 和 subflow_header 类型）
  const moduleCount = useMemo(() => {
    return nodes.filter(n => n.type !== 'groupNode' && n.type !== 'noteNode' && n.type !== 'subflowHeaderNode').length
  }, [nodes])
  
  return (
    <div className="absolute top-4 left-4 z-10 animate-fade-in-down">
      <div className="glass-strong rounded-xl shadow-lg px-3 py-2 flex items-center gap-2">
        <Boxes className="w-4 h-4 text-blue-500" />
        <span className="text-sm font-medium text-muted-foreground">
          模块数量: <span className="text-blue-600 font-semibold">{moduleCount}</span>
        </span>
      </div>
    </div>
  )
}

// 操作提示组件
function ControlsHelp() {
  const [expanded, setExpanded] = useState(false)
  
  const shortcuts = [
    { keys: '左键拖拽', desc: '框选多个模块' },
    { keys: 'Shift+框选', desc: '跨区域累加选择' },
    { keys: 'Ctrl+点击', desc: '切换选中状态' },
    { keys: 'Shift+点击', desc: '范围选择' },
    { keys: '中键拖拽', desc: '平移画布' },
    { keys: '滚轮', desc: '缩放画布' },
    { keys: '双击画布', desc: '快速添加收藏模块' },
    { keys: '右键画布', desc: '快速添加所有模块' },
    { keys: 'Delete', desc: '删除选中' },
    { keys: 'Ctrl+S', desc: '保存工作流' },
    { keys: 'Alt+N', desc: '新建工作流' },
    { keys: 'Ctrl+C', desc: '复制' },
    { keys: 'Ctrl+V', desc: '粘贴' },
    { keys: 'Ctrl+A', desc: '全选' },
    { keys: 'Ctrl+D', desc: '禁用/启用' },
    { keys: 'Ctrl+Z', desc: '撤销' },
    { keys: 'Ctrl+Y', desc: '重做' },
  ]
  
  return (
    <div className="absolute top-4 right-4 z-10 animate-fade-in-down">
      <div className="glass-strong rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-blue-600 w-full transition-colors"
        >
          <Keyboard className="w-4 h-4" />
          <span className="font-medium">操作提示</span>
          {expanded ? <ChevronDown className="w-4 h-4 ml-auto" /> : <ChevronUp className="w-4 h-4 ml-auto" />}
        </button>
        {expanded && (
          <div className="px-3 pb-3 space-y-1.5 border-t border-blue-200/50 pt-2 animate-fade-in">
            {shortcuts.map((s, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <kbd className="px-1.5 py-0.5 bg-blue-100 rounded-md text-[10px] font-mono min-w-[80px] text-center text-blue-700 border border-blue-200/50">
                  {s.keys}
                </kbd>
                <span className="text-muted-foreground">{s.desc}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// 自定义节点类型
const nodeTypes = {
  moduleNode: ModuleNode,
  groupNode: GroupNode,
  subflowHeaderNode: SubflowHeaderNode,
  noteNode: NoteNode,
}

export function WorkflowEditor() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const reactFlowInstance = useRef<ReactFlowInstance<Node<NodeData>> | null>(null)
  const [selectedEdgeIds, setSelectedEdgeIds] = useState<string[]>([])
  const [isDraggingFile, setIsDraggingFile] = useState(false)
  const [showBrowserBusyDialog, setShowBrowserBusyDialog] = useState(false)
  const [showBrowserClosedDialog, setShowBrowserClosedDialog] = useState(false)
  
  // 快速模块选择器状态
  const [showQuickPicker, setShowQuickPicker] = useState(false)
  const [quickPickerPosition, setQuickPickerPosition] = useState({ x: 0, y: 0 })
  const [quickPickerFavoritesOnly, setQuickPickerFavoritesOnly] = useState(false) // 是否仅显示收藏
  
  // 远程协助状态
  const [remoteConnected, setRemoteConnected] = useState(false)
  const lastMouseSendRef = useRef<number>(0)
  const mouseSendThrottleMs = 50 // 鼠标移动发送节流时间
  
  // 鼠标在画布中的位置（用于粘贴）
  const mousePositionRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 })
  
  // 用于防抖处理框选时的节点选择更新
  const selectionDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pendingSelectionRef = useRef<string | null>(null)
  
  // 用于 Shift 范围选择
  const lastClickedNodeIdRef = useRef<string | null>(null)
  
  // 用于 Shift 框选（保持已选中的节点）
  const isShiftKeyPressedRef = useRef(false)
  const isCtrlKeyPressedRef = useRef(false)
  const preSelectionNodesRef = useRef<string[]>([]) // 框选开始前已选中的节点
  const isApplyingShiftSelectionRef = useRef(false) // 标志：正在应用 Shift 选择
  
  const {
    nodes,
    edges,
    variables,
    name: workflowName,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
    selectNode,
    selectedNodeId,
    deleteNode,
    copyNodes,
    pasteNodes,
    pasteNodesFromClipboard,
    addLog,
    mergeWorkflow,
    toggleNodesDisabled,
    undo,
    redo,
    loadWorkflow,
    executionStatus,
  } = useWorkflowStore()

  // 获取选中的节点
  const selectedNodes = nodes.filter(n => n.selected)

  // 使用 ref 存储最新状态，避免 useEffect 依赖问题
  const stateRef = useRef({ nodes, edges, variables, workflowName })
  useEffect(() => {
    stateRef.current = { nodes, edges, variables, workflowName }
  }, [nodes, edges, variables, workflowName])

  // 上一次同步的状态快照（用于检测变化）
  const lastSyncRef = useRef<string>('')
  
  // 监听 store 变化，发送完整同步（节流）
  // 上次同步的节点位置（用于检测位置变化）
  const lastNodePositionsRef = useRef<Record<string, { x: number; y: number }>>({})
  const pendingSyncRef = useRef(false)
  
  const syncThrottleRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const rafRef = useRef<number | null>(null)
  
  useEffect(() => {
    if (!remoteConnected || remoteService.isApplyingRemoteOperation()) {
      return
    }
    
    // 检查是否只是位置变化
    const currentPositions: Record<string, { x: number; y: number }> = {}
    let hasPositionChange = false
    
    for (const node of nodes) {
      currentPositions[node.id] = { x: node.position.x, y: node.position.y }
      const lastPos = lastNodePositionsRef.current[node.id]
      if (!lastPos || lastPos.x !== node.position.x || lastPos.y !== node.position.y) {
        hasPositionChange = true
      }
    }
    
    // 检查节点数量是否变化
    const lastIds = Object.keys(lastNodePositionsRef.current)
    const currentIds = Object.keys(currentPositions)
    const structureChanged = lastIds.length !== currentIds.length || !lastIds.every(id => currentIds.includes(id))
    
    // 生成当前状态的快照（不包含位置）
    const nodesWithoutPosition = nodes.map(n => ({ ...n, position: { x: 0, y: 0 } }))
    const currentSnapshot = JSON.stringify({ nodes: nodesWithoutPosition, edges, variables })
    const contentChanged = currentSnapshot !== lastSyncRef.current
    
    // 如果结构或内容变化，完整同步
    if (structureChanged || contentChanged) {
      if (syncThrottleRef.current) {
        clearTimeout(syncThrottleRef.current)
      }
      
      syncThrottleRef.current = setTimeout(() => {
        if (remoteService.isConnected() && !remoteService.isApplyingRemoteOperation()) {
          lastSyncRef.current = currentSnapshot
          lastNodePositionsRef.current = currentPositions
          remoteService.send({
            type: 'full_sync',
            nodes,
            edges,
            variables,
            workflowName,
          })
        }
      }, 50)
    } else if (hasPositionChange) {
      // 只有位置变化，使用 RAF 实现更流畅的同步
      lastNodePositionsRef.current = currentPositions
      
      if (!pendingSyncRef.current) {
        pendingSyncRef.current = true
        
        if (rafRef.current) {
          cancelAnimationFrame(rafRef.current)
        }
        
        rafRef.current = requestAnimationFrame(() => {
          pendingSyncRef.current = false
          if (remoteService.isConnected() && !remoteService.isApplyingRemoteOperation()) {
            remoteService.send({
              type: 'nodes_position',
              positions: lastNodePositionsRef.current,
            })
          }
        })
      }
    }
    
    return () => {
      if (syncThrottleRef.current) {
        clearTimeout(syncThrottleRef.current)
      }
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
      }
    }
  }, [nodes, edges, workflowName, remoteConnected])

  // 注册浏览器被占用错误回调
  useEffect(() => {
    socketService.setBrowserBusyCallback(() => {
      setShowBrowserBusyDialog(true)
    })
    return () => {
      socketService.setBrowserBusyCallback(null)
    }
  }, [])

  // 注册浏览器意外关闭回调
  useEffect(() => {
    socketService.setBrowserClosedCallback(() => {
      setShowBrowserClosedDialog(true)
    })
    return () => {
      socketService.setBrowserClosedCallback(null)
    }
  }, [])

  // 远程协助 - 监听连接状态和消息
  useEffect(() => {
    const unsubStatus = remoteService.onStatus((status) => {
      const connected = status === 'connected'
      setRemoteConnected(connected)
      
      if (connected) {
        const connType = remoteService.getConnectionType()
        const connTypeText = connType === 'p2p' ? '（P2P 直连）' : ''
        addLog({ level: 'info', message: `远程协助已连接${connTypeText}` })
        // 重置同步快照
        lastSyncRef.current = ''
      } else if (status === 'disconnected') {
        addLog({ level: 'info', message: '远程协助已断开' })
      }
    })

    // 监听同步数据
    const unsubSync = remoteService.onSyncData((data) => {
      // 应用同步数据到画布
      remoteService.setApplyingRemote(true)
      // 更新快照防止循环
      lastSyncRef.current = JSON.stringify({ nodes: data.nodes, edges: data.edges })
      try {
        loadWorkflow({
          nodes: data.nodes as Node<NodeData>[],
          edges: data.edges,
          name: data.workflowName || '远程协助工作流',
        })
        // 不再打印同步日志，太频繁了
      } finally {
        setTimeout(() => remoteService.setApplyingRemote(false), 200)
      }
    })

    // 监听远程操作消息
    const unsubMessage = remoteService.onMessage((message) => {
      const session = remoteService.getSession()
      if (!session || session.status !== 'connected') return

      switch (message.type) {
        case 'sync_request': {
          // 对方请求同步，发送当前完整状态
          const state = stateRef.current
          remoteService.send({
            type: 'full_sync',
            nodes: state.nodes,
            edges: state.edges,
            variables: state.variables,
            workflowName: state.workflowName,
          })
          break
        }
        
        case 'full_sync': {
          // 收到完整同步数据
          if (message.nodes && message.edges) {
            remoteService.setApplyingRemote(true)
            // 更新快照防止循环
            const nodesWithoutPosition = (message.nodes as Node<NodeData>[]).map(n => ({ ...n, position: { x: 0, y: 0 } }))
            lastSyncRef.current = JSON.stringify({ 
              nodes: nodesWithoutPosition, 
              edges: message.edges, 
              variables: message.variables || [] 
            })
            // 更新位置快照
            const positions: Record<string, { x: number; y: number }> = {}
            for (const node of message.nodes as Node<NodeData>[]) {
              positions[node.id] = { x: node.position.x, y: node.position.y }
            }
            lastNodePositionsRef.current = positions
            try {
              loadWorkflow({
                nodes: message.nodes as Node<NodeData>[],
                edges: message.edges as Edge[],
                name: (message.workflowName as string) || stateRef.current.workflowName,
              })
            } finally {
              setTimeout(() => remoteService.setApplyingRemote(false), 200)
            }
          }
          break
        }
        
        case 'nodes_position': {
          // 只更新节点位置（更高效）
          const positions = message.positions as Record<string, { x: number; y: number }>
          if (positions) {
            remoteService.setApplyingRemote(true)
            lastNodePositionsRef.current = positions
            // 直接更新节点位置，不重新加载整个画布
            onNodesChange(
              Object.entries(positions).map(([id, pos]) => ({
                type: 'position' as const,
                id,
                position: pos,
              }))
            )
            // 使用 RAF 延迟重置标记，确保不会触发循环
            requestAnimationFrame(() => {
              remoteService.setApplyingRemote(false)
            })
          }
          break
        }
        
        case 'mouse_move':
        case 'mouse_click':
          // 鼠标消息直接转发给处理器（RemoteCursor 组件会处理）
          break
      }
    })

    return () => {
      unsubStatus()
      unsubSync()
      unsubMessage()
    }
  }, [addLog, loadWorkflow, onNodesChange])

  // 处理滚轮事件：鼠标滚轮缩放，触摸板双指滑动平移
  useEffect(() => {
    const wrapper = reactFlowWrapper.current
    if (!wrapper) return

    const handleWheel = (event: WheelEvent) => {
      if (!reactFlowInstance.current) return
      
      // 触摸板双指滑动通常会带有 ctrlKey（捏合缩放）或者 deltaX 不为0（平移）
      // 鼠标滚轮通常只有 deltaY，且 deltaX 为 0
      const isTouchpad = event.ctrlKey || Math.abs(event.deltaX) > 0
      
      if (isTouchpad) {
        // 触摸板操作
        if (event.ctrlKey) {
          // Ctrl + 双指 = 缩放（触摸板捏合手势）
          event.preventDefault()
          const delta = event.deltaY > 0 ? 0.95 : 1.05
          const currentZoom = reactFlowInstance.current.getZoom()
          const newZoom = Math.min(Math.max(currentZoom * delta, 0.1), 2)
          reactFlowInstance.current.zoomTo(newZoom, { duration: 0 })
        } else {
          // 双指滑动 = 平移
          event.preventDefault()
          const { x, y } = reactFlowInstance.current.getViewport()
          const currentZoom = reactFlowInstance.current.getZoom()
          reactFlowInstance.current.setViewport({
            x: x - event.deltaX / currentZoom,
            y: y - event.deltaY / currentZoom,
            zoom: currentZoom,
          }, { duration: 0 })
        }
      } else {
        // 鼠标滚轮 = 缩放
        event.preventDefault()
        const delta = event.deltaY > 0 ? 0.9 : 1.1
        const currentZoom = reactFlowInstance.current.getZoom()
        const newZoom = Math.min(Math.max(currentZoom * delta, 0.1), 2)
        reactFlowInstance.current.zoomTo(newZoom, { duration: 0 })
      }
    }

    wrapper.addEventListener('wheel', handleWheel, { passive: false })
    return () => wrapper.removeEventListener('wheel', handleWheel)
  }, [])

  // 全局拦截浏览器右键菜单
  useEffect(() => {
    const handleContextMenu = (event: MouseEvent) => {
      event.preventDefault()
    }
    
    document.addEventListener('contextmenu', handleContextMenu)
    return () => document.removeEventListener('contextmenu', handleContextMenu)
  }, [])

  // 监听框选开始，记录已选中的节点（用于 Shift+框选）
  useEffect(() => {
    const handleMouseDown = (event: MouseEvent) => {
      if (event.button === 0 && reactFlowWrapper.current) {
        const target = event.target as HTMLElement
        // 检查是否点击在画布背景上（开始框选）
        if (target.classList.contains('react-flow__pane') || 
            target.classList.contains('react-flow__renderer') ||
            target.classList.contains('react-flow__selectionpane')) {
          // 如果按住 Shift 键，记录当前已选中的节点
          if (isShiftKeyPressedRef.current) {
            preSelectionNodesRef.current = nodes.filter(n => n.selected).map(n => n.id)
          } else {
            preSelectionNodesRef.current = []
          }
        }
      }
    }
    
    document.addEventListener('mousedown', handleMouseDown)
    return () => document.removeEventListener('mousedown', handleMouseDown)
  }, [nodes])



  // 监听键盘事件
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // 跟踪 Ctrl 和 Shift 键状态
      if (event.ctrlKey || event.metaKey) {
        isCtrlKeyPressedRef.current = true
      }
      if (event.shiftKey) {
        isShiftKeyPressedRef.current = true
      }
      
      // 如果焦点在输入框中，不处理快捷键
      const target = event.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return
      }
      
      // 检查是否在 Monaco Editor 或其他代码编辑器中
      if (target.closest('.monaco-editor') || target.closest('[role="textbox"]')) {
        return
      }
      
      // Delete/Backspace 删除选中节点或边
      if (event.key === 'Delete' || event.key === 'Backspace') {
        event.preventDefault()
        
        // 优先删除多选的节点
        if (selectedNodes.length > 0) {
          const nodeIds = selectedNodes.map(n => n.id)
          nodeIds.forEach(id => deleteNode(id))
          selectNode(null)
          addLog({ level: 'info', message: `已删除 ${nodeIds.length} 个模块` })
        } else if (selectedEdgeIds.length > 0) {
          // 删除选中的边（支持多选）
          onEdgesChange(selectedEdgeIds.map(id => ({ type: 'remove', id })))
          setSelectedEdgeIds([])
          addLog({ level: 'info', message: `已删除 ${selectedEdgeIds.length} 条连线` })
        } else if (selectedNodeId) {
          // 删除单个选中的节点
          deleteNode(selectedNodeId)
          selectNode(null)
        }
      }
      
      // Ctrl+C 复制节点（支持多选）- 写入系统剪贴板实现跨工作流复制
      if ((event.ctrlKey || event.metaKey) && event.key === 'c') {
        event.preventDefault()
        const nodesToCopy = selectedNodes.length > 0 
          ? selectedNodes 
          : (selectedNodeId ? nodes.filter(n => n.id === selectedNodeId) : [])
        
        if (nodesToCopy.length > 0) {
          // 复制节点之间的连线
          const nodeIdSet = new Set(nodesToCopy.map(n => n.id))
          const edgesToCopy = edges.filter(
            (e) => nodeIdSet.has(e.source) && nodeIdSet.has(e.target)
          )
          
          // 写入系统剪贴板
          const clipboardData = {
            type: 'webrpa-nodes',
            nodes: nodesToCopy,
            edges: edgesToCopy,
          }
          navigator.clipboard.writeText(JSON.stringify(clipboardData)).then(() => {
            // 同时保存到内部剪贴板（作为备份）
            copyNodes(nodesToCopy.map(n => n.id))
            addLog({ level: 'info', message: `已复制 ${nodesToCopy.length} 个模块到剪贴板` })
          }).catch(() => {
            // 如果系统剪贴板失败，使用内部剪贴板
            copyNodes(nodesToCopy.map(n => n.id))
            addLog({ level: 'info', message: `已复制 ${nodesToCopy.length} 个模块` })
          })
        }
      }
      
      // Ctrl+V 粘贴节点 - 从系统剪贴板读取，粘贴到鼠标位置
      if ((event.ctrlKey || event.metaKey) && event.key === 'v') {
        event.preventDefault()
        
        // 获取鼠标在画布中的位置
        const position = mousePositionRef.current
        
        // 尝试从系统剪贴板读取
        navigator.clipboard.readText().then((text) => {
          try {
            const data = JSON.parse(text)
            if (data.type === 'webrpa-nodes' && Array.isArray(data.nodes)) {
              // 从系统剪贴板粘贴（支持跨工作流）
              pasteNodesFromClipboard(data.nodes, data.edges || [], position)
              addLog({ level: 'success', message: `已粘贴 ${data.nodes.length} 个模块` })
            } else {
              // 不是有效的节点数据，使用内部剪贴板
              pasteNodes(position)
            }
          } catch {
            // JSON解析失败，使用内部剪贴板
            pasteNodes(position)
          }
        }).catch(() => {
          // 系统剪贴板读取失败，使用内部剪贴板
          pasteNodes(position)
        })
      }
      
      // Ctrl+D 禁用/启用节点
      if ((event.ctrlKey || event.metaKey) && event.key === 'd') {
        event.preventDefault()
        if (selectedNodes.length > 0) {
          const nodeIds = selectedNodes.map(n => n.id)
          toggleNodesDisabled(nodeIds)
          const firstNode = selectedNodes[0]
          const willBeDisabled = !firstNode.data.disabled
          addLog({ level: 'info', message: `已${willBeDisabled ? '禁用' : '启用'} ${nodeIds.length} 个模块` })
        } else if (selectedNodeId) {
          const node = nodes.find(n => n.id === selectedNodeId)
          if (node) {
            toggleNodesDisabled([selectedNodeId])
            const willBeDisabled = !node.data.disabled
            addLog({ level: 'info', message: `已${willBeDisabled ? '禁用' : '启用'}模块` })
          }
        }
      }
      
      // Ctrl+A 全选
      if ((event.ctrlKey || event.metaKey) && event.key === 'a') {
        event.preventDefault()
        onNodesChange(nodes.map(n => ({ type: 'select' as const, id: n.id, selected: true })))
      }
      
      // Ctrl+Z 撤销
      if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
        event.preventDefault()
        undo()
      }
      
      // Ctrl+Y 或 Ctrl+Shift+Z 重做
      if ((event.ctrlKey || event.metaKey) && (event.key === 'y' || (event.key === 'z' && event.shiftKey))) {
        event.preventDefault()
        redo()
      }
    }
    
    const handleKeyUp = (event: KeyboardEvent) => {
      // 重置 Ctrl 和 Shift 键状态
      if (!event.ctrlKey && !event.metaKey) {
        isCtrlKeyPressedRef.current = false
      }
      if (!event.shiftKey) {
        isShiftKeyPressedRef.current = false
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [selectedNodeId, selectedEdgeIds, selectedNodes, nodes, edges, deleteNode, selectNode, copyNodes, pasteNodes, pasteNodesFromClipboard, addLog, onEdgesChange, onNodesChange, toggleNodesDisabled, undo, redo])

  // 清理防抖定时器
  useEffect(() => {
    return () => {
      if (selectionDebounceRef.current) {
        clearTimeout(selectionDebounceRef.current)
      }
    }
  }, [])

  const onInit = useCallback((instance: ReactFlowInstance<Node<NodeData>>) => {
    reactFlowInstance.current = instance
  }, [])

  // 处理日志点击 - 定位到对应节点
  const handleLogClick = useCallback((nodeId: string) => {
    if (!reactFlowInstance.current) return
    
    // 查找节点位置
    const node = nodes.find(n => n.id === nodeId)
    if (node) {
      // 先选中节点（提供视觉反馈）
      onNodesChange(
        nodes.map((n) => ({
          type: 'select' as const,
          id: n.id,
          selected: n.id === nodeId,
        }))
      )
      
      // 定位到节点并居中显示（带动画效果）
      reactFlowInstance.current.setCenter(
        node.position.x + (node.width || 200) / 2,  // 节点中心X坐标
        node.position.y + (node.height || 100) / 2,  // 节点中心Y坐标
        { zoom: 1, duration: 500 }  // 缩放级别和动画时长
      )
    }
  }, [nodes, onNodesChange])
  
  // 监听执行状态变化
  useEffect(() => {
    // 执行状态变化时的处理（如果需要）
  }, [executionStatus])
  
  // MiniMap 点击处理 - 点击跳转到指定位置
  const handleMiniMapClick = useCallback((_event: React.MouseEvent, position: { x: number; y: number }) => {
    if (!reactFlowInstance.current) return
    
    // 获取当前缩放级别
    const { zoom } = reactFlowInstance.current.getViewport()
    
    // 设置新的视口位置，使点击的位置居中显示（带动画效果）
    reactFlowInstance.current.setCenter(position.x, position.y, { zoom, duration: 300 })
  }, [])

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    // 检查是否是文件拖拽
    if (event.dataTransfer.types.includes('Files')) {
      event.dataTransfer.dropEffect = 'copy'
    } else {
      event.dataTransfer.dropEffect = 'move'
    }
  }, [])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()

      // 如果是文件拖拽，由外层容器处理
      if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
        return
      }

      // 模块拖拽逻辑
      const type = event.dataTransfer.getData('application/reactflow') as ModuleType
      if (!type || !reactFlowInstance.current || !reactFlowWrapper.current) {
        return
      }

      // screenToFlowPosition 需要屏幕坐标，直接使用 clientX/clientY
      const position = reactFlowInstance.current.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })

      addNode(type, position)
    },
    [addNode]
  )

  // 处理文件拖拽到画布
  const handleFileDragOver = useCallback((event: React.DragEvent) => {
    // 只处理文件拖拽
    if (event.dataTransfer.types.includes('Files')) {
      event.preventDefault()
      event.stopPropagation()
      event.dataTransfer.dropEffect = 'copy'
      setIsDraggingFile(true)
    }
  }, [])

  const handleFileDragLeave = useCallback((event: React.DragEvent) => {
    // 检查是否真的离开了容器
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
    const x = event.clientX
    const y = event.clientY
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      setIsDraggingFile(false)
    }
  }, [])

  const handleFileDrop = useCallback((event: React.DragEvent) => {
    setIsDraggingFile(false)
    
    // 检查是否是文件拖拽
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      event.preventDefault()
      event.stopPropagation()
      
      const files = Array.from(event.dataTransfer.files)
      const jsonFiles = files.filter(f => f.name.endsWith('.json'))
      
      if (jsonFiles.length > 0 && reactFlowInstance.current && reactFlowWrapper.current) {
        // screenToFlowPosition 需要屏幕坐标
        const position = reactFlowInstance.current.screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        })
        
        // 读取并导入所有JSON文件
        jsonFiles.forEach((file, index) => {
          const reader = new FileReader()
          reader.onload = (e) => {
            const content = e.target?.result as string
            if (content) {
              // 每个文件在Y方向上偏移一些，避免重叠
              const success = mergeWorkflow(content, { 
                x: position.x, 
                y: position.y + index * 150 
              })
              if (success) {
                addLog({ level: 'success', message: `已导入工作流: ${file.name}` })
              } else {
                addLog({ level: 'error', message: `导入失败: ${file.name}，文件格式无效` })
              }
            }
          }
          reader.onerror = () => {
            addLog({ level: 'error', message: `读取文件失败: ${file.name}` })
          }
          reader.readAsText(file)
        })
      }
    }
  }, [mergeWorkflow, addLog])

  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: { id: string }) => {
      const isCtrlPressed = event.ctrlKey || event.metaKey
      const isShiftPressed = event.shiftKey
      
      if (isCtrlPressed) {
        // Ctrl + 点击：切换选中状态
        const currentNode = nodes.find(n => n.id === node.id)
        if (currentNode) {
          const isCurrentlySelected = currentNode.selected
          onNodesChange([{
            type: 'select',
            id: node.id,
            selected: !isCurrentlySelected
          }])
          
          // 如果选中了，记录为最后点击的节点
          if (!isCurrentlySelected) {
            lastClickedNodeIdRef.current = node.id
          }
        }
        setSelectedEdgeIds([])
      } else if (isShiftPressed && lastClickedNodeIdRef.current) {
        // Shift + 点击：范围选择
        const lastNodeIndex = nodes.findIndex(n => n.id === lastClickedNodeIdRef.current)
        const currentNodeIndex = nodes.findIndex(n => n.id === node.id)
        
        if (lastNodeIndex !== -1 && currentNodeIndex !== -1) {
          const start = Math.min(lastNodeIndex, currentNodeIndex)
          const end = Math.max(lastNodeIndex, currentNodeIndex)
          
          // 选中范围内的所有节点
          const changes = nodes.slice(start, end + 1).map(n => ({
            type: 'select' as const,
            id: n.id,
            selected: true
          }))
          
          onNodesChange(changes)
          addLog({ level: 'info', message: `已选中 ${end - start + 1} 个模块` })
        }
        setSelectedEdgeIds([])
      } else {
        // 普通点击：单选
        selectNode(node.id)
        lastClickedNodeIdRef.current = node.id
        setSelectedEdgeIds([])
      }
    },
    [nodes, selectNode, onNodesChange, addLog]
  )

  const onEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => {
      setSelectedEdgeIds([edge.id])
      selectNode(null)
    },
    [selectNode]
  )

  // 用于检测双击的 ref
  const lastPaneClickTimeRef = useRef<number>(0)
  const doubleClickThreshold = 300 // 双击时间阈值（毫秒）
  
  const onPaneClick = useCallback((event: React.MouseEvent) => {
    const now = Date.now()
    const timeSinceLastClick = now - lastPaneClickTimeRef.current
    
    // 检测双击
    if (timeSinceLastClick < doubleClickThreshold) {
      // 双击：唤出快速模块选择器（仅显示收藏）
      event.preventDefault()
      setQuickPickerPosition({
        x: event.clientX,
        y: event.clientY
      })
      setQuickPickerFavoritesOnly(true) // 仅显示收藏
      setShowQuickPicker(true)
      lastPaneClickTimeRef.current = 0 // 重置，避免三击触发
    } else {
      // 单击：取消所有选择
      selectNode(null)
      setSelectedEdgeIds([])
      lastClickedNodeIdRef.current = null
      lastPaneClickTimeRef.current = now
    }
  }, [selectNode])
  
  // 右键画布空白区域唤出快速模块选择器（显示所有模块）
  const handlePaneContextMenu = useCallback((event: React.MouseEvent | MouseEvent) => {
    event.preventDefault()
    setQuickPickerPosition({
      x: event.clientX,
      y: event.clientY
    })
    setQuickPickerFavoritesOnly(false) // 显示所有模块
    setShowQuickPicker(true)
  }, [])
  
  // 处理快速模块选择
  const { incrementUsage } = useModuleStatsStore()
  const handleQuickModuleSelect = useCallback((moduleType: ModuleType) => {
    if (reactFlowInstance.current) {
      const position = reactFlowInstance.current.screenToFlowPosition({
        x: quickPickerPosition.x,
        y: quickPickerPosition.y
      })
      
      if (position) {
        addNode(moduleType, position)
        incrementUsage(moduleType)
      }
    }
  }, [quickPickerPosition, addNode, incrementUsage])

  // 跟踪鼠标在画布中的位置（用于粘贴和远程协助）
  const onMouseMove = useCallback((event: React.MouseEvent) => {
    if (reactFlowInstance.current) {
      const position = reactFlowInstance.current.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })
      mousePositionRef.current = position

      // 远程协助 - 发送鼠标位置（节流）- 发送画布坐标
      const session = remoteService.getSession()
      if (session && session.status === 'connected') {
        const now = Date.now()
        if (now - lastMouseSendRef.current >= mouseSendThrottleMs) {
          lastMouseSendRef.current = now
          remoteService.send({
            type: 'mouse_move',
            x: position.x,  // 画布坐标
            y: position.y,
          })
        }
      }
    }
  }, [])

  // 处理框选变化（包括节点和边）- 使用防抖优化性能
  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes, edges: selectedEdges }: OnSelectionChangeParams) => {
      // 更新选中的边（边的选择不需要防抖，因为不会触发重渲染）
      setSelectedEdgeIds(selectedEdges.map(e => e.id))
      
      // 如果正在应用 Shift 选择，跳过此次回调，避免循环
      if (isApplyingShiftSelectionRef.current) {
        return
      }
      
      // 如果按住 Shift 键框选，且有预先选中的节点，合并选择
      if (preSelectionNodesRef.current.length > 0 && selectedNodes.length > 0) {
        const newlySelectedIds = selectedNodes.map(n => n.id)
        const allSelectedIds = Array.from(new Set([...preSelectionNodesRef.current, ...newlySelectedIds]))
        
        // 只在第一次合并时更新，避免循环
        if (allSelectedIds.length > newlySelectedIds.length) {
          // 设置标志，防止循环
          isApplyingShiftSelectionRef.current = true
          
          // 使用 setTimeout 延迟执行，避免在 onSelectionChange 回调中直接调用 onNodesChange
          setTimeout(() => {
            // 获取最新的 nodes
            const currentNodes = useWorkflowStore.getState().nodes
            const changes = currentNodes.map(n => ({
              type: 'select' as const,
              id: n.id,
              selected: allSelectedIds.includes(n.id)
            }))
            
            onNodesChange(changes)
            
            // 延迟重置标志，确保选择已经应用
            setTimeout(() => {
              isApplyingShiftSelectionRef.current = false
            }, 100)
          }, 0)
          
          // 清空预选节点，避免重复触发
          preSelectionNodesRef.current = []
          
          // 多选时不显示配置面板
          selectNode(null)
          
          return
        }
      }
      
      // 对节点选择使用防抖，避免框选过程中频繁更新配置面板导致卡顿
      const newSelectedNodeId = selectedNodes.length === 1 ? selectedNodes[0].id : null
      
      // 如果选择没有变化，不做任何处理
      if (pendingSelectionRef.current === newSelectedNodeId) {
        return
      }
      
      pendingSelectionRef.current = newSelectedNodeId
      
      // 清除之前的防抖定时器
      if (selectionDebounceRef.current) {
        clearTimeout(selectionDebounceRef.current)
      }
      
      // 使用防抖延迟更新，框选结束后才更新配置面板
      selectionDebounceRef.current = setTimeout(() => {
        selectNode(pendingSelectionRef.current)
        
        // 记录最后选中的节点（用于 Shift 范围选择）
        if (pendingSelectionRef.current) {
          lastClickedNodeIdRef.current = pendingSelectionRef.current
        }
      }, 50) // 50ms 防抖延迟，足够短以保证响应性，又能避免频繁更新
    },
    [selectNode, onNodesChange]
  )

  // 验证连接是否有效
  const isValidConnection = useCallback((connection: Connection | Edge) => {
    // 不允许自环连接
    if (connection.source === connection.target) {
      addLog({
        level: 'error',
        message: '❌ 不允许将模块连接到自己！'
      })
      return false
    }
    return true
  }, [addLog])

  return (
    <div className="h-full w-full flex flex-col">
      {/* 顶部工具栏 */}
      <Toolbar />
      
      {/* 主内容区 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧模块面板 */}
        <ModuleSidebar />
        
        {/* 中间画布区域 */}
        <main 
          className="flex-1 relative gradient-mesh"
          ref={reactFlowWrapper}
          onDragOver={handleFileDragOver}
          onDragLeave={handleFileDragLeave}
          onDrop={handleFileDrop}
        >
          <ModuleCount />
          <ControlsHelp />
          
          {/* 远程光标 */}
          {remoteConnected && reactFlowInstance.current && (
            <RemoteCursor 
              flowToScreenPosition={(pos) => reactFlowInstance.current!.flowToScreenPosition(pos)} 
            />
          )}
          
          {/* 拖拽文件提示遮罩 */}
          {isDraggingFile && (
            <div className="absolute inset-0 z-50 bg-blue-500/10 border-2 border-dashed border-blue-500 flex items-center justify-center pointer-events-none animate-fade-in">
              <div className="glass-strong rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-4 animate-scale-in">
                <div className="p-4 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg">
                  <FileJson className="w-10 h-10 text-white" />
                </div>
                <div className="text-center">
                  <p className="text-lg font-semibold text-gradient">释放以导入工作流</p>
                  <p className="text-sm text-muted-foreground mt-1">支持导入 .json 格式的工作流文件</p>
                </div>
              </div>
            </div>
          )}
          
          <ReactFlow
            nodes={nodes.map(n => ({
              ...n,
              data: {
                ...n.data
              }
            })) as Node<NodeData>[]}
            edges={edges.map(e => ({
              ...e,
              selected: selectedEdgeIds.includes(e.id),
              style: selectedEdgeIds.includes(e.id) ? { stroke: '#ef4444', strokeWidth: 3 } : e.style
            })) as typeof edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            isValidConnection={isValidConnection}
            onInit={onInit}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={onNodeClick}
            onEdgeClick={onEdgeClick}
            onPaneClick={onPaneClick}
            onPaneContextMenu={handlePaneContextMenu}
            onMouseMove={onMouseMove}
            onSelectionChange={onSelectionChange}
            nodeTypes={nodeTypes}
            fitView
            snapToGrid
            snapGrid={[15, 15]}
            selectionOnDrag
            selectionMode={SelectionMode.Partial}
            selectNodesOnDrag={false}
            panOnDrag={[1]}
            panOnScroll={false}
            zoomOnScroll={false}
            zoomOnPinch={false}
            zoomOnDoubleClick={false}
            elevateNodesOnSelect={false}
            defaultEdgeOptions={{
              type: 'smoothstep',
              animated: true,
              selectable: true,
            }}
            proOptions={{ hideAttribution: true }}
          >
            <Background gap={15} size={1} />
            <Controls />
            <MiniMap 
              nodeColor={(node) => {
                const data = node.data as NodeData
                if (data.moduleType?.startsWith('condition') || data.moduleType?.startsWith('loop') || data.moduleType?.startsWith('foreach')) {
                  return '#22c55e'
                }
                if (data.moduleType?.includes('captcha')) {
                  return '#f97316'
                }
                if (['select_dropdown', 'set_checkbox', 'drag_element', 'scroll_page', 'upload_file', 'download_file', 'save_image'].includes(data.moduleType)) {
                  return '#a855f7'
                }
                return '#3b82f6'
              }}
              zoomable
              pannable
              onClick={handleMiniMapClick}
              maskColor="rgba(0, 0, 0, 0.1)"
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                cursor: 'pointer',
                overflow: 'hidden',
              }}
            />
          </ReactFlow>
        </main>
        
        {/* 右侧配置面板 */}
        <ConfigPanel selectedNodeId={selectedNodeId} />
        
        {/* 快速模块选择器 */}
        <QuickModulePicker
          isOpen={showQuickPicker}
          position={quickPickerPosition}
          onClose={() => setShowQuickPicker(false)}
          onSelectModule={handleQuickModuleSelect}
          availableModules={getAllAvailableModules()}
          favoritesOnly={quickPickerFavoritesOnly}
        />
      </div>
      
      {/* 底部日志面板 */}
      <LogPanel onLogClick={handleLogClick} />
      
      {/* 浏览器被占用提示弹窗 */}
      {showBrowserBusyDialog && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scale-in">
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 rounded-full bg-amber-100">
                  <AlertTriangle className="w-6 h-6 text-amber-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">浏览器被占用</h3>
              </div>
              <p className="text-gray-600 mb-4">
                检测到自动化浏览器正在被其他程序使用，无法启动新的浏览器实例。
              </p>
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg mb-4">
                <p className="text-sm text-amber-800">
                  <strong>解决方法：</strong><br />
                  1. 关闭所有已打开的自动化浏览器窗口<br />
                  2. 如果使用了"自动化浏览器"功能，请先关闭它<br />
                  3. 然后重新运行工作流
                </p>
              </div>
              <button
                onClick={() => setShowBrowserBusyDialog(false)}
                className="w-full py-2 px-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg font-medium hover:from-blue-600 hover:to-cyan-600 transition-all"
              >
                我知道了
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* 浏览器意外关闭提示弹窗 */}
      {showBrowserClosedDialog && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scale-in">
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 rounded-full bg-red-100">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">浏览器意外关闭</h3>
              </div>
              <p className="text-gray-600 mb-4">
                检测到自动化浏览器已被关闭，工作流已自动停止运行。
              </p>
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg mb-4">
                <p className="text-sm text-red-800">
                  <strong>提示：</strong><br />
                  工作流运行期间请勿手动关闭自动化浏览器窗口，否则会导致工作流中断。
                </p>
              </div>
              <button
                onClick={() => setShowBrowserClosedDialog(false)}
                className="w-full py-2 px-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg font-medium hover:from-blue-600 hover:to-cyan-600 transition-all"
              >
                我知道了
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
