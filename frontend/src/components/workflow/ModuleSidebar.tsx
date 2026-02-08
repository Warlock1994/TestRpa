import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { moduleTypeLabels } from '@/store/workflowStore'
import { useModuleStatsStore } from '@/store/moduleStatsStore'
import type { ModuleType } from '@/types'
import { useState, useMemo, useEffect, useRef } from 'react'
import { pinyinMatch } from '@/lib/pinyin'
import { createPortal } from 'react-dom'
import {
  Globe,
  MousePointer,
  MousePointerClick,
  Type,
  Search,
  Clock,
  Timer,
  X,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CheckSquare,
  GripHorizontal,
  ArrowDownUp,
  Upload,
  Download,
  ImageDown,
  Eye,
  SlidersHorizontal,
  GitBranch,
  Repeat,
  ListOrdered,
  LogOut,
  SkipForward,
  Variable,
  MessageSquareText,
  MessageSquare,
  MessageSquareMore,
  Mail,
  Bell,
  Music,
  TextCursorInput,
  Bot,
  Send,
  FileJson,
  Dices,
  CalendarClock,
  Camera,
  FileSpreadsheet,
  ListPlus,
  ListMinus,
  Hash,
  BookOpen,
  KeyRound,
  Braces,
  ScanText,
  Square,
  AudioLines,
  Code,
  Code2,
  Table2,
  TableProperties,
  Columns3,
  Grid3X3,
  Trash2,
  FileOutput,
  FileDown,
  ClipboardPaste,
  Keyboard,
  RefreshCw,
  ArrowLeft,
  ArrowRight,
  MessageCircleWarning,
  StickyNote,
  Regex,
  Replace,
  Scissors,
  Link2,
  TextSelect,
  CaseSensitive,
  RemoveFormatting,
  ClipboardCopy,
  Plus,
  Workflow,
  Database,
  DatabaseZap,
  TableCellsSplit,
  CirclePlus,
  Pencil,
  CircleMinus,
  Unplug,
  Power,
  Lock,
  Move,
  Terminal,
  Image,
  Crosshair,
  Monitor,
  FileEdit,
  Radio,
  FileVideo,
  FileAudio,
  ImageMinus,
  Film,
  Video,
  Clapperboard,
  Combine,
  Droplets,
  UserCheck,
  ScanLine,
  FolderOpen,
  Copy,
  FileX,
  FolderPlus,
  FileQuestion,
  FileText,
  FilePen,
  Files,
  RotateCw,
  Gauge,
  ImagePlus,
  Subtitles,
  Volume,
  Maximize2,
  Users,
  User,
  FileUp,
  FileType,
  Split,
  FileKey,
  FileLock2,
  Info,
  Minimize2,
  ArrowUpDown,
  ScrollText,
  LetterText,
  MousePointer2,
  Share2,
  StopCircle,
  Star,
  ScreenShare,
  ScreenShareOff,
  Webhook,
  FolderSearch,
  FolderSync,
  Frame,
  ArrowUpFromLine,
  Layers,
  Sun,
  Palette,
  Zap,
  Sparkles,
  Eraser,
  Shield,
  Fingerprint,
  Printer,
  FlipHorizontal,
} from 'lucide-react'

// 收藏模块现在统一由 moduleStatsStore 管理，不再使用单独的 localStorage

// 模块图标映射 - 优化后更直观的图标
const moduleIcons: Record<ModuleType, React.ElementType> = {
  // 页面导航
  open_page: Globe,
  close_page: X,
  refresh_page: RefreshCw,
  go_back: ArrowLeft,
  go_forward: ArrowRight,
  // 元素交互
  click_element: MousePointerClick,
  hover_element: MousePointer,
  input_text: Type,
  select_dropdown: ChevronDown,
  set_checkbox: CheckSquare,
  drag_element: GripHorizontal,
  scroll_page: ArrowDownUp,
  handle_dialog: MessageCircleWarning,
  inject_javascript: Code,
  switch_iframe: Frame,
  switch_to_main: ArrowUpFromLine,
  switch_tab: Layers,
  // 数据提取
  get_element_info: Search,
  screenshot: Camera,
  save_image: ImageDown,
  download_file: Download,
  // 文件上传
  upload_file: Upload,
  // 元素操作
  get_child_elements: ListOrdered,
  get_sibling_elements: Columns3,
  // 等待控制
  wait: Clock,
  wait_element: Timer,
  wait_image: Eye,
  // 变量与数据
  set_variable: Variable,
  json_parse: FileJson,
  base64: Code2,
  random_number: Dices,
  get_time: CalendarClock,
  // 字符串处理
  regex_extract: Regex,
  string_replace: Replace,
  string_split: Scissors,
  string_join: Link2,
  string_concat: Plus,
  string_trim: RemoveFormatting,
  string_case: CaseSensitive,
  string_substring: TextSelect,
  // 列表操作
  list_operation: ListPlus,
  list_get: ListMinus,
  list_length: Hash,
  list_export: FileDown,
  // 字典操作
  dict_operation: Braces,
  dict_get: BookOpen,
  dict_keys: KeyRound,
  // 数据表格
  table_add_row: TableProperties,
  table_add_column: Columns3,
  table_set_cell: Grid3X3,
  table_get_cell: Table2,
  table_delete_row: Trash2,
  table_clear: X,
  table_export: FileOutput,
  // Excel
  read_excel: FileSpreadsheet,
  // 数据库操作
  db_connect: Database,
  db_query: DatabaseZap,
  db_execute: TableCellsSplit,
  db_insert: CirclePlus,
  db_update: Pencil,
  db_delete: CircleMinus,
  db_close: Unplug,
  // 流程控制
  condition: GitBranch,
  loop: Repeat,
  foreach: ListOrdered,
  break_loop: LogOut,
  continue_loop: SkipForward,
  scheduled_task: Clock,
  subflow: Workflow,
  // 触发器
  webhook_trigger: Webhook,
  hotkey_trigger: Keyboard,
  file_watcher_trigger: FolderSearch,
  email_trigger: Mail,
  api_trigger: RefreshCw,
  mouse_trigger: MousePointer2,
  image_trigger: Eye,
  sound_trigger: Volume,
  face_trigger: UserCheck,
  element_change_trigger: RefreshCw,
  // 网络请求
  api_request: Send,
  // AI
  ai_chat: Bot,
  ai_vision: ScanText,
  ai_smart_scraper: Bot,
  ai_element_selector: Crosshair,
  firecrawl_scrape: Globe,
  firecrawl_map: FolderSearch,
  firecrawl_crawl: Search,
  // 验证码
  ocr_captcha: Eye,
  slider_captcha: SlidersHorizontal,
  // 消息通知
  print_log: MessageSquareText,
  play_sound: Bell,
  system_notification: Bell,
  play_music: Music,
  play_video: Film,
  view_image: Image,
  text_to_speech: AudioLines,
  send_email: Mail,
  // QQ自动化
  qq_send_message: MessageSquare,
  qq_send_image: Image,
  qq_send_file: FileUp,
  qq_get_friends: Users,
  qq_get_groups: Users,
  qq_get_group_members: Users,
  qq_get_login_info: User,
  qq_wait_message: MessageSquareMore,
  // 微信自动化
  wechat_send_message: MessageSquare,
  wechat_send_file: FileUp,
  // 用户交互
  input_prompt: TextCursorInput,
  // 系统操作
  set_clipboard: ClipboardPaste,
  get_clipboard: ClipboardCopy,
  keyboard_action: Keyboard,
  real_mouse_scroll: MousePointer,
  shutdown_system: Power,
  lock_screen: Lock,
  window_focus: Maximize2,
  real_mouse_click: MousePointerClick,
  real_mouse_move: Move,
  real_mouse_drag: GripHorizontal,
  real_keyboard: Keyboard,
  run_command: Terminal,
  click_image: Image,
  get_mouse_position: Crosshair,
  screenshot_screen: Monitor,
  network_capture: Radio,
  // 媒体处理
  format_convert: FileVideo,
  compress_image: ImageMinus,
  compress_video: Film,
  // 格式工厂
  image_format_convert: ImagePlus,
  video_format_convert: FileVideo,
  audio_format_convert: FileAudio,
  video_to_audio: FileAudio,
  video_to_gif: Film,
  batch_format_convert: FolderSync,
  extract_audio: FileAudio,
  trim_video: Clapperboard,
  merge_media: Combine,
  add_watermark: Droplets,
  download_m3u8: Download,
  rotate_video: RotateCw,
  video_speed: Gauge,
  extract_frame: ImagePlus,
  add_subtitle: Subtitles,
  adjust_volume: Volume,
  resize_video: Maximize2,
  // AI识别
  face_recognition: UserCheck,
  image_ocr: ScanLine,
  // PDF处理
  pdf_to_images: ImagePlus,
  images_to_pdf: FileType,
  pdf_merge: Combine,
  pdf_split: Split,
  pdf_extract_text: FileText,
  pdf_extract_images: ImageDown,
  pdf_encrypt: FileKey,
  pdf_decrypt: FileLock2,
  pdf_add_watermark: Droplets,
  pdf_rotate: RotateCw,
  pdf_delete_pages: Trash2,
  pdf_get_info: Info,
  pdf_compress: Minimize2,
  pdf_insert_pages: CirclePlus,
  pdf_reorder_pages: ArrowUpDown,
  pdf_to_word: FileType,
  // 文档转换
  markdown_to_html: FileType,
  html_to_markdown: FileType,
  markdown_to_pdf: FileType,
  markdown_to_docx: FileType,
  docx_to_markdown: FileType,
  html_to_docx: FileType,
  docx_to_html: FileType,
  markdown_to_epub: BookOpen,
  epub_to_markdown: BookOpen,
  latex_to_pdf: FileType,
  rst_to_html: FileType,
  org_to_html: FileType,
  universal_doc_convert: RefreshCw,
  // 其他
  export_log: ScrollText,
  click_text: LetterText,
  hover_image: MousePointer2,
  hover_text: MousePointer2,
  drag_image: GripHorizontal,
  // 图像处理
  image_grayscale: ImageMinus,
  image_round_corners: Square,
  // Pillow图像处理
  image_resize: Maximize2,
  image_crop: Scissors,
  image_rotate: RotateCw,
  image_flip: FlipHorizontal,
  image_blur: Droplets,
  image_sharpen: Zap,
  image_brightness: Sun,
  image_contrast: Gauge,
  image_color_balance: Palette,
  image_convert_format: FileType,
  image_add_text: Type,
  image_merge: Combine,
  image_thumbnail: ImageMinus,
  image_filter: Sparkles,
  image_get_info: Info,
  image_remove_bg: Eraser,
  // 音频处理
  audio_to_text: AudioLines,
  // 二维码
  qr_generate: Grid3X3,
  qr_decode: ScanLine,
  // 录屏
  screen_record: Monitor,
  camera_capture: Camera,
  camera_record: Video,
  // 网络共享
  share_folder: Share2,
  share_file: Share2,
  stop_share: StopCircle,
  // 屏幕共享
  start_screen_share: ScreenShare,
  stop_screen_share: ScreenShareOff,
  // 文件操作
  list_files: FolderOpen,
  copy_file: Copy,
  move_file: Files,
  delete_file: FileX,
  create_folder: FolderPlus,
  file_exists: FileQuestion,
  get_file_info: FileText,
  read_text_file: FileText,
  write_text_file: FilePen,
  rename_file: FileEdit,
  rename_folder: FolderOpen,
  // 宏录制器
  macro_recorder: Film,
  // 脚本
  js_script: Code2,
  python_script: Code,
  extract_table_data: Table2,
  // 画布工具
  group: Square,
  subflow_header: Workflow,
  note: StickyNote,
  // 实用工具
  file_hash_compare: Shield,
  file_diff_compare: FileEdit,
  folder_hash_compare: Shield,
  folder_diff_compare: FolderSearch,
  random_password_generator: KeyRound,
  url_encode_decode: Link2,
  md5_encrypt: Fingerprint,
  sha_encrypt: Shield,
  timestamp_converter: Clock,
  rgb_to_hsv: Palette,
  rgb_to_cmyk: Palette,
  hex_to_cmyk: Palette,
  uuid_generator: Hash,
  printer_call: Printer,
}

// 模块搜索关键词（用于模糊搜索）
const moduleKeywords: Record<ModuleType, string[]> = {
  open_page: ['打开', '网页', '浏览器', 'url', '地址', 'open', 'page'],
  click_element: ['点击', '单击', '双击', '右键', 'click', '按钮'],
  hover_element: ['悬停', '鼠标', '移动', 'hover', 'mouse', '移入', '经过', '停留'],
  input_text: ['输入', '文本', '填写', 'input', 'text', '表单'],
  get_element_info: ['提取', '数据', '获取', '元素', '信息', 'get', 'element', '采集'],
  wait: ['等待', '延迟', '暂停', 'wait', 'delay', '时间', '固定'],
  wait_element: ['等待', '元素', '出现', '消失', 'wait', 'element', '存在', '隐藏'],
  wait_image: ['等待', '图像', '图片', '出现', '识别', 'wait', 'image', '屏幕', '匹配'],
  close_page: ['关闭', '网页', 'close', 'page'],
  refresh_page: ['刷新', '页面', '重新加载', 'refresh', 'reload', 'f5'],
  go_back: ['返回', '上一页', '后退', 'back', 'history', '历史'],
  go_forward: ['前进', '下一页', 'forward', 'history', '历史'],
  handle_dialog: ['弹窗', '对话框', '确认', '取消', 'alert', 'confirm', 'prompt', 'dialog', '提示框'],
  inject_javascript: ['js', 'javascript', '脚本', '注入', '执行', 'eval', '代码', 'script'],
  switch_iframe: ['切换', 'iframe', '内嵌', '框架', 'frame', '子页面', '嵌入', '内联框架', 'qhiframe', 'qh', 'nq', 'kj', 'zyym', 'qiehuan', 'neiqian', 'kuangjia', 'ziyemian', 'qianru', 'neilianku angjia'],
  switch_to_main: ['切换', '主页面', '退出', 'iframe', 'frame', '返回', '主框架', 'main', 'qhzyym', 'qh', 'zyym', 'tc', 'fh', 'zkj', 'qiehuan', 'zhuyemian', 'tuichu', 'fanhui', 'zhukuangjia'],
  switch_tab: ['切换', '标签页', 'tab', '页面', '窗口', '索引', '标题', 'url', '下一个', '上一个', 'qhbqy', 'qh', 'bqy', 'ym', 'ck', 'qiehuan', 'biaoqianye', 'yemian', 'chuangkou'],
  set_variable: ['设置', '变量', 'set', 'variable', '赋值'],
  json_parse: ['json', '解析', '提取', 'parse', '数据', 'jsonpath'],
  base64: ['base64', '编码', '解码', 'encode', 'decode', '转换', '图片', '文件'],
  random_number: ['随机', '数字', 'random', '生成', '随机数'],
  get_time: ['时间', '日期', 'time', 'date', '当前', '获取'],
  print_log: ['打印', '日志', 'print', 'log', '输出'],
  play_sound: ['播放', '提示音', '声音', 'sound', 'beep', '滴'],
  system_notification: ['系统', '消息', '通知', '弹窗', 'notification', 'toast', '提醒', '右下角'],
  play_music: ['播放', '音乐', '音频', 'music', 'audio', 'mp3', '歌曲', 'url'],
  play_video: ['播放', '视频', 'video', 'mp4', '影片', '电影'],
  view_image: ['查看', '图片', '图像', 'image', '照片', 'jpg', 'png', '预览'],
  input_prompt: ['用户', '输入', '弹窗', '对话框', 'prompt', 'input'],
  text_to_speech: ['语音', '播报', '朗读', 'tts', 'speech', '文本转语音', '读'],
  js_script: ['执行', '脚本', 'js', 'javascript', 'script', '代码', 'code', '自定义', '函数'],
  python_script: ['执行', '脚本', 'python', 'py', 'script', '代码', 'code', '自定义', '函数', 'Python3.13'],
  extract_table_data: ['表格', '数据', '提取', '爬取', '采集', 'table', 'extract', '批量', '列表', 'excel', '导出', '二维'],
  set_clipboard: ['剪贴板', '写入', '复制', '粘贴', 'clipboard', 'copy', 'paste', '图片', '文本'],
  get_clipboard: ['剪贴板', '读取', '获取', '粘贴', 'clipboard', 'paste', '内容'],
  keyboard_action: ['模拟', '按键', '键盘', '快捷键', 'keyboard', 'key', 'ctrl', 'alt', 'shift', '热键'],
  real_mouse_scroll: ['真实', '鼠标', '滚轮', '滚动', '物理', 'mouse', 'scroll', 'wheel', '系统', '硬件', '模拟'],
  shutdown_system: ['关机', '重启', '注销', '休眠', 'shutdown', 'restart', 'reboot', '电源', '系统'],
  lock_screen: ['锁屏', '锁定', '屏幕', 'lock', 'screen', '安全'],
  window_focus: ['窗口', '聚焦', '置顶', '前台', '激活', 'focus', 'window', 'foreground', '切换'],
  real_mouse_click: ['真实', '鼠标', '点击', '物理', 'mouse', 'click', '系统', '硬件', '左键', '右键', '中键'],
  real_mouse_move: ['真实', '鼠标', '移动', '物理', 'mouse', 'move', '系统', '硬件', '坐标', '位置'],
  real_mouse_drag: ['真实', '鼠标', '拖拽', '拖动', '物理', 'mouse', 'drag', '系统', '硬件', '长按', '拖放'],
  real_keyboard: ['真实', '键盘', '按键', '物理', 'keyboard', 'key', '系统', '硬件', '输入', '打字'],
  run_command: ['执行', '命令', '终端', 'cmd', 'command', 'shell', 'powershell', '脚本', '系统'],
  click_image: ['点击', '图像', '图片', '识别', 'image', 'click', '屏幕', '匹配', '查找'],
  get_mouse_position: ['获取', '鼠标', '位置', '坐标', 'mouse', 'position', 'cursor', '光标'],
  screenshot_screen: ['截屏', '屏幕', '截图', '桌面', 'screenshot', 'screen', 'capture', '全屏'],
  network_capture: ['网络', '抓包', '请求', 'network', 'capture', 'request', 'url', '监听', 'F12'],
  // 媒体处理
  format_convert: ['格式', '转换', '视频', '音频', '图片', 'convert', 'format', 'ffmpeg', 'mp4', 'mp3', 'jpg', 'png'],
  // 格式工厂
  image_format_convert: ['图片', '格式', '转换', 'image', 'convert', 'jpg', 'png', 'webp', 'bmp', 'gif', 'ico', 'tiff'],
  video_format_convert: ['视频', '格式', '转换', 'video', 'convert', 'mp4', 'avi', 'mkv', 'mov', 'flv', 'webm'],
  audio_format_convert: ['音频', '格式', '转换', 'audio', 'convert', 'mp3', 'aac', 'wav', 'flac', 'ogg', 'm4a'],
  video_to_audio: ['视频', '转', '音频', '提取', 'video', 'audio', 'extract', 'mp3', 'wav'],
  video_to_gif: ['视频', '转', 'GIF', '动图', 'video', 'gif', 'animation'],
  batch_format_convert: ['批量', '格式', '转换', 'batch', 'convert', '文件夹', '多个'],
  compress_image: ['压缩', '图片', '图像', '缩小', 'compress', 'image', '质量', '体积', 'jpg', 'png'],
  compress_video: ['压缩', '视频', '缩小', 'compress', 'video', '质量', '体积', 'mp4', '码率'],
  extract_audio: ['提取', '音频', '视频', '分离', 'extract', 'audio', 'mp3', '声音', '音轨'],
  trim_video: ['裁剪', '视频', '剪切', '截取', 'trim', 'cut', 'video', '片段', '时长'],
  merge_media: ['合并', '视频', '音频', '拼接', 'merge', 'concat', '连接', '组合', '混合', '替换', '配音', '背景音乐'],
  add_watermark: ['水印', '添加', '图片', '视频', 'watermark', '标记', '文字', 'logo'],
  download_m3u8: ['下载', 'M3U8', 'HLS', '视频', '流媒体', 'download', 'm3u8', 'stream', '直播', '录制'],
  rotate_video: ['旋转', '翻转', '视频', '方向', 'rotate', 'flip', '镜像', '倒转', '90度', '180度'],
  video_speed: ['倍速', '加速', '减速', '快进', '慢放', 'speed', 'fast', 'slow', '2倍速', '0.5倍'],
  extract_frame: ['截取', '帧', '视频', '图片', '封面', 'frame', 'extract', 'thumbnail', '关键帧'],
  add_subtitle: ['字幕', '添加', '视频', '烧录', 'subtitle', 'srt', 'ass', '硬字幕'],
  adjust_volume: ['音量', '调节', '增大', '减小', '音频', 'volume', '声音', '响度', '静音'],
  resize_video: ['分辨率', '调整', '缩放', '视频', '尺寸', 'resize', 'scale', '1080p', '720p', '4K'],
  // AI识别
  face_recognition: ['人脸', '识别', '面部', '检测', 'face', 'recognition', '比对', '匹配', '身份'],
  image_ocr: ['图片', 'OCR', '文字', '识别', '提取', 'text', '扫描', '文本'],
  // PDF处理
  pdf_to_images: ['PDF', '转', '图片', '导出', 'pdf', 'image', 'convert', '转换', '页面'],
  images_to_pdf: ['图片', '转', 'PDF', '合成', 'image', 'pdf', 'convert', '转换', '生成'],
  pdf_merge: ['PDF', '合并', '拼接', 'merge', 'combine', '组合', '多个'],
  pdf_split: ['PDF', '拆分', '分割', 'split', '分离', '单页'],
  pdf_extract_text: ['PDF', '提取', '文本', '文字', 'extract', 'text', 'OCR', '内容'],
  pdf_extract_images: ['PDF', '提取', '图片', '图像', 'extract', 'image', '导出'],
  pdf_encrypt: ['PDF', '加密', '密码', 'encrypt', 'password', '保护', '安全'],
  pdf_decrypt: ['PDF', '解密', '密码', 'decrypt', 'password', '解锁'],
  pdf_add_watermark: ['PDF', '水印', '添加', 'watermark', '标记', '文字', '图片'],
  pdf_rotate: ['PDF', '旋转', '页面', 'rotate', '方向', '90度', '180度'],
  pdf_delete_pages: ['PDF', '删除', '页面', 'delete', 'page', '移除'],
  pdf_get_info: ['PDF', '信息', '属性', 'info', '页数', '大小', '元数据'],
  pdf_compress: ['PDF', '压缩', '缩小', 'compress', '体积', '优化'],
  pdf_insert_pages: ['PDF', '插入', '页面', 'insert', 'page', '添加'],
  pdf_reorder_pages: ['PDF', '重排', '页面', '顺序', 'reorder', 'page', '调整'],
  pdf_to_word: ['PDF', '转', 'Word', '文档', 'docx', '转换', 'convert'],
  // 其他
  export_log: ['导出', '日志', 'export', 'log', '保存', '记录', 'txt', 'json', 'csv'],
  click_text: ['点击', '文本', '文字', 'OCR', 'click', 'text', '识别', '屏幕'],
  hover_image: ['悬停', '图像', '图片', 'hover', 'image', '鼠标', '移动'],
  hover_text: ['悬停', '文本', '文字', 'hover', 'text', 'OCR', '鼠标'],
  drag_image: ['拖拽', '图像', '图片', 'drag', 'image', '拖动', '移动', '长按'],
  // 图像处理
  image_grayscale: ['图片', '去色', '灰度', '黑白', 'grayscale', 'gray', '转换'],
  image_round_corners: ['图片', '圆角', '圆角化', 'round', 'corners', '边角', '美化'],
  // 音频处理
  audio_to_text: ['音频', '转', '文本', '语音', '识别', 'speech', 'text', '转写', '听写'],
  // 二维码
  qr_generate: ['二维码', '生成', 'QR', 'qrcode', '创建', '制作'],
  qr_decode: ['二维码', '解码', '识别', 'QR', 'qrcode', '扫描', '读取'],
  // 录屏
  screen_record: ['录屏', '屏幕', '录制', 'record', 'screen', '视频', '桌面'],
  camera_capture: ['摄像头', '拍照', '照相', 'camera', 'capture', 'photo', '相机', '摄影'],
  camera_record: ['摄像头', '录像', '录制', 'camera', 'record', 'video', '相机', '摄影'],
  // 网络共享
  share_folder: ['共享', '文件夹', '网络', '局域网', 'share', 'folder', 'LAN', '分享', '传输'],
  share_file: ['共享', '文件', '网络', '局域网', 'share', 'file', 'LAN', '分享', '传输'],
  stop_share: ['停止', '共享', '关闭', 'stop', 'share', '结束'],
  // 屏幕共享
  start_screen_share: ['屏幕', '共享', '开始', '直播', '投屏', 'screen', 'share', 'cast', '局域网', '实时', '画面'],
  stop_screen_share: ['屏幕', '共享', '停止', '结束', 'screen', 'share', 'stop', '关闭'],
  // 文件操作
  list_files: ['文件', '列表', '目录', '文件夹', '获取', 'list', 'files', 'folder', 'directory', '遍历', '扫描'],
  copy_file: ['复制', '文件', '拷贝', 'copy', 'file', '副本'],
  move_file: ['移动', '文件', '剪切', 'move', 'file', '转移'],
  delete_file: ['删除', '文件', '移除', 'delete', 'file', 'remove', '清除'],
  create_folder: ['创建', '文件夹', '目录', 'create', 'folder', 'mkdir', 'directory', '新建'],
  file_exists: ['文件', '存在', '判断', '检查', 'exists', 'file', 'check'],
  get_file_info: ['文件', '信息', '属性', '大小', '时间', 'info', 'file', 'size', 'stat'],
  read_text_file: ['读取', '文本', '文件', 'read', 'text', 'file', '内容', 'txt'],
  write_text_file: ['写入', '文本', '文件', 'write', 'text', 'file', '保存', 'txt'],
  rename_file: ['重命名', '文件', '改名', 'rename', 'file', '修改', '名称'],
  rename_folder: ['重命名', '文件夹', '目录', '改名', 'rename', 'folder', 'directory', '修改', '名称'],
  macro_recorder: ['宏', '录制', '鼠标', '键盘', '回放', '播放', 'macro', 'record', 'replay', '自动化', '操作', '录像'],
  // QQ自动化
  qq_send_message: ['QQ', '发送', '消息', '私聊', '群聊', 'qq', 'message', 'send', '聊天'],
  qq_send_image: ['QQ', '发送', '图片', '私聊', '群聊', 'qq', 'image', 'send', '照片'],
  qq_send_file: ['QQ', '发送', '文件', '私聊', '群聊', 'qq', 'file', 'send', '上传', '群文件'],
  qq_get_friends: ['QQ', '好友', '列表', '获取', 'qq', 'friends', 'list', '联系人'],
  qq_get_groups: ['QQ', '群', '列表', '获取', 'qq', 'groups', 'list', '群组'],
  qq_get_group_members: ['QQ', '群成员', '列表', '获取', 'qq', 'group', 'members', '成员'],
  qq_get_login_info: ['QQ', '登录', '信息', '获取', 'qq', 'login', 'info', '账号', '用户'],
  qq_wait_message: ['QQ', '等待', '消息', '接收', '监听', 'qq', 'wait', 'message', 'receive', '触发'],
  // 微信自动化
  wechat_send_message: ['微信', '发送', '消息', 'wechat', 'weixin', 'message', 'send', '聊天'],
  wechat_send_file: ['微信', '发送', '文件', '图片', 'wechat', 'weixin', 'file', 'image', 'send', '上传'],
  select_dropdown: ['下拉', '选择', 'select', 'dropdown'],
  set_checkbox: ['复选框', '勾选', 'checkbox', '选中'],
  drag_element: ['拖拽', '拖动', 'drag', '移动'],
  scroll_page: ['滚动', '滑动', 'scroll', '翻页'],
  upload_file: ['上传', '文件', 'upload', 'file'],
  get_child_elements: ['子元素', '获取', '列表', 'child', 'children', 'elements', '子节点'],
  get_sibling_elements: ['兄弟元素', '同级', '获取', '列表', 'sibling', 'elements', '兄弟节点'],
  download_file: ['下载', '文件', 'download', 'file'],
  save_image: ['保存', '图片', 'save', 'image'],
  screenshot: ['截图', '网页', '网页截图', 'screenshot', '快照', '页面'],
  read_excel: ['读取', 'excel', '表格', 'xlsx', 'xls', '数据', '文件', '资产'],
  // 字符串操作
  regex_extract: ['正则', '提取', '匹配', 'regex', 'regexp', '表达式', '搜索', 'match', 'find', '查找'],
  string_replace: ['替换', '字符串', 'replace', '文本', '修改', '更换'],
  string_split: ['分割', '拆分', '字符串', 'split', '切割', '分隔'],
  string_join: ['连接', '合并', '拼接', 'join', '字符串', '组合', '列表'],
  string_concat: ['拼接', '字符串', 'concat', '合并', '连接', '组合', '加'],
  string_trim: ['去除', '空白', '空格', 'trim', '修剪', '清理', '首尾'],
  string_case: ['大小写', '转换', '大写', '小写', 'case', 'upper', 'lower', '首字母'],
  string_substring: ['截取', '子串', '字符串', 'substring', 'slice', '切片', '部分'],
  // 列表操作
  list_operation: ['列表', '数组', '添加', '删除', '修改', 'list', 'array', 'push', 'pop', 'append'],
  list_get: ['列表', '取值', '获取', '元素', '索引', 'list', 'get', 'index'],
  list_length: ['列表', '长度', '数量', 'length', 'count', 'size'],
  list_export: ['列表', '导出', 'txt', '文本', '保存', 'export', 'save', '文件'],
  // 字典操作
  dict_operation: ['字典', '对象', '添加', '删除', '修改', 'dict', 'object', 'set', 'key', 'value'],
  dict_get: ['字典', '取值', '获取', '值', 'dict', 'get', 'key'],
  dict_keys: ['字典', '键', '列表', '所有', 'keys', 'dict'],
  // 数据表格操作
  table_add_row: ['数据', '表格', '添加', '行', 'table', 'row', 'add', '新增', '插入'],
  table_add_column: ['数据', '表格', '添加', '列', 'table', 'column', 'add', '新增'],
  table_set_cell: ['数据', '表格', '设置', '单元格', 'table', 'cell', 'set', '修改', '更新'],
  table_get_cell: ['数据', '表格', '读取', '单元格', 'table', 'cell', 'get', '获取', '取值'],
  table_delete_row: ['数据', '表格', '删除', '行', 'table', 'row', 'delete', '移除'],
  table_clear: ['数据', '表格', '清空', 'table', 'clear', '清除', '重置'],
  table_export: ['数据', '表格', '导出', 'table', 'export', 'excel', 'csv', '下载', '保存'],
  api_request: ['http', '请求', 'api', 'get', 'post', 'request', '接口', '网络'],
  send_email: ['发送', '邮件', 'email', 'mail', 'qq'],
  ai_chat: ['ai', '对话', '智能', 'chat', 'gpt', '大模型', '智谱', 'deepseek', '聊天', '问答'],
  ai_vision: ['图像', '识别', 'ai', '视觉', '图片', 'vision', '看图', 'glm', '理解', '分析'],
  ai_smart_scraper: ['ai', '智能', '爬虫', '抓取', '提取', 'scraper', '数据', '网页', '自然语言', '自适应', '结构变化', 'scrapegraph'],
  ai_element_selector: ['ai', '智能', '元素', '选择器', 'selector', '查找', '定位', '自然语言', '自适应', '结构变化', 'scrapegraph'],
  firecrawl_scrape: ['ai', '单页', '抓取', '数据', 'firecrawl', 'scrape', '网页', '智能', '提取', '爬虫', '采集'],
  firecrawl_map: ['ai', '网站', '链接', '抓取', 'firecrawl', 'map', '地图', '导航', '站点', '结构', '爬虫'],
  firecrawl_crawl: ['ai', '全站', '抓取', '数据', 'firecrawl', 'crawl', '爬虫', '网站', '批量', '深度', '采集'],
  ocr_captcha: ['ocr', '识别', '验证码', '文字', 'captcha'],
  slider_captcha: ['滑块', '验证', '验证码', 'slider', '拖动'],
  condition: ['条件', '判断', 'if', 'condition', '分支'],
  loop: ['循环', '重复', 'loop', 'for', '次数'],
  foreach: ['遍历', '列表', 'foreach', '数组', 'each'],
  break_loop: ['跳出', '循环', 'break', '退出'],
  continue_loop: ['跳过', '当前', '本次', '循环', 'continue', '下一次', 'skip'],
  scheduled_task: ['定时', '执行', '计划', '任务', 'schedule', 'timer', 'cron', '时间', '延迟'],
  subflow: ['子流程', '复用', '调用', '函数', 'subflow', 'call', '引用', '嵌套', '模块化'],
  // 触发器
  webhook_trigger: ['webhook', '触发器', 'http', '请求', '回调', 'trigger', 'api', '接口', '钩子'],
  hotkey_trigger: ['热键', '快捷键', '触发器', 'hotkey', 'shortcut', 'trigger', '按键', '组合键', 'ctrl', 'alt', 'shift'],
  file_watcher_trigger: ['文件', '监控', '触发器', '文件夹', 'file', 'watcher', 'trigger', '创建', '修改', '删除', '变化'],
  email_trigger: ['邮件', '触发器', 'email', 'mail', 'trigger', '收件', '邮箱', 'imap', '监控'],
  api_trigger: ['api', '触发器', '轮询', 'trigger', 'polling', '接口', '状态', '检查', '等待'],
  mouse_trigger: ['鼠标', '触发器', 'mouse', 'trigger', '点击', '移动', '滚轮', '左键', '右键', '中键'],
  image_trigger: ['图像', '触发器', 'image', 'trigger', '图片', '识别', '检测', '出现', '屏幕'],
  sound_trigger: ['声音', '触发器', 'sound', 'trigger', '音频', '音量', '检测', '监听', '麦克风'],
  face_trigger: ['人脸', '触发器', 'face', 'trigger', '面部', '识别', '检测', '摄像头', '相机'],
  element_change_trigger: ['元素', '变化', '触发器', 'element', 'change', 'trigger', '子元素', '数量', '监控', '直播', '评论', '聊天', '消息', '实时'],
  group: ['分组', '注释', '备注', 'group', 'comment', '框', '区域'],
  subflow_header: ['子流程头', '函数头', '子流程定义', 'header', 'function'],
  note: ['便签', '笔记', '备注', 'note', 'sticky', '文本', '说明'],
  // 数据库操作
  db_connect: ['数据库', '连接', 'mysql', 'database', 'connect', '登录', '链接'],
  db_query: ['数据库', '查询', 'select', 'query', '搜索', '读取', '获取'],
  db_execute: ['数据库', '执行', 'sql', 'execute', '语句', '命令'],
  db_insert: ['数据库', '插入', 'insert', '添加', '新增', '写入'],
  db_update: ['数据库', '更新', 'update', '修改', '编辑'],
  db_delete: ['数据库', '删除', 'delete', '移除', '清除'],
  db_close: ['数据库', '关闭', '断开', 'close', 'disconnect', '连接'],
  // 文档转换 (13个)
  markdown_to_html: ['markdown', 'md', 'html', '转换', '文档', 'convert', '网页', '格式'],
  html_to_markdown: ['html', 'markdown', 'md', '转换', '文档', 'convert', '网页', '格式'],
  markdown_to_pdf: ['markdown', 'md', 'pdf', '转换', '文档', 'convert', '格式', 'latex'],
  markdown_to_docx: ['markdown', 'md', 'word', 'docx', '转换', '文档', 'convert', '格式'],
  docx_to_markdown: ['word', 'docx', 'markdown', 'md', '转换', '文档', 'convert', '格式'],
  html_to_docx: ['html', 'word', 'docx', '转换', '文档', 'convert', '网页', '格式'],
  docx_to_html: ['word', 'docx', 'html', '转换', '文档', 'convert', '网页', '格式'],
  markdown_to_epub: ['markdown', 'md', 'epub', '电子书', '转换', '文档', 'convert', '格式', '书籍'],
  epub_to_markdown: ['epub', '电子书', 'markdown', 'md', '转换', '文档', 'convert', '格式'],
  latex_to_pdf: ['latex', 'tex', 'pdf', '转换', '文档', 'convert', '格式', '论文'],
  rst_to_html: ['rst', 'restructuredtext', 'html', '转换', '文档', 'convert', '格式'],
  org_to_html: ['org', 'orgmode', 'html', '转换', '文档', 'convert', '格式', 'emacs'],
  universal_doc_convert: ['文档', '转换', '通用', 'pandoc', 'convert', '格式', '万能', '任意'],
  // Pillow图像处理 (16个)
  image_resize: ['图片', '缩放', '调整', '大小', '尺寸', 'resize', 'scale', '放大', '缩小', '宽度', '高度'],
  image_crop: ['图片', '裁剪', '剪切', '截取', 'crop', 'cut', '区域', '选区'],
  image_rotate: ['图片', '旋转', '角度', 'rotate', '转动', '方向', '90度', '180度'],
  image_flip: ['图片', '翻转', '镜像', 'flip', 'mirror', '水平', '垂直', '倒转'],
  image_blur: ['图片', '模糊', '虚化', 'blur', '高斯', '柔化', '朦胧'],
  image_sharpen: ['图片', '锐化', '清晰', 'sharpen', '增强', '细节', '锐利'],
  image_brightness: ['图片', '亮度', '明暗', 'brightness', '调节', '增亮', '变暗'],
  image_contrast: ['图片', '对比度', 'contrast', '调节', '增强', '反差'],
  image_color_balance: ['图片', '色彩', '饱和度', '颜色', 'color', 'balance', '调节', '鲜艳'],
  image_convert_format: ['图片', '格式', '转换', 'convert', 'format', 'png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif', 'heic'],
  image_add_text: ['图片', '添加', '文字', '文本', '水印', 'text', 'add', '标注', '字体'],
  image_merge: ['图片', '拼接', '合并', '组合', 'merge', 'concat', '横向', '纵向', '拼图'],
  image_thumbnail: ['图片', '缩略图', '预览', 'thumbnail', '小图', '图标'],
  image_filter: ['图片', '滤镜', '特效', 'filter', '效果', '风格', '艺术', '边缘', '浮雕'],
  image_get_info: ['图片', '信息', '属性', '元数据', 'info', 'exif', '尺寸', '格式', '大小'],
  image_remove_bg: ['图片', '去背景', '抠图', '透明', 'background', 'remove', '去除', '背景色'],
  // 实用工具模块
  file_hash_compare: ['文件', '哈希', '对比', '比较', 'hash', 'compare', 'md5', 'sha', '校验', '相同'],
  file_diff_compare: ['文件', '差异', '对比', '比较', 'diff', 'compare', '不同', '变化', '修改'],
  folder_hash_compare: ['文件夹', '目录', '哈希', '对比', '比较', 'folder', 'hash', 'compare', '相同'],
  folder_diff_compare: ['文件夹', '目录', '差异', '对比', '比较', 'folder', 'diff', 'compare', '不同', '变化'],
  random_password_generator: ['密码', '生成', '随机', 'password', 'random', 'generate', '安全', '强度'],
  url_encode_decode: ['URL', '编码', '解码', 'encode', 'decode', '转义', '网址', '链接'],
  md5_encrypt: ['MD5', '加密', '哈希', 'hash', 'encrypt', '摘要', '校验'],
  sha_encrypt: ['SHA', '加密', '哈希', 'hash', 'encrypt', 'sha1', 'sha256', 'sha512', '摘要'],
  timestamp_converter: ['时间戳', '转换', 'timestamp', 'convert', '日期', '时间', 'unix'],
  rgb_to_hsv: ['RGB', 'HSV', '颜色', '转换', 'color', 'convert', '色彩空间'],
  rgb_to_cmyk: ['RGB', 'CMYK', '颜色', '转换', 'color', 'convert', '印刷', '色彩空间'],
  hex_to_cmyk: ['HEX', 'CMYK', '颜色', '转换', 'color', 'convert', '十六进制', '印刷'],
  uuid_generator: ['UUID', '生成', 'generate', '唯一', '标识符', 'guid', '随机'],
  printer_call: ['打印', '打印机', 'printer', 'print', '文档', 'PDF', 'Word', '图片'],
}

// 模块分类 - 优化后更清晰的分类结构
const moduleCategories = [
  // ===== 浏览器自动化 =====
  {
    name: '🌐 页面操作',
    color: 'bg-blue-500',
    modules: ['open_page', 'close_page', 'refresh_page', 'go_back', 'go_forward', 'inject_javascript', 'switch_iframe', 'switch_to_main', 'switch_tab'] as ModuleType[],
  },
  {
    name: '🖱️ 元素交互',
    color: 'bg-indigo-500',
    modules: ['click_element', 'hover_element', 'input_text', 'select_dropdown', 'set_checkbox', 'drag_element', 'scroll_page', 'handle_dialog', 'upload_file'] as ModuleType[],
  },
  {
    name: '🔍 元素操作',
    color: 'bg-purple-500',
    modules: ['get_child_elements', 'get_sibling_elements'] as ModuleType[],
  },
  {
    name: '📥 数据采集',
    color: 'bg-emerald-500',
    modules: ['get_element_info', 'screenshot', 'save_image', 'download_file', 'extract_table_data'] as ModuleType[],
  },
  {
    name: '⏱️ 等待控制',
    color: 'bg-cyan-500',
    modules: ['wait', 'wait_element', 'wait_image'] as ModuleType[],
  },
  {
    name: '🔧 高级操作',
    color: 'bg-sky-600',
    modules: ['network_capture'] as ModuleType[],
  },
  // ===== 桌面自动化 =====
  {
    name: '🖱️ 鼠标模拟',
    color: 'bg-violet-500',
    modules: ['real_mouse_click', 'real_mouse_move', 'real_mouse_drag', 'real_mouse_scroll', 'get_mouse_position'] as ModuleType[],
  },
  {
    name: '⌨️ 键盘模拟',
    color: 'bg-purple-500',
    modules: ['real_keyboard', 'keyboard_action'] as ModuleType[],
  },
  {
    name: '🎯 图像/文字识别点击',
    color: 'bg-rose-500',
    modules: ['click_image', 'click_text', 'hover_image', 'hover_text', 'drag_image'] as ModuleType[],
  },
  {
    name: '📷 屏幕操作',
    color: 'bg-pink-500',
    modules: ['screenshot_screen', 'screen_record', 'window_focus', 'camera_capture', 'camera_record'] as ModuleType[],
  },
  {
    name: '🎹 宏录制',
    color: 'bg-fuchsia-500',
    modules: ['macro_recorder'] as ModuleType[],
  },
  {
    name: '🖥️ 系统控制',
    color: 'bg-gray-600',
    modules: ['shutdown_system', 'lock_screen', 'run_command'] as ModuleType[],
  },
  {
    name: '📋 剪贴板',
    color: 'bg-stone-600',
    modules: ['set_clipboard', 'get_clipboard'] as ModuleType[],
  },
  // ===== 数据处理 =====
  {
    name: '📝 变量操作',
    color: 'bg-teal-500',
    modules: ['set_variable', 'json_parse', 'base64', 'random_number', 'get_time'] as ModuleType[],
  },
  {
    name: '✂️ 文本处理',
    color: 'bg-lime-600',
    modules: ['string_concat', 'string_replace', 'string_split', 'string_join', 'string_trim', 'string_case', 'string_substring', 'regex_extract'] as ModuleType[],
  },
  {
    name: '📋 列表/字典',
    color: 'bg-green-600',
    modules: ['list_operation', 'list_get', 'list_length', 'list_export', 'dict_operation', 'dict_get', 'dict_keys'] as ModuleType[],
  },
  {
    name: '📊 数据表格',
    color: 'bg-sky-500',
    modules: ['table_add_row', 'table_add_column', 'table_set_cell', 'table_get_cell', 'table_delete_row', 'table_clear', 'table_export', 'read_excel'] as ModuleType[],
  },
  {
    name: '🗄️ 数据库',
    color: 'bg-sky-600',
    modules: ['db_connect', 'db_query', 'db_execute', 'db_insert', 'db_update', 'db_delete', 'db_close'] as ModuleType[],
  },
  // ===== 流程控制 =====
  {
    name: '🔀 流程控制',
    color: 'bg-orange-500',
    modules: ['condition', 'loop', 'foreach', 'break_loop', 'continue_loop', 'scheduled_task', 'subflow', 'subflow_header'] as ModuleType[],
  },
  // ===== 触发器 =====
  {
    name: '⚡ 触发器',
    color: 'bg-yellow-500',
    modules: ['webhook_trigger', 'hotkey_trigger', 'file_watcher_trigger', 'email_trigger', 'api_trigger', 'mouse_trigger', 'image_trigger', 'sound_trigger', 'face_trigger', 'element_change_trigger'] as ModuleType[],
  },
  // ===== 文件与文档 =====
  {
    name: '📁 文件管理',
    color: 'bg-amber-600',
    modules: ['list_files', 'copy_file', 'move_file', 'delete_file', 'rename_file', 'create_folder', 'rename_folder', 'file_exists', 'get_file_info', 'read_text_file', 'write_text_file'] as ModuleType[],
  },
  {
    name: '📄 PDF处理',
    color: 'bg-red-600',
    modules: ['pdf_to_images', 'images_to_pdf', 'pdf_merge', 'pdf_split', 'pdf_extract_text', 'pdf_extract_images', 'pdf_encrypt', 'pdf_decrypt', 'pdf_add_watermark', 'pdf_rotate', 'pdf_delete_pages', 'pdf_get_info', 'pdf_compress', 'pdf_insert_pages', 'pdf_reorder_pages', 'pdf_to_word'] as ModuleType[],
  },
  {
    name: '📋 文档转换',
    color: 'bg-orange-600',
    modules: ['markdown_to_html', 'html_to_markdown', 'markdown_to_pdf', 'markdown_to_docx', 'docx_to_markdown', 'html_to_docx', 'docx_to_html', 'markdown_to_epub', 'epub_to_markdown', 'latex_to_pdf', 'rst_to_html', 'org_to_html', 'universal_doc_convert'] as ModuleType[],
  },
  // ===== 媒体处理 =====
  {
    name: '🔄 格式工厂',
    color: 'bg-rose-600',
    modules: ['image_format_convert', 'video_format_convert', 'audio_format_convert', 'video_to_audio', 'video_to_gif', 'batch_format_convert'] as ModuleType[],
  },
  {
    name: '🎬 视频编辑',
    color: 'bg-purple-600',
    modules: ['format_convert', 'compress_video', 'trim_video', 'merge_media', 'rotate_video', 'video_speed', 'extract_frame', 'add_subtitle', 'resize_video', 'download_m3u8'] as ModuleType[],
  },
  {
    name: '🎵 音频编辑',
    color: 'bg-violet-600',
    modules: ['extract_audio', 'adjust_volume', 'audio_to_text'] as ModuleType[],
  },
  {
    name: '🖼️ 图像编辑',
    color: 'bg-pink-600',
    modules: ['compress_image', 'image_resize', 'image_crop', 'image_rotate', 'image_flip', 'image_blur', 'image_sharpen', 'image_brightness', 'image_contrast', 'image_color_balance', 'image_add_text', 'image_merge', 'image_thumbnail', 'image_filter', 'image_grayscale', 'image_round_corners', 'image_remove_bg'] as ModuleType[],
  },
  {
    name: '🎨 图像工具',
    color: 'bg-fuchsia-600',
    modules: ['add_watermark', 'image_get_info', 'qr_generate', 'qr_decode'] as ModuleType[],
  },
  // ===== AI能力 =====
  {
    name: '🤖 AI对话',
    color: 'bg-violet-700',
    modules: ['ai_chat', 'ai_vision'] as ModuleType[],
  },
  {
    name: '🧠 AI爬虫',
    color: 'bg-purple-700',
    modules: ['ai_smart_scraper', 'ai_element_selector', 'firecrawl_scrape', 'firecrawl_map', 'firecrawl_crawl'] as ModuleType[],
  },
  {
    name: '🔍 AI识别',
    color: 'bg-fuchsia-700',
    modules: ['ocr_captcha', 'slider_captcha', 'face_recognition', 'image_ocr'] as ModuleType[],
  },
  // ===== 网络通信 =====
  {
    name: '🌐 网络请求',
    color: 'bg-sky-700',
    modules: ['api_request', 'send_email'] as ModuleType[],
  },
  {
    name: '💬 QQ机器人',
    color: 'bg-blue-500',
    modules: ['qq_send_message', 'qq_send_image', 'qq_send_file', 'qq_wait_message', 'qq_get_friends', 'qq_get_groups', 'qq_get_group_members', 'qq_get_login_info'] as ModuleType[],
  },
  {
    name: '💚 微信机器人',
    color: 'bg-green-500',
    modules: ['wechat_send_message', 'wechat_send_file'] as ModuleType[],
  },
  {
    name: '🔗 网络共享',
    color: 'bg-cyan-500',
    modules: ['share_folder', 'share_file', 'stop_share', 'start_screen_share', 'stop_screen_share'] as ModuleType[],
  },
  // ===== 实用工具 =====
  {
    name: '🔧 文件对比',
    color: 'bg-teal-800',
    modules: ['file_hash_compare', 'file_diff_compare', 'folder_hash_compare', 'folder_diff_compare'] as ModuleType[],
  },
  {
    name: '🔐 加密编码',
    color: 'bg-indigo-800',
    modules: ['md5_encrypt', 'sha_encrypt', 'url_encode_decode', 'random_password_generator'] as ModuleType[],
  },
  {
    name: '🎨 格式转换',
    color: 'bg-pink-800',
    modules: ['rgb_to_hsv', 'rgb_to_cmyk', 'hex_to_cmyk', 'timestamp_converter'] as ModuleType[],
  },
  {
    name: '🛠️ 其他工具',
    color: 'bg-gray-700',
    modules: ['uuid_generator', 'printer_call'] as ModuleType[],
  },
  // ===== 辅助功能 =====
  {
    name: '📢 消息通知',
    color: 'bg-amber-700',
    modules: ['print_log', 'play_sound', 'system_notification', 'text_to_speech', 'export_log'] as ModuleType[],
  },
  {
    name: '🎮 媒体播放',
    color: 'bg-rose-700',
    modules: ['play_music', 'play_video', 'view_image'] as ModuleType[],
  },
  {
    name: '💬 用户交互',
    color: 'bg-cyan-800',
    modules: ['input_prompt'] as ModuleType[],
  },
  {
    name: '🎯 脚本执行',
    color: 'bg-slate-700',
    modules: ['js_script', 'python_script'] as ModuleType[],
  },
  // ===== 画布工具 =====
  {
    name: '📝 画布工具',
    color: 'bg-stone-500',
    modules: ['group', 'note'] as ModuleType[],
  },
]

interface ModuleItemProps {
  type: ModuleType
  highlight?: string
  isFavorite?: boolean
  customColor?: string
  onToggleFavorite?: (type: ModuleType) => void
  onSetCustomColor?: (type: ModuleType, color: string | undefined) => void
  onIncrementUsage?: (type: ModuleType) => void  // 添加使用统计回调
  // 拖拽排序相关（仅在收藏模块视图中使用）
  enableSortDrag?: boolean
  onSortDragStart?: (type: ModuleType) => void
  onSortDragOver?: (type: ModuleType) => void
  onSortDrop?: (type: ModuleType) => void
  sortDragOverType?: ModuleType | null
  sortDraggingType?: ModuleType | null
}

function ModuleItem({ 
  type, 
  highlight, 
  isFavorite,
  customColor,
  onToggleFavorite,
  onSetCustomColor,
  onIncrementUsage,
  enableSortDrag,
  onSortDragStart,
  onSortDragOver,
  onSortDrop,
  sortDragOverType,
  sortDraggingType
}: ModuleItemProps) {
  const Icon = moduleIcons[type]
  const label = moduleTypeLabels[type]
  const [showColorPicker, setShowColorPicker] = useState(false)
  const [pickerPosition, setPickerPosition] = useState({ x: 0, y: 0 })
  const colorButtonRef = useRef<HTMLButtonElement>(null)

  // 预设颜色
  const presetColors = [
    { name: '默认', value: undefined },
    { name: '红色', value: '#ef4444' },
    { name: '橙色', value: '#f97316' },
    { name: '黄色', value: '#eab308' },
    { name: '绿色', value: '#22c55e' },
    { name: '青色', value: '#06b6d4' },
    { name: '蓝色', value: '#3b82f6' },
    { name: '紫色', value: '#a855f7' },
    { name: '粉色', value: '#ec4899' },
  ]

  // 点击外部关闭颜色选择器
  useEffect(() => {
    if (showColorPicker) {
      const handleClickOutside = (e: MouseEvent) => {
        const target = e.target as HTMLElement
        if (!target.closest('.color-picker-container')) {
          setShowColorPicker(false)
        }
      }
      setTimeout(() => document.addEventListener('click', handleClickOutside), 0)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [showColorPicker])

  // 模块主体的拖拽 - 始终用于添加到画布
  const onMainDragStart = (event: React.DragEvent) => {
    event.dataTransfer.setData('application/reactflow', type)
    event.dataTransfer.effectAllowed = 'move'
    // 增加使用统计
    onIncrementUsage?.(type)
  }

  // 排序手柄的拖拽
  const onHandleDragStart = (event: React.DragEvent) => {
    event.stopPropagation()
    event.dataTransfer.setData('application/sort-favorite', type)
    event.dataTransfer.effectAllowed = 'move'
    onSortDragStart?.(type)
  }

  const onDragOver = (event: React.DragEvent) => {
    if (enableSortDrag && onSortDragOver && event.dataTransfer.types.includes('application/sort-favorite')) {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
      onSortDragOver(type)
    }
  }

  const onDrop = (event: React.DragEvent) => {
    if (enableSortDrag && onSortDrop && event.dataTransfer.types.includes('application/sort-favorite')) {
      event.preventDefault()
      onSortDrop(type)
    }
  }

  // 高亮匹配的文字
  const highlightText = (text: string, query: string) => {
    if (!query) return text
    const lowerText = text.toLowerCase()
    const lowerQuery = query.toLowerCase()
    const index = lowerText.indexOf(lowerQuery)
    if (index === -1) return text
    return (
      <>
        {text.slice(0, index)}
        <span className="bg-yellow-200 rounded px-0.5">{text.slice(index, index + query.length)}</span>
        {text.slice(index + query.length)}
      </>
    )
  }

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    onToggleFavorite?.(type)
  }

  const handleColorClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    console.log('Color button clicked!', type, showColorPicker)
    
    // 计算弹窗位置
    if (colorButtonRef.current) {
      const rect = colorButtonRef.current.getBoundingClientRect()
      setPickerPosition({
        x: rect.right + 8, // 按钮右侧8px
        y: rect.top
      })
    }
    
    setShowColorPicker(!showColorPicker)
  }

  const handleColorSelect = (color: string | undefined) => {
    console.log('Color selected:', color, type)
    onSetCustomColor?.(type, color)
    setShowColorPicker(false)
  }

  const isDropTarget = sortDragOverType === type && sortDraggingType && sortDraggingType !== type
  const isDragging = sortDraggingType === type

  // 应用自定义颜色样式
  const customStyle = customColor ? {
    backgroundColor: `${customColor}15`,
    borderLeft: `3px solid ${customColor}`
  } : {}

  return (
    <div className="relative">
      <div
        style={customStyle}
        className={`flex items-center gap-2 rounded-md 
          hover:bg-gradient-to-r hover:from-blue-50 hover:to-cyan-50 
          transition-all duration-200 ease-out
          hover:translate-x-1 hover:shadow-sm
          group
          ${isDropTarget ? 'border-t-2 border-blue-500 bg-blue-50/50 translate-y-1' : ''}
          ${isDragging ? 'opacity-50 scale-95' : ''}`}
      >
        {/* 可拖拽区域 */}
        <div
          className="flex items-center gap-2 px-3 py-2 flex-1 cursor-grab active:scale-95 active:opacity-80"
          draggable
          onDragStart={onMainDragStart}
          onDragOver={onDragOver}
          onDrop={onDrop}
        >
          {/* 收藏模块视图中显示拖拽排序手柄 */}
          {enableSortDrag && (
            <div 
              className="p-1 rounded cursor-grab text-gray-300 hover:text-gray-600 hover:bg-gray-100 transition-all"
              draggable
              onDragStart={onHandleDragStart}
              title="拖拽此处调整顺序"
            >
              <GripHorizontal className="w-3.5 h-3.5" />
            </div>
          )}
          <div className="p-1 rounded transition-all duration-200 group-hover:bg-white/50 group-hover:scale-110">
            <Icon 
              className="w-4 h-4 text-muted-foreground transition-colors duration-200 group-hover:text-blue-600" 
              style={customColor ? { color: customColor } : {}}
            />
          </div>
          <span 
            className="text-sm transition-colors duration-200 group-hover:text-foreground flex-1"
            style={customColor ? { color: customColor } : {}}
          >
            {highlight ? highlightText(label, highlight) : label}
          </span>
        </div>
        
        {/* 按钮区域 - 不可拖拽 */}
        <div className="flex items-center gap-1 pr-2">
          {onSetCustomColor && (
            <button
              ref={colorButtonRef}
              onClick={handleColorClick}
              className="p-1 rounded transition-all duration-200 hover:scale-110 hover:bg-gray-100 opacity-0 group-hover:opacity-100 cursor-pointer"
              title="设置标签颜色"
            >
              <div 
                className="w-3.5 h-3.5 rounded-full border-2"
                style={{ 
                  backgroundColor: customColor || '#d1d5db',
                  borderColor: customColor ? customColor : '#d1d5db'
                }}
              />
            </button>
          )}
          {onToggleFavorite && (
            <button
              onClick={handleFavoriteClick}
              className={`p-1 rounded transition-all duration-200 opacity-0 group-hover:opacity-100 hover:scale-110 cursor-pointer ${
                isFavorite 
                  ? 'text-yellow-500 opacity-100' 
                  : 'text-gray-300 hover:text-yellow-400'
              }`}
              title={isFavorite ? '取消收藏' : '收藏模块'}
            >
              <Star className={`w-3.5 h-3.5 ${isFavorite ? 'fill-current' : ''}`} />
            </button>
          )}
        </div>
      </div>
      
      {/* 颜色选择器弹窗 - 使用 Portal 渲染到 body，避免被父容器裁剪 */}
      {showColorPicker && createPortal(
        <div 
          className="color-picker-container fixed z-[9999] bg-white rounded-lg shadow-xl border border-gray-200 p-3"
          style={{ left: `${pickerPosition.x}px`, top: `${pickerPosition.y}px` }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="text-xs font-medium text-gray-700 mb-2">选择标签颜色</div>
          <div className="grid grid-cols-3 gap-2">
            {presetColors.map((color) => (
              <button
                key={color.name}
                onClick={() => handleColorSelect(color.value)}
                className="flex flex-col items-center gap-1 p-2 rounded hover:bg-gray-50 transition-colors"
                title={color.name}
              >
                <div 
                  className="w-6 h-6 rounded-full border-2 border-gray-300"
                  style={{ backgroundColor: color.value || '#d1d5db' }}
                />
                <span className="text-[10px] text-gray-600">{color.name}</span>
              </button>
            ))}
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}

export function ModuleSidebar() {
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set())
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false)

  // 导入模块统计 store（包含收藏管理）
  const { getSortedModules, incrementUsage, toggleFavorite, stats } = useModuleStatsStore()

  // 在组件挂载时获取一次排序结果并缓存（只在浏览器刷新时排序）
  const [sortedCategoriesCache] = useState(() => {
    return moduleCategories.map(category => ({
      ...category,
      modules: getSortedModules(category.modules)
    }))
  })

  // 从 store 中获取所有收藏的模块
  const favoriteModules = useMemo(() => {
    return Object.entries(stats)
      .filter(([_, stat]) => stat.isFavorite)
      .map(([type, _]) => type as ModuleType)
  }, [stats])

  // 切换分类展开/收起
  const toggleCategory = (categoryName: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev)
      if (next.has(categoryName)) {
        next.delete(categoryName)
      } else {
        next.add(categoryName)
      }
      return next
    })
  }

  // 模糊搜索过滤（支持拼音和首字母）+ 使用缓存的排序结果
  const filteredCategories = useMemo(() => {
    // 使用缓存的排序结果，而不是每次都重新排序
    let categories = sortedCategoriesCache

    // 如果只显示收藏
    if (showFavoritesOnly) {
      // 收藏模块按照缓存中的顺序排列
      const sortedFavorites = favoriteModules.sort((a, b) => {
        // 在缓存中查找模块的位置
        let indexA = -1
        let indexB = -1
        for (const cat of sortedCategoriesCache) {
          const idxA = cat.modules.indexOf(a)
          const idxB = cat.modules.indexOf(b)
          if (idxA !== -1) indexA = idxA
          if (idxB !== -1) indexB = idxB
        }
        return indexA - indexB
      })
      
      return [{
        name: '⭐ 收藏模块',
        color: 'bg-yellow-500',
        modules: sortedFavorites
      }].filter(cat => cat.modules.length > 0)
    }

    if (!searchQuery.trim()) {
      // 没有搜索时，直接使用缓存的排序结果
      return categories
    }

    const query = searchQuery.trim()
    
    return categories.map(category => ({
      ...category,
      modules: category.modules.filter(type => {
        const label = moduleTypeLabels[type]
        const keywords = moduleKeywords[type] || []
        
        // 使用拼音匹配标签名
        if (pinyinMatch(label, query)) return true
        
        // 匹配关键词（也支持拼音）
        if (keywords.some(kw => pinyinMatch(kw, query))) return true
        
        // 匹配模块类型（英文）
        if (type.toLowerCase().includes(query.toLowerCase())) return true
        
        return false
      })
    })).filter(category => category.modules.length > 0)
  }, [searchQuery, showFavoritesOnly, favoriteModules, sortedCategoriesCache])

  // 搜索结果模块数
  const filteredModulesCount = filteredCategories.reduce((sum, cat) => sum + cat.modules.length, 0)
  
  // 总模块数
  const totalModulesCount = useMemo(() => {
    return moduleCategories.reduce((sum, cat) => sum + cat.modules.length, 0)
  }, [])

  // 搜索时自动展开所有分类
  const isExpanded = (categoryName: string) => {
    if (searchQuery.trim() || showFavoritesOnly) return true
    return expandedCategories.has(categoryName)
  }

  return (
    <aside className={`border-r bg-gradient-to-b from-white to-blue-50/30 flex flex-col animate-slide-in-left transition-all duration-300 group/sidebar ${isCollapsed ? 'w-12' : 'w-64'}`}>
      {/* 收起状态下的图标列表 */}
      {isCollapsed ? (
        <div 
          className="flex flex-col items-center py-4 gap-3 cursor-pointer hover:bg-blue-50/50 transition-colors h-full"
          onClick={() => setIsCollapsed(false)}
          title="点击展开模块列表"
        >
          <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-md">
            <ChevronRight className="w-4 h-4" />
          </div>
          <div className="w-px h-4 bg-gray-200" />
          {moduleCategories.slice(0, 8).map((category) => (
            <div
              key={category.name}
              className={`w-2.5 h-2.5 rounded-full ${category.color} hover:scale-125 transition-transform`}
              title={category.name}
            />
          ))}
          {moduleCategories.length > 8 && (
            <span className="text-[10px] text-muted-foreground">+{moduleCategories.length - 8}</span>
          )}
        </div>
      ) : (
        <>
          <div className="p-4 border-b bg-gradient-to-r from-blue-50/50 to-cyan-50/50 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-medium text-gradient">模块列表</h2>
                  <span className="text-xs text-muted-foreground bg-muted/50 px-1.5 py-0.5 rounded-full">
                    共 {totalModulesCount} 个
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">拖拽模块到画布添加</p>
              </div>
              <button
                onClick={() => setIsCollapsed(true)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all duration-200"
                title="收起"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative group flex-1">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground transition-colors group-focus-within:text-blue-500" />
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="搜索模块..."
                  className="pl-8 h-8 text-sm transition-all duration-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white/80"
                />
                {searchQuery && (
                  <button
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-all duration-200 hover:scale-110"
                    onClick={() => setSearchQuery('')}
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
              {/* 收藏筛选按钮 */}
              <button
                onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
                className={`flex items-center justify-center h-8 w-8 rounded-md transition-all duration-200 ${
                  showFavoritesOnly
                    ? 'bg-yellow-100 text-yellow-600 border border-yellow-300'
                    : 'bg-gray-100 text-gray-500 hover:bg-yellow-50 hover:text-yellow-500'
                }`}
                title={showFavoritesOnly ? `收藏 (${favoriteModules.length}) - 点击显示全部` : `收藏 (${favoriteModules.length})`}
              >
                <Star className={`w-4 h-4 ${showFavoritesOnly ? 'fill-current' : ''}`} />
              </button>
            </div>
            {searchQuery && (
              <p className="text-xs text-muted-foreground animate-fade-in">
                找到 <span className="text-gradient font-semibold">{filteredModulesCount}</span> 个模块
              </p>
            )}
          </div>
          
          <ScrollArea className="flex-1 p-2">
            {filteredCategories.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-muted-foreground animate-fade-in">
                <Search className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm">未找到模块</p>
                <p className="text-xs mt-1">试试其他关键词</p>
              </div>
            ) : (
              filteredCategories.map((category, categoryIndex) => {
                const expanded = isExpanded(category.name)
                return (
                  <div 
                    key={category.name} 
                    className="mb-2 animate-fade-in-up"
                    style={{ animationDelay: `${categoryIndex * 30}ms` }}
                  >
                    <button
                      className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md 
                        hover:bg-gradient-to-r hover:from-transparent hover:to-blue-50/50 
                        transition-all duration-200 group"
                      onClick={() => toggleCategory(category.name)}
                    >
                      <div className={`transition-transform duration-200 ${expanded ? 'rotate-0' : '-rotate-90'}`}>
                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                      </div>
                      <div className={`w-2 h-2 rounded-full ${category.color} transition-transform duration-200 group-hover:scale-125`} />
                      <span className="text-xs font-medium flex-1 text-left transition-colors group-hover:text-foreground">
                        {category.name}
                      </span>
                      <span className="text-xs text-muted-foreground bg-muted/50 px-1.5 py-0.5 rounded-full transition-colors group-hover:bg-blue-100 group-hover:text-blue-700">
                        {category.modules.length}
                      </span>
                    </button>
                    <div className={`overflow-hidden transition-all duration-300 ease-out ${expanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'}`}>
                      <div className="ml-4 space-y-0.5 mt-1">
                        {category.modules.map((type, index) => {
                          return (
                            <div 
                              key={type} 
                              className="animate-fade-in"
                              style={{ animationDelay: `${index * 20}ms` }}
                            >
                              <ModuleItem 
                                type={type} 
                                highlight={searchQuery}
                                isFavorite={favoriteModules.includes(type)}
                                customColor={stats[type]?.customColor}
                                onToggleFavorite={toggleFavorite}
                                onSetCustomColor={(type, color) => {
                                  const { setCustomColor } = useModuleStatsStore.getState()
                                  setCustomColor(type, color)
                                }}
                                onIncrementUsage={incrementUsage}
                                // 禁用手动排序，使用智能排序
                                enableSortDrag={false}
                                onSortDragStart={undefined}
                                onSortDragOver={undefined}
                                onSortDrop={undefined}
                                sortDragOverType={null}
                                sortDraggingType={null}
                              />
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </ScrollArea>
        </>
      )}
    </aside>
  )
}

// 导出模块分类数据供其他组件使用
export { moduleCategories }

// 导出模块图标映射
export { moduleIcons }

// 获取所有可用模块的扁平列表
export function getAllAvailableModules() {
  return moduleCategories.flatMap(category => 
    category.modules.map(type => ({
      type,
      label: moduleTypeLabels[type] || type,
      category: category.name,
      icon: moduleIcons[type] || Globe
    }))
  )
}
