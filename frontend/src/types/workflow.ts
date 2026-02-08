// 位置
export interface Position {
  x: number
  y: number
}

// 模块类型
export type ModuleType =
  // 浏览器操作
  | 'open_page'
  | 'click_element'
  | 'hover_element'
  | 'input_text'
  | 'get_element_info'
  | 'wait'
  | 'wait_element'
  | 'wait_image'
  | 'close_page'
  | 'refresh_page'
  | 'go_back'
  | 'go_forward'
  | 'handle_dialog'
  | 'inject_javascript'
  | 'switch_iframe'
  | 'switch_to_main'
  | 'switch_tab'
  // 表单操作
  | 'select_dropdown'
  | 'set_checkbox'
  | 'drag_element'
  | 'scroll_page'
  | 'upload_file'
  // 元素操作
  | 'get_child_elements'
  | 'get_sibling_elements'
  // 数据处理
  | 'set_variable'
  | 'json_parse'
  | 'base64'
  | 'random_number'
  | 'get_time'
  | 'download_file'
  | 'save_image'
  | 'screenshot'
  | 'read_excel'
  // 字符串操作
  | 'regex_extract'
  | 'string_replace'
  | 'string_split'
  | 'string_join'
  | 'string_concat'
  | 'string_trim'
  | 'string_case'
  | 'string_substring'
  // 列表操作
  | 'list_operation'
  | 'list_get'
  | 'list_length'
  | 'list_export'
  // 字典操作
  | 'dict_operation'
  | 'dict_get'
  | 'dict_keys'
  // 数据表格操作
  | 'table_add_row'
  | 'table_add_column'
  | 'table_set_cell'
  | 'table_get_cell'
  | 'table_delete_row'
  | 'table_clear'
  | 'table_export'
  // 数据库操作
  | 'db_connect'
  | 'db_query'
  | 'db_execute'
  | 'db_insert'
  | 'db_update'
  | 'db_delete'
  | 'db_close'
  // 网络请求
  | 'api_request'
  | 'send_email'
  // QQ自动化
  | 'qq_send_message'
  | 'qq_send_image'
  | 'qq_send_file'
  | 'qq_wait_message'
  | 'qq_get_friends'
  | 'qq_get_groups'
  | 'qq_get_group_members'
  | 'qq_get_login_info'
  // 微信自动化
  | 'wechat_send_message'
  | 'wechat_send_file'
  // AI能力
  | 'ai_chat'
  | 'ai_vision'
  | 'ai_smart_scraper'
  | 'ai_element_selector'
  | 'firecrawl_scrape'
  | 'firecrawl_map'
  | 'firecrawl_crawl'
  // 验证码
  | 'ocr_captcha'
  | 'slider_captcha'
  // 流程控制
  | 'condition'
  | 'loop'
  | 'foreach'
  | 'break_loop'
  | 'continue_loop'
  | 'scheduled_task'
  | 'subflow'  // 子流程调用
  | 'subflow_header'  // 子流程头（函数头形式）
  // 触发器
  | 'webhook_trigger'
  | 'hotkey_trigger'
  | 'file_watcher_trigger'
  | 'email_trigger'
  | 'api_trigger'
  | 'mouse_trigger'
  | 'image_trigger'
  | 'sound_trigger'
  | 'face_trigger'
  | 'element_change_trigger'
  // 辅助工具
  | 'print_log'
  | 'play_sound'
  | 'system_notification'
  | 'play_music'
  | 'play_video'
  | 'view_image'
  | 'input_prompt'
  | 'text_to_speech'
  | 'js_script'
  | 'python_script'
  | 'extract_table_data'
  | 'set_clipboard'
  | 'get_clipboard'
  | 'keyboard_action'
  | 'real_mouse_scroll'
  // 系统操作
  | 'shutdown_system'
  | 'lock_screen'
  | 'window_focus'
  | 'real_mouse_click'
  | 'real_mouse_move'
  | 'real_mouse_drag'
  | 'real_keyboard'
  | 'run_command'
  | 'click_image'
  | 'get_mouse_position'
  | 'screenshot_screen'
  | 'rename_file'
  | 'network_capture'
  // 文件操作
  | 'list_files'
  | 'copy_file'
  | 'move_file'
  | 'delete_file'
  | 'create_folder'
  | 'file_exists'
  | 'get_file_info'
  | 'read_text_file'
  | 'write_text_file'
  | 'rename_folder'
  // 宏录制器
  | 'macro_recorder'
  // 媒体处理（FFmpeg）
  | 'format_convert'
  | 'compress_image'
  | 'compress_video'
  | 'extract_audio'
  | 'trim_video'
  | 'merge_media'
  | 'add_watermark'
  | 'download_m3u8'
  | 'rotate_video'
  | 'video_speed'
  | 'extract_frame'
  | 'add_subtitle'
  | 'adjust_volume'
  | 'resize_video'
  // AI识别
  | 'face_recognition'
  | 'image_ocr'
  // PDF处理
  | 'pdf_to_images'
  | 'images_to_pdf'
  | 'pdf_merge'
  | 'pdf_split'
  | 'pdf_extract_text'
  | 'pdf_extract_images'
  | 'pdf_encrypt'
  | 'pdf_decrypt'
  | 'pdf_add_watermark'
  | 'pdf_rotate'
  | 'pdf_delete_pages'
  | 'pdf_get_info'
  | 'pdf_compress'
  | 'pdf_insert_pages'
  | 'pdf_reorder_pages'
  | 'pdf_to_word'
  // 文档转换（Pandoc）
  | 'markdown_to_html'
  | 'html_to_markdown'
  | 'markdown_to_pdf'
  | 'markdown_to_docx'
  | 'docx_to_markdown'
  | 'html_to_docx'
  | 'docx_to_html'
  | 'markdown_to_epub'
  | 'epub_to_markdown'
  | 'latex_to_pdf'
  | 'rst_to_html'
  | 'org_to_html'
  | 'universal_doc_convert'
  // 其他
  | 'export_log'
  | 'click_text'
  | 'hover_image'
  | 'hover_text'
  | 'drag_image'
  // 图像处理
  | 'image_grayscale'
  | 'image_round_corners'
  // Pillow图像处理
  | 'image_resize'
  | 'image_crop'
  | 'image_rotate'
  | 'image_flip'
  | 'image_blur'
  | 'image_sharpen'
  | 'image_brightness'
  | 'image_contrast'
  | 'image_color_balance'
  | 'image_convert_format'
  | 'image_add_text'
  | 'image_merge'
  | 'image_thumbnail'
  | 'image_filter'
  | 'image_get_info'
  | 'image_remove_bg'
  // 音频处理
  | 'audio_to_text'
  // 二维码
  | 'qr_generate'
  | 'qr_decode'
  // 录屏
  | 'screen_record'
  | 'camera_capture'
  | 'camera_record'
  // 网络共享
  | 'share_folder'
  | 'share_file'
  | 'stop_share'
  // 屏幕共享
  | 'start_screen_share'
  | 'stop_screen_share'
  // 分组/备注
  | 'group'
  | 'note'
  // 实用工具
  | 'file_hash_compare'
  | 'file_diff_compare'
  | 'folder_hash_compare'
  | 'folder_diff_compare'
  | 'random_password_generator'
  | 'url_encode_decode'
  | 'md5_encrypt'
  | 'sha_encrypt'
  | 'timestamp_converter'
  | 'rgb_to_hsv'
  | 'rgb_to_cmyk'
  | 'hex_to_cmyk'
  | 'uuid_generator'
  | 'printer_call'

// Excel文件资源
export interface DataAsset {
  id: string
  name: string
  originalName: string
  size: number
  uploadedAt: string
  sheetNames: string[]
  folder: string
}

// 图像资源
export interface ImageAsset {
  id: string
  name: string
  originalName: string
  size: number
  uploadedAt: string
  folder: string
  extension: string
  path?: string  // 图像文件的真实路径
}

// 工作流节点
export interface WorkflowNode {
  id: string
  type: ModuleType
  position: Position
  data: ModuleConfig
}

// 工作流边
export interface WorkflowEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string | null
  targetHandle?: string | null
}

// 变量类型
export type VariableType = 'string' | 'number' | 'boolean' | 'array' | 'object'

// 变量
export interface Variable {
  name: string
  value: unknown
  type: VariableType
  scope: 'global' | 'local'
}

// 工作流
export interface Workflow {
  id: string
  name: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  variables: Variable[]
  createdAt: string
  updatedAt: string
}

// 模块配置基类
export interface ModuleConfig {
  name?: string
  description?: string
  timeout?: number
  timeoutAction?: 'retry' | 'skip'  // 超时后的处理方式：重试或跳过
  retryCount?: number
  [key: string]: unknown
}

// 执行状态
export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'stopped'

// 执行结果
export interface ExecutionResult {
  workflowId: string
  status: ExecutionStatus
  startedAt: string
  completedAt?: string
  totalNodes: number
  executedNodes: number
  failedNodes: number
  errorMessage?: string
  dataFile?: string
}

// 日志级别
export type LogLevel = 'info' | 'warning' | 'error' | 'success'

// 日志条目
export interface LogEntry {
  id: string
  timestamp: string
  level: LogLevel
  nodeId?: string
  message: string
  details?: Record<string, unknown>
  duration?: number
}
