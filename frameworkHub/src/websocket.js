/**
 * WebSocket 服务 - 远程协助实时通信
 */

import { WebSocketServer } from 'ws'
import {
  getSession,
  getSessionByClientId,
  findSessionAsGuest,
  setHostWs,
  setGuestWs,
  updateHeartbeat,
  cleanupSession,
  removeGuest
} from './routes/remote.js'

// 心跳检测间隔
const HEARTBEAT_INTERVAL = 5000 // 5秒

// 存储所有连接
const clients = new Map() // clientId -> { ws, role, assistCode, lastPing }

export function setupWebSocket(server) {
  const wss = new WebSocketServer({ 
    server,
    path: '/ws/remote'
  })

  console.log('✅ WebSocket 服务已启动 (路径: /ws/remote)')

  wss.on('connection', (ws) => {
    let clientId = null
    let role = null // 'host' | 'guest'

    console.log('[WS] 新连接')

    ws.isAlive = true

    ws.on('pong', () => {
      ws.isAlive = true
      if (clientId) {
        updateHeartbeat(clientId)
      }
    })

    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data.toString())
        handleMessage(ws, message, { clientId, role }, (newClientId, newRole) => {
          clientId = newClientId
          role = newRole
        })
      } catch (e) {
        console.error('[WS] 消息解析错误:', e)
        ws.send(JSON.stringify({ type: 'error', message: '消息格式错误' }))
      }
    })

    ws.on('close', () => {
      console.log(`[WS] 连接关闭: ${clientId || 'unknown'}`)
      if (clientId) {
        handleDisconnect(clientId, role)
        clients.delete(clientId)
      }
    })

    ws.on('error', (err) => {
      console.error('[WS] 连接错误:', err.message)
    })
  })

  // 心跳检测
  const heartbeatInterval = setInterval(() => {
    wss.clients.forEach((ws) => {
      if (ws.isAlive === false) {
        return ws.terminate()
      }
      ws.isAlive = false
      ws.ping()
    })
  }, HEARTBEAT_INTERVAL)

  wss.on('close', () => {
    clearInterval(heartbeatInterval)
  })

  return wss
}

function handleMessage(ws, message, context, setContext) {
  const { type } = message

  switch (type) {
    case 'auth': {
      // 认证并绑定会话
      const { clientId, assistCode, role: requestedRole } = message

      if (!clientId || !assistCode) {
        ws.send(JSON.stringify({ type: 'error', message: '缺少认证信息' }))
        return
      }

      const session = getSession(assistCode)
      if (!session) {
        ws.send(JSON.stringify({ type: 'auth_failed', message: '会话不存在' }))
        return
      }

      if (requestedRole === 'host') {
        if (session.hostId !== clientId) {
          ws.send(JSON.stringify({ type: 'auth_failed', message: '身份验证失败' }))
          return
        }
        setHostWs(clientId, ws)
        setContext(clientId, 'host')
        clients.set(clientId, { ws, role: 'host', assistCode, lastPing: Date.now() })
        
        ws.send(JSON.stringify({ 
          type: 'auth_success', 
          role: 'host',
          hasGuest: !!session.guestId 
        }))

        // 如果已有 guest，通知双方
        if (session.guestId && session.guestWs) {
          session.guestWs.send(JSON.stringify({ type: 'host_connected' }))
          ws.send(JSON.stringify({ type: 'guest_connected' }))
        }

        console.log(`[WS] Host 认证成功: ${assistCode}`)
      } else if (requestedRole === 'guest') {
        if (session.guestId !== clientId) {
          ws.send(JSON.stringify({ type: 'auth_failed', message: '身份验证失败' }))
          return
        }
        const sess = setGuestWs(clientId, ws)
        setContext(clientId, 'guest')
        clients.set(clientId, { ws, role: 'guest', assistCode, lastPing: Date.now() })

        ws.send(JSON.stringify({ type: 'auth_success', role: 'guest' }))

        // 通知 host
        if (sess && sess.hostWs) {
          sess.hostWs.send(JSON.stringify({ type: 'guest_connected' }))
        }

        console.log(`[WS] Guest 认证成功: ${assistCode}`)
      }
      break
    }

    case 'heartbeat': {
      // 心跳响应
      if (context.clientId) {
        updateHeartbeat(context.clientId)
      }
      ws.send(JSON.stringify({ type: 'heartbeat_ack', timestamp: Date.now() }))
      break
    }

    // WebRTC 信令消息 - 转发给对方
    case 'offer':
    case 'answer':
    case 'ice_candidate': {
      forwardToOther(context, message)
      break
    }

    case 'mouse_move':
    case 'mouse_click':
    case 'node_select':
    case 'node_move':
    case 'node_add':
    case 'node_delete':
    case 'edge_add':
    case 'edge_delete':
    case 'viewport_change':
    case 'node_config':
    case 'sync_request':
    case 'sync_data':
    case 'full_sync':
    case 'nodes_change':
    case 'nodes_position':
    case 'edges_change':
    case 'node_update':
    case 'variable_change':
    case 'chat': {
      // 转发给对方
      forwardToOther(context, message)
      break
    }

    default:
      console.log(`[WS] 未知消息类型: ${type}`)
  }
}

function forwardToOther(context, message) {
  const { clientId, role } = context
  if (!clientId) return

  let session
  if (role === 'host') {
    session = getSessionByClientId(clientId)
    if (session && session.guestWs && session.guestWs.readyState === 1) {
      session.guestWs.send(JSON.stringify(message))
    }
  } else if (role === 'guest') {
    session = findSessionAsGuest(clientId)
    if (session && session.hostWs && session.hostWs.readyState === 1) {
      session.hostWs.send(JSON.stringify(message))
    }
  }
}

function handleDisconnect(clientId, role) {
  if (role === 'host') {
    const session = cleanupSession(clientId)
    if (session && session.guestWs) {
      try {
        session.guestWs.send(JSON.stringify({ type: 'session_closed', reason: 'host_disconnected' }))
      } catch (e) {}
    }
    console.log(`[WS] Host 断开，会话已清理`)
  } else if (role === 'guest') {
    const session = removeGuest(clientId)
    if (session && session.hostWs) {
      try {
        session.hostWs.send(JSON.stringify({ type: 'guest_left' }))
      } catch (e) {}
    }
    console.log(`[WS] Guest 断开`)
  }
}
