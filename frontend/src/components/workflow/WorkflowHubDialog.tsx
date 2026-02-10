/**
 * 工作流仓库对话框
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  X,
  Search,
  Download,
  Upload,
  RefreshCw,
  Settings,
  Package,
  User,
  Calendar,
  Tag,
  AlertCircle,
  CheckCircle,
  Loader2,
  FileUp,
  FileJson,
  Plus,
  Trash2,
  Edit,
  FolderOpen,
  Copy,
  Key,
  MessageSquare,
  Send,
  Users,
  Link,
  Unlink,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { SelectNative as Select } from '@/components/ui/select-native'
import { useWorkflowStore } from '@/store/workflowStore'
import { useConfirm } from '@/components/ui/confirm-dialog'
import { remoteService, type RemoteSession } from '@/services/remote'

// 默认仓库地址
const DEFAULT_HUB_URL = 'https://hub.pmhs.top'

// 从 localStorage 获取仓库地址
function getHubUrl(): string {
  return localStorage.getItem('workflow_hub_url') || DEFAULT_HUB_URL
}

// 保存仓库地址到 localStorage
function setHubUrl(url: string) {
  localStorage.setItem('workflow_hub_url', url)
}

// 获取或生成客户端 ID
function getClientId(): string {
  let clientId = localStorage.getItem('workflow_hub_client_id')
  if (!clientId) {
    // 生成一个随机的客户端 ID
    clientId = 'client_' + Math.random().toString(36).substring(2) + Date.now().toString(36)
    localStorage.setItem('workflow_hub_client_id', clientId)
  }
  return clientId
}

// 工作流类型
interface HubWorkflow {
  id: string
  name: string
  description: string
  author: string
  category: string
  tags: string[]
  node_count: number
  download_count: number
  comment_count?: number
  created_at: string
  content?: {
    nodes: unknown[]
    edges: unknown[]
    variables: unknown[]
  }
}

interface Category {
  name: string
  count: number
}

// 评论类型
interface Comment {
  id: number
  nickname: string
  content: string
  comment_type: string
  created_at: string
  isOwner: boolean
}

// 留言类型
interface GuestbookMessage {
  id: number
  nickname: string
  content: string
  message_type: string
  created_at: string
  isOwner: boolean
}

// 评论类型选项
const COMMENT_TYPES = ['使用心得', '问题求助', '建议改进', '感谢', '其他']

// 留言类型选项
const MESSAGE_TYPES = ['建议', '问题求助', 'Bug报告', '功能请求', '闲聊', '其他']

// 缓存数据结构
interface CacheData {
  workflows: HubWorkflow[]
  categories: Category[]
  hasMore: boolean
  sortBy: string
  category: string
  search: string
  hubUrl: string
}

interface Props {
  open: boolean
  onClose: () => void
}

export function WorkflowHubDialog({ open, onClose }: Props) {
  const { nodes, edges, variables, importWorkflow, mergeWorkflow } = useWorkflowStore()
  const { confirm, alert, ConfirmDialog } = useConfirm()

  // 缓存引用（跨渲染保持）
  const cacheRef = useRef<CacheData | null>(null)
  const hasLoadedRef = useRef(false)
  const listContainerRef = useRef<HTMLDivElement>(null)

  // 状态
  const [activeTab, setActiveTab] = useState<'browse' | 'publish' | 'my' | 'guestbook' | 'remote' | 'settings'>('browse')
  const [hubUrl, setHubUrlState] = useState(getHubUrl())
  const [tempHubUrl, setTempHubUrl] = useState(hubUrl)
  const [tempClientId, setTempClientId] = useState('')

  // 浏览状态
  const [workflows, setWorkflows] = useState<HubWorkflow[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedCategory, setSelectedCategory] = useState('全部')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'newest' | 'popular' | 'downloads'>('newest')
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 发布状态
  const [publishName, setPublishName] = useState('')
  const [publishDescription, setPublishDescription] = useState('')
  const [publishAuthor, setPublishAuthor] = useState('')
  const [publishCategory, setPublishCategory] = useState('其他')
  const [publishTags, setPublishTags] = useState('')
  const [publishing, setPublishing] = useState(false)
  const [publishError, setPublishError] = useState<string | null>(null)
  const [publishSuccess, setPublishSuccess] = useState(false)
  
  // 文件上传状态
  const [publishMode, setPublishMode] = useState<'current' | 'file'>('current')
  const [uploadedWorkflow, setUploadedWorkflow] = useState<{
    nodes: unknown[]
    edges: unknown[]
    variables?: unknown[]
  } | null>(null)
  const [uploadFileName, setUploadFileName] = useState('')

  // 详情状态
  const [selectedWorkflow, setSelectedWorkflow] = useState<HubWorkflow | null>(null)
  const [downloading, setDownloading] = useState(false)
  const [isOwner, setIsOwner] = useState(false)
  const [deleting, setDeleting] = useState(false)

  // 我的工作流状态
  const [myWorkflows, setMyWorkflows] = useState<HubWorkflow[]>([])
  const [myWorkflowsLoading, setMyWorkflowsLoading] = useState(false)
  const [myWorkflowsError, setMyWorkflowsError] = useState<string | null>(null)

  // 编辑状态
  const [editingWorkflow, setEditingWorkflow] = useState<HubWorkflow | null>(null)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editAuthor, setEditAuthor] = useState('')
  const [editCategory, setEditCategory] = useState('')
  const [editTags, setEditTags] = useState('')
  const [updating, setUpdating] = useState(false)
  const [updateError, setUpdateError] = useState<string | null>(null)
  
  // 编辑工作流内容状态
  const [editContentMode, setEditContentMode] = useState<'none' | 'current' | 'file'>('none')
  const [editUploadedWorkflow, setEditUploadedWorkflow] = useState<{
    nodes: unknown[]
    edges: unknown[]
    variables?: unknown[]
  } | null>(null)
  const [editUploadFileName, setEditUploadFileName] = useState('')

  // 评论状态
  const [comments, setComments] = useState<Comment[]>([])
  const [commentsLoading, setCommentsLoading] = useState(false)
  const [commentsPage, setCommentsPage] = useState(1)
  const [commentsHasMore, setCommentsHasMore] = useState(true)
  const [commentNickname, setCommentNickname] = useState('')
  const [commentContent, setCommentContent] = useState('')
  const [commentType, setCommentType] = useState('使用心得')
  const [submittingComment, setSubmittingComment] = useState(false)

  // 留言板状态
  const [guestbookMessages, setGuestbookMessages] = useState<GuestbookMessage[]>([])
  const [guestbookLoading, setGuestbookLoading] = useState(false)
  const [guestbookPage, setGuestbookPage] = useState(1)
  const [guestbookHasMore, setGuestbookHasMore] = useState(true)
  const [guestbookNickname, setGuestbookNickname] = useState('')
  const [guestbookContent, setGuestbookContent] = useState('')
  const [guestbookType, setGuestbookType] = useState('建议')
  const [submittingGuestbook, setSubmittingGuestbook] = useState(false)

  // 远程协助状态
  const [remoteMode, setRemoteMode] = useState<'none' | 'host' | 'guest'>('none')
  const [remoteStatus, setRemoteStatus] = useState<RemoteSession['status']>('disconnected')
  const [remoteAssistCode, setRemoteAssistCode] = useState('')
  const [remoteInputCode, setRemoteInputCode] = useState('')
  const [remoteLoading, setRemoteLoading] = useState(false)
  const [remoteError, setRemoteError] = useState<string | null>(null)
  const [remoteGuestConnected, setRemoteGuestConnected] = useState(false)
  const [remoteConnectionType, setRemoteConnectionType] = useState<'p2p' | 'relay' | null>(null)

  // 加载分类
  const loadCategories = useCallback(async () => {
    try {
      const response = await fetch(`${hubUrl}/api/workflows/categories`)
      if (response.ok) {
        const data = await response.json()
        setCategories(data.categories || [])
      }
    } catch (e) {
      console.error('加载分类失败:', e)
    }
  }, [hubUrl])

  // 加载我的工作流
  const loadMyWorkflows = useCallback(async () => {
    setMyWorkflowsLoading(true)
    setMyWorkflowsError(null)

    try {
      const response = await fetch(`${hubUrl}/api/workflows/my-workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientId: getClientId() }),
      })

      if (!response.ok) {
        throw new Error('加载失败')
      }

      const data = await response.json()
      setMyWorkflows(data.workflows || [])
    } catch (e) {
      setMyWorkflowsError('无法加载我的工作流')
      setMyWorkflows([])
    } finally {
      setMyWorkflowsLoading(false)
    }
  }, [hubUrl])

  // 加载工作流评论
  const loadComments = useCallback(async (workflowId: string, append = false) => {
    if (append && !commentsHasMore) return

    setCommentsLoading(true)
    try {
      const currentPage = append ? commentsPage : 1
      const clientId = getClientId()
      const response = await fetch(`${hubUrl}/api/comments/${workflowId}?page=${currentPage}&limit=10&clientId=${encodeURIComponent(clientId)}`)
      if (response.ok) {
        const data = await response.json()
        const newComments = data.comments || []
        const totalPages = data.pagination?.totalPages || 1

        if (append) {
          setComments(prev => [...prev, ...newComments])
          setCommentsPage(currentPage + 1)
        } else {
          setComments(newComments)
          setCommentsPage(2)
        }
        setCommentsHasMore(currentPage < totalPages)
      }
    } catch (e) {
      console.error('加载评论失败:', e)
    } finally {
      setCommentsLoading(false)
    }
  }, [hubUrl, commentsPage, commentsHasMore])

  // 发布评论
  const handleSubmitComment = async (workflowId: string) => {
    if (!commentContent.trim()) return

    setSubmittingComment(true)
    try {
      const response = await fetch(`${hubUrl}/api/comments/${workflowId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nickname: commentNickname.trim() || '匿名用户',
          content: commentContent.trim(),
          commentType: commentType,
          clientId: getClientId(),
        }),
      })

      if (response.ok) {
        setCommentContent('')
        // 重置分页，重新加载评论
        setCommentsPage(1)
        setCommentsHasMore(true)
        setComments([])
        loadComments(workflowId, false)
      } else {
        const data = await response.json()
        await alert(data.error || '评论发布失败', { title: '发布失败' })
      }
    } catch (e) {
      await alert('网络错误，请稍后重试', { title: '发布失败' })
    } finally {
      setSubmittingComment(false)
    }
  }

  // 删除评论
  const handleDeleteComment = async (commentId: number) => {
    const confirmed = await confirm('确定要删除这条评论吗？', {
      title: '删除评论',
      type: 'warning',
      confirmText: '删除',
      cancelText: '取消'
    })
    if (!confirmed) return

    try {
      const response = await fetch(`${hubUrl}/api/comments/${commentId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientId: getClientId() }),
      })

      if (response.ok) {
        // 从列表中移除该评论
        setComments(prev => prev.filter(c => c.id !== commentId))
      } else {
        const data = await response.json()
        await alert(data.error || '删除失败', { title: '删除失败' })
      }
    } catch (e) {
      await alert('网络错误，请稍后重试', { title: '删除失败' })
    }
  }

  // 加载留言板
  const loadGuestbook = useCallback(async (append = false) => {
    if (append && !guestbookHasMore) return

    setGuestbookLoading(true)
    try {
      const currentPage = append ? guestbookPage : 1
      const clientId = getClientId()
      const response = await fetch(`${hubUrl}/api/guestbook?page=${currentPage}&limit=10&clientId=${encodeURIComponent(clientId)}`)
      if (response.ok) {
        const data = await response.json()
        const newMessages = data.messages || []
        const totalPages = data.pagination?.totalPages || 1

        if (append) {
          setGuestbookMessages(prev => [...prev, ...newMessages])
          setGuestbookPage(currentPage + 1)
        } else {
          setGuestbookMessages(newMessages)
          setGuestbookPage(2)
        }
        setGuestbookHasMore(currentPage < totalPages)
      }
    } catch (e) {
      console.error('加载留言板失败:', e)
    } finally {
      setGuestbookLoading(false)
    }
  }, [hubUrl, guestbookPage, guestbookHasMore])

  // 发布留言
  const handleSubmitGuestbook = async () => {
    if (!guestbookContent.trim()) return

    setSubmittingGuestbook(true)
    try {
      const response = await fetch(`${hubUrl}/api/guestbook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nickname: guestbookNickname.trim() || '匿名用户',
          content: guestbookContent.trim(),
          messageType: guestbookType,
          clientId: getClientId(),
        }),
      })

      if (response.ok) {
        setGuestbookContent('')
        setGuestbookPage(1)
        setGuestbookHasMore(true)
        loadGuestbook(false)
      } else {
        const data = await response.json()
        await alert(data.error || '留言发布失败', { title: '发布失败' })
      }
    } catch (e) {
      await alert('网络错误，请稍后重试', { title: '发布失败' })
    } finally {
      setSubmittingGuestbook(false)
    }
  }

  // 删除留言
  const handleDeleteGuestbook = async (messageId: number) => {
    const confirmed = await confirm('确定要删除这条留言吗？', {
      title: '删除留言',
      type: 'warning',
      confirmText: '删除',
      cancelText: '取消'
    })
    if (!confirmed) return

    try {
      const response = await fetch(`${hubUrl}/api/guestbook/${messageId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientId: getClientId() }),
      })

      if (response.ok) {
        // 从列表中移除该留言
        setGuestbookMessages(prev => prev.filter(m => m.id !== messageId))
      } else {
        const data = await response.json()
        await alert(data.error || '删除失败', { title: '删除失败' })
      }
    } catch (e) {
      await alert('网络错误，请稍后重试', { title: '删除失败' })
    }
  }

  // 远程协助 - 创建协助码
  const handleCreateRemoteSession = async () => {
    setRemoteLoading(true)
    setRemoteError(null)

    const result = await remoteService.createSession()
    
    if (result.success && result.assistCode) {
      setRemoteMode('host')
      setRemoteAssistCode(result.assistCode)
      setRemoteStatus('waiting')
    } else {
      setRemoteError(result.error || '创建失败')
    }
    
    setRemoteLoading(false)
  }

  // 远程协助 - 加入协助
  const handleJoinRemoteSession = async () => {
    if (!remoteInputCode.trim() || remoteInputCode.length !== 6) {
      setRemoteError('请输入6位协助码')
      return
    }

    setRemoteLoading(true)
    setRemoteError(null)

    const result = await remoteService.joinSession(remoteInputCode.trim())
    
    if (result.success) {
      setRemoteMode('guest')
      setRemoteAssistCode(remoteInputCode.trim())
      setRemoteStatus('connecting')
    } else {
      setRemoteError(result.error || '加入失败')
    }
    
    setRemoteLoading(false)
  }

  // 远程协助 - 断开连接
  const handleCloseRemoteSession = async () => {
    await remoteService.closeSession()
    setRemoteMode('none')
    setRemoteAssistCode('')
    setRemoteInputCode('')
    setRemoteStatus('disconnected')
    setRemoteGuestConnected(false)
    setRemoteError(null)
  }

  // 监听远程协助状态变化
  useEffect(() => {
    const unsubStatus = remoteService.onStatus((status, info) => {
      setRemoteStatus(status)
      // 更新连接类型
      setRemoteConnectionType(remoteService.getConnectionType())
      if (status === 'disconnected' && info) {
        setRemoteError(info)
        setRemoteMode('none')
        setRemoteAssistCode('')
        setRemoteGuestConnected(false)
        setRemoteConnectionType(null)
      }
    })

    const unsubGuest = remoteService.onGuestStatus((connected) => {
      setRemoteGuestConnected(connected)
      
      // 当 guest 连接时，host 发送完整画布数据
      if (connected && remoteMode === 'host') {
        // 延迟一点发送，确保 guest 已准备好接收
        setTimeout(() => {
          remoteService.send({
            type: 'full_sync',
            nodes,
            edges,
            variables,
          })
        }, 500)
      }
    })

    return () => {
      unsubStatus()
      unsubGuest()
    }
  }, [remoteMode, nodes, edges, variables])

  // 弹窗关闭时清理远程协助
  useEffect(() => {
    if (!open && remoteMode !== 'none') {
      // 弹窗关闭但远程协助仍在进行，不断开连接
      // 用户可以继续使用远程协助功能
    }
  }, [open, remoteMode])

  // 开始编辑工作流
  const startEditWorkflow = (workflow: HubWorkflow) => {
    setEditingWorkflow(workflow)
    setEditName(workflow.name)
    setEditDescription(workflow.description || '')
    setEditAuthor(workflow.author || '')
    setEditCategory(workflow.category || '其他')
    setEditTags(workflow.tags?.join(', ') || '')
    setUpdateError(null)
    setEditContentMode('none')
    setEditUploadedWorkflow(null)
    setEditUploadFileName('')
  }

  // 取消编辑
  const cancelEdit = () => {
    setEditingWorkflow(null)
    setUpdateError(null)
    setEditContentMode('none')
    setEditUploadedWorkflow(null)
    setEditUploadFileName('')
  }

  // 处理编辑时的文件上传
  const handleEditFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.json')) {
      setUpdateError('请上传 JSON 格式的文件')
      return
    }

    if (file.size > 1024 * 1024) {
      setUpdateError('文件大小不能超过 1MB')
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const content = JSON.parse(e.target?.result as string)
        
        if (!content || typeof content !== 'object') {
          setUpdateError('无效的 JSON 文件')
          return
        }

        if (!Array.isArray(content.nodes)) {
          setUpdateError('无效的工作流文件：缺少 nodes 字段')
          return
        }

        if (!Array.isArray(content.edges)) {
          setUpdateError('无效的工作流文件：缺少 edges 字段')
          return
        }

        if (content.nodes.length === 0) {
          setUpdateError('工作流文件中没有任何节点')
          return
        }

        setEditUploadedWorkflow({
          nodes: content.nodes,
          edges: content.edges,
          variables: content.variables || []
        })
        setEditUploadFileName(file.name)
        setUpdateError(null)
        setEditContentMode('file')
      } catch {
        setUpdateError('JSON 解析失败，请检查文件格式')
      }
    }
    reader.onerror = () => {
      setUpdateError('文件读取失败')
    }
    reader.readAsText(file)
    event.target.value = ''
  }

  // 清除编辑时上传的文件
  const handleClearEditUpload = () => {
    setEditUploadedWorkflow(null)
    setEditUploadFileName('')
    setEditContentMode('none')
    setUpdateError(null)
  }

  // 更新工作流
  const handleUpdateWorkflow = async () => {
    if (!editingWorkflow) return

    if (!editName.trim()) {
      setUpdateError('请输入工作流名称')
      return
    }

    // 如果选择了更新内容，验证内容
    let workflowContent = null
    if (editContentMode === 'current') {
      if (nodes.length === 0) {
        setUpdateError('当前工作流为空，无法更新')
        return
      }
      workflowContent = { nodes, edges, variables }
    } else if (editContentMode === 'file') {
      if (!editUploadedWorkflow) {
        setUpdateError('请先上传工作流文件')
        return
      }
      workflowContent = editUploadedWorkflow
    }

    setUpdating(true)
    setUpdateError(null)

    try {
      const tagsArray = editTags
        .split(/[,，]/)
        .map((t) => t.trim())
        .filter(Boolean)
        .slice(0, 5)

      const updateData: Record<string, unknown> = {
        clientId: getClientId(),
        name: editName.trim(),
        description: editDescription.trim(),
        author: editAuthor.trim() || '匿名',
        category: editCategory,
        tags: tagsArray,
      }

      // 如果有新的工作流内容，添加到更新数据中
      if (workflowContent) {
        updateData.content = workflowContent
      }

      const response = await fetch(`${hubUrl}/api/workflows/${editingWorkflow.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || '更新失败')
      }

      const successMsg = workflowContent ? '工作流信息和内容已更新' : '工作流信息已更新'
      await alert(successMsg, { title: '更新成功' })
      cancelEdit()
      loadMyWorkflows()
      // 清除浏览缓存以便刷新时获取最新数据
      cacheRef.current = null
    } catch (e) {
      setUpdateError(e instanceof Error ? e.message : '更新失败，请稍后重试')
    } finally {
      setUpdating(false)
    }
  }

  // 从我的工作流删除
  const handleDeleteMyWorkflow = async (workflow: HubWorkflow) => {
    const confirmed = await confirm(
      `确定要删除工作流「${workflow.name}」吗？此操作不可恢复。`,
      { title: '删除工作流', type: 'warning', confirmText: '删除', cancelText: '取消' }
    )

    if (!confirmed) return

    try {
      const response = await fetch(`${hubUrl}/api/workflows/${workflow.id}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientId: getClientId() }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || '删除失败')
      }

      await alert('工作流已成功删除', { title: '删除成功' })
      loadMyWorkflows()
      // 清除浏览缓存
      cacheRef.current = null
    } catch (e) {
      await alert(e instanceof Error ? e.message : '删除失败，请稍后重试', { title: '删除失败' })
    }
  }

  // 加载工作流列表（带缓存支持）
  const loadWorkflows = useCallback(async (forceRefresh = false, append = false) => {
    // 如果是追加加载且没有更多数据，直接返回
    if (append && !hasMore) return

    // 检查缓存是否有效（相同的查询条件，且不是追加加载）
    const cache = cacheRef.current
    if (!forceRefresh && !append && cache && 
        cache.hubUrl === hubUrl &&
        cache.sortBy === sortBy &&
        cache.category === selectedCategory &&
        cache.search === searchQuery) {
      // 使用缓存数据
      setWorkflows(cache.workflows)
      setCategories(cache.categories)
      setHasMore(cache.hasMore)
      return
    }

    // 设置加载状态
    if (append) {
      setLoadingMore(true)
    } else {
      setLoading(true)
    }
    setError(null)

    try {
      const currentPage = append ? page : 1
      const params = new URLSearchParams({
        page: String(currentPage),
        limit: '24',
        sort: sortBy,
      })

      if (selectedCategory && selectedCategory !== '全部') {
        params.set('category', selectedCategory)
      }

      if (searchQuery) {
        params.set('search', searchQuery)
      }

      const response = await fetch(`${hubUrl}/api/workflows?${params}`)

      if (!response.ok) {
        throw new Error('加载失败')
      }

      const data = await response.json()
      const newWorkflows = data.workflows || []
      const totalPages = data.pagination?.totalPages || 1
      const newHasMore = currentPage < totalPages

      if (append) {
        // 追加数据
        setWorkflows(prev => [...prev, ...newWorkflows])
        setPage(currentPage + 1)
      } else {
        // 替换数据
        setWorkflows(newWorkflows)
        setPage(2) // 下次加载第2页
      }
      setHasMore(newHasMore)

      // 更新缓存（只缓存首页数据）
      if (!append) {
        cacheRef.current = {
          workflows: newWorkflows,
          categories: categories,
          hasMore: newHasMore,
          sortBy,
          category: selectedCategory,
          search: searchQuery,
          hubUrl,
        }
      }
    } catch (e) {
      if (!append) {
        setError('无法连接到仓库服务器，请检查网络或仓库地址')
        setWorkflows([])
      }
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [hubUrl, page, sortBy, selectedCategory, searchQuery, categories, hasMore])

  // 强制刷新（用户点击刷新按钮或发布成功后）
  const forceRefresh = useCallback(() => {
    cacheRef.current = null
    setPage(1)
    setHasMore(true)
    loadCategories()
    loadWorkflows(true, false)
  }, [loadCategories, loadWorkflows])

  // 加载更多
  const loadMore = useCallback(() => {
    if (!loadingMore && hasMore) {
      loadWorkflows(false, true)
    }
  }, [loadWorkflows, loadingMore, hasMore])

  // 滚动监听 - 无限滚动
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement
    const { scrollTop, scrollHeight, clientHeight } = target
    // 当滚动到距离底部 200px 时加载更多
    if (scrollHeight - scrollTop - clientHeight < 200) {
      loadMore()
    }
  }, [loadMore])

  // 初始加载（仅首次打开时从服务器加载）
  useEffect(() => {
    if (open && activeTab === 'browse') {
      if (!hasLoadedRef.current) {
        // 首次加载
        hasLoadedRef.current = true
        loadCategories()
        loadWorkflows(true)
      } else {
        // 非首次，使用缓存
        loadWorkflows(false)
      }
    }
    // 切换到"我的工作流"标签时加载
    if (open && activeTab === 'my') {
      loadMyWorkflows()
    }
    // 切换到"留言板"标签时加载
    if (open && activeTab === 'guestbook') {
      loadGuestbook(false)
    }
  }, [open, activeTab])

  // 弹窗关闭时重置状态
  useEffect(() => {
    if (!open) {
      setSelectedWorkflow(null)
      setPublishSuccess(false)
      setPublishError(null)
    }
  }, [open])

  // 搜索、排序、分类变化时需要重新加载
  useEffect(() => {
    if (!open || activeTab !== 'browse' || !hasLoadedRef.current) return

    const timer = setTimeout(() => {
      setPage(1)
      setHasMore(true)
      loadWorkflows(true, false) // 查询条件变化时强制刷新
    }, 300)

    return () => clearTimeout(timer)
  }, [searchQuery, sortBy, selectedCategory])

  // 下载工作流
  const handleDownload = async (workflow: HubWorkflow, mode: 'replace' | 'merge' = 'replace') => {
    if (mode === 'replace') {
      const confirmed = await confirm(
        `确定要导入工作流「${workflow.name}」吗？这将替换当前的工作流内容。`,
        { title: '覆盖导入', confirmText: '确定覆盖', cancelText: '取消' }
      )
      if (!confirmed) return
    }

    setDownloading(true)

    try {
      const response = await fetch(`${hubUrl}/api/workflows/${workflow.id}/download`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error('下载失败')
      }

      const data = await response.json()

      if (data.content) {
        if (mode === 'merge') {
          // 扩展导入：追加到现有画布
          const success = mergeWorkflow(JSON.stringify(data.content))
          if (success) {
            // 更新本地下载量显示
            setWorkflows(prev => prev.map(w => 
              w.id === workflow.id ? { ...w, download_count: w.download_count + 1 } : w
            ))
            setSelectedWorkflow(prev => 
              prev && prev.id === workflow.id ? { ...prev, download_count: prev.download_count + 1 } : prev
            )
            // 清除缓存以便下次刷新时获取最新数据
            cacheRef.current = null
            
            await alert(`工作流「${workflow.name}」已追加到当前画布！`, { title: '导入成功' })
          } else {
            await alert('导入失败，工作流格式可能不正确', { title: '导入失败' })
          }
        } else {
          // 覆盖导入 - 添加工作流名称
          const workflowData = {
            ...data.content,
            name: workflow.name,
          }
          importWorkflow(workflowData)
          
          // 更新本地下载量显示
          setWorkflows(prev => prev.map(w => 
            w.id === workflow.id ? { ...w, download_count: w.download_count + 1 } : w
          ))
          // 清除缓存以便下次刷新时获取最新数据
          cacheRef.current = null
          
          await alert(`工作流「${workflow.name}」已成功导入！`, { title: '导入成功' })
        }
        setSelectedWorkflow(null)
        onClose()
      }
    } catch (e) {
      await alert('无法下载工作流，请稍后重试', { title: '导入失败' })
    } finally {
      setDownloading(false)
    }
  }

  // 检查是否为工作流所有者
  const checkOwnership = async (workflowId: string) => {
    try {
      const response = await fetch(`${hubUrl}/api/workflows/${workflowId}/check-owner`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientId: getClientId() }),
      })
      if (response.ok) {
        const data = await response.json()
        setIsOwner(data.isOwner)
      } else {
        setIsOwner(false)
      }
    } catch {
      setIsOwner(false)
    }
  }

  // 删除工作流
  const handleDelete = async (workflow: HubWorkflow) => {
    const confirmed = await confirm(
      `确定要删除工作流「${workflow.name}」吗？此操作不可恢复。`,
      { title: '删除工作流', type: 'warning', confirmText: '删除', cancelText: '取消' }
    )

    if (!confirmed) return

    setDeleting(true)

    try {
      const response = await fetch(`${hubUrl}/api/workflows/${workflow.id}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientId: getClientId() }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || '删除失败')
      }

      await alert('工作流已成功删除', { title: '删除成功' })
      setSelectedWorkflow(null)
      forceRefresh()
    } catch (e) {
      await alert(e instanceof Error ? e.message : '删除失败，请稍后重试', { title: '删除失败' })
    } finally {
      setDeleting(false)
    }
  }

  // 发布工作流
  const handlePublish = async () => {
    if (!publishName.trim()) {
      setPublishError('请输入工作流名称')
      return
    }

    // 根据发布模式选择工作流内容
    const workflowContent = publishMode === 'file' ? uploadedWorkflow : { nodes, edges, variables }

    if (!workflowContent || (workflowContent.nodes?.length || 0) === 0) {
      setPublishError(publishMode === 'file' ? '请先上传工作流文件' : '当前工作流为空，无法发布')
      return
    }

    setPublishing(true)
    setPublishError(null)
    setPublishSuccess(false)

    try {
      // 先检查是否已存在
      const checkResponse = await fetch(`${hubUrl}/api/workflows/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: workflowContent,
        }),
      })

      if (checkResponse.ok) {
        const checkData = await checkResponse.json()
        if (checkData.exists) {
          setPublishError(`该工作流已存在于仓库中（名称：${checkData.existingName}）`)
          setPublishing(false)
          return
        }
      } else {
        const errorData = await checkResponse.json()
        setPublishError(errorData.error || '验证失败')
        setPublishing(false)
        return
      }

      // 发布
      const tagsArray = publishTags
        .split(/[,，]/)
        .map((t) => t.trim())
        .filter(Boolean)
        .slice(0, 5)

      const publishData: Record<string, unknown> = {
        name: publishName.trim(),
        description: publishDescription.trim() || undefined,
        author: publishAuthor.trim() || '匿名',
        category: publishCategory,
        content: workflowContent,
        clientId: getClientId(),
      }

      // 只有当有标签时才添加 tags 字段
      if (tagsArray.length > 0) {
        publishData.tags = tagsArray
      }

      const response = await fetch(`${hubUrl}/api/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(publishData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        // 如果有详细的验证错误，显示第一个
        if (errorData.details && errorData.details.length > 0) {
          const firstError = errorData.details[0]
          throw new Error(firstError.msg || errorData.error || '发布失败')
        }
        throw new Error(errorData.error || '发布失败')
      }

      setPublishSuccess(true)
      setPublishName('')
      setPublishDescription('')
      setPublishTags('')
      setUploadedWorkflow(null)
      setUploadFileName('')

      // 刷新列表（强制刷新缓存）
      setTimeout(() => {
        setActiveTab('browse')
        forceRefresh()
      }, 2000)
    } catch (e) {
      setPublishError(e instanceof Error ? e.message : '发布失败，请稍后重试')
    } finally {
      setPublishing(false)
    }
  }

  // 处理文件上传
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // 检查文件类型
    if (!file.name.endsWith('.json')) {
      setPublishError('请上传 JSON 格式的文件')
      return
    }

    // 检查文件大小（最大 1MB）
    if (file.size > 1024 * 1024) {
      setPublishError('文件大小不能超过 1MB')
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const content = JSON.parse(e.target?.result as string)
        
        // 基本验证
        if (!content || typeof content !== 'object') {
          setPublishError('无效的 JSON 文件')
          return
        }

        if (!Array.isArray(content.nodes)) {
          setPublishError('无效的工作流文件：缺少 nodes 字段')
          return
        }

        if (!Array.isArray(content.edges)) {
          setPublishError('无效的工作流文件：缺少 edges 字段')
          return
        }

        if (content.nodes.length === 0) {
          setPublishError('工作流文件中没有任何节点')
          return
        }

        // 设置上传的工作流
        setUploadedWorkflow({
          nodes: content.nodes,
          edges: content.edges,
          variables: content.variables || []
        })
        setUploadFileName(file.name)
        setPublishError(null)
        setPublishMode('file')
      } catch {
        setPublishError('JSON 解析失败，请检查文件格式')
      }
    }
    reader.onerror = () => {
      setPublishError('文件读取失败')
    }
    reader.readAsText(file)

    // 清空 input 以便重复选择同一文件
    event.target.value = ''
  }

  // 清除上传的文件
  const handleClearUpload = () => {
    setUploadedWorkflow(null)
    setUploadFileName('')
    setPublishMode('current')
    setPublishError(null)
  }

  // 保存仓库设置
  const handleSaveSettings = () => {
    const url = tempHubUrl.trim() || DEFAULT_HUB_URL
    setHubUrl(url)
    setHubUrlState(url)
    setActiveTab('browse')
    setPage(1)
  }

  // 重置仓库地址
  const handleResetUrl = () => {
    setTempHubUrl(DEFAULT_HUB_URL)
  }

  if (!open) return null

  return (
    <div 
      className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-purple-700 to-purple-900 text-white">
          <div className="flex items-center gap-3">
            <Package className="w-6 h-6" />
            <h2 className="text-xl font-bold">工作流仓库</h2>
          </div>
          <div className="flex items-center gap-2">
            {/* 标签页切换 */}
            <div className="flex bg-white/20 rounded-lg p-1 mr-4">
              <button
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1 ${
                  activeTab === 'browse' ? 'bg-white text-purple-600' : 'text-white hover:bg-white/10'
                }`}
                onClick={() => setActiveTab('browse')}
              >
                <Search className="w-4 h-4" />
                浏览
              </button>
              <button
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1 ${
                  activeTab === 'my' ? 'bg-white text-purple-600' : 'text-white hover:bg-white/10'
                }`}
                onClick={() => setActiveTab('my')}
              >
                <FolderOpen className="w-4 h-4" />
                我的
              </button>
              <button
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1 ${
                  activeTab === 'publish' ? 'bg-white text-purple-600' : 'text-white hover:bg-white/10'
                }`}
                onClick={() => {
                  setActiveTab('publish')
                  setPublishSuccess(false)
                  setPublishError(null)
                }}
              >
                <Upload className="w-4 h-4" />
                发布
              </button>
              <button
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1 ${
                  activeTab === 'guestbook' ? 'bg-white text-purple-600' : 'text-white hover:bg-white/10'
                }`}
                onClick={() => setActiveTab('guestbook')}
              >
                <MessageSquare className="w-4 h-4" />
                留言板
              </button>
              <button
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1 ${
                  activeTab === 'remote' ? 'bg-white text-purple-600' : 'text-white hover:bg-white/10'
                }`}
                onClick={() => setActiveTab('remote')}
              >
                <Users className="w-4 h-4" />
                远程协助
                {remoteMode !== 'none' && (
                  <span className={`w-2 h-2 rounded-full ${remoteStatus === 'connected' ? 'bg-green-400' : 'bg-yellow-400'} animate-pulse`} />
                )}
              </button>
              <button
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'settings' ? 'bg-white text-purple-600' : 'text-white hover:bg-white/10'
                }`}
                onClick={() => setActiveTab('settings')}
              >
                <Settings className="w-4 h-4" />
              </button>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-white/20 rounded">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 内容区域 - 使用calc计算剩余高度 */}
        <div style={{ height: 'calc(90vh - 73px)' }}>
          {/* 浏览标签页 */}
          {activeTab === 'browse' && (
            <div className="h-full flex flex-col">
              {/* 搜索和筛选 */}
              <div className="p-4 border-b bg-gray-50 flex flex-wrap gap-4 items-center flex-shrink-0">
                <div className="flex-1 min-w-[200px] relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="搜索工作流..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
                  {categories.map((cat) => (
                    <option key={cat.name} value={cat.name}>
                      {cat.name} ({cat.count})
                    </option>
                  ))}
                </Select>
                <Select value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)}>
                  <option value="newest">最新发布</option>
                  <option value="popular">最受欢迎</option>
                  <option value="downloads">下载最多</option>
                </Select>
                <Button variant="outline" size="sm" onClick={forceRefresh} disabled={loading}>
                  <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                  刷新
                </Button>
              </div>

              {/* 工作流列表 */}
              <div 
                ref={listContainerRef}
                className="flex-1 overflow-y-auto p-4"
                style={{ minHeight: 0 }}
                onScroll={handleScroll}
              >
                {loading ? (
                  <div className="flex items-center justify-center h-64">
                    <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                  </div>
                ) : error ? (
                  <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                    <AlertCircle className="w-12 h-12 mb-4 text-red-400" />
                    <p>{error}</p>
                    <Button variant="outline" size="sm" className="mt-4" onClick={forceRefresh}>
                      重试
                    </Button>
                  </div>
                ) : workflows.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                    <Package className="w-12 h-12 mb-4 text-gray-300" />
                    <p>暂无工作流</p>
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {workflows.map((workflow) => (
                        <div
                          key={workflow.id}
                          className="border rounded-lg p-4 hover:shadow-md transition-shadow bg-white cursor-pointer"
                          onClick={() => {
                            setSelectedWorkflow(workflow)
                            setIsOwner(false)
                            checkOwnership(workflow.id)
                            // 重置评论状态
                            setComments([])
                            setCommentsPage(1)
                            setCommentsHasMore(true)
                            loadComments(workflow.id, false)
                          }}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <h3 className="font-semibold text-gray-900 truncate flex-1">{workflow.name}</h3>
                            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded ml-2">
                              {workflow.category}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 line-clamp-2 mb-3 min-h-[40px]">
                            {workflow.description || '暂无描述'}
                          </p>
                          <div className="flex items-center justify-between text-xs text-gray-500">
                            <div className="flex items-center gap-3">
                              <span className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                {workflow.author}
                              </span>
                              <span className="flex items-center gap-1">
                                <Package className="w-3 h-3" />
                                {workflow.node_count} 节点
                              </span>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className="flex items-center gap-1">
                                <MessageSquare className="w-3 h-3" />
                                {workflow.comment_count || 0}
                              </span>
                              <span className="flex items-center gap-1">
                                <Download className="w-3 h-3" />
                                {workflow.download_count}
                              </span>
                            </div>
                          </div>
                          {workflow.tags && workflow.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {workflow.tags.slice(0, 3).map((tag, i) => (
                                <span key={i} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                    {/* 加载更多提示 */}
                    {loadingMore && (
                      <div className="flex items-center justify-center py-4 mt-4">
                        <Loader2 className="w-5 h-5 animate-spin text-purple-500 mr-2" />
                        <span className="text-sm text-gray-500">加载更多...</span>
                      </div>
                    )}
                    {!hasMore && workflows.length > 0 && (
                      <div className="text-center py-4 mt-4 text-sm text-gray-400">
                        已加载全部工作流
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}

          {/* 我的工作流标签页 */}
          {activeTab === 'my' && (
            <div className="h-full flex flex-col">
              <div className="p-4 border-b bg-gray-50 flex-shrink-0">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <FolderOpen className="w-5 h-5 text-purple-500" />
                    <span className="font-medium">我发布的工作流</span>
                    <span className="text-sm text-gray-500">({myWorkflows.length})</span>
                  </div>
                  <Button variant="outline" size="sm" onClick={loadMyWorkflows} disabled={myWorkflowsLoading}>
                    <RefreshCw className={`w-4 h-4 mr-1 ${myWorkflowsLoading ? 'animate-spin' : ''}`} />
                    刷新
                  </Button>
                </div>
                {/* 用户身份ID显示 */}
                <div className="flex items-center gap-2 p-2 bg-purple-50 rounded-lg border border-purple-200">
                  <Key className="w-4 h-4 text-purple-500 flex-shrink-0" />
                  <span className="text-xs text-purple-700 flex-shrink-0">我的身份ID:</span>
                  <code className="text-xs bg-white px-2 py-0.5 rounded border flex-1 truncate font-mono text-gray-700">
                    {getClientId()}
                  </code>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-purple-600 hover:text-purple-700 hover:bg-purple-100"
                    onClick={async () => {
                      navigator.clipboard.writeText(getClientId())
                      await alert('身份ID已复制到剪贴板，你可以在其他浏览器中使用此ID', { title: '已复制' })
                    }}
                  >
                    <Copy className="w-3.5 h-3.5 mr-1" />
                    复制
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  💡 提示：复制身份ID后，可在其他浏览器的设置中导入，以保持你的发布者身份
                </p>
              </div>

              <div className="flex-1 overflow-y-auto p-4" style={{ minHeight: 0 }}>
                {myWorkflowsLoading ? (
                  <div className="flex items-center justify-center h-64">
                    <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                  </div>
                ) : myWorkflowsError ? (
                  <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                    <AlertCircle className="w-12 h-12 mb-4 text-red-400" />
                    <p>{myWorkflowsError}</p>
                    <Button variant="outline" size="sm" className="mt-4" onClick={loadMyWorkflows}>
                      重试
                    </Button>
                  </div>
                ) : myWorkflows.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                    <Package className="w-12 h-12 mb-4 text-gray-300" />
                    <p>你还没有发布过工作流</p>
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-4"
                      onClick={() => setActiveTab('publish')}
                    >
                      <Upload className="w-4 h-4 mr-1" />
                      去发布
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {myWorkflows.map((workflow) => (
                      <div
                        key={workflow.id}
                        className="border rounded-lg p-4 bg-white hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-semibold text-gray-900">{workflow.name}</h3>
                              <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                                {workflow.category}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                              {workflow.description || '暂无描述'}
                            </p>
                            <div className="flex items-center gap-4 text-xs text-gray-500">
                              <span className="flex items-center gap-1">
                                <Package className="w-3 h-3" />
                                {workflow.node_count} 节点
                              </span>
                              <span className="flex items-center gap-1">
                                <Download className="w-3 h-3" />
                                {workflow.download_count} 下载
                              </span>
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {new Date(workflow.created_at).toLocaleDateString()}
                              </span>
                            </div>
                            {workflow.tags && workflow.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {workflow.tags.map((tag, i) => (
                                  <span key={i} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                          <div className="flex gap-2 ml-4">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => startEditWorkflow(workflow)}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="border-red-300 text-red-600 hover:bg-red-50"
                              onClick={() => handleDeleteMyWorkflow(workflow)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 发布标签页 */}
          {activeTab === 'publish' && (
            <div className="h-full overflow-y-auto p-6">
                <div className="max-w-xl mx-auto space-y-6">
                <div className="text-center mb-8">
                  <Upload className="w-12 h-12 mx-auto text-purple-500 mb-3" />
                  <h3 className="text-lg font-semibold">发布工作流到仓库</h3>
                  <p className="text-sm text-gray-500 mt-1">分享你的工作流，帮助其他用户</p>
                </div>

                {publishSuccess ? (
                  <div className="text-center py-8">
                    <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
                    <h3 className="text-lg font-semibold text-green-700">发布成功！</h3>
                    <p className="text-sm text-gray-500 mt-2">你的工作流已成功发布到仓库</p>
                  </div>
                ) : (
                  <>
                    {/* 发布模式选择 */}
                    <div className="flex gap-2 p-1 bg-gray-100 rounded-lg">
                      <button
                        className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors flex items-center justify-center gap-2 ${
                          publishMode === 'current'
                            ? 'bg-white text-purple-600 shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                        onClick={() => {
                          setPublishMode('current')
                          setPublishError(null)
                        }}
                      >
                        <Package className="w-4 h-4" />
                        发布当前工作流
                      </button>
                      <button
                        className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors flex items-center justify-center gap-2 ${
                          publishMode === 'file'
                            ? 'bg-white text-purple-600 shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                        onClick={() => {
                          setPublishMode('file')
                          setPublishError(null)
                        }}
                      >
                        <FileUp className="w-4 h-4" />
                        上传 JSON 文件
                      </button>
                    </div>

                    {/* 当前工作流信息 */}
                    {publishMode === 'current' && (
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-sm text-blue-800">
                          <strong>当前工作流：</strong>
                          {nodes.length} 个节点，{edges.length} 条连线
                        </p>
                      </div>
                    )}

                    {/* 文件上传区域 */}
                    {publishMode === 'file' && (
                      <div className="space-y-3">
                        {uploadedWorkflow ? (
                          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <FileJson className="w-5 h-5 text-green-600" />
                                <div>
                                  <p className="text-sm font-medium text-green-800">{uploadFileName}</p>
                                  <p className="text-xs text-green-600">
                                    {uploadedWorkflow.nodes.length} 个节点，{uploadedWorkflow.edges.length} 条连线
                                  </p>
                                </div>
                              </div>
                              <button
                                onClick={handleClearUpload}
                                className="p-1 hover:bg-green-100 rounded text-green-600"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ) : (
                          <label className="block">
                            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-purple-400 hover:bg-purple-50 transition-colors">
                              <FileUp className="w-10 h-10 mx-auto text-gray-400 mb-3" />
                              <p className="text-sm text-gray-600 mb-1">点击或拖拽上传工作流 JSON 文件</p>
                              <p className="text-xs text-gray-400">支持 .json 格式，最大 1MB</p>
                            </div>
                            <input
                              type="file"
                              accept=".json"
                              onChange={handleFileUpload}
                              className="hidden"
                            />
                          </label>
                        )}
                      </div>
                    )}

                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="publish-name">
                          工作流名称 <span className="text-red-500">*</span>
                        </Label>
                        <Input
                          id="publish-name"
                          value={publishName}
                          onChange={(e) => setPublishName(e.target.value)}
                          placeholder="给你的工作流起个名字"
                          maxLength={50}
                        />
                      </div>

                      <div>
                        <Label htmlFor="publish-description">功能描述</Label>
                        <textarea
                          id="publish-description"
                          value={publishDescription}
                          onChange={(e) => setPublishDescription(e.target.value)}
                          placeholder="描述一下这个工作流的功能和用途..."
                          className="w-full px-3 py-2 border rounded-md text-sm resize-none h-24"
                          maxLength={500}
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="publish-author">作者名称</Label>
                          <Input
                            id="publish-author"
                            value={publishAuthor}
                            onChange={(e) => setPublishAuthor(e.target.value)}
                            placeholder="匿名"
                            maxLength={30}
                          />
                        </div>
                        <div>
                          <Label htmlFor="publish-category">分类</Label>
                          <Select
                            id="publish-category"
                            value={publishCategory}
                            onChange={(e) => setPublishCategory(e.target.value)}
                          >
                            <option value="数据采集">数据采集</option>
                            <option value="自动化操作">自动化操作</option>
                            <option value="表单填写">表单填写</option>
                            <option value="AI应用">AI应用</option>
                            <option value="定时任务">定时任务</option>
                            <option value="其他">其他</option>
                          </Select>
                        </div>
                      </div>

                      <div>
                        <Label htmlFor="publish-tags">标签（用逗号分隔，最多5个）</Label>
                        <Input
                          id="publish-tags"
                          value={publishTags}
                          onChange={(e) => setPublishTags(e.target.value)}
                          placeholder="例如：爬虫, 自动化, 签到"
                        />
                      </div>
                    </div>

                    {publishError && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                        <span className="text-sm">{publishError}</span>
                      </div>
                    )}

                    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-sm text-yellow-800">
                        <strong>⚠️ 注意：</strong>
                        发布前请确保工作流中不包含敏感信息（如 API Key、密码等），系统会自动过滤部分敏感内容。
                      </p>
                    </div>

                    <Button
                      className="w-full"
                      onClick={handlePublish}
                      disabled={
                        publishing ||
                        (publishMode === 'current' && nodes.length === 0) ||
                        (publishMode === 'file' && !uploadedWorkflow)
                      }
                    >
                      {publishing ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          发布中...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4 mr-2" />
                          发布工作流
                        </>
                      )}
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* 留言板标签页 */}
          {activeTab === 'guestbook' && (
            <div className="h-full flex flex-col">
              {/* 发布留言区域 */}
              <div className="p-4 border-b bg-gray-50 flex-shrink-0">
                <div className="max-w-2xl mx-auto">
                  <div className="flex items-center gap-2 mb-3">
                    <MessageSquare className="w-5 h-5 text-purple-500" />
                    <span className="font-medium">发表留言</span>
                  </div>
                  <div className="space-y-3">
                    <div className="flex gap-3">
                      <Input
                        placeholder="昵称（可选）"
                        value={guestbookNickname}
                        onChange={(e) => setGuestbookNickname(e.target.value)}
                        className="w-32"
                        maxLength={20}
                      />
                      <Select
                        value={guestbookType}
                        onChange={(e) => setGuestbookType(e.target.value)}
                        className="w-32"
                      >
                        {MESSAGE_TYPES.map((type) => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </Select>
                    </div>
                    <div className="flex gap-2">
                      <textarea
                        placeholder="写下你的留言..."
                        value={guestbookContent}
                        onChange={(e) => setGuestbookContent(e.target.value)}
                        className="flex-1 px-3 py-2 border rounded-md text-sm resize-none h-20"
                        maxLength={1000}
                      />
                      <Button
                        onClick={handleSubmitGuestbook}
                        disabled={submittingGuestbook || !guestbookContent.trim()}
                        className="self-end"
                      >
                        {submittingGuestbook ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Send className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* 留言列表 */}
              <div 
                className="flex-1 overflow-y-auto p-4" 
                style={{ minHeight: 0 }}
                onScroll={(e) => {
                  const target = e.target as HTMLDivElement
                  const { scrollTop, scrollHeight, clientHeight } = target
                  // 滚动到距离底部 100px 时加载更多
                  if (scrollHeight - scrollTop - clientHeight < 100 && !guestbookLoading && guestbookHasMore) {
                    loadGuestbook(true)
                  }
                }}
              >
                <div className="max-w-2xl mx-auto">
                  {guestbookLoading && guestbookMessages.length === 0 ? (
                    <div className="flex items-center justify-center h-64">
                      <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                  ) : guestbookMessages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                      <MessageSquare className="w-12 h-12 mb-4 text-gray-300" />
                      <p>暂无留言，来发表第一条吧！</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {guestbookMessages.map((msg) => (
                        <div key={msg.id} className="border rounded-lg p-4 bg-white">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-gray-900">{msg.nickname}</span>
                              <span className={`text-xs px-2 py-0.5 rounded ${
                                msg.message_type === '建议' ? 'bg-blue-100 text-blue-700' :
                                msg.message_type === '问题求助' ? 'bg-yellow-100 text-yellow-700' :
                                msg.message_type === 'Bug报告' ? 'bg-red-100 text-red-700' :
                                msg.message_type === '功能请求' ? 'bg-purple-100 text-purple-700' :
                                msg.message_type === '闲聊' ? 'bg-green-100 text-green-700' :
                                'bg-gray-100 text-gray-700'
                              }`}>
                                {msg.message_type}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-500">
                                {new Date(msg.created_at).toLocaleString()}
                              </span>
                              {msg.isOwner && (
                                <button
                                  onClick={() => handleDeleteGuestbook(msg.id)}
                                  className="text-xs text-red-500 hover:text-red-700 hover:underline"
                                >
                                  删除
                                </button>
                              )}
                            </div>
                          </div>
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      ))}
                      {guestbookLoading && (
                        <div className="flex items-center justify-center py-4">
                          <Loader2 className="w-5 h-5 animate-spin text-purple-500 mr-2" />
                          <span className="text-sm text-gray-500">加载更多...</span>
                        </div>
                      )}
                      {!guestbookHasMore && guestbookMessages.length > 0 && (
                        <div className="text-center py-4 text-sm text-gray-400">
                          已加载全部留言
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 远程协助标签页 */}
          {activeTab === 'remote' && (
            <div className="h-full overflow-y-auto p-6">
              <div className="max-w-xl mx-auto space-y-6">
                <div className="text-center mb-8">
                  <Users className="w-12 h-12 mx-auto text-purple-500 mb-3" />
                  <h3 className="text-lg font-semibold">远程协助</h3>
                  <p className="text-sm text-gray-500 mt-1">让其他用户远程帮助你操作工作流画布</p>
                </div>

                {remoteMode === 'none' ? (
                  // 未开始状态 - 选择模式
                  <div className="space-y-6">
                    {/* 作为主机 - 生成协助码 */}
                    <div className="p-6 border-2 border-dashed border-purple-200 rounded-xl bg-purple-50/50 hover:border-purple-400 transition-colors">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="p-3 rounded-full bg-purple-100">
                          <Link className="w-6 h-6 text-purple-600" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-900">我需要帮助</h4>
                          <p className="text-sm text-gray-500">生成协助码，让他人远程帮助你</p>
                        </div>
                      </div>
                      <Button
                        className="w-full"
                        onClick={handleCreateRemoteSession}
                        disabled={remoteLoading}
                      >
                        {remoteLoading ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            生成中...
                          </>
                        ) : (
                          <>
                            <Link className="w-4 h-4 mr-2" />
                            生成协助码
                          </>
                        )}
                      </Button>
                    </div>

                    {/* 作为协助者 - 输入协助码 */}
                    <div className="p-6 border-2 border-dashed border-blue-200 rounded-xl bg-blue-50/50 hover:border-blue-400 transition-colors">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="p-3 rounded-full bg-blue-100">
                          <Users className="w-6 h-6 text-blue-600" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-900">我来帮助他人</h4>
                          <p className="text-sm text-gray-500">输入对方的协助码，远程帮助操作</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Input
                          placeholder="输入6位协助码"
                          value={remoteInputCode}
                          onChange={(e) => setRemoteInputCode(e.target.value.toUpperCase().slice(0, 6))}
                          className="flex-1 text-center text-lg font-mono tracking-widest"
                          maxLength={6}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && remoteInputCode.length === 6) {
                              handleJoinRemoteSession()
                            }
                          }}
                        />
                        <Button
                          onClick={handleJoinRemoteSession}
                          disabled={remoteLoading || remoteInputCode.length !== 6}
                        >
                          {remoteLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            '加入'
                          )}
                        </Button>
                      </div>
                    </div>

                    {remoteError && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                        <span className="text-sm">{remoteError}</span>
                      </div>
                    )}

                    {/* 说明 */}
                    <div className="p-4 bg-gray-50 border rounded-lg">
                      <h4 className="font-medium mb-2">使用说明</h4>
                      <ul className="text-sm text-gray-600 space-y-1">
                        <li>• 协助码有效期为 5 分钟，过期需重新生成</li>
                        <li>• 每个协助码只允许一人加入（一对一）</li>
                        <li>• 使用 P2P 直连技术，数据直接在两端传输，延迟极低</li>
                        <li>• 连接后双方画布完全同步，任何操作都会实时同步</li>
                        <li>• 双方都可以添加、删除、移动模块和连线</li>
                        <li>• 你可以随时断开连接结束协助</li>
                      </ul>
                    </div>
                  </div>
                ) : remoteMode === 'host' ? (
                  // 主机模式 - 等待/已连接
                  <div className="space-y-6">
                    <div className="p-6 border rounded-xl bg-white shadow-sm">
                      <div className="text-center mb-6">
                        <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${
                          remoteStatus === 'connected' 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          <span className={`w-2 h-2 rounded-full ${
                            remoteStatus === 'connected' ? 'bg-green-500' : 'bg-yellow-500'
                          } animate-pulse`} />
                          {remoteStatus === 'connected' ? '已连接' : '等待协助者加入...'}
                        </div>
                      </div>

                      <div className="mb-6">
                        <Label className="text-center block mb-2">你的协助码</Label>
                        <div className="flex items-center justify-center gap-2">
                          <div className="text-4xl font-mono font-bold tracking-[0.5em] text-purple-600 bg-purple-50 px-6 py-4 rounded-xl border-2 border-purple-200">
                            {remoteAssistCode}
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              navigator.clipboard.writeText(remoteAssistCode)
                              alert('协助码已复制', { title: '已复制' })
                            }}
                          >
                            <Copy className="w-4 h-4" />
                          </Button>
                        </div>
                        <p className="text-center text-sm text-gray-500 mt-2">
                          将此协助码发送给需要帮助你的人
                        </p>
                      </div>

                      {remoteGuestConnected && (
                        <div className="p-3 bg-green-50 border border-green-200 rounded-lg mb-4">
                          <div className="flex items-center gap-2 text-green-700">
                            <CheckCircle className="w-4 h-4" />
                            <span className="text-sm font-medium">
                              协助者已连接，画布已同步，双方操作实时共享
                              {remoteConnectionType === 'p2p' && (
                                <span className="ml-2 px-1.5 py-0.5 bg-green-100 text-green-600 text-xs rounded">P2P 直连</span>
                              )}
                            </span>
                          </div>
                        </div>
                      )}

                      <Button
                        variant="outline"
                        className="w-full border-red-300 text-red-600 hover:bg-red-50"
                        onClick={handleCloseRemoteSession}
                      >
                        <Unlink className="w-4 h-4 mr-2" />
                        断开连接
                      </Button>
                    </div>

                    {remoteError && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                        <span className="text-sm">{remoteError}</span>
                      </div>
                    )}
                  </div>
                ) : (
                  // 协助者模式 - 连接中/已连接
                  <div className="space-y-6">
                    <div className="p-6 border rounded-xl bg-white shadow-sm">
                      <div className="text-center mb-6">
                        <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${
                          remoteStatus === 'connected' 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-blue-100 text-blue-700'
                        }`}>
                          <span className={`w-2 h-2 rounded-full ${
                            remoteStatus === 'connected' ? 'bg-green-500' : 'bg-blue-500'
                          } animate-pulse`} />
                          {remoteStatus === 'connected' ? '已连接' : '正在连接...'}
                        </div>
                      </div>

                      <div className="mb-6 text-center">
                        <p className="text-sm text-gray-500 mb-2">正在协助</p>
                        <div className="text-2xl font-mono font-bold tracking-widest text-blue-600">
                          {remoteAssistCode}
                        </div>
                      </div>

                      {remoteStatus === 'connected' && (
                        <div className="p-3 bg-green-50 border border-green-200 rounded-lg mb-4">
                          <div className="flex items-center gap-2 text-green-700">
                            <CheckCircle className="w-4 h-4" />
                            <span className="text-sm font-medium">
                              已连接，画布已同步，你的操作会实时同步到对方
                              {remoteConnectionType === 'p2p' && (
                                <span className="ml-2 px-1.5 py-0.5 bg-green-100 text-green-600 text-xs rounded">P2P 直连</span>
                              )}
                            </span>
                          </div>
                        </div>
                      )}

                      <Button
                        variant="outline"
                        className="w-full border-red-300 text-red-600 hover:bg-red-50"
                        onClick={handleCloseRemoteSession}
                      >
                        <Unlink className="w-4 h-4 mr-2" />
                        断开连接
                      </Button>
                    </div>

                    {remoteError && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                        <span className="text-sm">{remoteError}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 设置标签页 */}
          {activeTab === 'settings' && (
            <div className="h-full overflow-y-auto p-6">
              <div className="max-w-xl mx-auto space-y-6">
                <div className="text-center mb-8">
                  <Settings className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                  <h3 className="text-lg font-semibold">仓库设置</h3>
                </div>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="hub-url">仓库服务器地址</Label>
                    <Input
                      id="hub-url"
                      value={tempHubUrl}
                      onChange={(e) => setTempHubUrl(e.target.value)}
                      placeholder={DEFAULT_HUB_URL}
                    />
                    <p className="text-xs text-gray-500 mt-1">默认地址：{DEFAULT_HUB_URL}</p>
                  </div>

                  <div className="flex gap-2">
                    <Button variant="outline" onClick={handleResetUrl}>
                      重置为默认
                    </Button>
                    <Button onClick={handleSaveSettings}>保存设置</Button>
                  </div>
                </div>

                {/* 身份ID管理 */}
                <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg space-y-3">
                  <div className="flex items-center gap-2">
                    <Key className="w-5 h-5 text-purple-500" />
                    <h4 className="font-medium text-purple-900">身份ID管理</h4>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-purple-700 flex-shrink-0">当前ID:</span>
                    <code className="text-xs bg-white px-2 py-1 rounded border flex-1 truncate font-mono text-gray-700">
                      {getClientId()}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-purple-600 hover:text-purple-700 hover:bg-purple-100"
                      onClick={async () => {
                        navigator.clipboard.writeText(getClientId())
                        await alert('身份ID已复制到剪贴板', { title: '已复制' })
                      }}
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                  <div className="pt-2 border-t border-purple-200">
                    <Label htmlFor="import-client-id" className="text-sm text-purple-700">导入身份ID</Label>
                    <div className="flex gap-2 mt-1">
                      <Input
                        id="import-client-id"
                        value={tempClientId}
                        onChange={(e) => setTempClientId(e.target.value)}
                        placeholder="粘贴其他浏览器的身份ID..."
                        className="flex-1"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={!tempClientId.trim()}
                        onClick={async () => {
                          const confirmed = await confirm('导入后将替换当前的身份ID，你之前发布的工作流将不再显示在"我的"列表中（除非你保存了当前ID）。确定要继续吗？', { title: '确认导入身份ID？' })
                          if (confirmed) {
                            localStorage.setItem('workflow_hub_client_id', tempClientId.trim())
                            setTempClientId('')
                            loadMyWorkflows()
                            await alert('身份ID已更新，现在你可以管理该ID下发布的工作流了', { title: '导入成功' })
                          }
                        }}
                      >
                        导入
                      </Button>
                    </div>
                    <p className="text-xs text-purple-600 mt-1">
                      从其他浏览器的"我的"页面复制身份ID，粘贴到这里即可同步身份
                    </p>
                  </div>
                </div>

                <div className="p-4 bg-gray-50 border rounded-lg">
                  <h4 className="font-medium mb-2">关于工作流仓库</h4>
                  <p className="text-sm text-gray-600">
                    工作流仓库是一个公共平台，用户可以在这里分享和下载工作流。
                    你也可以搭建自己的私有仓库服务器，只需将地址改为你的服务器地址即可。
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 工作流详情弹窗 */}
        {selectedWorkflow && (
          <div className="fixed inset-0 z-60 bg-black/40 flex items-center justify-center p-4 animate-fade-in">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col animate-scale-in">
              <div className="p-6 overflow-y-auto flex-1">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-bold">{selectedWorkflow.name}</h3>
                    <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                      {selectedWorkflow.category}
                    </span>
                  </div>
                  <button onClick={() => setSelectedWorkflow(null)} className="p-1 hover:bg-gray-100 rounded">
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <p className="text-gray-600 mb-4">{selectedWorkflow.description || '暂无描述'}</p>

                <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                  <div className="flex items-center gap-2 text-gray-600">
                    <User className="w-4 h-4" />
                    <span>作者：{selectedWorkflow.author}</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600">
                    <Package className="w-4 h-4" />
                    <span>节点数：{selectedWorkflow.node_count}</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600">
                    <Download className="w-4 h-4" />
                    <span>下载量：{selectedWorkflow.download_count}</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600">
                    <Calendar className="w-4 h-4" />
                    <span>发布于：{new Date(selectedWorkflow.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {selectedWorkflow.tags && selectedWorkflow.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    <Tag className="w-4 h-4 text-gray-400" />
                    {selectedWorkflow.tags.map((tag, i) => (
                      <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                <div className="flex gap-2">
                  <Button
                    className="flex-1"
                    onClick={() => handleDownload(selectedWorkflow, 'replace')}
                    disabled={downloading || deleting}
                  >
                    {downloading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        导入中...
                      </>
                    ) : (
                      <>
                        <Download className="w-4 h-4 mr-2" />
                        覆盖导入
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => handleDownload(selectedWorkflow, 'merge')}
                    disabled={downloading || deleting}
                  >
                    {downloading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        导入中...
                      </>
                    ) : (
                      <>
                        <Plus className="w-4 h-4 mr-2" />
                        追加导入
                      </>
                    )}
                  </Button>
                </div>
                {isOwner && (
                  <Button
                    variant="outline"
                    className="w-full mt-2 border-red-300 text-red-600 hover:bg-red-50"
                    onClick={() => handleDelete(selectedWorkflow)}
                    disabled={deleting || downloading}
                  >
                    {deleting ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        删除中...
                      </>
                    ) : (
                      <>
                        <Trash2 className="w-4 h-4 mr-2" />
                        删除此工作流
                      </>
                    )}
                  </Button>
                )}

                {/* 评论区 */}
                <div className="mt-6 pt-4 border-t">
                  <div className="flex items-center gap-2 mb-4">
                    <MessageSquare className="w-5 h-5 text-purple-500" />
                    <span className="font-medium">评论区</span>
                    <span className="text-sm text-gray-500">({comments.length})</span>
                  </div>

                  {/* 发表评论 */}
                  <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                    <div className="flex gap-2 mb-2">
                      <Input
                        placeholder="昵称（可选）"
                        value={commentNickname}
                        onChange={(e) => setCommentNickname(e.target.value)}
                        className="w-28"
                        maxLength={20}
                      />
                      <Select
                        value={commentType}
                        onChange={(e) => setCommentType(e.target.value)}
                        className="w-24"
                      >
                        {COMMENT_TYPES.map((type) => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </Select>
                    </div>
                    <div className="flex gap-2">
                      <Input
                        placeholder="写下你的评论..."
                        value={commentContent}
                        onChange={(e) => setCommentContent(e.target.value)}
                        className="flex-1"
                        maxLength={500}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey && commentContent.trim()) {
                            handleSubmitComment(selectedWorkflow.id)
                          }
                        }}
                      />
                      <Button
                        size="sm"
                        onClick={() => handleSubmitComment(selectedWorkflow.id)}
                        disabled={submittingComment || !commentContent.trim()}
                      >
                        {submittingComment ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Send className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* 评论列表 */}
                  <div 
                    className="space-y-3 max-h-60 overflow-y-auto"
                    onScroll={(e) => {
                      const target = e.target as HTMLDivElement
                      const { scrollTop, scrollHeight, clientHeight } = target
                      // 滚动到距离底部 50px 时加载更多
                      if (scrollHeight - scrollTop - clientHeight < 50 && !commentsLoading && commentsHasMore && selectedWorkflow) {
                        loadComments(selectedWorkflow.id, true)
                      }
                    }}
                  >
                    {commentsLoading && comments.length === 0 ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="w-5 h-5 animate-spin text-purple-500" />
                      </div>
                    ) : comments.length === 0 ? (
                      <div className="text-center py-8 text-gray-500 text-sm">
                        暂无评论，来发表第一条吧！
                      </div>
                    ) : (
                      <>
                        {comments.map((comment) => (
                          <div key={comment.id} className="p-3 bg-white border rounded-lg">
                            <div className="flex items-center justify-between mb-1">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-sm">{comment.nickname}</span>
                                <span className={`text-xs px-1.5 py-0.5 rounded ${
                                  comment.comment_type === '使用心得' ? 'bg-blue-100 text-blue-700' :
                                  comment.comment_type === '问题求助' ? 'bg-yellow-100 text-yellow-700' :
                                  comment.comment_type === '建议改进' ? 'bg-green-100 text-green-700' :
                                  comment.comment_type === '感谢' ? 'bg-pink-100 text-pink-700' :
                                  'bg-gray-100 text-gray-700'
                                }`}>
                                  {comment.comment_type}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-400">
                                  {new Date(comment.created_at).toLocaleString()}
                                </span>
                                {comment.isOwner && (
                                  <button
                                    onClick={() => handleDeleteComment(comment.id)}
                                    className="text-xs text-red-500 hover:text-red-700 hover:underline"
                                  >
                                    删除
                                  </button>
                                )}
                              </div>
                            </div>
                            <p className="text-sm text-gray-700">{comment.content}</p>
                          </div>
                        ))}
                        {commentsLoading && (
                          <div className="flex items-center justify-center py-2">
                            <Loader2 className="w-4 h-4 animate-spin text-purple-500 mr-2" />
                            <span className="text-xs text-gray-500">加载更多...</span>
                          </div>
                        )}
                        {!commentsHasMore && comments.length > 0 && (
                          <div className="text-center py-2 text-xs text-gray-400">
                            已加载全部评论
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 编辑工作流弹窗 */}
        {editingWorkflow && (
          <div className="fixed inset-0 z-60 bg-black/40 flex items-center justify-center p-4 animate-fade-in">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col animate-scale-in">
              <div className="p-6 overflow-y-auto">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold">编辑工作流</h3>
                  <button onClick={cancelEdit} className="p-1 hover:bg-gray-100 rounded">
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="edit-name">
                      工作流名称 <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="edit-name"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      placeholder="工作流名称"
                      maxLength={50}
                    />
                  </div>

                  <div>
                    <Label htmlFor="edit-description">功能描述</Label>
                    <textarea
                      id="edit-description"
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      placeholder="描述一下这个工作流的功能和用途..."
                      className="w-full px-3 py-2 border rounded-md text-sm resize-none h-24"
                      maxLength={500}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="edit-author">作者名称</Label>
                      <Input
                        id="edit-author"
                        value={editAuthor}
                        onChange={(e) => setEditAuthor(e.target.value)}
                        placeholder="匿名"
                        maxLength={30}
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-category">分类</Label>
                      <Select
                        id="edit-category"
                        value={editCategory}
                        onChange={(e) => setEditCategory(e.target.value)}
                      >
                        <option value="数据采集">数据采集</option>
                        <option value="自动化操作">自动化操作</option>
                        <option value="表单填写">表单填写</option>
                        <option value="AI应用">AI应用</option>
                        <option value="定时任务">定时任务</option>
                        <option value="其他">其他</option>
                      </Select>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="edit-tags">标签（用逗号分隔，最多5个）</Label>
                    <Input
                      id="edit-tags"
                      value={editTags}
                      onChange={(e) => setEditTags(e.target.value)}
                      placeholder="例如：爬虫, 自动化, 签到"
                    />
                  </div>

                  {/* 更新工作流内容 */}
                  <div className="border-t pt-4">
                    <Label className="mb-2 block">更新工作流内容（可选）</Label>
                    <div className="flex gap-2 p-1 bg-gray-100 rounded-lg mb-3">
                      <button
                        className={`flex-1 py-2 px-3 rounded-md text-xs font-medium transition-colors ${
                          editContentMode === 'none'
                            ? 'bg-white text-gray-700 shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                        onClick={() => {
                          setEditContentMode('none')
                          setEditUploadedWorkflow(null)
                          setEditUploadFileName('')
                        }}
                      >
                        不更新内容
                      </button>
                      <button
                        className={`flex-1 py-2 px-3 rounded-md text-xs font-medium transition-colors ${
                          editContentMode === 'current'
                            ? 'bg-white text-purple-600 shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                        onClick={() => {
                          setEditContentMode('current')
                          setEditUploadedWorkflow(null)
                          setEditUploadFileName('')
                        }}
                      >
                        用当前工作流
                      </button>
                      <button
                        className={`flex-1 py-2 px-3 rounded-md text-xs font-medium transition-colors ${
                          editContentMode === 'file'
                            ? 'bg-white text-purple-600 shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                        onClick={() => setEditContentMode('file')}
                      >
                        上传文件
                      </button>
                    </div>

                    {editContentMode === 'current' && (
                      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-sm text-blue-800">
                          将使用当前画布的工作流替换：{nodes.length} 个节点，{edges.length} 条连线
                        </p>
                      </div>
                    )}

                    {editContentMode === 'file' && (
                      <div>
                        {editUploadedWorkflow ? (
                          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <FileJson className="w-5 h-5 text-green-600" />
                                <div>
                                  <p className="text-sm font-medium text-green-800">{editUploadFileName}</p>
                                  <p className="text-xs text-green-600">
                                    {editUploadedWorkflow.nodes.length} 个节点，{editUploadedWorkflow.edges.length} 条连线
                                  </p>
                                </div>
                              </div>
                              <button
                                onClick={handleClearEditUpload}
                                className="p-1 hover:bg-green-100 rounded text-green-600"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ) : (
                          <label className="block">
                            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center cursor-pointer hover:border-purple-400 hover:bg-purple-50 transition-colors">
                              <FileUp className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                              <p className="text-sm text-gray-600">点击上传工作流 JSON 文件</p>
                            </div>
                            <input
                              type="file"
                              accept=".json"
                              onChange={handleEditFileUpload}
                              className="hidden"
                            />
                          </label>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {updateError && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span className="text-sm">{updateError}</span>
                  </div>
                )}

                <div className="flex gap-2 mt-6">
                  <Button variant="outline" className="flex-1" onClick={cancelEdit} disabled={updating}>
                    取消
                  </Button>
                  <Button className="flex-1" onClick={handleUpdateWorkflow} disabled={updating}>
                    {updating ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        保存中...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        保存修改
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 确认对话框 */}
        {ConfirmDialog}
      </div>
    </div>
  )
}
