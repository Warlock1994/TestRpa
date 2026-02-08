/**
 * 远程协助 API 路由
 */

import express, { Router } from 'express'
import { body, param, validationResult } from 'express-validator'
import rateLimit from 'express-rate-limit'

const router = Router()

// 存储活跃的协助会话
// key: assistCode, value: { hostId, hostWs, guestId, guestWs, createdAt, lastHeartbeat }
const sessions = new Map()

// 存储 WebSocket 连接
// key: odId, value: ws
const connections = new Map()

// 协助码到会话的映射
const codeToSession = new Map()

// 生成6位数字协助码
function generateAssistCode() {
  let code
  do {
    code = Math.floor(100000 + Math.random() * 900000).toString()
  } while (codeToSession.has(code))
  return code
}

// 清理过期会话（5分钟未使用的协助码）
function cleanupExpiredSessions() {
  const now = Date.now()
  const expireTime = 5 * 60 * 1000 // 5分钟

  for (const [code, session] of codeToSession.entries()) {
    // 如果没有客人连接且超过5分钟，清理
    if (!session.guestId && now - session.createdAt > expireTime) {
      codeToSession.delete(code)
      sessions.delete(session.hostId)
      console.log(`[Remote] 协助码 ${code} 已过期，已清理`)
    }
  }
}

// 每分钟清理一次过期会话
setInterval(cleanupExpiredSessions, 60 * 1000)

// 速率限制
const createLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 5,
  message: { error: '创建协助码过于频繁，请稍后再试' }
})

/**
 * 创建远程协助码
 * POST /api/remote/create
 */
router.post('/create',
  createLimiter,
  [
    body('clientId')
      .isString()
      .trim()
      .isLength({ min: 16, max: 64 })
      .withMessage('无效的客户端ID')
  ],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({ error: '参数错误', details: errors.array() })
    }

    const { clientId } = req.body

    // 检查是否已有活跃会话
    if (sessions.has(clientId)) {
      const existingSession = sessions.get(clientId)
      return res.json({
        success: true,
        assistCode: existingSession.code,
        expiresIn: Math.max(0, 300 - Math.floor((Date.now() - existingSession.createdAt) / 1000)),
        isExisting: true
      })
    }

    // 生成新的协助码
    const assistCode = generateAssistCode()
    const session = {
      code: assistCode,
      hostId: clientId,
      hostWs: null,
      guestId: null,
      guestWs: null,
      createdAt: Date.now(),
      lastHeartbeat: Date.now(),
      status: 'waiting' // waiting, connected, closed
    }

    sessions.set(clientId, session)
    codeToSession.set(assistCode, session)

    console.log(`[Remote] 创建协助码: ${assistCode} (host: ${clientId.substring(0, 16)}...)`)

    res.json({
      success: true,
      assistCode,
      expiresIn: 300 // 5分钟
    })
  }
)

/**
 * 加入远程协助
 * POST /api/remote/join
 */
router.post('/join',
  [
    body('clientId')
      .isString()
      .trim()
      .isLength({ min: 16, max: 64 })
      .withMessage('无效的客户端ID'),
    body('assistCode')
      .isString()
      .trim()
      .matches(/^\d{6}$/)
      .withMessage('无效的协助码格式')
  ],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({ error: '参数错误', details: errors.array() })
    }

    const { clientId, assistCode } = req.body

    // 查找会话
    const session = codeToSession.get(assistCode)
    if (!session) {
      return res.status(404).json({ error: '协助码不存在或已过期' })
    }

    // 检查是否是自己的协助码
    if (session.hostId === clientId) {
      return res.status(400).json({ error: '不能加入自己的协助会话' })
    }

    // 检查是否已有人加入
    if (session.guestId && session.guestId !== clientId) {
      return res.status(400).json({ error: '该协助会话已被其他用户占用' })
    }

    // 检查是否过期
    if (Date.now() - session.createdAt > 5 * 60 * 1000) {
      codeToSession.delete(assistCode)
      sessions.delete(session.hostId)
      return res.status(400).json({ error: '协助码已过期' })
    }

    // 加入会话
    session.guestId = clientId
    session.status = 'connected'
    session.lastHeartbeat = Date.now()

    console.log(`[Remote] 用户加入协助: ${assistCode} (guest: ${clientId.substring(0, 16)}...)`)

    res.json({
      success: true,
      hostId: session.hostId
    })
  }
)

/**
 * 关闭远程协助
 * POST /api/remote/close
 */
router.post('/close',
  express.text({ type: '*/*' }), // 支持 sendBeacon 发送的 text/plain
  (req, res) => {
    let clientId
    
    // 处理不同格式的请求体
    if (typeof req.body === 'string') {
      try {
        const parsed = JSON.parse(req.body)
        clientId = parsed.clientId
      } catch (e) {
        return res.status(400).json({ error: '无效的请求格式' })
      }
    } else {
      clientId = req.body?.clientId
    }

    if (!clientId || typeof clientId !== 'string' || clientId.length < 16 || clientId.length > 64) {
      return res.status(400).json({ error: '无效的客户端ID' })
    }

    // 查找并关闭会话
    const session = sessions.get(clientId)
    if (session) {
      // 通知对方断开
      if (session.hostWs) {
        try {
          session.hostWs.send(JSON.stringify({ type: 'session_closed', reason: 'host_closed' }))
        } catch (e) {}
      }
      if (session.guestWs) {
        try {
          session.guestWs.send(JSON.stringify({ type: 'session_closed', reason: 'host_closed' }))
        } catch (e) {}
      }

      codeToSession.delete(session.code)
      sessions.delete(clientId)
      console.log(`[Remote] 会话关闭: ${session.code}`)
    }

    // 也检查是否作为 guest 在某个会话中
    for (const [hostId, sess] of sessions.entries()) {
      if (sess.guestId === clientId) {
        sess.guestId = null
        sess.guestWs = null
        sess.status = 'waiting'
        if (sess.hostWs) {
          try {
            sess.hostWs.send(JSON.stringify({ type: 'guest_left' }))
          } catch (e) {}
        }
        console.log(`[Remote] Guest 离开会话: ${sess.code}`)
      }
    }

    res.json({ success: true })
  }
)

/**
 * 检查会话状态
 * GET /api/remote/status/:assistCode
 */
router.get('/status/:assistCode',
  [param('assistCode').matches(/^\d{6}$/)],
  (req, res) => {
    const { assistCode } = req.params

    const session = codeToSession.get(assistCode)
    if (!session) {
      return res.status(404).json({ error: '会话不存在' })
    }

    res.json({
      status: session.status,
      hasGuest: !!session.guestId,
      createdAt: session.createdAt,
      expiresIn: Math.max(0, 300 - Math.floor((Date.now() - session.createdAt) / 1000))
    })
  }
)

// 导出会话管理函数供 WebSocket 使用
export function getSession(assistCode) {
  return codeToSession.get(assistCode)
}

export function getSessionByClientId(clientId) {
  return sessions.get(clientId)
}

export function findSessionAsGuest(clientId) {
  for (const session of sessions.values()) {
    if (session.guestId === clientId) {
      return session
    }
  }
  return null
}

export function setHostWs(clientId, ws) {
  const session = sessions.get(clientId)
  if (session) {
    session.hostWs = ws
    session.lastHeartbeat = Date.now()
  }
}

export function setGuestWs(clientId, ws) {
  for (const session of sessions.values()) {
    if (session.guestId === clientId) {
      session.guestWs = ws
      session.lastHeartbeat = Date.now()
      return session
    }
  }
  return null
}

export function updateHeartbeat(clientId) {
  const session = sessions.get(clientId)
  if (session) {
    session.lastHeartbeat = Date.now()
    return
  }
  // 也检查作为 guest
  for (const sess of sessions.values()) {
    if (sess.guestId === clientId) {
      sess.lastHeartbeat = Date.now()
      return
    }
  }
}

export function cleanupSession(clientId) {
  const session = sessions.get(clientId)
  if (session) {
    codeToSession.delete(session.code)
    sessions.delete(clientId)
    return session
  }
  return null
}

export function removeGuest(clientId) {
  for (const session of sessions.values()) {
    if (session.guestId === clientId) {
      session.guestId = null
      session.guestWs = null
      session.status = 'waiting'
      return session
    }
  }
  return null
}

export default router
