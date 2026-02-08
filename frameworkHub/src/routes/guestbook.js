/**
 * 留言板 API 路由
 */

import { Router } from 'express'
import { body, query, param, validationResult } from 'express-validator'
import rateLimit from 'express-rate-limit'
import xss from 'xss'
import db from '../database.js'
import { getClientIP } from '../utils/ip.js'

const router = Router()

// XSS 过滤配置
const xssOptions = {
  whiteList: {},
  stripIgnoreTag: true,
  stripIgnoreTagBody: ['script']
}

// 留言类型选项
const MESSAGE_TYPES = ['建议', '问题求助', 'Bug报告', '功能请求', '闲聊', '其他']

// 发布留言的速率限制
const guestbookLimiter = rateLimit({
  windowMs: 60 * 1000, // 1分钟
  max: 3, // 每分钟最多3条留言
  message: { error: '留言过于频繁，请稍后再试' }
})

/**
 * 获取留言板列表
 * GET /api/guestbook
 */
router.get('/',
  [
    query('page').optional().isInt({ min: 1 }).toInt(),
    query('limit').optional().isInt({ min: 1, max: 50 }).toInt(),
    query('clientId').optional().isString().trim()
  ],
  (req, res) => {
    const page = req.query.page || 1
    const limit = req.query.limit || 20
    const offset = (page - 1) * limit
    const clientId = req.query.clientId || ''

    // 获取总数
    const countStmt = db.prepare('SELECT COUNT(*) as total FROM guestbook WHERE is_active = 1')
    const { total } = countStmt.get()

    // 获取留言列表（包含 client_id 用于判断是否为自己的留言）
    const listStmt = db.prepare(`
      SELECT id, nickname, content, message_type, client_id, created_at
      FROM guestbook
      WHERE is_active = 1
      ORDER BY created_at DESC
      LIMIT ? OFFSET ?
    `)
    const messages = listStmt.all(limit, offset)

    // 处理返回数据，标记是否为自己的留言
    const processedMessages = messages.map(m => ({
      id: m.id,
      nickname: m.nickname,
      content: m.content,
      message_type: m.message_type,
      created_at: m.created_at,
      isOwner: clientId && m.client_id === clientId
    }))

    res.json({
      messages: processedMessages,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit)
      }
    })
  }
)

/**
 * 发布留言
 * POST /api/guestbook
 */
router.post('/',
  guestbookLimiter,
  [
    body('nickname')
      .optional()
      .isString()
      .trim()
      .isLength({ max: 20 })
      .withMessage('昵称不能超过20个字符'),
    body('content')
      .isString()
      .trim()
      .isLength({ min: 1, max: 1000 })
      .withMessage('留言内容长度应在1-1000个字符之间'),
    body('messageType')
      .optional()
      .isIn(MESSAGE_TYPES)
      .withMessage('无效的留言类型'),
    body('clientId')
      .optional()
      .isString()
      .trim()
  ],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({ error: '参数验证失败', details: errors.array() })
    }

    const { nickname, content, messageType, clientId } = req.body
    const clientIP = getClientIP(req)

    // XSS 过滤
    const safeNickname = nickname ? xss(nickname, xssOptions) : '匿名用户'
    const safeContent = xss(content, xssOptions)

    try {
      db.prepare(`
        INSERT INTO guestbook (nickname, content, message_type, client_id, ip_address)
        VALUES (?, ?, ?, ?, ?)
      `).run(safeNickname, safeContent, messageType || '建议', clientId || null, clientIP)

      res.status(201).json({ success: true, message: '留言发布成功' })
    } catch (error) {
      console.error('发布留言失败:', error)
      res.status(500).json({ error: '发布失败，请稍后重试' })
    }
  }
)

/**
 * 删除留言
 * DELETE /api/guestbook/:messageId
 */
router.delete('/:messageId',
  [
    param('messageId').isInt({ min: 1 }),
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

    const messageId = parseInt(req.params.messageId)
    const { clientId } = req.body

    // 检查留言是否存在
    const checkStmt = db.prepare('SELECT id, client_id FROM guestbook WHERE id = ? AND is_active = 1')
    const message = checkStmt.get(messageId)

    if (!message) {
      return res.status(404).json({ error: '留言不存在' })
    }

    // 验证是否为留言发布者
    if (!message.client_id || message.client_id !== clientId) {
      return res.status(403).json({ error: '无权删除此留言' })
    }

    try {
      // 软删除
      db.prepare('UPDATE guestbook SET is_active = 0 WHERE id = ?').run(messageId)
      res.json({ success: true, message: '留言已删除' })
    } catch (error) {
      console.error('删除留言失败:', error)
      res.status(500).json({ error: '删除失败，请稍后重试' })
    }
  }
)

export default router
