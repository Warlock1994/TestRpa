/**
 * 评论 API 路由
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

// 评论类型
const COMMENT_TYPES = ['使用心得', '问题求助', '建议改进', '感谢', '其他']

// 发布评论的速率限制
const commentLimiter = rateLimit({
  windowMs: 60 * 1000, // 1分钟
  max: 5, // 每分钟最多5条评论
  message: { error: '评论过于频繁，请稍后再试' }
})

/**
 * 获取工作流的评论列表
 * GET /api/comments/:workflowId
 */
router.get('/:workflowId',
  [
    param('workflowId').isUUID(),
    query('page').optional().isInt({ min: 1 }).toInt(),
    query('limit').optional().isInt({ min: 1, max: 50 }).toInt(),
    query('clientId').optional().isString().trim()
  ],
  (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({ error: '参数错误' })
    }

    const workflowId = req.params.workflowId
    const page = req.query.page || 1
    const limit = req.query.limit || 20
    const offset = (page - 1) * limit
    const clientId = req.query.clientId || ''

    // 获取总数
    const countStmt = db.prepare('SELECT COUNT(*) as total FROM comments WHERE workflow_id = ? AND is_active = 1')
    const { total } = countStmt.get(workflowId)

    // 获取评论列表（包含 client_id 用于判断是否为自己的评论）
    const listStmt = db.prepare(`
      SELECT id, nickname, content, comment_type, client_id, created_at
      FROM comments
      WHERE workflow_id = ? AND is_active = 1
      ORDER BY created_at DESC
      LIMIT ? OFFSET ?
    `)
    const comments = listStmt.all(workflowId, limit, offset)

    // 处理返回数据，标记是否为自己的评论
    const processedComments = comments.map(c => ({
      id: c.id,
      nickname: c.nickname,
      content: c.content,
      comment_type: c.comment_type,
      created_at: c.created_at,
      isOwner: clientId && c.client_id === clientId
    }))

    res.json({
      comments: processedComments,
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
 * 发布评论
 * POST /api/comments/:workflowId
 */
router.post('/:workflowId',
  commentLimiter,
  [
    param('workflowId').isUUID(),
    body('nickname')
      .optional()
      .isString()
      .trim()
      .isLength({ max: 20 })
      .withMessage('昵称不能超过20个字符'),
    body('content')
      .isString()
      .trim()
      .isLength({ min: 1, max: 500 })
      .withMessage('评论内容长度应在1-500个字符之间'),
    body('commentType')
      .optional()
      .isIn(COMMENT_TYPES)
      .withMessage('无效的评论类型'),
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

    const workflowId = req.params.workflowId
    const { nickname, content, commentType, clientId } = req.body
    const clientIP = getClientIP(req)

    // 检查工作流是否存在
    const checkStmt = db.prepare('SELECT id FROM workflows WHERE id = ? AND is_active = 1')
    if (!checkStmt.get(workflowId)) {
      return res.status(404).json({ error: '工作流不存在' })
    }

    // XSS 过滤
    const safeNickname = nickname ? xss(nickname, xssOptions) : '匿名用户'
    const safeContent = xss(content, xssOptions)

    try {
      db.prepare(`
        INSERT INTO comments (workflow_id, nickname, content, comment_type, client_id, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
      `).run(workflowId, safeNickname, safeContent, commentType || '使用心得', clientId || null, clientIP)

      res.status(201).json({ success: true, message: '评论发布成功' })
    } catch (error) {
      console.error('发布评论失败:', error)
      res.status(500).json({ error: '发布失败，请稍后重试' })
    }
  }
)

export default router


/**
 * 删除评论
 * DELETE /api/comments/:commentId
 */
router.delete('/:commentId',
  [
    param('commentId').isInt({ min: 1 }),
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

    const commentId = parseInt(req.params.commentId)
    const { clientId } = req.body

    // 检查评论是否存在
    const checkStmt = db.prepare('SELECT id, client_id FROM comments WHERE id = ? AND is_active = 1')
    const comment = checkStmt.get(commentId)

    if (!comment) {
      return res.status(404).json({ error: '评论不存在' })
    }

    // 验证是否为评论发布者
    if (!comment.client_id || comment.client_id !== clientId) {
      return res.status(403).json({ error: '无权删除此评论' })
    }

    try {
      // 软删除
      db.prepare('UPDATE comments SET is_active = 0 WHERE id = ?').run(commentId)
      res.json({ success: true, message: '评论已删除' })
    } catch (error) {
      console.error('删除评论失败:', error)
      res.status(500).json({ error: '删除失败，请稍后重试' })
    }
  }
)
