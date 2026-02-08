import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { cn } from '@/lib/utils'
import type { NodeData } from '@/store/workflowStore'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import {
  Globe,
  MousePointer,
  Type,
  Search,
  Clock,
  Hourglass,
  X,
  ChevronDown,
  CheckSquare,
  Move,
  ArrowDown,
  Upload,
  Download,
  Image,
  Eye,
  SlidersHorizontal,
  GitBranch,
  Repeat,
  List,
  LogOut,
  SkipForward,
  Variable,
  MessageSquare,
  Mail,
  Volume2,
  Bell,
  FormInput,
  Brain,
  Send,
  FileJson,
  Dices,
  Calendar,
  Camera,
  ListPlus,
  ListMinus,
  Hash,
  BookOpen,
  Key,
  Braces,
  FileSpreadsheet,
  ScanEye,
  RefreshCw,
  ArrowLeft,
  ArrowRight,
  MessageCircle,
  Music,
  Speech,
  Code,
  Clipboard,
  Keyboard,
  RowsIcon,
  Columns,
  Grid3X3,
  TableProperties,
  Trash2,
  FileDown,
  Square,
  StickyNote,
  Workflow,
  Radio,
  FileVideo,
  ImageDown,
  Film,
  Video,
  AudioLines,
  Scissors,
  Merge,
  Droplets,
  UserCheck,
  ScanLine,
  FolderOpen,
  Copy,
  FolderPlus,
  FileCheck,
  FileSearch,
  FileInput,
  FileOutput,
  RotateCw,
  Gauge,
  ImagePlus,
  Subtitles,
  Volume,
  Maximize2,
  Users,
  User,
  MessageSquareMore,
  Share2,
  StopCircle,
  ScreenShare,
  ScreenShareOff,
  FileUp,
  FileText,
  ImageMinus,
  Monitor,
  Database,
  DatabaseZap,
  CirclePlus,
  Pencil,
  CircleMinus,
  Unplug,
  Power,
  Lock,
  Terminal,
  Crosshair,
  Files,
  FileX,
  FilePen,
  FileType,
  Split,
  FileKey,
  FileLock2,
  Info,
  Minimize2,
  ArrowUpDown,
  ScrollText,
  GripHorizontal,
  ListTree,
  Target,
  Webhook,
  FolderSearch,
  MousePointer2,
  Frame,
  ArrowUpFromLine,
  Sun,
  Palette,
  Zap,
  Sparkles,
  Eraser,
  FlipHorizontal,
  Combine,
} from 'lucide-react'
import type { ModuleType } from '@/types'

// 模块图标映射
const moduleIcons: Record<ModuleType, React.ElementType> = {
  // 浏览器操作
  open_page: Globe,
  click_element: MousePointer,
  hover_element: MousePointer,
  input_text: Type,
  get_element_info: Search,
  wait: Clock,
  wait_element: Hourglass,
  wait_image: Eye,
  close_page: X,
  refresh_page: RefreshCw,
  go_back: ArrowLeft,
  go_forward: ArrowRight,
  handle_dialog: MessageCircle,
  inject_javascript: Code,
  // 表单操作
  select_dropdown: ChevronDown,
  set_checkbox: CheckSquare,
  drag_element: Move,
  scroll_page: ArrowDown,
  upload_file: Upload,
  // 数据处理
  set_variable: Variable,
  json_parse: FileJson,
  base64: Code,
  random_number: Dices,
  get_time: Calendar,
  download_file: Download,
  save_image: Image,
  screenshot: Camera,
  read_excel: FileSpreadsheet,
  // 字符串操作
  regex_extract: Search,
  string_replace: Type,
  string_split: List,
  string_join: ListPlus,
  string_concat: ListPlus,
  string_trim: Type,
  string_case: Type,
  string_substring: Type,
  // 列表操作
  list_operation: ListPlus,
  list_get: ListMinus,
  list_length: Hash,
  list_export: FileDown,
  // 字典操作
  dict_operation: Braces,
  dict_get: BookOpen,
  dict_keys: Key,
  // 数据表格操作
  table_add_row: RowsIcon,
  table_add_column: Columns,
  table_set_cell: Grid3X3,
  table_get_cell: TableProperties,
  table_delete_row: Trash2,
  table_clear: X,
  table_export: FileDown,
  // 数据库操作
  db_connect: Database,
  db_query: DatabaseZap,
  db_execute: Terminal,
  db_insert: CirclePlus,
  db_update: Pencil,
  db_delete: CircleMinus,
  db_close: Unplug,
  // 网络请求
  api_request: Send,
  send_email: Mail,
  // QQ自动化
  qq_send_message: MessageSquare,
  qq_send_image: Image,
  qq_send_file: FileUp,
  qq_wait_message: MessageSquareMore,
  qq_get_friends: Users,
  qq_get_groups: Users,
  qq_get_group_members: Users,
  qq_get_login_info: User,
  // 微信自动化
  wechat_send_message: MessageSquare,
  wechat_send_file: FileUp,
  // AI能力
  ai_chat: Brain,
  ai_vision: ScanEye,
  // 验证码
  ocr_captcha: Eye,
  slider_captcha: SlidersHorizontal,
  // 流程控制
  condition: GitBranch,
  loop: Repeat,
  foreach: List,
  break_loop: LogOut,
  continue_loop: SkipForward,
  scheduled_task: Clock,
  subflow: Workflow,
  // 辅助工具
  print_log: MessageSquare,
  play_sound: Volume2,
  system_notification: Bell,
  play_music: Music,
  play_video: Film,
  view_image: Image,
  input_prompt: FormInput,
  text_to_speech: Speech,
  js_script: Code,
  set_clipboard: Clipboard,
  get_clipboard: Clipboard,
  keyboard_action: Keyboard,
  real_mouse_scroll: MousePointer,
  // 系统操作
  shutdown_system: Power,
  lock_screen: Lock,
  window_focus: Maximize2,
  real_mouse_click: MousePointer,
  real_mouse_move: Move,
  real_mouse_drag: Move,
  real_keyboard: Keyboard,
  run_command: Terminal,
  click_image: Image,
  get_mouse_position: Crosshair,
  screenshot_screen: Camera,
  rename_file: FilePen,
  network_capture: Radio,
  // 文件操作
  list_files: Files,
  copy_file: Copy,
  move_file: Move,
  delete_file: FileX,
  create_folder: FolderPlus,
  file_exists: FileCheck,
  get_file_info: FileSearch,
  read_text_file: FileInput,
  write_text_file: FileOutput,
  rename_folder: FolderOpen,
  // 宏录制器
  macro_recorder: Film,
  // 媒体处理（FFmpeg）
  format_convert: FileVideo,
  compress_image: ImageDown,
  compress_video: Film,
  extract_audio: AudioLines,
  trim_video: Scissors,
  merge_media: Merge,
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
  images_to_pdf: FileText,
  pdf_merge: Merge,
  pdf_split: Split,
  pdf_extract_text: FileType,
  pdf_extract_images: ImagePlus,
  pdf_encrypt: FileKey,
  pdf_decrypt: FileLock2,
  pdf_add_watermark: Droplets,
  pdf_rotate: RotateCw,
  pdf_delete_pages: FileX,
  pdf_get_info: Info,
  pdf_compress: Minimize2,
  pdf_insert_pages: FilePen,
  pdf_reorder_pages: ArrowUpDown,
  pdf_to_word: FileText,
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
  click_text: Type,
  hover_image: Image,
  hover_text: Type,
  drag_image: GripHorizontal,
  // 元素操作
  get_child_elements: ListTree,
  get_sibling_elements: ListTree,
  // AI能力扩展
  ai_smart_scraper: Brain,
  ai_element_selector: Target,
  firecrawl_scrape: Webhook,
  firecrawl_map: FolderSearch,
  firecrawl_crawl: MousePointer2,
  // iframe操作
  switch_iframe: Frame,
  switch_to_main: ArrowUpFromLine,
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
  // 图像处理
  image_grayscale: ImageMinus,
  image_round_corners: Image,
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
  audio_to_text: Speech,
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
  // 分组/备注
  group: Square,
  subflow_header: Workflow,
  note: StickyNote,
}

// 模块颜色映射 - 使用不透明背景
const moduleColors: Record<string, string> = {
  // 浏览器操作 - 蓝色
  open_page: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  click_element: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  hover_element: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  input_text: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  get_element_info: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  wait: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  wait_element: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  wait_image: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  close_page: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  refresh_page: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  go_back: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  go_forward: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  handle_dialog: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  inject_javascript: 'border-purple-500 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',
  // iframe操作 - 蓝色
  switch_iframe: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  switch_to_main: 'border-blue-500 bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
  // 表单操作 - 靛蓝色
  select_dropdown: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',
  set_checkbox: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',
  drag_element: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',
  scroll_page: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',
  upload_file: 'border-indigo-500 bg-indigo-100 dark:bg-indigo-900 text-indigo-900 dark:text-indigo-100',
  // 数据处理 - 青色
  set_variable: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  json_parse: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  base64: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  random_number: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  get_time: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  download_file: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  save_image: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  screenshot: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  read_excel: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  // 列表操作 - 青绿色
  list_operation: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',
  list_get: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',
  list_length: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',
  list_export: 'border-teal-500 bg-teal-100 dark:bg-teal-900 text-teal-900 dark:text-teal-100',
  // 字典操作 - 琥珀色
  dict_operation: 'border-amber-500 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',
  dict_get: 'border-amber-500 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',
  dict_keys: 'border-amber-500 bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-100',
  // 字符串操作 - 青色
  regex_extract: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  string_replace: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  string_split: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  string_join: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  string_concat: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  string_trim: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  string_case: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  string_substring: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  // 数据表格操作 - 粉红色
  table_add_row: 'border-pink-500 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',
  table_add_column: 'border-pink-500 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',
  table_set_cell: 'border-pink-500 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',
  table_get_cell: 'border-pink-500 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',
  table_delete_row: 'border-pink-500 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',
  table_clear: 'border-pink-500 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',
  table_export: 'border-pink-500 bg-pink-100 dark:bg-pink-900 text-pink-900 dark:text-pink-100',
  // 数据库操作 - 天蓝色
  db_connect: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  db_query: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  db_execute: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  db_insert: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  db_update: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  db_delete: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  db_close: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  // 网络请求 - 紫色
  api_request: 'border-purple-500 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',
  send_email: 'border-purple-500 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',
  // AI能力 - 紫罗兰色
  ai_chat: 'border-violet-500 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',
  ai_vision: 'border-violet-500 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',
  // 验证码模块 - 橙色
  ocr_captcha: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',
  slider_captcha: 'border-orange-500 bg-orange-100 dark:bg-orange-900 text-orange-900 dark:text-orange-100',
  // 流程控制模块 - 绿色
  condition: 'border-green-500 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',
  loop: 'border-green-500 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',
  foreach: 'border-green-500 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',
  break_loop: 'border-green-500 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',
  continue_loop: 'border-green-500 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',
  scheduled_task: 'border-green-500 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',
  subflow: 'border-emerald-500 bg-emerald-100 dark:bg-emerald-900 text-emerald-900 dark:text-emerald-100',
  // 辅助工具 - 灰色
  print_log: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  play_sound: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  system_notification: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  play_music: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  input_prompt: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  text_to_speech: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  js_script: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  set_clipboard: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  get_clipboard: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  keyboard_action: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  real_mouse_scroll: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  shutdown_system: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  lock_screen: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  window_focus: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  real_mouse_click: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  real_mouse_move: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  real_mouse_drag: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  real_keyboard: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  run_command: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  click_image: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  get_mouse_position: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  screenshot_screen: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  rename_file: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  network_capture: 'border-purple-500 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',
  macro_recorder: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  // 网络共享 - 青色
  share_folder: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  share_file: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  stop_share: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  // 屏幕共享 - 青色
  start_screen_share: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  stop_screen_share: 'border-cyan-500 bg-cyan-100 dark:bg-cyan-900 text-cyan-900 dark:text-cyan-100',
  // 媒体处理 - 玫红色
  format_convert: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  compress_image: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  compress_video: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  extract_audio: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  trim_video: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  merge_media: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  add_watermark: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  // AI识别 - 紫罗兰色
  face_recognition: 'border-violet-500 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',
  image_ocr: 'border-violet-500 bg-violet-100 dark:bg-violet-900 text-violet-900 dark:text-violet-100',
  // QQ自动化 - 天蓝色
  qq_send_message: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  qq_send_image: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  qq_send_file: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  qq_wait_message: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  qq_get_friends: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  qq_get_groups: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  qq_get_group_members: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  qq_get_login_info: 'border-sky-500 bg-sky-100 dark:bg-sky-900 text-sky-900 dark:text-sky-100',
  // 微信自动化 - 绿色
  wechat_send_message: 'border-green-500 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',
  wechat_send_file: 'border-green-500 bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',
  // 文件操作 - 石板色
  list_files: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  copy_file: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  move_file: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  delete_file: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  create_folder: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  file_exists: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  get_file_info: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  read_text_file: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  write_text_file: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  rename_folder: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  // PDF处理 - 红色
  pdf_to_images: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  images_to_pdf: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_merge: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_split: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_extract_text: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_extract_images: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_encrypt: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_decrypt: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_add_watermark: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_rotate: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_delete_pages: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_get_info: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_compress: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_insert_pages: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_reorder_pages: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  pdf_to_word: 'border-red-500 bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  // 其他模块
  export_log: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  click_text: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  hover_image: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  hover_text: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  drag_image: 'border-slate-500 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100',
  // 图像处理 - 玫红色
  image_grayscale: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  image_round_corners: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  // 音频处理 - 玫红色
  audio_to_text: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  // 二维码 - 紫色
  qr_generate: 'border-purple-500 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',
  qr_decode: 'border-purple-500 bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',
  // 录屏 - 玫红色
  screen_record: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  camera_capture: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  camera_record: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  // 更多媒体处理
  download_m3u8: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  rotate_video: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  video_speed: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  extract_frame: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  add_subtitle: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  adjust_volume: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  resize_video: 'border-rose-500 bg-rose-100 dark:bg-rose-900 text-rose-900 dark:text-rose-100',
  // 播放视频/图片
  play_video: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  view_image: 'border-gray-500 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
  // 分组/备注
  group: 'border-gray-400 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300',
  subflow_header: 'border-emerald-500 bg-emerald-100 dark:bg-emerald-900 text-emerald-900 dark:text-emerald-100',
  note: 'border-yellow-500 bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',
}

function ModuleNodeComponent({ data, selected }: NodeProps) {
  const nodeData = data as NodeData
  // 移除执行动画以提升性能
  const isDisabled = nodeData.disabled === true
  const isHighlighted = nodeData.isHighlighted === true
  
  // 获取全局配置的连接点尺寸
  const handleSize = useGlobalConfigStore((state) => state.config.display?.handleSize || 12)
  
  const Icon = moduleIcons[nodeData.moduleType] || Globe
  const colorClass = moduleColors[nodeData.moduleType] || 'border-gray-500 bg-gray-50'
  
  // 获取配置摘要
  const getSummary = () => {
    if (nodeData.url) return nodeData.url as string
    if (nodeData.selector) return nodeData.selector as string
    if (nodeData.text) return nodeData.text as string
    if (nodeData.logMessage) return nodeData.logMessage as string
    if (nodeData.variableName) return `→ ${nodeData.variableName}`
    if (nodeData.userPrompt) return nodeData.userPrompt as string
    if (nodeData.requestUrl) return nodeData.requestUrl as string
    return ''
  }
  
  // 截断文本
  const truncateText = (text: string, maxLen: number) => {
    if (text.length <= maxLen) return text
    return text.slice(0, maxLen) + '...'
  }
  
  const summary = truncateText(getSummary(), 30)
  const customName = nodeData.name as string | undefined

  return (
    <div
      className={cn(
        'relative px-4 py-3 rounded-lg border-2 shadow-sm min-w-[180px] max-w-[280px] transition-all duration-200 hover:shadow-lg',
        isDisabled ? 'border-gray-300 bg-gray-100 dark:bg-gray-800 opacity-50' : colorClass,
        selected && 'ring-2 ring-primary ring-offset-2 shadow-lg scale-[1.02]',
        isHighlighted && 'ring-4 ring-amber-500 ring-offset-2 shadow-2xl scale-105 animate-pulse border-amber-500'
      )}
    >
      {/* 禁用标记 */}
      {isDisabled && (
        <div className="absolute -top-2 -right-2 bg-gray-500 text-white text-[10px] px-1.5 py-0.5 rounded-full animate-pulse">
          已禁用
        </div>
      )}
      
      {/* 输入连接点 */}
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-gray-400 !border-2 !border-white"
        style={{ width: `${handleSize}px`, height: `${handleSize}px` }}
      />
      
      {/* 节点内容 */}
      <div className="flex items-center gap-2">
        <Icon className="w-5 h-5" />
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm truncate">
            {nodeData.label}
            {customName && (
              <span className="text-amber-600 dark:text-amber-400 font-normal ml-1">
                ({customName})
              </span>
            )}
          </div>
          {summary && (
            <div className="text-xs opacity-75 truncate mt-0.5">
              {summary}
            </div>
          )}
        </div>
      </div>
      
      {/* 输出连接点 */}
      {nodeData.moduleType === 'condition' || nodeData.moduleType === 'face_recognition' ? (
        // 条件判断/人脸识别：绿色=true/匹配，红色=false/不匹配，右侧=异常
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="true"
            className="!bg-green-500 !border-2 !border-white"
            style={{ left: '30%', width: `${handleSize}px`, height: `${handleSize}px` }}
          />
          <div className="absolute -bottom-5 text-[10px] text-green-600 font-medium" style={{ left: '30%', transform: 'translateX(-50%)' }}>
            {nodeData.moduleType === 'face_recognition' ? '匹配' : '是'}
          </div>
          <Handle
            type="source"
            position={Position.Bottom}
            id="false"
            className="!bg-red-500 !border-2 !border-white"
            style={{ left: '70%', width: `${handleSize}px`, height: `${handleSize}px` }}
          />
          <div className="absolute -bottom-5 text-[10px] text-red-600 font-medium" style={{ left: '70%', transform: 'translateX(-50%)' }}>
            {nodeData.moduleType === 'face_recognition' ? '不匹配' : '否'}
          </div>
          {/* 异常处理连接点 */}
          <Handle
            type="source"
            position={Position.Right}
            id="error"
            className="!bg-orange-500 !border-2 !border-white"
            style={{ top: '50%', width: `${handleSize * 0.83}px`, height: `${handleSize * 0.83}px` }}
          />
        </>
      ) : nodeData.moduleType === 'loop' || nodeData.moduleType === 'foreach' ? (
        // 循环模块：绿色=循环体，红色=循环结束后，右侧=异常
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="loop"
            className="!bg-green-500 !border-2 !border-white"
            style={{ left: '30%', width: `${handleSize}px`, height: `${handleSize}px` }}
          />
          <div className="absolute -bottom-5 text-[10px] text-green-600 font-medium" style={{ left: '30%', transform: 'translateX(-50%)' }}>循环</div>
          <Handle
            type="source"
            position={Position.Bottom}
            id="done"
            className="!bg-red-500 !border-2 !border-white"
            style={{ left: '70%', width: `${handleSize}px`, height: `${handleSize}px` }}
          />
          <div className="absolute -bottom-5 text-[10px] text-red-600 font-medium" style={{ left: '70%', transform: 'translateX(-50%)' }}>完成</div>
          {/* 异常处理连接点 */}
          <Handle
            type="source"
            position={Position.Right}
            id="error"
            className="!bg-orange-500 !border-2 !border-white"
            style={{ top: '50%', width: `${handleSize * 0.83}px`, height: `${handleSize * 0.83}px` }}
          />
        </>
      ) : (
        // 普通模块：底部=正常流程，右侧=异常处理
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            className="!bg-gray-400 !border-2 !border-white"
            style={{ width: `${handleSize}px`, height: `${handleSize}px` }}
          />
          {/* 异常处理连接点 */}
          <Handle
            type="source"
            position={Position.Right}
            id="error"
            className="!bg-orange-500 !border-2 !border-white"
            style={{ top: '50%', width: `${handleSize * 0.83}px`, height: `${handleSize * 0.83}px` }}
          />
        </>
      )}
    </div>
  )
}

export const ModuleNode = memo(ModuleNodeComponent)
