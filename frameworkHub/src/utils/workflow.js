/**
 * 工作流处理工具函数
 */

import { createHash } from 'crypto'

/**
 * 计算工作流内容的哈希值
 * 用于判断工作流是否重复
 */
export function calculateWorkflowHash(content) {
  // 只对关键内容计算哈希，忽略 id、位置等可变信息
  const normalizedContent = normalizeWorkflowForHash(content)
  const jsonStr = JSON.stringify(normalizedContent)
  return createHash('sha256').update(jsonStr).digest('hex')
}

/**
 * 标准化工作流内容用于哈希计算
 * 移除位置、ID等不影响功能的信息
 */
function normalizeWorkflowForHash(content) {
  const nodes = (content.nodes || []).map(node => ({
    type: node.type,
    data: normalizeNodeData(node.data || node.config || {})
  })).sort((a, b) => {
    // 按类型和配置排序，确保顺序一致
    const typeCompare = (a.type || '').localeCompare(b.type || '')
    if (typeCompare !== 0) return typeCompare
    return JSON.stringify(a.data).localeCompare(JSON.stringify(b.data))
  })

  // 边的连接关系（标准化）
  const edges = (content.edges || []).map(edge => ({
    sourceType: findNodeType(content.nodes, edge.source),
    targetType: findNodeType(content.nodes, edge.target),
    sourceHandle: edge.sourceHandle || null,
    targetHandle: edge.targetHandle || null
  })).sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)))

  return { nodes, edges }
}

/**
 * 标准化节点数据
 */
function normalizeNodeData(data) {
  const normalized = {}
  const ignoreKeys = ['label', 'name', 'description', 'x', 'y', 'position', 'id']
  
  for (const [key, value] of Object.entries(data)) {
    if (!ignoreKeys.includes(key) && value !== undefined && value !== null && value !== '') {
      normalized[key] = value
    }
  }
  
  return normalized
}

/**
 * 根据节点ID查找节点类型
 */
function findNodeType(nodes, nodeId) {
  const node = (nodes || []).find(n => n.id === nodeId)
  return node?.type || 'unknown'
}

/**
 * 验证工作流内容的有效性
 * 严格检查是否为本项目的工作流格式
 */
export function validateWorkflowContent(content) {
  // 基本类型检查
  if (!content || typeof content !== 'object') {
    return { valid: false, error: '无效的JSON格式，请上传正确的工作流文件' }
  }

  // 检查是否为数组（常见错误：上传了数组而非对象）
  if (Array.isArray(content)) {
    return { valid: false, error: '工作流格式错误：应为对象而非数组' }
  }

  // 检查必要字段
  if (!('nodes' in content)) {
    return { valid: false, error: '不是有效的工作流文件：缺少 nodes 字段' }
  }

  if (!('edges' in content)) {
    return { valid: false, error: '不是有效的工作流文件：缺少 edges 字段' }
  }

  if (!Array.isArray(content.nodes)) {
    return { valid: false, error: '工作流格式错误：nodes 必须是数组' }
  }

  if (!Array.isArray(content.edges)) {
    return { valid: false, error: '工作流格式错误：edges 必须是数组' }
  }

  // 检查节点数量
  if (content.nodes.length === 0) {
    return { valid: false, error: '工作流至少需要一个节点' }
  }

  if (content.nodes.length > 500) {
    return { valid: false, error: '工作流节点数量不能超过500个' }
  }

  // 验证每个节点的基本格式
  for (let i = 0; i < content.nodes.length; i++) {
    const node = content.nodes[i]

    // 检查节点是否为对象
    if (!node || typeof node !== 'object') {
      return { valid: false, error: `节点 #${i + 1} 格式无效` }
    }

    // 检查节点ID
    if (!node.id || typeof node.id !== 'string') {
      return { valid: false, error: `节点 #${i + 1} 缺少有效的 id 字段` }
    }

    // 检查节点位置（可选但应为对象）
    if (node.position && typeof node.position !== 'object') {
      return { valid: false, error: `节点 "${node.id}" 的 position 格式无效` }
    }

    // 检查节点数据大小
    const nodeDataStr = JSON.stringify(node.data || {})
    if (nodeDataStr.length > 50000) {
      return { valid: false, error: `节点 "${node.id}" 的配置数据过大（超过50KB）` }
    }
  }

  // 检查边的有效性
  const nodeIds = new Set(content.nodes.map(n => n.id))
  for (let i = 0; i < content.edges.length; i++) {
    const edge = content.edges[i]

    if (!edge || typeof edge !== 'object') {
      return { valid: false, error: `连线 #${i + 1} 格式无效` }
    }

    if (!edge.source || typeof edge.source !== 'string') {
      return { valid: false, error: `连线 #${i + 1} 缺少有效的 source 字段` }
    }

    if (!edge.target || typeof edge.target !== 'string') {
      return { valid: false, error: `连线 #${i + 1} 缺少有效的 target 字段` }
    }

    if (!nodeIds.has(edge.source)) {
      return { valid: false, error: `连线引用了不存在的源节点: ${edge.source}` }
    }

    if (!nodeIds.has(edge.target)) {
      return { valid: false, error: `连线引用了不存在的目标节点: ${edge.target}` }
    }
  }

  // 检查变量格式（如果存在）
  if (content.variables !== undefined) {
    if (!Array.isArray(content.variables)) {
      return { valid: false, error: '变量字段格式错误：应为数组' }
    }

    for (let i = 0; i < content.variables.length; i++) {
      const variable = content.variables[i]
      if (!variable || typeof variable !== 'object') {
        return { valid: false, error: `变量 #${i + 1} 格式无效` }
      }
      if (!variable.name || typeof variable.name !== 'string') {
        return { valid: false, error: `变量 #${i + 1} 缺少有效的 name 字段` }
      }
    }
  }

  // 检查总大小
  const totalSize = JSON.stringify(content).length
  if (totalSize > 500000) { // 500KB
    return { valid: false, error: '工作流内容过大（超过500KB），请精简后再发布' }
  }

  return { valid: true, nodeCount: content.nodes.length }
}

/**
 * 原样返回工作流内容，不做任何修改
 * 确保用户上传的工作流与下载的完全一致
 */
export function sanitizeWorkflow(content) {
  // 直接返回原始内容，不做任何修改
  return content
}
