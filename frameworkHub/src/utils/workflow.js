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

  // 本项目支持的所有模块类型 (共240个)
  const validModuleTypes = new Set([
    // 页面操作 (8)
    'open_page', 'close_page', 'refresh_page', 'go_back', 'go_forward', 'inject_javascript',
    'switch_iframe', 'switch_to_main',
    // 标签页管理 (1)
    'switch_tab',
    // 元素交互 (9)
    'click_element', 'hover_element', 'input_text', 'select_dropdown', 'set_checkbox',
    'drag_element', 'scroll_page', 'handle_dialog', 'upload_file',
    // 元素操作 (2)
    'get_child_elements', 'get_sibling_elements',
    // 数据采集 (5)
    'get_element_info', 'screenshot', 'save_image', 'download_file', 'extract_table_data',
    // 等待控制 (3)
    'wait', 'wait_element', 'wait_image',
    // 高级操作 (1)
    'network_capture',
    // 鼠标模拟 (5)
    'real_mouse_click', 'real_mouse_move', 'real_mouse_drag', 'real_mouse_scroll', 'get_mouse_position',
    // 键盘模拟 (2)
    'real_keyboard', 'keyboard_action',
    // 图像/文字识别点击 (5)
    'click_image', 'click_text', 'hover_image', 'hover_text', 'drag_image',
    // 屏幕操作 (5)
    'screenshot_screen', 'screen_record', 'window_focus', 'camera_capture', 'camera_record',
    // 宏录制 (1)
    'macro_recorder',
    // 系统控制 (3)
    'shutdown_system', 'lock_screen', 'run_command',
    // 剪贴板 (2)
    'set_clipboard', 'get_clipboard',
    // 变量操作 (5)
    'set_variable', 'json_parse', 'base64', 'random_number', 'get_time',
    // 文本处理 (8)
    'string_concat', 'string_replace', 'string_split', 'string_join',
    'string_trim', 'string_case', 'string_substring', 'regex_extract',
    // 列表/字典 (7)
    'list_operation', 'list_get', 'list_length', 'list_export',
    'dict_operation', 'dict_get', 'dict_keys',
    // 数据表格 (8)
    'table_add_row', 'table_add_column', 'table_set_cell', 'table_get_cell',
    'table_delete_row', 'table_clear', 'table_export', 'read_excel',
    // 数据库 (7)
    'db_connect', 'db_query', 'db_execute', 'db_insert', 'db_update', 'db_delete', 'db_close',
    // 流程控制 (8)
    'condition', 'loop', 'foreach', 'break_loop', 'continue_loop', 'scheduled_task', 'subflow', 'subflow_header',
    // 触发器 (10)
    'webhook_trigger', 'hotkey_trigger', 'file_watcher_trigger', 'email_trigger', 'api_trigger',
    'mouse_trigger', 'image_trigger', 'sound_trigger', 'face_trigger', 'element_change_trigger',
    // 文件管理 (11)
    'list_files', 'copy_file', 'move_file', 'delete_file', 'create_folder',
    'file_exists', 'get_file_info', 'read_text_file', 'write_text_file',
    'rename_file', 'rename_folder',
    // PDF处理 (16)
    'pdf_to_images', 'images_to_pdf', 'pdf_merge', 'pdf_split', 'pdf_extract_text',
    'pdf_extract_images', 'pdf_encrypt', 'pdf_decrypt', 'pdf_add_watermark', 'pdf_rotate',
    'pdf_delete_pages', 'pdf_get_info', 'pdf_compress', 'pdf_insert_pages', 'pdf_reorder_pages',
    'pdf_to_word',
    // 文档转换 (13)
    'markdown_to_html', 'html_to_markdown', 'markdown_to_pdf', 'markdown_to_docx', 'docx_to_markdown',
    'html_to_docx', 'docx_to_html', 'markdown_to_epub', 'epub_to_markdown', 'latex_to_pdf',
    'rst_to_html', 'org_to_html', 'universal_doc_convert',
    // 格式工厂 (6)
    'image_format_convert', 'video_format_convert', 'audio_format_convert',
    'video_to_audio', 'video_to_gif', 'batch_format_convert',
    // 视频处理 (10)
    'format_convert', 'compress_video', 'trim_video', 'merge_media', 'rotate_video',
    'video_speed', 'extract_frame', 'add_subtitle', 'resize_video', 'download_m3u8',
    // 音频处理 (3)
    'extract_audio', 'adjust_volume', 'audio_to_text',
    // 图像处理 (17)
    'compress_image', 'image_resize', 'image_crop', 'image_rotate', 'image_flip', 'image_blur', 'image_sharpen',
    'image_brightness', 'image_contrast', 'image_color_balance', 'image_add_text', 'image_merge', 'image_thumbnail',
    'image_filter', 'image_grayscale', 'image_round_corners', 'image_remove_bg',
    // 图像工具 (4)
    'add_watermark', 'image_get_info', 'qr_generate', 'qr_decode',
    // AI对话 (2)
    'ai_chat', 'ai_vision',
    // AI爬虫 (5)
    'ai_smart_scraper', 'ai_element_selector', 'firecrawl_scrape', 'firecrawl_map', 'firecrawl_crawl',
    // AI识别 (4)
    'ocr_captcha', 'slider_captcha', 'face_recognition', 'image_ocr',
    // 网络请求 (2)
    'api_request', 'send_email',
    // QQ机器人 (8)
    'qq_send_message', 'qq_send_image', 'qq_send_file', 'qq_wait_message',
    'qq_get_friends', 'qq_get_groups', 'qq_get_group_members', 'qq_get_login_info',
    // 微信机器人 (2)
    'wechat_send_message', 'wechat_send_file',
    // 网络共享 (5)
    'share_folder', 'share_file', 'stop_share', 'start_screen_share', 'stop_screen_share',
    // 实用工具 - 文件对比 (4)
    'file_hash_compare', 'file_diff_compare', 'folder_hash_compare', 'folder_diff_compare',
    // 实用工具 - 加密编码 (4)
    'md5_encrypt', 'sha_encrypt', 'url_encode_decode', 'random_password_generator',
    // 实用工具 - 格式转换 (4)
    'rgb_to_hsv', 'rgb_to_cmyk', 'hex_to_cmyk', 'timestamp_converter',
    // 实用工具 - 其他工具 (2)
    'uuid_generator', 'printer_call',
    // 消息通知 (5)
    'print_log', 'play_sound', 'system_notification', 'text_to_speech', 'export_log',
    // 媒体播放 (3)
    'play_music', 'play_video', 'view_image',
    // 用户交互 (1)
    'input_prompt',
    // 脚本执行 (2)
    'js_script', 'python_script',
    // 画布工具 (2)
    'group', 'note'
  ])

  // React Flow 的节点类型
  const validReactFlowTypes = new Set(['moduleNode', 'groupNode', 'noteNode', 'subflowHeaderNode'])

  // 统计有效节点类型数量
  let validNodeCount = 0
  let invalidTypes = []

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

    // 检查节点类型 - 支持两种格式：
    // 1. React Flow 格式：type = 'moduleNode'/'groupNode', data.moduleType = 实际模块类型
    // 2. 简化格式：type = 实际模块类型
    let moduleType = null
    
    if (node.data && node.data.moduleType) {
      // React Flow 格式
      moduleType = node.data.moduleType
      // 验证 React Flow 节点类型
      if (node.type && !validReactFlowTypes.has(node.type)) {
        // 不是标准的 React Flow 类型，可能是其他格式
      }
    } else if (node.type) {
      // 简化格式或直接使用 type
      moduleType = node.type
    }

    if (!moduleType) {
      return { valid: false, error: `节点 "${node.id}" 缺少模块类型` }
    }

    if (validModuleTypes.has(moduleType)) {
      validNodeCount++
    } else if (!validReactFlowTypes.has(moduleType)) {
      // 不是有效的模块类型，也不是 React Flow 类型
      invalidTypes.push(moduleType)
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

  // 如果没有任何有效的节点类型，说明不是本项目的工作流
  if (validNodeCount === 0) {
    return { 
      valid: false, 
      error: '这不是 Web RPA 的工作流文件，未找到任何有效的模块类型' 
    }
  }

  // 如果有无效的节点类型，给出提示
  if (invalidTypes.length > 0) {
    const uniqueInvalid = [...new Set(invalidTypes)]
    if (uniqueInvalid.length > 3) {
      return { 
        valid: false, 
        error: `包含 ${uniqueInvalid.length} 个不支持的模块类型，这可能不是 Web RPA 的工作流文件` 
      }
    }
    return { 
      valid: false, 
      error: `包含不支持的模块类型: ${uniqueInvalid.slice(0, 3).join(', ')}${uniqueInvalid.length > 3 ? '...' : ''}` 
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
