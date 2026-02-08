/**
 * 远程协助服务 - P2P 优先，WebSocket 中转备用
 */

import type { Node, Edge } from '@xyflow/react'

// 获取仓库地址
function getHubUrl(): string {
  return localStorage.getItem('workflow_hub_url') || 'https://hub.pmhs.top'
}

// 获取 WebSocket 地址
function getWsUrl(): string {
  const hubUrl = getHubUrl()
  return hubUrl.replace(/^http/, 'ws') + '/ws/remote'
}

// 获取客户端 ID
function getClientId(): string {
  let clientId = localStorage.getItem('workflow_hub_client_id')
  if (!clientId) {
    clientId = 'client_' + Math.random().toString(36).substring(2) + Date.now().toString(36)
    localStorage.setItem('workflow_hub_client_id', clientId)
  }
  return clientId
}

// WebRTC 配置
const RTC_CONFIG: RTCConfiguration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
  ],
}

export interface RemoteSession {
  assistCode: string
  role: 'host' | 'guest'
  status: 'connecting' | 'waiting' | 'connected' | 'disconnected'
  guestConnected?: boolean
  connectionType?: 'p2p' | 'relay'
}

export type RemoteMessageType = 
  | 'mouse_move'
  | 'mouse_click'
  | 'node_add'
  | 'node_delete'
  | 'node_move'
  | 'node_update'
  | 'nodes_change'
  | 'edge_add'
  | 'edge_delete'
  | 'edges_change'
  | 'variable_add'
  | 'variable_update'
  | 'variable_delete'
  | 'sync_request'
  | 'sync_data'
  | 'full_sync'

export interface RemoteMessage {
  type: RemoteMessageType | string
  [key: string]: unknown
}

export interface SyncData {
  nodes: Node[]
  edges: Edge[]
  variables: unknown[]
  workflowName?: string
}

type MessageHandler = (message: RemoteMessage) => void
type StatusHandler = (status: RemoteSession['status'], info?: string) => void
type GuestStatusHandler = (connected: boolean) => void
type SyncDataHandler = (data: SyncData) => void

class RemoteService {
  private ws: WebSocket | null = null
  private session: RemoteSession | null = null
  private messageHandlers: Set<MessageHandler> = new Set()
  private statusHandlers: Set<StatusHandler> = new Set()
  private guestStatusHandlers: Set<GuestStatusHandler> = new Set()
  private syncDataHandlers: Set<SyncDataHandler> = new Set()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  
  // WebRTC 相关
  private peerConnection: RTCPeerConnection | null = null
  private dataChannel: RTCDataChannel | null = null
  private pendingCandidates: RTCIceCandidate[] = []
  
  // 防止操作循环的标记
  private isApplyingRemote = false

  // 创建协助码（作为 host）
  async createSession(): Promise<{ success: boolean; assistCode?: string; error?: string }> {
    try {
      const response = await fetch(`${getHubUrl()}/api/remote/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientId: getClientId() }),
      })

      const data = await response.json()
      if (!response.ok) {
        return { success: false, error: data.error || '创建失败' }
      }

      this.session = {
        assistCode: data.assistCode,
        role: 'host',
        status: 'waiting',
        guestConnected: false,
        connectionType: 'relay',
      }

      this.connectWebSocket()
      return { success: true, assistCode: data.assistCode }
    } catch (e) {
      return { success: false, error: '网络错误' }
    }
  }

  // 加入协助会话（作为 guest）
  async joinSession(assistCode: string): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await fetch(`${getHubUrl()}/api/remote/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientId: getClientId(), assistCode }),
      })

      const data = await response.json()
      if (!response.ok) {
        return { success: false, error: data.error || '加入失败' }
      }

      this.session = {
        assistCode,
        role: 'guest',
        status: 'connecting',
        connectionType: 'relay',
      }

      this.connectWebSocket()
      return { success: true }
    } catch (e) {
      return { success: false, error: '网络错误' }
    }
  }

  // 关闭会话
  async closeSession(): Promise<void> {
    this.stopHeartbeat()
    this.closePeerConnection()

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    try {
      await fetch(`${getHubUrl()}/api/remote/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientId: getClientId() }),
      })
    } catch (e) {
      // 忽略错误
    }

    this.session = null
    this.notifyStatus('disconnected')
  }

  // 连接 WebSocket
  private connectWebSocket(): void {
    if (this.ws) {
      this.ws.close()
    }

    const wsUrl = getWsUrl()
    console.log('[Remote] 连接 WebSocket:', wsUrl)

    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('[Remote] WebSocket 已连接')
      if (this.session) {
        this.ws?.send(JSON.stringify({
          type: 'auth',
          clientId: getClientId(),
          assistCode: this.session.assistCode,
          role: this.session.role,
        }))
      }
      this.startHeartbeat()
    }

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        this.handleMessage(message)
      } catch (e) {
        console.error('[Remote] 消息解析错误:', e)
      }
    }

    this.ws.onclose = () => {
      console.log('[Remote] WebSocket 已断开')
      this.stopHeartbeat()
      // 如果 P2P 连接还在，不通知断开
      if (this.dataChannel?.readyState === 'open') {
        console.log('[Remote] P2P 连接仍在，忽略 WebSocket 断开')
        return
      }
      if (this.session && this.session.status !== 'disconnected') {
        this.notifyStatus('disconnected', '连接已断开')
      }
    }

    this.ws.onerror = (error) => {
      console.error('[Remote] WebSocket 错误:', error)
    }
  }

  // 处理收到的消息
  private handleMessage(message: RemoteMessage): void {
    const { type } = message

    switch (type) {
      case 'auth_success':
        if (this.session) {
          this.session.status = this.session.role === 'host' ? 'waiting' : 'connected'
          if (message.hasGuest) {
            this.session.guestConnected = true
            this.session.status = 'connected'
          }
          this.notifyStatus(this.session.status)
          
          if (this.session.role === 'guest') {
            this.send({ type: 'sync_request' })
          }
        }
        break

      case 'auth_failed':
        this.notifyStatus('disconnected', message.message as string)
        this.closeSession()
        break

      case 'guest_connected':
        if (this.session) {
          this.session.guestConnected = true
          this.session.status = 'connected'
          this.notifyStatus('connected')
          this.notifyGuestStatus(true)
          // Host 发起 P2P 连接
          this.initiatePeerConnection()
        }
        break

      case 'guest_left':
        if (this.session) {
          this.session.guestConnected = false
          this.session.status = 'waiting'
          this.session.connectionType = 'relay'
          this.notifyStatus('waiting')
          this.notifyGuestStatus(false)
          this.closePeerConnection()
        }
        break

      case 'host_connected':
        if (this.session) {
          this.session.status = 'connected'
          this.notifyStatus('connected')
          this.send({ type: 'sync_request' })
        }
        break

      case 'session_closed':
        this.notifyStatus('disconnected', message.reason as string)
        this.closePeerConnection()
        this.session = null
        if (this.ws) {
          this.ws.close()
          this.ws = null
        }
        break

      case 'heartbeat_ack':
        break

      // WebRTC 信令
      case 'offer':
        this.handleOffer(message.sdp as RTCSessionDescriptionInit)
        break

      case 'answer':
        this.handleAnswer(message.sdp as RTCSessionDescriptionInit)
        break

      case 'ice_candidate':
        this.handleIceCandidate(message.candidate as RTCIceCandidateInit)
        break

      case 'sync_data':
      case 'full_sync':
        if (message.nodes && message.edges) {
          this.notifySyncData({
            nodes: message.nodes as Node[],
            edges: message.edges as Edge[],
            variables: (message.variables as unknown[]) || [],
            workflowName: message.workflowName as string,
          })
        }
        break

      default:
        this.messageHandlers.forEach(handler => handler(message))
    }
  }

  // ========== WebRTC P2P ==========
  
  private initiatePeerConnection(): void {
    if (this.session?.role !== 'host') return
    
    console.log('[Remote] Host 发起 P2P 连接')
    this.createPeerConnection(true)
  }

  private createPeerConnection(isHost: boolean): void {
    this.closePeerConnection()

    this.peerConnection = new RTCPeerConnection(RTC_CONFIG)

    this.peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        this.sendViaWs({ type: 'ice_candidate', candidate: event.candidate.toJSON() })
      }
    }

    this.peerConnection.onconnectionstatechange = () => {
      const state = this.peerConnection?.connectionState
      console.log('[Remote] P2P 连接状态:', state)
      
      if (state === 'connected' && this.session) {
        this.session.connectionType = 'p2p'
        console.log('[Remote] P2P 直连已建立！')
        this.notifyStatus('connected')
      } else if (state === 'failed' || state === 'disconnected') {
        // P2P 失败，回退到 WebSocket 中转
        if (this.session) {
          this.session.connectionType = 'relay'
        }
      }
    }

    if (isHost) {
      this.dataChannel = this.peerConnection.createDataChannel('remote', { ordered: true })
      this.setupDataChannel(this.dataChannel)
      
      this.peerConnection.createOffer()
        .then(offer => this.peerConnection!.setLocalDescription(offer))
        .then(() => {
          this.sendViaWs({ type: 'offer', sdp: this.peerConnection!.localDescription })
        })
        .catch(e => console.error('[Remote] 创建 Offer 失败:', e))
    } else {
      this.peerConnection.ondatachannel = (event) => {
        console.log('[Remote] 收到 DataChannel')
        this.dataChannel = event.channel
        this.setupDataChannel(this.dataChannel)
      }
    }
  }

  private setupDataChannel(channel: RTCDataChannel): void {
    channel.onopen = () => {
      console.log('[Remote] DataChannel 已打开')
    }

    channel.onclose = () => {
      console.log('[Remote] DataChannel 已关闭')
      if (this.session && this.session.status !== 'disconnected') {
        this.session.connectionType = 'relay'
        // 尝试重连 WebSocket
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
          this.notifyStatus('disconnected', 'P2P 连接已断开')
        }
      }
    }

    channel.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        // P2P 消息直接处理
        if (message.type === 'sync_data' || message.type === 'full_sync') {
          if (message.nodes && message.edges) {
            this.notifySyncData({
              nodes: message.nodes as Node[],
              edges: message.edges as Edge[],
              variables: (message.variables as unknown[]) || [],
              workflowName: message.workflowName as string,
            })
          }
        } else {
          this.messageHandlers.forEach(handler => handler(message))
        }
      } catch (e) {
        console.error('[Remote] P2P 消息解析错误:', e)
      }
    }
  }

  private async handleOffer(sdp: RTCSessionDescriptionInit): Promise<void> {
    console.log('[Remote] 收到 Offer')
    this.createPeerConnection(false)
    
    try {
      await this.peerConnection!.setRemoteDescription(new RTCSessionDescription(sdp))
      for (const c of this.pendingCandidates) {
        await this.peerConnection!.addIceCandidate(c)
      }
      this.pendingCandidates = []
      
      const answer = await this.peerConnection!.createAnswer()
      await this.peerConnection!.setLocalDescription(answer)
      this.sendViaWs({ type: 'answer', sdp: answer })
    } catch (e) {
      console.error('[Remote] 处理 Offer 失败:', e)
    }
  }

  private async handleAnswer(sdp: RTCSessionDescriptionInit): Promise<void> {
    console.log('[Remote] 收到 Answer')
    try {
      await this.peerConnection!.setRemoteDescription(new RTCSessionDescription(sdp))
      for (const c of this.pendingCandidates) {
        await this.peerConnection!.addIceCandidate(c)
      }
      this.pendingCandidates = []
    } catch (e) {
      console.error('[Remote] 处理 Answer 失败:', e)
    }
  }

  private async handleIceCandidate(candidateInit: RTCIceCandidateInit): Promise<void> {
    const candidate = new RTCIceCandidate(candidateInit)
    if (this.peerConnection?.remoteDescription) {
      await this.peerConnection.addIceCandidate(candidate)
    } else {
      this.pendingCandidates.push(candidate)
    }
  }

  private closePeerConnection(): void {
    if (this.dataChannel) {
      this.dataChannel.close()
      this.dataChannel = null
    }
    if (this.peerConnection) {
      this.peerConnection.close()
      this.peerConnection = null
    }
    this.pendingCandidates = []
  }

  // ========== 发送消息 ==========

  // 通过 WebSocket 发送（用于信令）
  private sendViaWs(message: RemoteMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  // 发送消息（优先 P2P，否则 WebSocket）
  send(message: RemoteMessage): void {
    if (this.dataChannel?.readyState === 'open') {
      this.dataChannel.send(JSON.stringify(message))
    } else {
      this.sendViaWs(message)
    }
  }

  sendOperation(message: RemoteMessage): void {
    if (this.isApplyingRemote) return
    this.send(message)
  }

  setApplyingRemote(value: boolean): void {
    this.isApplyingRemote = value
  }

  isApplyingRemoteOperation(): boolean {
    return this.isApplyingRemote
  }

  // ========== 心跳 ==========

  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'heartbeat' }))
      }
    }, 5000)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  // ========== 通知 ==========

  private notifyStatus(status: RemoteSession['status'], info?: string): void {
    this.statusHandlers.forEach(handler => handler(status, info))
  }

  private notifyGuestStatus(connected: boolean): void {
    this.guestStatusHandlers.forEach(handler => handler(connected))
  }

  private notifySyncData(data: SyncData): void {
    this.syncDataHandlers.forEach(handler => handler(data))
  }

  // ========== 公共方法 ==========

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler)
    return () => this.messageHandlers.delete(handler)
  }

  onStatus(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler)
    return () => this.statusHandlers.delete(handler)
  }

  onGuestStatus(handler: GuestStatusHandler): () => void {
    this.guestStatusHandlers.add(handler)
    return () => this.guestStatusHandlers.delete(handler)
  }

  onSyncData(handler: SyncDataHandler): () => void {
    this.syncDataHandlers.add(handler)
    return () => this.syncDataHandlers.delete(handler)
  }

  getSession(): RemoteSession | null {
    return this.session
  }

  isConnected(): boolean {
    return this.session?.status === 'connected'
  }

  isHost(): boolean {
    return this.session?.role === 'host'
  }

  isGuest(): boolean {
    return this.session?.role === 'guest'
  }

  getConnectionType(): 'p2p' | 'relay' | null {
    return this.session?.connectionType || null
  }
}

export const remoteService = new RemoteService()
