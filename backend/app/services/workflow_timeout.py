"""工作流模块超时配置

根据模块实际使用场景设置合理的默认超时时间（毫秒）
超时为0表示不限制超时（非阻塞或需要用户交互的模块）
"""

# 模块默认超时时间配置（毫秒）
MODULE_DEFAULT_TIMEOUTS = {
    # 浏览器操作 - 网页加载可能较慢
    'open_page': 60000,        # 60秒
    'click_element': 30000,    # 30秒
    'hover_element': 30000,    # 30秒
    'input_text': 30000,       # 30秒
    'get_element_info': 30000, # 30秒
    'wait': 0,                 # 固定等待不需要超时（由模块内部控制）
    'wait_element': 60000,     # 60秒
    'close_page': 10000,       # 10秒
    'refresh_page': 60000,     # 60秒
    'go_back': 30000,          # 30秒
    'go_forward': 30000,       # 30秒
    'handle_dialog': 30000,    # 30秒
    # 表单操作
    'select_dropdown': 30000,  # 30秒
    'set_checkbox': 30000,     # 30秒
    'drag_element': 30000,     # 30秒
    'scroll_page': 30000,      # 30秒
    'upload_file': 120000,     # 2分钟
    # 数据处理 - 通常很快
    'set_variable': 5000,      # 5秒
    'json_parse': 5000,        # 5秒
    'base64': 10000,           # 10秒
    'random_number': 5000,     # 5秒
    'get_time': 5000,          # 5秒
    'download_file': 300000,   # 5分钟
    'save_image': 60000,       # 1分钟
    'screenshot': 30000,       # 30秒
    'read_excel': 60000,       # 1分钟
    # 字符串操作 - 很快
    'regex_extract': 10000,    # 10秒
    'string_replace': 5000,    # 5秒
    'string_split': 5000,      # 5秒
    'string_join': 5000,       # 5秒
    'string_concat': 5000,     # 5秒
    'string_trim': 5000,       # 5秒
    'string_case': 5000,       # 5秒
    'string_substring': 5000,  # 5秒
    # 列表/字典操作 - 很快
    'list_operation': 10000,   # 10秒
    'list_get': 5000,          # 5秒
    'list_length': 5000,       # 5秒
    'list_export': 60000,      # 1分钟（导出可能较慢）
    'dict_operation': 10000,   # 10秒
    'dict_get': 5000,          # 5秒
    'dict_keys': 5000,         # 5秒
    # 数据表格操作
    'table_add_row': 5000,     # 5秒
    'table_add_column': 5000,  # 5秒
    'table_set_cell': 5000,    # 5秒
    'table_get_cell': 5000,    # 5秒
    'table_delete_row': 5000,  # 5秒
    'table_clear': 5000,       # 5秒
    'table_export': 60000,     # 1分钟
    # 数据库操作
    'db_connect': 30000,       # 30秒
    'db_query': 120000,        # 2分钟
    'db_execute': 120000,      # 2分钟
    'db_insert': 60000,        # 1分钟
    'db_update': 60000,        # 1分钟
    'db_delete': 60000,        # 1分钟
    'db_close': 10000,         # 10秒
    # 网络请求
    'api_request': 120000,     # 2分钟
    'send_email': 60000,       # 1分钟
    # AI能力 - 需要较长时间
    'ai_chat': 180000,         # 3分钟
    'ai_vision': 180000,       # 3分钟
    # 验证码
    'ocr_captcha': 60000,      # 1分钟
    'slider_captcha': 60000,   # 1分钟
    # 流程控制 - 不超时（由内部逻辑控制）
    'condition': 5000,         # 5秒
    'loop': 0,                 # 循环本身不超时
    'foreach': 0,              # 遍历本身不超时
    'break_loop': 5000,        # 5秒
    'continue_loop': 5000,     # 5秒
    'scheduled_task': 0,       # 定时任务不超时
    'subflow': 0,              # 子流程不超时
    # 辅助工具
    'print_log': 5000,         # 5秒
    'play_sound': 10000,       # 10秒
    'system_notification': 5000, # 5秒
    'play_music': 0,           # 不超时（阻塞型，等待用户关闭）
    'play_video': 0,           # 不超时（阻塞型，等待用户关闭）
    'view_image': 0,           # 不超时（阻塞型，等待用户关闭）
    'input_prompt': 0,         # 不超时（阻塞型，等待用户输入）
    'text_to_speech': 120000,  # 2分钟
    'js_script': 60000,        # 1分钟
    'set_clipboard': 5000,     # 5秒
    'get_clipboard': 5000,     # 5秒
    'keyboard_action': 10000,  # 10秒
    'real_mouse_scroll': 10000,# 10秒
    # 系统操作
    'shutdown_system': 30000,  # 30秒
    'lock_screen': 10000,      # 10秒
    'window_focus': 10000,     # 10秒
    'real_mouse_click': 10000, # 10秒
    'real_mouse_move': 10000,  # 10秒
    'real_mouse_drag': 10000,  # 10秒
    'real_keyboard': 30000,    # 30秒
    'run_command': 300000,     # 5分钟
    'click_image': 60000,      # 1分钟
    'click_text': 120000,      # 2分钟（OCR识别较慢，首次需要下载模型）
    'hover_image': 60000,      # 1分钟
    'hover_text': 120000,      # 2分钟（OCR识别较慢）
    'drag_image': 60000,       # 1分钟
    'get_mouse_position': 5000,# 5秒
    'screenshot_screen': 10000,# 10秒
    'rename_file': 10000,      # 10秒
    'network_capture': 0,      # 不超时（非阻塞，后台运行）
    'macro_recorder': 0,       # 不超时（宏播放时间由用户录制内容决定）
    # 网络共享 - 非阻塞（启动服务后立即返回）
    'share_folder': 10000,     # 10秒（启动服务）
    'share_file': 10000,       # 10秒（启动服务）
    'stop_share': 5000,        # 5秒
    # 屏幕共享 - 非阻塞（启动服务后立即返回）
    'start_screen_share': 10000,  # 10秒（启动服务）
    'stop_screen_share': 5000,    # 5秒
    # 文件操作
    'list_files': 30000,       # 30秒
    'copy_file': 300000,       # 5分钟
    'move_file': 300000,       # 5分钟
    'delete_file': 30000,      # 30秒
    'create_folder': 10000,    # 10秒
    'file_exists': 5000,       # 5秒
    'get_file_info': 10000,    # 10秒
    'read_text_file': 60000,   # 1分钟
    'write_text_file': 60000,  # 1分钟
    'rename_folder': 10000,    # 10秒
    # 媒体处理 - FFmpeg操作耗时
    'format_convert': 600000,  # 10分钟
    'compress_image': 120000,  # 2分钟
    'compress_video': 1800000, # 30分钟
    'extract_audio': 300000,   # 5分钟
    'trim_video': 600000,      # 10分钟
    'merge_media': 1800000,    # 30分钟
    'add_watermark': 600000,   # 10分钟
    'download_m3u8': 1800000,  # 30分钟（下载可能很慢）
    'rotate_video': 600000,    # 10分钟
    'video_speed': 600000,     # 10分钟
    'extract_frame': 60000,    # 1分钟
    'add_subtitle': 600000,    # 10分钟
    'adjust_volume': 300000,   # 5分钟
    'resize_video': 600000,    # 10分钟
    # 图像处理
    'image_grayscale': 60000,  # 1分钟
    'image_round_corners': 60000, # 1分钟
    # 音频处理
    'audio_to_text': 300000,   # 5分钟（语音识别可能较慢）
    # 二维码
    'qr_generate': 10000,      # 10秒
    'qr_decode': 30000,        # 30秒
    # 录屏 - 非阻塞（启动后立即返回，后台录制）
    'screen_record': 10000,    # 10秒（启动录屏）
    # AI识别
    'face_recognition': 60000, # 1分钟
    'image_ocr': 60000,        # 1分钟
    # PDF处理
    'pdf_to_images': 300000,   # 5分钟
    'images_to_pdf': 300000,   # 5分钟
    'pdf_merge': 300000,       # 5分钟
    'pdf_split': 300000,       # 5分钟
    'pdf_extract_text': 120000,# 2分钟
    'pdf_extract_images': 300000, # 5分钟
    'pdf_encrypt': 60000,      # 1分钟
    'pdf_decrypt': 60000,      # 1分钟
    'pdf_add_watermark': 300000, # 5分钟
    'pdf_rotate': 120000,      # 2分钟
    'pdf_delete_pages': 120000,# 2分钟
    'pdf_get_info': 30000,     # 30秒
    'pdf_compress': 600000,    # 10分钟
    'pdf_insert_pages': 300000,# 5分钟
    'pdf_reorder_pages': 120000, # 2分钟
    'pdf_to_word': 600000,     # 10分钟
    # 其他
    'export_log': 30000,       # 30秒
    # QQ自动化
    'qq_wait_message': 0,      # 不超时（阻塞型，等待消息）
    'qq_send_message': 30000,  # 30秒
    'qq_send_image': 60000,    # 1分钟
    'qq_send_file': 120000,    # 2分钟
    'qq_get_friends': 30000,   # 30秒
    'qq_get_groups': 30000,    # 30秒
    'qq_get_group_members': 30000, # 30秒
    'qq_get_login_info': 10000,# 10秒
    # 微信自动化
    'wechat_wait_message': 0,  # 不超时（阻塞型，等待消息）
    'wechat_send_message': 30000,  # 30秒
    'wechat_send_file': 120000,    # 2分钟
    'wechat_get_messages': 30000,  # 30秒
    'wechat_get_sessions': 30000,  # 30秒
    'wechat_get_login_info': 10000,# 10秒
    # 分组/备注 - 不执行
    'group': 0,
    'note': 0,
}


# 需要使用内部超时逻辑的模块（忽略节点配置的 timeout 字段）
MODULES_WITH_INTERNAL_TIMEOUT = {
    'qq_wait_message', 'wechat_wait_message', 'wait', 'loop', 'foreach', 
    'scheduled_task', 'subflow', 'play_music', 'play_video', 'view_image', 'input_prompt'
}


# 重要模块列表 - 这些模块的日志在简洁模式下也会显示
IMPORTANT_MODULES = {
    # 用户交互/输出
    'print_log', 'input_prompt', 'system_notification', 'text_to_speech',
    # 网络共享
    'share_folder', 'share_file', 'stop_share',
    # 屏幕共享
    'start_screen_share', 'stop_screen_share',
    # 网络请求
    'api_request', 'send_email',
    # 数据库操作
    'db_connect', 'db_query', 'db_execute', 'db_insert', 'db_update', 'db_delete', 'db_close',
    # AI能力
    'ai_chat', 'ai_vision',
    # 图像/文本识别点击
    'click_image', 'click_text', 'hover_image', 'hover_text', 'image_ocr',
    # 命令/脚本执行
    'run_command', 'js_script',
    # 文件操作
    'download_file', 'upload_file', 'read_text_file', 'write_text_file',
    'copy_file', 'move_file', 'delete_file', 'rename_file',
    # QQ自动化
    'qq_send_message', 'qq_send_image', 'qq_send_file', 'qq_wait_message',
    # 微信自动化
    'wechat_send_message', 'wechat_send_file',
    # 子流程
    'subflow',
    # 录屏
    'screen_record',
    # 音频处理
    'audio_to_text',
    # 导出
    'export_log', 'table_export', 'list_export',
}


def get_module_default_timeout(module_type: str) -> int:
    """获取模块默认超时时间（毫秒）"""
    return MODULE_DEFAULT_TIMEOUTS.get(module_type, 30000)


def is_module_with_internal_timeout(module_type: str) -> bool:
    """检查模块是否使用内部超时逻辑"""
    return module_type in MODULES_WITH_INTERNAL_TIMEOUT


def is_important_module(module_type: str) -> bool:
    """检查模块是否为重要模块"""
    return module_type in IMPORTANT_MODULES
