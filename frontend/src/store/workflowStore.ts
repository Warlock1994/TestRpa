import { create } from 'zustand'
import { nanoid } from 'nanoid'
import type { Node, Edge, Connection, NodeChange, EdgeChange } from '@xyflow/react'
import { applyNodeChanges, applyEdgeChanges, addEdge } from '@xyflow/react'
import type { ModuleType, Variable, LogEntry, ExecutionStatus, ModuleConfig, DataAsset, ImageAsset } from '@/types'
import { useGlobalConfigStore } from './globalConfigStore'

// 底栏 Tab 类型
export type BottomPanelTab = 'logs' | 'data' | 'variables' | 'assets' | 'images'

// 历史记录快照类型
interface HistorySnapshot {
  nodes: Node<NodeData>[]
  edges: Edge[]
  name: string  // 工作流名称也纳入历史记录
}

// React Flow节点数据类型
export interface NodeData extends ModuleConfig {
  label: string
  moduleType: ModuleType
  isHighlighted?: boolean  // 用于日志点击高亮（可选）
}

// 数据行类型
export type DataRow = Record<string, unknown>

// 工作流状态
interface WorkflowState {
  // 工作流基本信息
  id: string
  name: string
  
  // React Flow节点和边
  nodes: Node<NodeData>[]
  edges: Edge[]
  
  // 变量
  variables: Variable[]
  
  // 选中的节点
  selectedNodeId: string | null
  
  // 剪贴板（用于复制粘贴，支持多选）
  clipboard: Node<NodeData>[]
  clipboardEdges: Edge[]  // 复制的连线
  
  // 执行状态
  executionStatus: ExecutionStatus
  
  // 日志
  logs: LogEntry[]
  
  // 详细日志开关（默认关闭，只显示打印日志模块的内容）
  verboseLog: boolean
  
  // 日志显示上限（用户选择的条数）
  maxLogCount: number
  
  // 收集的数据（用于预览和导出）
  collectedData: DataRow[]
  
  // Excel文件资源（上传的Excel文件）
  dataAssets: DataAsset[]
  
  // 图像资源（上传的图像文件）
  imageAssets: ImageAsset[]
  
  // 底栏当前激活的 Tab
  bottomPanelTab: BottomPanelTab
  
  // 是否有未保存的更改
  hasUnsavedChanges: boolean
  
  // 历史记录（用于撤销/重做）
  history: HistorySnapshot[]
  historyIndex: number
  
  // 节点操作
  onNodesChange: (changes: NodeChange<Node<NodeData>>[]) => void
  onEdgesChange: (changes: EdgeChange[]) => void
  onConnect: (connection: Connection) => void
  
  // 添加节点
  addNode: (type: ModuleType, position: { x: number; y: number }) => void
  
  // 更新节点数据
  updateNodeData: (nodeId: string, data: Partial<NodeData>) => void
  
  // 删除节点
  deleteNode: (nodeId: string) => void
  
  // 选择节点
  selectNode: (nodeId: string | null) => void
  
  // 复制粘贴（支持多选）
  copyNodes: (nodeIds: string[]) => void
  pasteNodes: (position?: { x: number; y: number }) => void
  pasteNodesFromClipboard: (nodes: Node<NodeData>[], edges: Edge[], position?: { x: number; y: number }) => void
  
  // 变量操作
  addVariable: (variable: Omit<Variable, 'name'> & { name: string }) => void
  updateVariable: (name: string, value: unknown) => void
  deleteVariable: (name: string) => void
  renameVariable: (oldName: string, newName: string) => void
  
  // 变量引用扫描和替换
  findVariableUsages: (varName: string) => { nodeId: string; field: string; value: string }[]
  replaceVariableReferences: (oldName: string, newName: string) => void
  
  // 日志操作
  addLog: (log: Omit<LogEntry, 'id' | 'timestamp'>) => void
  addLogs: (logs: Array<Omit<LogEntry, 'id' | 'timestamp'>>) => void
  clearLogs: () => void
  setVerboseLog: (enabled: boolean) => void
  setMaxLogCount: (count: number) => void
  
  // 执行状态
  setExecutionStatus: (status: ExecutionStatus) => void
  
  // 数据操作
  setCollectedData: (data: DataRow[]) => void
  addDataRow: (row: DataRow) => void
  addDataRows: (rows: DataRow[]) => void
  updateDataRow: (index: number, row: DataRow) => void
  deleteDataRow: (index: number) => void
  clearCollectedData: () => void
  
  // Excel文件资源操作
  setDataAssets: (assets: DataAsset[]) => void
  addDataAsset: (asset: DataAsset) => void
  deleteDataAsset: (id: string) => void
  
  // 图像资源操作
  setImageAssets: (assets: ImageAsset[]) => void
  addImageAsset: (asset: ImageAsset) => void
  deleteImageAsset: (id: string) => void
  
  // 底栏 Tab 操作
  setBottomPanelTab: (tab: BottomPanelTab) => void
  
  // 历史记录操作（撤销/重做）
  pushHistory: () => void
  undo: () => void
  redo: () => void
  canUndo: () => boolean
  canRedo: () => boolean
  
  // 工作流操作
  setWorkflowName: (name: string) => void
  setWorkflowNameWithHistory: (name: string) => void  // 设置名称并保存历史
  clearWorkflow: () => void
  loadWorkflow: (workflow: { nodes: Node<NodeData>[]; edges: Edge[]; name: string }) => void
  
  // 未保存状态管理
  markAsUnsaved: () => void
  markAsSaved: () => void
  
  // 导出工作流
  exportWorkflow: () => string
  
  // 导入工作流
  importWorkflow: (json: string | object) => boolean
  
  // 合并导入工作流（追加到现有画布）
  mergeWorkflow: (json: string, position?: { x: number; y: number }) => boolean
  
  // 禁用/启用节点
  toggleNodesDisabled: (nodeIds: string[]) => void
}

// 模块类型到标签的映射
export const moduleTypeLabels: Record<ModuleType, string> = {
  // 浏览器操作
  open_page: '打开网页',
  click_element: '点击元素',
  hover_element: '悬停元素',
  input_text: '输入文本',
  get_element_info: '提取数据',
  wait: '固定等待',
  wait_element: '等待元素',
  wait_image: '等待图像',
  close_page: '关闭网页',
  refresh_page: '刷新页面',
  go_back: '后退',
  go_forward: '前进',
  handle_dialog: '处理弹窗',
  inject_javascript: 'JS脚本注入',
  switch_iframe: '切换iframe',
  switch_to_main: '切换回主页面',
  switch_tab: '切换标签页',
  // 表单操作
  select_dropdown: '下拉选择',
  set_checkbox: '勾选框',
  drag_element: '拖拽元素',
  scroll_page: '滚动页面',
  upload_file: '上传文件',
  // 元素操作
  get_child_elements: '获取子元素',
  get_sibling_elements: '获取兄弟元素',
  // 数据处理
  set_variable: '设置变量',
  increment_decrement: '自增自减',
  json_parse: 'JSON解析',
  base64: 'Base64',
  random_number: '随机数',
  get_time: '获取时间',
  download_file: '下载文件',
  save_image: '保存图片',
  screenshot: '网页截图',
  read_excel: '读取Excel',
  // 字符串操作
  regex_extract: '正则提取',
  string_replace: '替换文本',
  string_split: '分割文本',
  string_join: '连接文本',
  string_concat: '拼接文本',
  string_trim: '去除空白',
  string_case: '大小写',
  string_substring: '截取文本',
  // 列表操作
  list_operation: '列表操作',
  list_get: '列表取值',
  list_length: '列表长度',
  list_export: '列表导出',
  // 字典操作
  dict_operation: '字典操作',
  dict_get: '字典取值',
  dict_keys: '字典键列表',
  // 数据表格操作
  table_add_row: '添加行',
  table_add_column: '添加列',
  table_set_cell: '设置单元格',
  table_get_cell: '读取单元格',
  table_delete_row: '删除行',
  table_clear: '清空表格',
  table_export: '导出表格',
  // 数据库操作
  db_connect: '连接数据库',
  db_query: '查询数据',
  db_execute: '执行SQL',
  db_insert: '插入数据',
  db_update: '更新数据',
  db_delete: '删除数据',
  db_close: '关闭连接',
  // 网络请求
  api_request: 'HTTP请求',
  send_email: '发送邮件',
  // QQ自动化
  qq_send_message: 'QQ发送消息',
  qq_send_image: 'QQ发送图片',
  qq_send_file: 'QQ发送文件',
  qq_wait_message: 'QQ等待消息',
  qq_get_friends: 'QQ好友列表',
  qq_get_groups: 'QQ群列表',
  qq_get_group_members: 'QQ群成员',
  qq_get_login_info: 'QQ登录信息',
  // 微信自动化
  wechat_send_message: '微信发送消息',
  wechat_send_file: '微信发送文件',
  // 手机自动化
  phone_tap: '📱 点击',
  phone_swipe: '📱 滑动',
  phone_long_press: '📱 长按',
  phone_input_text: '📱 输入文本',
  phone_press_key: '📱 按键操作',
  phone_screenshot: '📱 截图',
  phone_start_mirror: '📱 启动屏幕镜像',
  phone_stop_mirror: '📱 停止屏幕镜像',
  phone_install_app: '📱 安装应用',
  phone_start_app: '📱 启动应用',
  phone_stop_app: '📱 停止应用',
  phone_uninstall_app: '📱 卸载应用',
  phone_push_file: '📱 推送文件',
  phone_pull_file: '📱 拉取文件',
  phone_click_image: '📱 点击图像',
  phone_click_text: '📱 点击文本',
  phone_wait_image: '📱 等待图像',
  phone_image_exists: '📱 图像存在判断',
  phone_set_volume: '📱 设置音量',
  phone_set_brightness: '📱 设置亮度',
  phone_set_clipboard: '📱 写入剪贴板',
  phone_get_clipboard: '📱 读取剪贴板',
  // 测试报告
  allure_init: 'Allure初始化',
  allure_start_test: '开始测试用例',
  allure_add_step: '添加测试步骤',
  allure_add_attachment: '添加附件',
  allure_stop_test: '结束测试用例',
  allure_generate_report: '生成测试报告',
  // AI能力
  ai_chat: 'AI对话',
  ai_vision: '图像识别',
  ai_smart_scraper: '🧪 AI智能爬虫 (实验性)',
  ai_element_selector: '🧪 AI元素选择器 (实验性)',
  firecrawl_scrape: 'AI单页数据抓取',
  firecrawl_map: 'AI网站链接抓取',
  firecrawl_crawl: 'AI全站数据抓取',
  // 验证码
  ocr_captcha: 'OCR识别',
  slider_captcha: '滑块验证',
  // 流程控制
  condition: '条件判断',
  loop: '循环',
  foreach: '遍历列表',
  break_loop: '跳出循环',
  continue_loop: '跳过当前循环',
  scheduled_task: '定时任务',
  subflow: '子流程',
  // 触发器
  webhook_trigger: 'Webhook触发器',
  hotkey_trigger: '热键触发器',
  file_watcher_trigger: '文件监控触发器',
  email_trigger: '邮件触发器',
  api_trigger: 'API触发器',
  mouse_trigger: '鼠标触发器',
  image_trigger: '图像触发器',
  sound_trigger: '声音触发器',
  face_trigger: '人脸触发器',
  gesture_trigger: '手势触发器',
  element_change_trigger: '子元素变化触发器',
  // 辅助工具
  print_log: '打印日志',
  play_sound: '提示音',
  system_notification: '系统消息',
  play_music: '播放音乐',
  play_video: '播放视频',
  view_image: '查看图片',
  input_prompt: '用户输入',
  text_to_speech: '语音播报',
  js_script: 'JS脚本',
  python_script: 'Python脚本',
  extract_table_data: '表格数据提取',
  set_clipboard: '写入剪贴板',
  get_clipboard: '读取剪贴板',
  keyboard_action: '模拟按键',
  real_mouse_scroll: '真实鼠标滚动',
  // 系统操作
  shutdown_system: '关机/重启',
  lock_screen: '锁定屏幕',
  window_focus: '窗口聚焦',
  real_mouse_click: '真实鼠标点击',
  real_mouse_move: '真实鼠标移动',
  real_mouse_drag: '真实鼠标拖拽',
  real_keyboard: '真实键盘操作',
  run_command: '执行命令',
  click_image: '点击图像',
  image_exists: '图像存在判断',
  element_exists: '元素存在判断',
  element_visible: '元素可见判断',
  get_mouse_position: '获取鼠标位置',
  screenshot_screen: '屏幕截图',
  rename_file: '文件重命名',
  network_capture: '网络抓包',
  // 文件操作
  list_files: '获取文件列表',
  copy_file: '复制文件',
  move_file: '移动文件',
  delete_file: '删除文件',
  create_folder: '创建文件夹',
  file_exists: '文件是否存在',
  get_file_info: '获取文件信息',
  read_text_file: '读取文本文件',
  write_text_file: '写入文本文件',
  rename_folder: '文件夹重命名',
  // 宏录制器
  macro_recorder: '宏录制器',
  // 媒体处理（FFmpeg）
  format_convert: '格式转换',
  compress_image: '图片压缩',
  compress_video: '视频压缩',
  extract_audio: '提取音频',
  trim_video: '视频裁剪',
  merge_media: '媒体合并',
  add_watermark: '添加水印',
  download_m3u8: 'M3U8下载',
  rotate_video: '视频旋转',
  video_speed: '视频倍速',
  extract_frame: '截取帧',
  add_subtitle: '添加字幕',
  adjust_volume: '调节音量',
  resize_video: '调整分辨率',
  // 格式工厂
  image_format_convert: '图片格式转换',
  video_format_convert: '视频格式转换',
  audio_format_convert: '音频格式转换',
  video_to_audio: '视频转音频',
  video_to_gif: '视频转GIF',
  batch_format_convert: '批量格式转换',
  // AI识别
  face_recognition: '人脸识别',
  image_ocr: '图片OCR',
  // PDF处理
  pdf_to_images: 'PDF转图片',
  images_to_pdf: '图片转PDF',
  pdf_merge: 'PDF合并',
  pdf_split: 'PDF拆分',
  pdf_extract_text: 'PDF提取文本',
  pdf_extract_images: 'PDF提取图片',
  pdf_encrypt: 'PDF加密',
  pdf_decrypt: 'PDF解密',
  pdf_add_watermark: 'PDF添加水印',
  pdf_rotate: 'PDF旋转页面',
  pdf_delete_pages: 'PDF删除页面',
  pdf_get_info: 'PDF获取信息',
  pdf_compress: 'PDF压缩',
  pdf_insert_pages: 'PDF插入页面',
  pdf_reorder_pages: 'PDF重排页面',
  pdf_to_word: 'PDF转Word',
  // 文档转换
  markdown_to_html: 'Markdown转HTML',
  html_to_markdown: 'HTML转Markdown',
  markdown_to_pdf: 'Markdown转PDF',
  markdown_to_docx: 'Markdown转Word',
  docx_to_markdown: 'Word转Markdown',
  html_to_docx: 'HTML转Word',
  docx_to_html: 'Word转HTML',
  markdown_to_epub: 'Markdown转EPUB',
  epub_to_markdown: 'EPUB转Markdown',
  latex_to_pdf: 'LaTeX转PDF',
  rst_to_html: 'RST转HTML',
  org_to_html: 'Org转HTML',
  universal_doc_convert: '通用文档转换',
  // 其他
  export_log: '导出日志',
  click_text: '点击文本',
  hover_image: '悬停图像',
  hover_text: '悬停文本',
  drag_image: '拖拽图像',
  // 图像处理
  image_grayscale: '图片去色',
  image_round_corners: '图片圆角化',
  // Pillow图像处理
  image_resize: '图像缩放',
  image_crop: '图像裁剪',
  image_rotate: '图像旋转',
  image_flip: '图像翻转',
  image_blur: '图像模糊',
  image_sharpen: '图像锐化',
  image_brightness: '亮度调整',
  image_contrast: '对比度调整',
  image_color_balance: '色彩平衡',
  image_convert_format: '图像格式转换',
  image_add_text: '图像添加文字',
  image_merge: '图像拼接',
  image_thumbnail: '生成缩略图',
  image_filter: '图像滤镜',
  image_get_info: '获取图像信息',
  image_remove_bg: '简单去背景',
  // 音频处理
  audio_to_text: '音频转文本',
  // 二维码
  qr_generate: '二维码生成',
  qr_decode: '二维码解码',
  // 录屏
  screen_record: '桌面录屏',
  camera_capture: '摄像头拍照',
  camera_record: '摄像头录像',
  // 网络共享
  share_folder: '文件夹网络共享',
  share_file: '文件网络共享',
  stop_share: '停止网络共享',
  // 屏幕共享
  start_screen_share: '开始屏幕共享',
  stop_screen_share: '停止屏幕共享',
  // 分组/备注
  group: '分组',
  subflow_header: '子流程头',
  note: '便签',
  // 实用工具
  file_hash_compare: '文件哈希对比',
  file_diff_compare: '文件差异对比',
  folder_hash_compare: '文件夹哈希对比',
  folder_diff_compare: '文件夹差异对比',
  random_password_generator: '随机密码生成',
  url_encode_decode: 'URL编解码',
  md5_encrypt: 'MD5加密',
  sha_encrypt: 'SHA加密',
  timestamp_converter: '时间戳转换',
  rgb_to_hsv: 'RGB转HSV',
  rgb_to_cmyk: 'RGB转CMYK',
  hex_to_cmyk: 'HEX转CMYK',
  uuid_generator: 'UUID生成器',
  printer_call: '打印机调用',
}

// 模块默认超时时间配置（毫秒）
// 根据模块实际使用场景设置合理的默认超时
export const moduleDefaultTimeouts: Partial<Record<ModuleType, number>> = {
  // 浏览器操作 - 网页加载可能较慢
  open_page: 60000,        // 60秒，网页加载可能慢
  click_element: 60000,    // 60秒
  hover_element: 60000,    // 60秒
  input_text: 60000,       // 60秒
  get_element_info: 60000, // 60秒
  wait: 0,                 // 固定等待不需要超时
  wait_element: 60000,     // 60秒，等待元素可能需要较长时间
  wait_image: 60000,       // 60秒，等待图像可能需要较长时间
  close_page: 10000,       // 10秒
  refresh_page: 60000,     // 60秒
  go_back: 60000,          // 60秒
  go_forward: 60000,       // 60秒
  handle_dialog: 60000,    // 60秒
  inject_javascript: 60000, // 60秒
  switch_iframe: 10000,    // 10秒
  switch_to_main: 5000,    // 5秒
  // 表单操作
  select_dropdown: 60000,  // 60秒
  set_checkbox: 60000,     // 60秒
  drag_element: 60000,     // 60秒
  scroll_page: 60000,      // 60秒
  upload_file: 120000,     // 2分钟，大文件上传需要时间
  // 元素操作
  get_child_elements: 60000,   // 60秒
  get_sibling_elements: 60000, // 60秒
  // 数据处理 - 通常很快
  set_variable: 5000,      // 5秒
  increment_decrement: 5000, // 5秒
  json_parse: 5000,        // 5秒
  base64: 10000,           // 10秒
  random_number: 5000,     // 5秒
  get_time: 5000,          // 5秒
  download_file: 300000,   // 5分钟，大文件下载
  save_image: 60000,       // 1分钟
  screenshot: 60000,       // 60秒
  read_excel: 60000,       // 1分钟，大Excel文件
  // 字符串操作 - 很快
  regex_extract: 10000,    // 10秒
  string_replace: 5000,    // 5秒
  string_split: 5000,      // 5秒
  string_join: 5000,       // 5秒
  string_concat: 5000,     // 5秒
  string_trim: 5000,       // 5秒
  string_case: 5000,       // 5秒
  string_substring: 5000,  // 5秒
  // 列表/字典操作 - 很快
  list_operation: 10000,   // 10秒
  list_get: 5000,          // 5秒
  list_length: 5000,       // 5秒
  list_export: 60000,      // 60秒
  dict_operation: 10000,   // 10秒
  dict_get: 5000,          // 5秒
  dict_keys: 5000,         // 5秒
  // 数据表格操作
  table_add_row: 5000,     // 5秒
  table_add_column: 5000,  // 5秒
  table_set_cell: 5000,    // 5秒
  table_get_cell: 5000,    // 5秒
  table_delete_row: 5000,  // 5秒
  table_clear: 5000,       // 5秒
  table_export: 60000,     // 1分钟，大数据导出
  // 数据库操作
  db_connect: 60000,       // 60秒
  db_query: 120000,        // 2分钟，复杂查询
  db_execute: 120000,      // 2分钟
  db_insert: 60000,        // 1分钟
  db_update: 60000,        // 1分钟
  db_delete: 60000,        // 1分钟
  db_close: 10000,         // 10秒
  // 网络请求
  api_request: 120000,     // 2分钟
  send_email: 60000,       // 1分钟
  // QQ自动化
  qq_send_message: 60000,  // 60秒
  qq_send_image: 60000,    // 1分钟
  qq_send_file: 120000,    // 2分钟，文件上传可能较慢
  qq_wait_message: 0,      // 不超时，模块内部有自己的超时逻辑
  qq_get_friends: 60000,   // 60秒
  qq_get_groups: 60000,    // 60秒
  qq_get_group_members: 60000, // 60秒
  qq_get_login_info: 10000, // 10秒
  // 微信自动化
  wechat_send_message: 60000,  // 60秒
  wechat_send_file: 120000,    // 2分钟
  // AI能力 - 需要较长时间
  ai_chat: 180000,         // 3分钟，AI响应可能慢
  ai_vision: 180000,       // 3分钟
  ai_smart_scraper: 300000,    // 5分钟，AI智能爬虫需要更长时间
  ai_element_selector: 120000, // 2分钟，AI元素选择器
  firecrawl_scrape: 60000,     // 1分钟
  firecrawl_map: 120000,       // 2分钟
  firecrawl_crawl: 600000,     // 10分钟，全站爬取需要很长时间
  // 验证码
  ocr_captcha: 60000,      // 1分钟
  slider_captcha: 60000,   // 1分钟
  // 流程控制
  condition: 5000,         // 5秒
  loop: 0,                 // 循环本身不超时
  foreach: 0,              // 遍历本身不超时
  break_loop: 5000,        // 5秒
  continue_loop: 5000,     // 5秒
  scheduled_task: 0,       // 定时任务不超时
  subflow: 0,              // 子流程不超时，由内部模块控制
  // 触发器 - 默认不超时，由用户配置
  webhook_trigger: 0,      // Webhook触发器不超时
  hotkey_trigger: 0,       // 热键触发器不超时
  file_watcher_trigger: 0, // 文件监控触发器不超时
  email_trigger: 0,        // 邮件触发器不超时
  api_trigger: 0,          // API触发器不超时
  mouse_trigger: 0,        // 鼠标触发器不超时
  image_trigger: 0,        // 图像触发器不超时
  sound_trigger: 0,        // 声音触发器不超时
  face_trigger: 0,         // 人脸触发器不超时
  gesture_trigger: 60,      // 手势触发器默认60秒超时
  element_change_trigger: 0, // 子元素变化触发器不超时
  // 辅助工具
  print_log: 5000,         // 5秒
  play_sound: 10000,       // 10秒
  system_notification: 10000, // 10秒
  play_music: 600000,      // 10分钟，一首歌3-5分钟
  play_video: 7200000,     // 2小时，视频可能很长
  view_image: 300000,      // 5分钟，查看图片
  input_prompt: 300000,    // 5分钟，等待用户输入
  text_to_speech: 120000,  // 2分钟
  js_script: 60000,        // 1分钟
  python_script: 60000,    // 1分钟
  extract_table_data: 60000, // 60秒
  switch_tab: 10000,       // 10秒
  set_clipboard: 5000,     // 5秒
  get_clipboard: 5000,     // 5秒
  keyboard_action: 10000,  // 10秒
  real_mouse_scroll: 10000,// 10秒
  // 系统操作
  shutdown_system: 60000,  // 60秒
  lock_screen: 10000,      // 10秒
  window_focus: 10000,     // 10秒
  real_mouse_click: 10000, // 10秒
  real_mouse_move: 10000,  // 10秒
  real_mouse_drag: 60000,  // 60秒，拖拽可能需要更长时间
  real_keyboard: 60000,    // 60秒
  run_command: 300000,     // 5分钟，命令可能耗时
  click_image: 60000,      // 1分钟
  image_exists: 60000,     // 1分钟
  element_exists: 60000,   // 1分钟
  element_visible: 60000,  // 1分钟
  get_mouse_position: 5000,// 5秒
  screenshot_screen: 10000,// 10秒
  rename_file: 10000,      // 10秒
  network_capture: 300000, // 5分钟
  // 文件操作
  list_files: 60000,       // 60秒
  copy_file: 300000,       // 5分钟，大文件复制
  move_file: 300000,       // 5分钟
  delete_file: 60000,      // 60秒
  create_folder: 10000,    // 10秒
  file_exists: 5000,       // 5秒
  get_file_info: 10000,    // 10秒
  read_text_file: 60000,   // 1分钟
  write_text_file: 60000,  // 1分钟
  rename_folder: 10000,    // 10秒
  // 媒体处理 - FFmpeg操作耗时
  format_convert: 600000,  // 10分钟
  compress_image: 120000,  // 2分钟
  compress_video: 1800000, // 30分钟，视频压缩很慢
  extract_audio: 300000,   // 5分钟
  trim_video: 600000,      // 10分钟
  merge_media: 1800000,    // 30分钟
  add_watermark: 600000,   // 10分钟
  // 格式工厂 - 格式转换操作耗时
  image_format_convert: 120000,  // 2分钟
  video_format_convert: 1800000, // 30分钟
  audio_format_convert: 300000,  // 5分钟
  video_to_audio: 300000,        // 5分钟
  video_to_gif: 600000,          // 10分钟
  batch_format_convert: 3600000, // 60分钟，批量转换很耗时
  // AI识别
  face_recognition: 60000, // 1分钟
  image_ocr: 60000,        // 1分钟
  // PDF处理
  pdf_to_images: 120000,     // 2分钟
  images_to_pdf: 120000,     // 2分钟
  pdf_merge: 120000,         // 2分钟
  pdf_split: 120000,         // 2分钟
  pdf_extract_text: 60000,   // 1分钟
  pdf_extract_images: 120000, // 2分钟
  pdf_encrypt: 60000,        // 1分钟
  pdf_decrypt: 60000,        // 1分钟
  pdf_add_watermark: 120000, // 2分钟
  pdf_rotate: 60000,         // 1分钟
  pdf_delete_pages: 60000,   // 1分钟
  pdf_get_info: 60000,       // 60秒
  pdf_compress: 180000,      // 3分钟
  pdf_insert_pages: 60000,   // 1分钟
  pdf_reorder_pages: 60000,  // 1分钟
  pdf_to_word: 300000,       // 5分钟
  // 其他
  export_log: 60000,         // 60秒
  click_text: 60000,         // 60秒
  hover_image: 60000,        // 60秒
  hover_text: 60000,         // 60秒
  drag_image: 60000,         // 1分钟
  // 图像处理
  image_grayscale: 60000,    // 60秒
  image_round_corners: 60000, // 60秒
  // 音频处理
  audio_to_text: 120000,     // 2分钟
  // 二维码
  qr_generate: 10000,        // 10秒
  qr_decode: 10000,          // 10秒
  // 录屏
  screen_record: 5000,       // 5秒（非阻塞，只是启动）
  camera_capture: 10000,     // 10秒
  camera_record: 300000,     // 5分钟（根据录制时长动态调整）
  // 手机自动化
  phone_tap: 10000,          // 10秒
  phone_swipe: 10000,        // 10秒
  phone_long_press: 10000,   // 10秒
  phone_input_text: 30000,   // 30秒
  phone_press_key: 10000,    // 10秒
  phone_screenshot: 30000,   // 30秒
  phone_start_mirror: 30000, // 30秒
  phone_stop_mirror: 10000,  // 10秒
  phone_install_app: 120000, // 2分钟
  phone_start_app: 30000,    // 30秒
  phone_stop_app: 10000,     // 10秒
  phone_uninstall_app: 60000, // 1分钟
  phone_push_file: 120000,   // 2分钟
  phone_pull_file: 120000,   // 2分钟
  phone_click_image: 60000,  // 1分钟
  phone_click_text: 60000,   // 1分钟
  phone_wait_image: 60000,   // 1分钟
  phone_image_exists: 60000, // 1分钟
  phone_set_volume: 30000,   // 30秒
  phone_set_brightness: 10000, // 10秒
  phone_set_clipboard: 10000, // 10秒
  phone_get_clipboard: 10000, // 10秒
  // 测试报告
  allure_init: 30000,          // 30秒
  allure_start_test: 10000,    // 10秒
  allure_add_step: 5000,       // 5秒
  allure_add_attachment: 60000, // 1分钟，文件复制可能较慢
  allure_stop_test: 10000,     // 10秒
  allure_generate_report: 300000, // 5分钟，生成报告可能较慢
  // 网络共享
  share_folder: 10000,       // 10秒
  share_file: 10000,         // 10秒
  stop_share: 5000,          // 5秒
  // 分组/备注 - 不执行
  group: 0,
  subflow_header: 0,
  note: 0,
}

// 获取模块默认超时时间
export function getModuleDefaultTimeout(moduleType: ModuleType): number {
  return moduleDefaultTimeouts[moduleType] ?? 60000  // 默认60秒，避免30秒超时过短
}

// 创建store
export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  id: nanoid(),
  name: '未命名工作流',
  nodes: [],
  edges: [],
  variables: [],
  selectedNodeId: null,
  clipboard: [],
  clipboardEdges: [],
  executionStatus: 'pending',
  logs: [],
  verboseLog: false,
  maxLogCount: 100,
  collectedData: [],
  dataAssets: [],
  imageAssets: [],
  bottomPanelTab: 'logs',
  hasUnsavedChanges: false,
  history: [{ nodes: [], edges: [], name: '未命名工作流' }],
  historyIndex: 0,

  onNodesChange: (changes) => {
    // 检查是否有实质性变化（位置拖拽结束、删除、添加）
    const hasSubstantialChange = changes.some(c => 
      (c.type === 'position' && (c as { dragging?: boolean }).dragging === false) ||
      c.type === 'remove' ||
      c.type === 'add' ||
      c.type === 'dimensions'
    )
    
    // 先保存历史（变化之前）
    if (hasSubstantialChange) {
      get().pushHistory()
      get().markAsUnsaved()  // 标记为未保存
    }
    
    let updatedNodes = applyNodeChanges(changes, get().nodes)
    
    // 确保 groupNode 和 noteNode 的 zIndex 始终保持在底层
    updatedNodes = updatedNodes.map(node => {
      if (node.type === 'groupNode' || node.type === 'noteNode') {
        return { ...node, zIndex: -1 }
      }
      return node
    })
    
    set({ nodes: updatedNodes })
  },

  onEdgesChange: (changes) => {
    // 检查是否有实质性变化
    const hasSubstantialChange = changes.some(c => 
      c.type === 'remove' || c.type === 'add'
    )
    
    // 先保存历史（变化之前）
    if (hasSubstantialChange) {
      get().pushHistory()
      get().markAsUnsaved()  // 标记为未保存
    }
    
    set({
      edges: applyEdgeChanges(changes, get().edges),
    })
  },

  onConnect: (connection) => {
    // 检查是否是自环连接（节点连接到自己）
    if (connection.source === connection.target) {
      // 添加错误日志
      get().addLog({
        level: 'error',
        message: '❌ 不允许将模块连接到自己！请连接到其他模块。'
      })
      return // 阻止连接
    }
    
    // 先保存当前状态到历史（连线之前）
    get().pushHistory()
    set({
      edges: addEdge(connection, get().edges),
    })
  },

  addNode: (type, position) => {
    // 先保存当前状态到历史（添加节点之前）
    get().pushHistory()
    
    // 获取全局配置
    const globalConfig = useGlobalConfigStore.getState().config
    
    // 根据模块类型应用默认配置
    let defaultData: Partial<NodeData> = {}
    
    if (type === 'gesture_trigger') {
      // 手势触发器默认配置
      defaultData = {
        timeout: 60000,  // 默认60秒（60000毫秒）
        cameraIndex: 0,
        confidenceThreshold: 0.6,  // 默认60%置信度
        saveToVariable: 'gesture_data',
      }
    } else if (type === 'ai_chat') {
      defaultData = {
        apiUrl: globalConfig.ai.apiUrl,
        apiKey: globalConfig.ai.apiKey,
        model: globalConfig.ai.model,
        temperature: globalConfig.ai.temperature,
        maxTokens: globalConfig.ai.maxTokens,
        systemPrompt: globalConfig.ai.systemPrompt,
        resultVariable: 'ai_response',
      }
    } else if (type === 'ai_smart_scraper') {
      // AI智能爬虫模块默认配置
      defaultData = {
        llmProvider: globalConfig.aiScraper.llmProvider,
        apiUrl: globalConfig.aiScraper.apiUrl,
        llmModel: globalConfig.aiScraper.llmModel,
        apiKey: globalConfig.aiScraper.apiKey,
        azureEndpoint: globalConfig.aiScraper.azureEndpoint,
        variableName: 'scraper_result',
        headless: true,
        verbose: false,
        waitTime: 3,  // 默认等待3秒
      }
    } else if (type === 'ai_element_selector') {
      // AI元素选择器模块默认配置
      defaultData = {
        llmProvider: globalConfig.aiScraper.llmProvider,
        apiUrl: globalConfig.aiScraper.apiUrl,
        llmModel: globalConfig.aiScraper.llmModel,
        apiKey: globalConfig.aiScraper.apiKey,
        azureEndpoint: globalConfig.aiScraper.azureEndpoint,
        variableName: 'element_selector',
        verbose: false,
        url: '',  // 添加 URL 字段
        waitTime: 3,  // 默认等待3秒
      }
    } else if (type === 'send_email') {
      defaultData = {
        senderEmail: globalConfig.email.senderEmail,
        authCode: globalConfig.email.authCode,
      }
    } else if (type === 'loop') {
      // 循环模块默认变量
      defaultData = {
        loopType: 'count',
        indexVariable: 'loop_index',
      }
    } else if (type === 'foreach') {
      // 遍历列表模块默认变量
      defaultData = {
        itemVariable: 'item',
        indexVariable: 'index',
      }
    } else if (type === 'get_element_info') {
      // 提取数据模块默认变量
      defaultData = {
        variableName: 'element_value',
      }
    } else if (type === 'set_variable') {
      // 设置变量模块默认变量
      defaultData = {
        variableName: 'my_var',
      }
    } else if (type === 'random_number') {
      // 随机数模块默认变量
      defaultData = {
        variableName: 'random_num',
      }
    } else if (type === 'get_time') {
      // 获取时间模块默认变量
      defaultData = {
        variableName: 'current_time',
      }
    } else if (type === 'input_prompt') {
      // 变量输入框模块默认变量
      defaultData = {
        variableName: 'user_input',
      }
    } else if (type === 'js_script') {
      // JS脚本模块默认变量
      defaultData = {
        resultVariable: 'js_result',
      }
    } else if (type === 'api_request') {
      // API请求模块默认变量
      defaultData = {
        resultVariable: 'api_response',
      }
    } else if (type === 'json_parse') {
      // JSON解析模块默认变量
      defaultData = {
        resultVariable: 'parsed_json',
      }
    } else if (type === 'regex_extract') {
      // 正则提取模块默认变量
      defaultData = {
        resultVariable: 'regex_result',
      }
    } else if (type === 'list_operation') {
      // 列表操作模块默认变量
      defaultData = {
        resultVariable: 'list_result',
      }
    } else if (type === 'list_get') {
      // 列表取值模块默认变量
      defaultData = {
        resultVariable: 'list_item',
      }
    } else if (type === 'list_length') {
      // 列表长度模块默认变量
      defaultData = {
        resultVariable: 'list_len',
      }
    } else if (type === 'dict_operation') {
      // 字典操作模块默认变量
      defaultData = {
        resultVariable: 'dict_result',
      }
    } else if (type === 'dict_get') {
      // 字典取值模块默认变量
      defaultData = {
        resultVariable: 'dict_value',
      }
    } else if (type === 'dict_keys') {
      // 字典键列表模块默认变量
      defaultData = {
        resultVariable: 'dict_keys',
      }
    } else if (type === 'string_split') {
      // 字符串分割模块默认变量
      defaultData = {
        resultVariable: 'split_result',
      }
    } else if (type === 'string_concat') {
      // 字符串拼接模块默认变量
      defaultData = {
        resultVariable: 'concat_result',
      }
    } else if (type === 'string_replace') {
      // 字符串替换模块默认变量
      defaultData = {
        resultVariable: 'replace_result',
      }
    } else if (type === 'string_join') {
      // 字符串连接模块默认变量
      defaultData = {
        resultVariable: 'join_result',
      }
    } else if (type === 'string_trim') {
      // 字符串去空格模块默认变量
      defaultData = {
        resultVariable: 'trim_result',
      }
    } else if (type === 'string_case') {
      // 字符串大小写模块默认变量
      defaultData = {
        resultVariable: 'case_result',
      }
    } else if (type === 'string_substring') {
      // 字符串截取模块默认变量
      defaultData = {
        resultVariable: 'substring_result',
      }
    } else if (type === 'base64') {
      // Base64模块默认变量
      defaultData = {
        resultVariable: 'base64_result',
      }
    } else if (type === 'screenshot') {
      // 网页截图模块默认变量
      defaultData = {
        variableName: 'screenshot_path',
      }
    } else if (type === 'screenshot_screen') {
      // 屏幕截图模块默认变量
      defaultData = {
        variableName: 'screen_path',
      }
    } else if (type === 'ocr_captcha') {
      // OCR验证码模块默认变量
      defaultData = {
        resultVariable: 'captcha_text',
      }
    } else if (type === 'get_clipboard') {
      // 获取剪贴板模块默认变量
      defaultData = {
        variableName: 'clipboard_content',
      }
    } else if (type === 'get_mouse_position') {
      // 获取鼠标位置模块默认变量
      defaultData = {
        variableName: 'mouse_pos',
      }
    } else if (type === 'run_command') {
      // 运行命令模块默认变量
      defaultData = {
        resultVariable: 'cmd_output',
      }
    } else if (type === 'read_excel') {
      // 读取Excel模块默认变量
      defaultData = {
        resultVariable: 'excel_data',
      }
    } else if (type === 'table_get_cell') {
      // 获取单元格模块默认变量
      defaultData = {
        resultVariable: 'cell_value',
      }
    } else if (type === 'db_query') {
      // 数据库查询模块默认变量
      defaultData = {
        resultVariable: 'query_result',
      }
    } else if (type === 'network_capture') {
      // 网络抓包模块默认变量
      defaultData = {
        resultVariable: 'captured_data',
      }
    } else if (type === 'qq_send_message') {
      // QQ发送消息模块默认变量
      defaultData = {
        messageType: 'private',
        resultVariable: 'qq_msg_result',
      }
    } else if (type === 'qq_send_image') {
      // QQ发送图片模块默认变量
      defaultData = {
        messageType: 'private',
        resultVariable: 'qq_img_result',
      }
    } else if (type === 'qq_send_file') {
      // QQ发送文件模块默认变量
      defaultData = {
        messageType: 'private',
        resultVariable: 'qq_file_result',
      }
    } else if (type === 'qq_get_friends') {
      // QQ获取好友列表模块默认变量
      defaultData = {
        resultVariable: 'qq_friends',
      }
    } else if (type === 'qq_get_groups') {
      // QQ获取群列表模块默认变量
      defaultData = {
        resultVariable: 'qq_groups',
      }
    } else if (type === 'qq_get_group_members') {
      // QQ获取群成员列表模块默认变量
      defaultData = {
        resultVariable: 'qq_group_members',
      }
    } else if (type === 'qq_get_login_info') {
      // QQ获取登录信息模块默认变量
      defaultData = {
        resultVariable: 'qq_login_info',
      }
    } else if (type === 'qq_wait_message') {
      // QQ等待消息模块默认变量
      // 注意：这里的 timeout 是模块内部的超时（秒），不是工作流的超时（毫秒）
      defaultData = {
        sourceType: 'any',
        matchMode: 'contains',
        waitTimeout: 60,  // 等待超时（秒），0表示无限等待
        pollInterval: 0.5,
        resultVariable: 'qq_received_message',
      }
    } else if (type === 'wechat_send_message') {
      // 微信发送消息模块默认变量
      defaultData = {
        resultVariable: 'wechat_msg_result',
      }
    } else if (type === 'wechat_send_file') {
      // 微信发送文件模块默认变量
      defaultData = {
        resultVariable: 'wechat_file_result',
      }
    } else if (type === 'ai_vision') {
      // AI视觉模块默认变量
      defaultData = {
        resultVariable: 'vision_result',
      }
    } else if (type === 'format_convert') {
      // 格式转换模块默认变量
      defaultData = {
        mediaType: 'video',
        outputFormat: 'mp4',
        resultVariable: 'converted_path',
      }
    } else if (type === 'compress_image') {
      // 图片压缩模块默认变量
      defaultData = {
        quality: 80,
        resultVariable: 'compressed_image',
      }
    } else if (type === 'compress_video') {
      // 视频压缩模块默认变量
      defaultData = {
        preset: 'medium',
        crf: 23,
        resultVariable: 'compressed_video',
      }
    } else if (type === 'extract_audio') {
      // 提取音频模块默认变量
      defaultData = {
        audioFormat: 'mp3',
        audioBitrate: '192k',
        resultVariable: 'extracted_audio',
      }
    } else if (type === 'trim_video') {
      // 视频裁剪模块默认变量
      defaultData = {
        startTime: '00:00:00',
        resultVariable: 'trimmed_video',
      }
    } else if (type === 'merge_media') {
      // 媒体合并模块默认变量
      defaultData = {
        mergeType: 'video',
        resultVariable: 'merged_file',
      }
    } else if (type === 'add_watermark') {
      // 添加水印模块默认变量
      defaultData = {
        mediaType: 'video',
        watermarkType: 'image',
        position: 'bottomright',
        opacity: 0.8,
        resultVariable: 'watermarked_file',
      }
    } else if (type === 'face_recognition') {
      // 人脸识别模块默认变量
      defaultData = {
        tolerance: 0.6,
        resultVariable: 'face_match_result',
      }
    } else if (type === 'image_ocr') {
      // 图片OCR模块默认变量
      defaultData = {
        language: 'chi_sim+eng',
        resultVariable: 'ocr_text',
      }
    } else if (type === 'list_files') {
      // 获取文件列表模块默认变量
      defaultData = {
        listType: 'files',
        includeExtension: true,
        resultVariable: 'file_list',
      }
    } else if (type === 'copy_file') {
      // 复制文件模块默认变量
      defaultData = {
        resultVariable: 'copied_path',
      }
    } else if (type === 'move_file') {
      // 移动文件模块默认变量
      defaultData = {
        resultVariable: 'moved_path',
      }
    } else if (type === 'delete_file') {
      // 删除文件模块默认变量
      defaultData = {}
    } else if (type === 'create_folder') {
      // 创建文件夹模块默认变量
      defaultData = {
        resultVariable: 'folder_path',
      }
    } else if (type === 'file_exists') {
      // 文件是否存在模块默认变量
      defaultData = {
        resultVariable: 'exists',
      }
    } else if (type === 'get_file_info') {
      // 获取文件信息模块默认变量
      defaultData = {
        resultVariable: 'file_info',
      }
    } else if (type === 'read_text_file') {
      // 读取文本文件模块默认变量
      defaultData = {
        encoding: 'utf-8',
        resultVariable: 'file_content',
      }
    } else if (type === 'write_text_file') {
      // 写入文本文件模块默认变量
      defaultData = {
        encoding: 'utf-8',
        writeMode: 'overwrite',
        resultVariable: 'write_path',
      }
    } else if (type === 'rename_folder') {
      // 文件夹重命名模块默认变量
      defaultData = {
        resultVariable: 'new_folder_path',
      }
    } else if (type === 'phone_screenshot') {
      // 手机截图模块默认变量
      defaultData = {
        variableName: 'phone_screenshot_path',
      }
    } else if (type === 'phone_pull_file') {
      // 手机拉取文件模块默认变量
      defaultData = {
        variableName: 'phone_file_path',
      }
    } else if (type === 'phone_click_image') {
      // 手机点击图像模块默认变量
      defaultData = {
        resultVariable: 'phone_click_result',
      }
    } else if (type === 'phone_wait_image') {
      // 手机等待图像模块默认变量
      defaultData = {
        resultVariable: 'phone_wait_result',
      }
    } else if (type === 'phone_image_exists') {
      // 手机图像存在判断模块默认变量
      defaultData = {
        resultVariable: 'phone_image_exists_result',
      }
    } else if (type === 'phone_get_clipboard') {
      // 手机读取剪贴板模块默认变量
      defaultData = {
        variableName: 'phone_clipboard',
      }
    } else if (type === 'file_hash_compare') {
      // 文件哈希对比模块默认变量
      defaultData = {
        resultVariable: 'hash_compare_result',
      }
    } else if (type === 'file_diff_compare') {
      // 文件差异对比模块默认变量
      defaultData = {
        resultVariable: 'diff_result',
      }
    } else if (type === 'folder_hash_compare') {
      // 文件夹哈希对比模块默认变量
      defaultData = {
        resultVariable: 'folder_hash_result',
      }
    } else if (type === 'folder_diff_compare') {
      // 文件夹差异对比模块默认变量
      defaultData = {
        resultVariable: 'folder_diff_result',
      }
    } else if (type === 'random_password_generator') {
      // 随机密码生成模块默认变量
      defaultData = {
        resultVariable: 'random_password',
      }
    } else if (type === 'url_encode_decode') {
      // URL编解码模块默认变量
      defaultData = {
        resultVariable: 'url_result',
      }
    } else if (type === 'md5_encrypt') {
      // MD5加密模块默认变量
      defaultData = {
        resultVariable: 'md5_hash',
      }
    } else if (type === 'sha_encrypt') {
      // SHA加密模块默认变量
      defaultData = {
        resultVariable: 'sha_hash',
      }
    } else if (type === 'timestamp_converter') {
      // 时间戳转换模块默认变量
      defaultData = {
        resultVariable: 'converted_time',
      }
    } else if (type === 'rgb_to_hsv') {
      // RGB转HSV模块默认变量
      defaultData = {
        resultVariable: 'hsv_color',
      }
    } else if (type === 'rgb_to_cmyk') {
      // RGB转CMYK模块默认变量
      defaultData = {
        resultVariable: 'cmyk_color',
      }
    } else if (type === 'hex_to_cmyk') {
      // HEX转CMYK模块默认变量
      defaultData = {
        resultVariable: 'cmyk_color',
      }
    } else if (type === 'uuid_generator') {
      // UUID生成器模块默认变量
      defaultData = {
        resultVariable: 'uuid',
      }
    } else if (type === 'webhook_trigger') {
      // Webhook触发器模块默认变量
      defaultData = {
        saveToVariable: 'webhook_data',
      }
    } else if (type === 'hotkey_trigger') {
      // 热键触发器模块默认变量
      defaultData = {
        saveToVariable: 'hotkey_data',
      }
    } else if (type === 'file_watcher_trigger') {
      // 文件监控触发器模块默认变量
      defaultData = {
        saveToVariable: 'file_event',
      }
    } else if (type === 'email_trigger') {
      // 邮件触发器模块默认变量
      defaultData = {
        saveToVariable: 'email_data',
      }
    } else if (type === 'api_trigger') {
      // API触发器模块默认变量
      defaultData = {
        saveToVariable: 'api_request',
      }
    } else if (type === 'mouse_trigger') {
      // 鼠标触发器模块默认变量
      defaultData = {
        saveToVariable: 'mouse_event',
      }
    } else if (type === 'image_trigger') {
      // 图像触发器模块默认变量
      defaultData = {
        saveToVariable: 'image_event',
      }
    } else if (type === 'sound_trigger') {
      // 声音触发器模块默认变量
      defaultData = {
        saveToVariable: 'sound_event',
      }
    } else if (type === 'face_trigger') {
      // 人脸触发器模块默认变量
      defaultData = {
        saveToVariable: 'face_event',
      }
    } else if (type === 'element_change_trigger') {
      // 子元素变化触发器模块默认变量
      defaultData = {
        saveNewElementSelector: 'new_element_selector',
        saveChangeInfo: 'change_info',
      }
    } else if (type === 'image_resize') {
      // 图像缩放模块默认变量
      defaultData = {
        resultVariable: 'resized_image',
      }
    } else if (type === 'image_crop') {
      // 图像裁剪模块默认变量
      defaultData = {
        resultVariable: 'cropped_image',
      }
    } else if (type === 'image_rotate') {
      // 图像旋转模块默认变量
      defaultData = {
        resultVariable: 'rotated_image',
      }
    } else if (type === 'image_flip') {
      // 图像翻转模块默认变量
      defaultData = {
        resultVariable: 'flipped_image',
      }
    } else if (type === 'image_blur') {
      // 图像模糊模块默认变量
      defaultData = {
        resultVariable: 'blurred_image',
      }
    } else if (type === 'image_sharpen') {
      // 图像锐化模块默认变量
      defaultData = {
        resultVariable: 'sharpened_image',
      }
    } else if (type === 'image_brightness') {
      // 亮度调整模块默认变量
      defaultData = {
        resultVariable: 'brightness_image',
      }
    } else if (type === 'image_contrast') {
      // 对比度调整模块默认变量
      defaultData = {
        resultVariable: 'contrast_image',
      }
    } else if (type === 'image_color_balance') {
      // 色彩平衡模块默认变量
      defaultData = {
        resultVariable: 'balanced_image',
      }
    } else if (type === 'image_convert_format') {
      // 图像格式转换模块默认变量
      defaultData = {
        resultVariable: 'converted_image',
      }
    } else if (type === 'image_add_text') {
      // 图像添加文字模块默认变量
      defaultData = {
        resultVariable: 'text_image',
      }
    } else if (type === 'image_merge') {
      // 图像拼接模块默认变量
      defaultData = {
        resultVariable: 'merged_image',
      }
    } else if (type === 'image_thumbnail') {
      // 生成缩略图模块默认变量
      defaultData = {
        resultVariable: 'thumbnail_image',
      }
    } else if (type === 'image_filter') {
      // 图像滤镜模块默认变量
      defaultData = {
        resultVariable: 'filtered_image',
      }
    } else if (type === 'image_get_info') {
      // 获取图像信息模块默认变量
      defaultData = {
        resultVariable: 'image_info',
      }
    } else if (type === 'image_remove_bg') {
      // 简单去背景模块默认变量
      defaultData = {
        resultVariable: 'nobg_image',
      }
    } else if (type === 'pdf_to_images') {
      // PDF转图片模块默认变量
      defaultData = {
        resultVariable: 'pdf_images',
      }
    } else if (type === 'images_to_pdf') {
      // 图片转PDF模块默认变量
      defaultData = {
        resultVariable: 'pdf_result',
      }
    } else if (type === 'pdf_merge') {
      // PDF合并模块默认变量
      defaultData = {
        resultVariable: 'merged_pdf',
      }
    } else if (type === 'pdf_split') {
      // PDF拆分模块默认变量
      defaultData = {
        resultVariable: 'split_pdfs',
      }
    } else if (type === 'pdf_extract_text') {
      // PDF提取文本模块默认变量
      defaultData = {
        resultVariable: 'pdf_text',
      }
    } else if (type === 'pdf_extract_images') {
      // PDF提取图片模块默认变量
      defaultData = {
        resultVariable: 'extracted_images',
      }
    } else if (type === 'pdf_encrypt') {
      // PDF加密模块默认变量
      defaultData = {
        resultVariable: 'encrypted_pdf',
      }
    } else if (type === 'pdf_decrypt') {
      // PDF解密模块默认变量
      defaultData = {
        resultVariable: 'decrypted_pdf',
      }
    } else if (type === 'pdf_add_watermark') {
      // PDF添加水印模块默认变量
      defaultData = {
        resultVariable: 'watermarked_pdf',
      }
    } else if (type === 'pdf_rotate') {
      // PDF旋转页面模块默认变量
      defaultData = {
        resultVariable: 'rotated_pdf',
      }
    } else if (type === 'pdf_delete_pages') {
      // PDF删除页面模块默认变量
      defaultData = {
        resultVariable: 'result_pdf',
      }
    } else if (type === 'pdf_get_info') {
      // PDF获取信息模块默认变量
      defaultData = {
        resultVariable: 'pdf_info',
      }
    } else if (type === 'pdf_compress') {
      // PDF压缩模块默认变量
      defaultData = {
        resultVariable: 'compressed_pdf',
      }
    } else if (type === 'pdf_insert_pages') {
      // PDF插入页面模块默认变量
      defaultData = {
        resultVariable: 'result_pdf',
      }
    } else if (type === 'pdf_reorder_pages') {
      // PDF重排页面模块默认变量
      defaultData = {
        resultVariable: 'reordered_pdf',
      }
    } else if (type === 'pdf_to_word') {
      // PDF转Word模块默认变量
      defaultData = {
        resultVariable: 'word_file',
      }
    } else if (type === 'markdown_to_html') {
      // Markdown转HTML模块默认变量
      defaultData = {
        resultVariable: 'html_output',
      }
    } else if (type === 'html_to_markdown') {
      // HTML转Markdown模块默认变量
      defaultData = {
        resultVariable: 'markdown_output',
      }
    } else if (type === 'markdown_to_pdf') {
      // Markdown转PDF模块默认变量
      defaultData = {
        resultVariable: 'pdf_output',
      }
    } else if (type === 'markdown_to_docx') {
      // Markdown转Word模块默认变量
      defaultData = {
        resultVariable: 'docx_output',
      }
    } else if (type === 'docx_to_markdown') {
      // Word转Markdown模块默认变量
      defaultData = {
        resultVariable: 'markdown_output',
      }
    } else if (type === 'html_to_docx') {
      // HTML转Word模块默认变量
      defaultData = {
        resultVariable: 'docx_output',
      }
    } else if (type === 'docx_to_html') {
      // Word转HTML模块默认变量
      defaultData = {
        resultVariable: 'html_output',
      }
    } else if (type === 'markdown_to_epub') {
      // Markdown转EPUB模块默认变量
      defaultData = {
        resultVariable: 'epub_output',
      }
    } else if (type === 'epub_to_markdown') {
      // EPUB转Markdown模块默认变量
      defaultData = {
        resultVariable: 'markdown_output',
      }
    } else if (type === 'latex_to_pdf') {
      // LaTeX转PDF模块默认变量
      defaultData = {
        resultVariable: 'pdf_output',
      }
    } else if (type === 'rst_to_html') {
      // RST转HTML模块默认变量
      defaultData = {
        resultVariable: 'html_output',
      }
    } else if (type === 'org_to_html') {
      // Org转HTML模块默认变量
      defaultData = {
        resultVariable: 'html_output',
      }
    } else if (type === 'universal_doc_convert') {
      // 通用文档转换模块默认变量
      defaultData = {
        resultVariable: 'convert_output',
      }
    }
    
    // 分组节点和便签节点使用特殊的节点类型和默认尺寸
    const isGroup = type === 'group'
    const isNote = type === 'note'
    
    // 获取模块默认超时时间
    const defaultTimeout = getModuleDefaultTimeout(type)
    
    const newNode: Node<NodeData> = {
      id: nanoid(),
      type: isGroup ? 'groupNode' : isNote ? 'noteNode' : 'moduleNode',
      position,
      ...(isGroup ? {
        style: { width: 300, height: 200 },
        zIndex: -1, // 分组节点在最底层
      } : {}),
      ...(isNote ? {
        style: { width: 200, height: 120 },
        zIndex: -1, // 便签也在底层
      } : {}),
      data: {
        label: isGroup ? '' : isNote ? '' : moduleTypeLabels[type],
        moduleType: type,
        // 设置默认超时时间（毫秒）
        ...(defaultTimeout > 0 ? { timeout: defaultTimeout } : {}),
        ...(isGroup ? { color: '#3b82f6', width: 300, height: 200 } : {}),
        ...(isNote ? { color: '#fef08a', content: '' } : {}),
        ...defaultData,
      },
    }
    
    // 将默认变量名添加到变量列表中
    const variableFields = [
      'variableName', 'resultVariable', 'itemVariable', 'indexVariable', 
      'loopIndexVariable', 'saveToVariable', 'saveNewElementSelector', 'saveChangeInfo',
      // 坐标相关
      'variableNameX', 'variableNameY',
      // Python脚本相关
      'stdoutVariable', 'stderrVariable', 'returnCodeVariable',
      // 数据提取相关
      'columnName',
      // 其他可能的变量名字段
      'outputVariable', 'targetVariable', 'dataVariable'
    ]
    const newVariables: string[] = []
    for (const field of variableFields) {
      const varName = newNode.data[field]
      if (varName && typeof varName === 'string' && varName.trim()) {
        newVariables.push(varName.trim())
      }
    }
    
    // 添加新变量到变量列表(去重)
    if (newVariables.length > 0) {
      const currentVariables = get().variables
      const existingNames = new Set(currentVariables.map(v => v.name))
      const variablesToAdd: Variable[] = newVariables
        .filter(name => !existingNames.has(name))
        .map(name => ({
          name,
          value: undefined,
          type: 'string' as const,
          scope: 'local' as const
        }))
      
      if (variablesToAdd.length > 0) {
        set({ variables: [...currentVariables, ...variablesToAdd] })
      }
    }
    
    set({
      nodes: [...get().nodes, newNode],
    })
  },

  updateNodeData: (nodeId, data) => {
    set({
      nodes: get().nodes.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...data } }
          : node
      ),
    })
  },

  deleteNode: (nodeId) => {
    // 先保存当前状态到历史（删除之前）
    get().pushHistory()
    set({
      nodes: get().nodes.filter((node) => node.id !== nodeId),
      edges: get().edges.filter(
        (edge) => edge.source !== nodeId && edge.target !== nodeId
      ),
      selectedNodeId: get().selectedNodeId === nodeId ? null : get().selectedNodeId,
    })
  },

  selectNode: (nodeId) => {
    set({ selectedNodeId: nodeId })
  },

  copyNodes: (nodeIds) => {
    const nodesToCopy = get().nodes.filter((n) => nodeIds.includes(n.id))
    if (nodesToCopy.length > 0) {
      // 同时复制节点之间的连线
      const nodeIdSet = new Set(nodeIds)
      const edgesToCopy = get().edges.filter(
        (e) => nodeIdSet.has(e.source) && nodeIdSet.has(e.target)
      )
      set({ 
        clipboard: nodesToCopy.map(n => ({ ...n })),
        clipboardEdges: edgesToCopy.map(e => ({ ...e })),
      })
    }
  },

  pasteNodes: (position) => {
    const clipboard = get().clipboard
    const clipboardEdges = (get() as WorkflowState & { clipboardEdges?: Edge[] }).clipboardEdges || []
    if (clipboard.length === 0) return
    
    // 计算边界框，用于确定粘贴位置
    const minX = Math.min(...clipboard.map(n => n.position.x))
    const minY = Math.min(...clipboard.map(n => n.position.y))
    
    // 计算偏移量
    const offsetX = position ? position.x - minX : 50
    const offsetY = position ? position.y - minY : 50

    // 创建旧ID到新ID的映射
    const idMap = new Map<string, string>()
    
    // 创建新节点，保持相对位置
    const newNodes: Node<NodeData>[] = clipboard.map(node => {
      const newId = nanoid()
      idMap.set(node.id, newId)
      return {
        ...node,
        id: newId,
        position: {
          x: node.position.x + offsetX,
          y: node.position.y + offsetY,
        },
        selected: true,
        data: {
          ...node.data,
        },
      }
    })

    // 创建新的连线，使用新的节点ID
    const newEdges: Edge[] = clipboardEdges.map(edge => ({
      ...edge,
      id: nanoid(),
      source: idMap.get(edge.source) || edge.source,
      target: idMap.get(edge.target) || edge.target,
    }))

    // 取消之前的选中状态
    const updatedNodes = get().nodes.map(n => ({ ...n, selected: false }))

    // 先保存当前状态到历史（粘贴之前）
    get().pushHistory()
    
    set({
      nodes: [...updatedNodes, ...newNodes],
      edges: [...get().edges, ...newEdges],
      selectedNodeId: newNodes.length === 1 ? newNodes[0].id : null,
    })
  },

  // 从系统剪贴板粘贴节点（支持跨工作流）
  pasteNodesFromClipboard: (clipboardNodes, clipboardEdges, position) => {
    if (clipboardNodes.length === 0) return
    
    // 计算边界框，用于确定粘贴位置
    const minX = Math.min(...clipboardNodes.map(n => n.position.x))
    const minY = Math.min(...clipboardNodes.map(n => n.position.y))
    
    // 计算偏移量
    const offsetX = position ? position.x - minX : 50
    const offsetY = position ? position.y - minY : 50

    // 创建旧ID到新ID的映射
    const idMap = new Map<string, string>()
    
    // 创建新节点，保持相对位置
    const newNodes: Node<NodeData>[] = clipboardNodes.map(node => {
      const newId = nanoid()
      idMap.set(node.id, newId)
      return {
        ...node,
        id: newId,
        position: {
          x: node.position.x + offsetX,
          y: node.position.y + offsetY,
        },
        selected: true,
        data: {
          ...node.data,
        },
      }
    })

    // 创建新的连线，使用新的节点ID
    const newEdges: Edge[] = clipboardEdges.map(edge => ({
      ...edge,
      id: nanoid(),
      source: idMap.get(edge.source) || edge.source,
      target: idMap.get(edge.target) || edge.target,
    }))

    // 取消之前的选中状态
    const updatedNodes = get().nodes.map(n => ({ ...n, selected: false }))

    // 先保存当前状态到历史（粘贴之前）
    get().pushHistory()
    
    set({
      nodes: [...updatedNodes, ...newNodes],
      edges: [...get().edges, ...newEdges],
      selectedNodeId: newNodes.length === 1 ? newNodes[0].id : null,
    })
  },

  addLog: (log) => {
    const maxLogs = get().maxLogCount
    const newLog: LogEntry = {
      ...log,
      id: nanoid(),
      timestamp: new Date().toISOString(),
    }
    const currentLogs = get().logs
    const updatedLogs = currentLogs.length >= maxLogs
      ? [...currentLogs.slice(currentLogs.length - maxLogs + 1), newLog]
      : [...currentLogs, newLog]
    set({ logs: updatedLogs })
  },

  addVariable: (variable) => {
    const existing = get().variables.find((v) => v.name === variable.name)
    if (existing) {
      get().updateVariable(variable.name, variable.value)
      return
    }
    set({
      variables: [...get().variables, variable],
    })
  },

  updateVariable: (name, value) => {
    set({
      variables: get().variables.map((v) =>
        v.name === name ? { ...v, value } : v
      ),
    })
  },

  deleteVariable: (name) => {
    set({
      variables: get().variables.filter((v) => v.name !== name),
    })
  },

  renameVariable: (oldName, newName) => {
    if (oldName === newName) return
    set({
      variables: get().variables.map((v) =>
        v.name === oldName ? { ...v, name: newName } : v
      ),
    })
  },

  findVariableUsages: (varName) => {
    const nodes = get().nodes
    const usages: { nodeId: string; field: string; value: string }[] = []
    const pattern = new RegExp(`\\{${varName}(\\[[^\\]]*\\])?\\}`, 'g')
    
    for (const node of nodes) {
      const data = node.data as NodeData
      for (const [key, value] of Object.entries(data)) {
        if (typeof value === 'string' && pattern.test(value)) {
          usages.push({ nodeId: node.id, field: key, value })
          pattern.lastIndex = 0
        }
      }
    }
    return usages
  },

  replaceVariableReferences: (oldName, newName) => {
    const nodes = get().nodes
    const pattern = new RegExp(`\\{${oldName}(\\[[^\\]]*\\])?\\}`, 'g')
    
    const updatedNodes = nodes.map(node => {
      const data = { ...node.data } as NodeData
      let hasChanges = false
      
      for (const [key, value] of Object.entries(data)) {
        if (typeof value === 'string' && pattern.test(value)) {
          pattern.lastIndex = 0
          data[key] = value.replace(pattern, (_match, indexPart) => {
            return `{${newName}${indexPart || ''}}`
          })
          hasChanges = true
        }
      }
      
      return hasChanges ? { ...node, data } : node
    })
    
    set({ nodes: updatedNodes })
  },

  addLogs: (logs) => {
    if (logs.length === 0) return
    const maxLogs = get().maxLogCount
    const currentLogs = get().logs
    
    // 批量创建新日志
    const newLogs: LogEntry[] = logs.map(log => ({
      ...log,
      id: nanoid(),
      timestamp: new Date().toISOString(),
    }))
    
    // 合并并限制数量
    const allLogs = [...currentLogs, ...newLogs]
    const updatedLogs = allLogs.length > maxLogs
      ? allLogs.slice(allLogs.length - maxLogs)
      : allLogs
    
    set({ logs: updatedLogs })
  },

  clearLogs: () => {
    set({ logs: [] })
  },

  setVerboseLog: (enabled) => {
    set({ verboseLog: enabled })
    // 同步到后端
    import('@/services/socket').then(({ socketService }) => {
      socketService.setVerboseLog(enabled)
    })
  },

  setMaxLogCount: (count) => {
    set({ maxLogCount: count })
  },

  setExecutionStatus: (status) => {
    set({ executionStatus: status })
  },

  // 数据操作
  setCollectedData: (data) => {
    set({ collectedData: data })
  },

  addDataRow: (row) => {
    // 最多接收20条数据用于实时预览
    const MAX_PREVIEW_ROWS = 20
    const currentData = get().collectedData
    if (currentData.length < MAX_PREVIEW_ROWS) {
      set({ collectedData: [...currentData, row] })
    }
  },

  addDataRows: (rows) => {
    if (rows.length === 0) return
    // 最多接收20条数据用于实时预览
    const MAX_PREVIEW_ROWS = 20
    const currentData = get().collectedData
    if (currentData.length >= MAX_PREVIEW_ROWS) return
    const remaining = MAX_PREVIEW_ROWS - currentData.length
    const rowsToAdd = rows.slice(0, remaining)
    set({ collectedData: [...currentData, ...rowsToAdd] })
  },

  updateDataRow: (index, row) => {
    const data = [...get().collectedData]
    data[index] = row
    set({ collectedData: data })
  },

  deleteDataRow: (index) => {
    set({ collectedData: get().collectedData.filter((_, i) => i !== index) })
  },

  clearCollectedData: () => {
    set({ collectedData: [] })
  },

  // Excel文件资源操作
  setDataAssets: (assets) => {
    set({ dataAssets: assets })
  },

  addDataAsset: (asset) => {
    set({ dataAssets: [...get().dataAssets, asset] })
  },

  deleteDataAsset: (id) => {
    set({ dataAssets: get().dataAssets.filter((a) => a.id !== id) })
  },
  
  // 图像资源操作
  setImageAssets: (assets) => {
    set({ imageAssets: assets })
  },

  addImageAsset: (asset) => {
    set({ imageAssets: [...get().imageAssets, asset] })
  },

  deleteImageAsset: (id) => {
    set({ imageAssets: get().imageAssets.filter((a) => a.id !== id) })
  },

  setBottomPanelTab: (tab) => {
    set({ bottomPanelTab: tab })
  },

  pushHistory: () => {
    const state = get()
    // 保存当前状态作为新的历史记录点
    const snapshot: HistorySnapshot = {
      nodes: JSON.parse(JSON.stringify(state.nodes)),
      edges: JSON.parse(JSON.stringify(state.edges)),
      name: state.name,
    }
    
    // 检查是否与当前历史记录相同（避免重复）
    const currentSnapshot = state.history[state.historyIndex]
    if (currentSnapshot && 
        JSON.stringify(currentSnapshot.nodes) === JSON.stringify(snapshot.nodes) &&
        JSON.stringify(currentSnapshot.edges) === JSON.stringify(snapshot.edges) &&
        currentSnapshot.name === snapshot.name) {
      return // 没有变化，不保存
    }
    
    // 如果当前不在历史末尾，截断后面的历史
    const newHistory = state.history.slice(0, state.historyIndex + 1)
    // 限制历史记录数量为50
    const MAX_HISTORY = 50
    if (newHistory.length >= MAX_HISTORY) {
      newHistory.shift()
    }
    newHistory.push(snapshot)
    set({
      history: newHistory,
      historyIndex: newHistory.length - 1,
    })
  },

  undo: () => {
    const state = get()
    if (state.historyIndex > 0) {
      const newIndex = state.historyIndex - 1
      const snapshot = state.history[newIndex]
      set({
        nodes: JSON.parse(JSON.stringify(snapshot.nodes)),
        edges: JSON.parse(JSON.stringify(snapshot.edges)),
        name: snapshot.name,
        historyIndex: newIndex,
        selectedNodeId: null,
      })
    }
  },

  redo: () => {
    const state = get()
    if (state.historyIndex < state.history.length - 1) {
      const newIndex = state.historyIndex + 1
      const snapshot = state.history[newIndex]
      set({
        nodes: JSON.parse(JSON.stringify(snapshot.nodes)),
        edges: JSON.parse(JSON.stringify(snapshot.edges)),
        name: snapshot.name,
        historyIndex: newIndex,
        selectedNodeId: null,
      })
    }
  },

  canUndo: () => {
    return get().historyIndex > 0
  },

  canRedo: () => {
    const state = get()
    return state.historyIndex < state.history.length - 1
  },

  setWorkflowName: (name) => {
    set({ name })
  },
  
  // 设置工作流名称并保存历史（用于需要记录历史的场景，如失焦时）
  setWorkflowNameWithHistory: (name) => {
    const state = get()
    // 只有名称真正改变时才保存历史
    if (state.name !== name) {
      get().pushHistory()
      set({ name })
    }
  },

  clearWorkflow: () => {
    set({
      id: nanoid(),
      name: '未命名工作流',
      nodes: [],
      edges: [],
      selectedNodeId: null,
      clipboard: [],
      clipboardEdges: [],
      executionStatus: 'pending',
      logs: [],
      collectedData: [],
      hasUnsavedChanges: false,  // 清空后标记为已保存
      history: [{ nodes: [], edges: [], name: '未命名工作流' }],
      historyIndex: 0,
    })
  },

  loadWorkflow: (workflow) => {
    const snapshot = {
      nodes: JSON.parse(JSON.stringify(workflow.nodes)),
      edges: JSON.parse(JSON.stringify(workflow.edges)),
      name: workflow.name,
    }
    set({
      nodes: workflow.nodes,
      edges: workflow.edges,
      name: workflow.name,
      selectedNodeId: null,
      hasUnsavedChanges: false,  // 加载后标记为已保存
      history: [snapshot],
      historyIndex: 0,
    })
  },
  
  markAsUnsaved: () => {
    set({ hasUnsavedChanges: true })
  },
  
  markAsSaved: () => {
    set({ hasUnsavedChanges: false })
  },

  exportWorkflow: () => {
    const state = get()
    
    // 转换节点类型：将 ReactFlow 的节点类型转换为后端期望的类型
    const convertedNodes = state.nodes.map(node => {
      let backendType = node.type
      
      // 转换特殊的节点类型
      if (node.type === 'groupNode') {
        backendType = 'group'
      } else if (node.type === 'noteNode') {
        backendType = 'note'
      } else if (node.type === 'subflowHeaderNode') {
        backendType = 'subflow_header'
      } else if (node.type === 'moduleNode') {
        // moduleNode 使用 data.moduleType 作为实际类型
        backendType = node.data.moduleType as string
      }
      
      return {
        ...node,
        type: backendType
      }
    })
    
    const workflow = {
      id: state.id,
      name: state.name,
      nodes: convertedNodes,
      edges: state.edges,
      variables: state.variables,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
    return JSON.stringify(workflow, null, 2)
  },

  importWorkflow: (json) => {
    try {
      // 支持字符串或对象
      const workflow = typeof json === 'string' ? JSON.parse(json) : json
      if (!workflow.nodes || !workflow.edges) {
        return false
      }
      
      // 转换节点类型：将后端格式转换为前端 ReactFlow 格式
      const convertedNodes = workflow.nodes.map((node: any) => {
        let frontendType = node.type
        let moduleType = node.data?.moduleType || node.type
        
        // 如果节点已经是前端格式（type 是 moduleNode/groupNode/noteNode/subflowHeaderNode）
        // 并且 data.moduleType 存在，则直接使用
        if (node.type === 'moduleNode' || node.type === 'groupNode' || 
            node.type === 'noteNode' || node.type === 'subflowHeaderNode') {
          // 已经是前端格式，保持不变
          return {
            ...node,
            data: {
              ...node.data,
              moduleType: moduleType,
            }
          }
        }
        
        // 否则，需要从后端格式转换为前端格式
        // 转换特殊的节点类型
        if (node.type === 'group') {
          frontendType = 'groupNode'
          moduleType = 'group'
        } else if (node.type === 'note') {
          frontendType = 'noteNode'
          moduleType = 'note'
        } else if (node.type === 'subflow_header') {
          frontendType = 'subflowHeaderNode'
          moduleType = 'subflow_header'
        } else {
          // 普通模块节点
          frontendType = 'moduleNode'
          moduleType = node.type
        }
        
        return {
          ...node,
          type: frontendType,
          data: {
            ...node.data,
            moduleType: moduleType,
          }
        }
      })
      
      // 导入变量（如果有）
      const importedVariables = workflow.variables || []
      
      set({
        id: workflow.id || nanoid(),
        name: workflow.name || '导入的工作流',
        nodes: convertedNodes,
        edges: workflow.edges,
        variables: importedVariables,  // 恢复变量
        selectedNodeId: null,
        hasUnsavedChanges: false,  // 导入后标记为已保存
      })
      return true
    } catch {
      return false
    }
  },
  
  mergeWorkflow: (json, position) => {
    try {
      const workflow = JSON.parse(json)
      if (!workflow.nodes || !workflow.edges) {
        return false
      }
      
      const state = get()
      
      // 生成新的节点ID映射（旧ID -> 新ID）
      const idMap = new Map<string, string>()
      workflow.nodes.forEach((node: any) => {
        idMap.set(node.id, nanoid())
      })
      
      // 计算导入节点的边界框
      let minX = Infinity, minY = Infinity
      workflow.nodes.forEach((node: any) => {
        if (node.position.x < minX) minX = node.position.x
        if (node.position.y < minY) minY = node.position.y
      })
      
      // 计算位置偏移（如果提供了目标位置）
      const offsetX = position ? position.x - minX : 0
      const offsetY = position ? position.y - minY : 0
      
      // 转换节点（更新ID、位置和类型）
      const newNodes: Node<NodeData>[] = workflow.nodes.map((node: any) => {
        let frontendType = node.type
        let moduleType = node.data?.moduleType || node.type
        
        // 如果节点已经是前端格式（type 是 moduleNode/groupNode/noteNode/subflowHeaderNode）
        // 并且 data.moduleType 存在，则直接使用
        if (node.type === 'moduleNode' || node.type === 'groupNode' || 
            node.type === 'noteNode' || node.type === 'subflowHeaderNode') {
          // 已经是前端格式，保持类型不变
          frontendType = node.type
        } else {
          // 否则，需要从后端格式转换为前端格式
          // 转换特殊的节点类型
          if (node.type === 'group') {
            frontendType = 'groupNode'
            moduleType = 'group'
          } else if (node.type === 'note') {
            frontendType = 'noteNode'
            moduleType = 'note'
          } else if (node.type === 'subflow_header') {
            frontendType = 'subflowHeaderNode'
            moduleType = 'subflow_header'
          } else {
            // 普通模块节点
            frontendType = 'moduleNode'
            moduleType = node.type
          }
        }
        
        return {
          ...node,
          id: idMap.get(node.id) || nanoid(),
          type: frontendType,
          position: {
            x: node.position.x + offsetX,
            y: node.position.y + offsetY,
          },
          data: {
            ...node.data,
            moduleType: moduleType,
          },
          selected: false,
        }
      })
      
      // 转换边（更新源和目标ID）
      const newEdges: Edge[] = workflow.edges.map((edge: Edge) => ({
        ...edge,
        id: nanoid(),
        source: idMap.get(edge.source) || edge.source,
        target: idMap.get(edge.target) || edge.target,
      }))
      
      // 合并变量（避免重复）
      const existingVarNames = new Set(state.variables.map(v => v.name))
      const newVariables = (workflow.variables || []).filter(
        (v: Variable) => !existingVarNames.has(v.name)
      )
      
      set({
        nodes: [...state.nodes, ...newNodes],
        edges: [...state.edges, ...newEdges],
        variables: [...state.variables, ...newVariables],
        selectedNodeId: null,
      })
      
      return true
    } catch {
      return false
    }
  },
  
  toggleNodesDisabled: (nodeIds) => {
    set({
      nodes: get().nodes.map((node) => {
        if (nodeIds.includes(node.id)) {
          return {
            ...node,
            data: {
              ...node.data,
              disabled: !node.data.disabled,
            },
          }
        }
        return node
      }),
    })
  },
}))
