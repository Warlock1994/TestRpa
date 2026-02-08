"""实用工具模块执行器 - 文件对比、密码生成、编解码、加密、时间戳、颜色转换、打印机等"""
import asyncio
import hashlib
import secrets
import string
import urllib.parse
from datetime import datetime
from pathlib import Path
import difflib
import filecmp
import uuid

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float


@register_executor
class FileHashCompareExecutor(ModuleExecutor):
    """文件哈希对比模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "file_hash_compare"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        file1_path = context.resolve_value(config.get("file1Path", ""))
        file2_path = context.resolve_value(config.get("file2Path", ""))
        hash_algorithm = context.resolve_value(config.get("hashAlgorithm", "md5"))
        result_variable = config.get("resultVariable", "files_equal")
        
        if not file1_path or not file2_path:
            return ModuleResult(success=False, error="两个文件路径都不能为空")
        
        try:
            file1 = Path(file1_path)
            file2 = Path(file2_path)
            
            if not file1.exists():
                return ModuleResult(success=False, error=f"文件1不存在: {file1_path}")
            if not file2.exists():
                return ModuleResult(success=False, error=f"文件2不存在: {file2_path}")
            
            # 计算文件哈希
            hash_func = getattr(hashlib, hash_algorithm.lower(), hashlib.md5)
            
            def calc_hash(file_path):
                h = hash_func()
                with open(file_path, 'rb') as f:
                    while chunk := f.read(8192):
                        h.update(chunk)
                return h.hexdigest()
            
            hash1 = calc_hash(file1)
            hash2 = calc_hash(file2)
            
            are_equal = (hash1 == hash2)
            
            if result_variable:
                context.set_variable(result_variable, are_equal)
            
            msg = f"文件{'相同' if are_equal else '不同'} (算法: {hash_algorithm})"
            return ModuleResult(success=True, message=msg, data={"equal": are_equal, "hash1": hash1, "hash2": hash2})
        
        except Exception as e:
            return ModuleResult(success=False, error=f"文件哈希对比失败: {str(e)}")


@register_executor
class FileDiffCompareExecutor(ModuleExecutor):
    """文件差异对比模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "file_diff_compare"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        file1_path = context.resolve_value(config.get("file1Path", ""))
        file2_path = context.resolve_value(config.get("file2Path", ""))
        result_variable = config.get("resultVariable", "file_diff")
        output_format = context.resolve_value(config.get("outputFormat", "unified"))
        
        if not file1_path or not file2_path:
            return ModuleResult(success=False, error="两个文件路径都不能为空")
        
        try:
            file1 = Path(file1_path)
            file2 = Path(file2_path)
            
            if not file1.exists():
                return ModuleResult(success=False, error=f"文件1不存在: {file1_path}")
            if not file2.exists():
                return ModuleResult(success=False, error=f"文件2不存在: {file2_path}")
            
            # 读取文件内容
            with open(file1, 'r', encoding='utf-8', errors='ignore') as f:
                file1_lines = f.readlines()
            with open(file2, 'r', encoding='utf-8', errors='ignore') as f:
                file2_lines = f.readlines()
            
            # 生成差异
            if output_format == "unified":
                diff = list(difflib.unified_diff(file1_lines, file2_lines, 
                                                 fromfile=str(file1), tofile=str(file2)))
            elif output_format == "context":
                diff = list(difflib.context_diff(file1_lines, file2_lines,
                                                 fromfile=str(file1), tofile=str(file2)))
            else:  # html
                diff_html = difflib.HtmlDiff().make_file(file1_lines, file2_lines,
                                                         fromdesc=str(file1), todesc=str(file2))
                diff = [diff_html]
            
            diff_text = ''.join(diff) if diff else "文件内容完全相同"
            
            if result_variable:
                context.set_variable(result_variable, diff_text)
            
            return ModuleResult(success=True, message=f"已生成文件差异对比 ({output_format}格式)", data=diff_text)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"文件差异对比失败: {str(e)}")



@register_executor
class FolderHashCompareExecutor(ModuleExecutor):
    """文件夹哈希对比模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "folder_hash_compare"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        folder1_path = context.resolve_value(config.get("folder1Path", ""))
        folder2_path = context.resolve_value(config.get("folder2Path", ""))
        result_variable = config.get("resultVariable", "folders_equal")
        
        if not folder1_path or not folder2_path:
            return ModuleResult(success=False, error="两个文件夹路径都不能为空")
        
        try:
            folder1 = Path(folder1_path)
            folder2 = Path(folder2_path)
            
            if not folder1.exists() or not folder1.is_dir():
                return ModuleResult(success=False, error=f"文件夹1不存在或不是目录: {folder1_path}")
            if not folder2.exists() or not folder2.is_dir():
                return ModuleResult(success=False, error=f"文件夹2不存在或不是目录: {folder2_path}")
            
            # 使用filecmp进行深度对比
            comparison = filecmp.dircmp(folder1, folder2)
            
            # 检查是否完全相同
            def are_dirs_equal(dcmp):
                if dcmp.left_only or dcmp.right_only or dcmp.diff_files or dcmp.funny_files:
                    return False
                for sub_dcmp in dcmp.subdirs.values():
                    if not are_dirs_equal(sub_dcmp):
                        return False
                return True
            
            are_equal = are_dirs_equal(comparison)
            
            if result_variable:
                context.set_variable(result_variable, are_equal)
            
            msg = f"文件夹{'完全相同' if are_equal else '存在差异'}"
            return ModuleResult(success=True, message=msg, data={"equal": are_equal})
        
        except Exception as e:
            return ModuleResult(success=False, error=f"文件夹哈希对比失败: {str(e)}")



@register_executor
class FolderDiffCompareExecutor(ModuleExecutor):
    """文件夹差异对比模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "folder_diff_compare"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        folder1_path = context.resolve_value(config.get("folder1Path", ""))
        folder2_path = context.resolve_value(config.get("folder2Path", ""))
        result_variable = config.get("resultVariable", "diff_files")
        
        if not folder1_path or not folder2_path:
            return ModuleResult(success=False, error="两个文件夹路径都不能为空")
        
        try:
            folder1 = Path(folder1_path)
            folder2 = Path(folder2_path)
            
            if not folder1.exists() or not folder1.is_dir():
                return ModuleResult(success=False, error=f"文件夹1不存在或不是目录: {folder1_path}")
            if not folder2.exists() or not folder2.is_dir():
                return ModuleResult(success=False, error=f"文件夹2不存在或不是目录: {folder2_path}")
            
            # 使用filecmp进行深度对比
            comparison = filecmp.dircmp(folder1, folder2)
            
            # 收集所有差异文件
            diff_files = []
            
            def collect_diffs(dcmp, rel_path=""):
                # 只在folder1中存在的文件
                for name in dcmp.left_only:
                    diff_files.append(str(Path(rel_path) / name) + " (仅在文件夹1)")
                
                # 只在folder2中存在的文件
                for name in dcmp.right_only:
                    diff_files.append(str(Path(rel_path) / name) + " (仅在文件夹2)")
                
                # 内容不同的文件
                for name in dcmp.diff_files:
                    diff_files.append(str(Path(rel_path) / name) + " (内容不同)")
                
                # 递归处理子目录
                for sub_name, sub_dcmp in dcmp.subdirs.items():
                    collect_diffs(sub_dcmp, str(Path(rel_path) / sub_name))
            
            collect_diffs(comparison)
            
            if result_variable:
                context.set_variable(result_variable, diff_files)
            
            msg = f"找到 {len(diff_files)} 个差异文件"
            return ModuleResult(success=True, message=msg, data=diff_files)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"文件夹差异对比失败: {str(e)}")



@register_executor
class RandomPasswordGeneratorExecutor(ModuleExecutor):
    """随机密码生成模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "random_password_generator"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        length = to_int(config.get("length", 16), 16, context)
        include_uppercase_raw = config.get("includeUppercase", True)
        if isinstance(include_uppercase_raw, str):
            include_uppercase_raw = context.resolve_value(include_uppercase_raw)
        include_uppercase = include_uppercase_raw in [True, 'true', 'True', '1', 1]
        
        include_lowercase_raw = config.get("includeLowercase", True)
        if isinstance(include_lowercase_raw, str):
            include_lowercase_raw = context.resolve_value(include_lowercase_raw)
        include_lowercase = include_lowercase_raw in [True, 'true', 'True', '1', 1]
        
        include_digits_raw = config.get("includeDigits", True)
        if isinstance(include_digits_raw, str):
            include_digits_raw = context.resolve_value(include_digits_raw)
        include_digits = include_digits_raw in [True, 'true', 'True', '1', 1]
        
        include_symbols_raw = config.get("includeSymbols", True)
        if isinstance(include_symbols_raw, str):
            include_symbols_raw = context.resolve_value(include_symbols_raw)
        include_symbols = include_symbols_raw in [True, 'true', 'True', '1', 1]
        
        exclude_ambiguous_raw = config.get("excludeAmbiguous", False)
        if isinstance(exclude_ambiguous_raw, str):
            exclude_ambiguous_raw = context.resolve_value(exclude_ambiguous_raw)
        exclude_ambiguous = exclude_ambiguous_raw in [True, 'true', 'True', '1', 1]
        
        result_variable = config.get("resultVariable", "generated_password")
        
        try:
            # 构建字符集
            charset = ""
            if include_uppercase:
                charset += string.ascii_uppercase
            if include_lowercase:
                charset += string.ascii_lowercase
            if include_digits:
                charset += string.digits
            if include_symbols:
                charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
            if not charset:
                return ModuleResult(success=False, error="至少需要选择一种字符类型")
            
            # 排除易混淆字符
            if exclude_ambiguous:
                ambiguous = "il1Lo0O"
                charset = ''.join(c for c in charset if c not in ambiguous)
            
            # 生成密码
            password = ''.join(secrets.choice(charset) for _ in range(length))
            
            if result_variable:
                context.set_variable(result_variable, password)
            
            return ModuleResult(success=True, message=f"已生成{length}位随机密码", data=password)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"密码生成失败: {str(e)}")



@register_executor
class URLEncodeDecodeExecutor(ModuleExecutor):
    """URL编解码模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "url_encode_decode"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_text = context.resolve_value(config.get("inputText", ""))
        operation = context.resolve_value(config.get("operation", "encode"))
        encoding = context.resolve_value(config.get("encoding", "utf-8"))
        result_variable = config.get("resultVariable", "url_result")
        
        if not input_text:
            return ModuleResult(success=False, error="输入文本不能为空")
        
        try:
            if operation == "encode":
                result = urllib.parse.quote(input_text, safe='', encoding=encoding)
                msg = "URL编码完成"
            else:  # decode
                result = urllib.parse.unquote(input_text, encoding=encoding)
                msg = "URL解码完成"
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=msg, data=result)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"URL编解码失败: {str(e)}")


@register_executor
class MD5EncryptExecutor(ModuleExecutor):
    """MD5加密模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "md5_encrypt"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_text = context.resolve_value(config.get("inputText", ""))
        encoding = context.resolve_value(config.get("encoding", "utf-8"))
        output_format = context.resolve_value(config.get("outputFormat", "hex"))
        result_variable = config.get("resultVariable", "md5_hash")
        
        if not input_text:
            return ModuleResult(success=False, error="输入文本不能为空")
        
        try:
            md5_hash = hashlib.md5(input_text.encode(encoding))
            
            if output_format == "hex":
                result = md5_hash.hexdigest()
            else:  # base64
                import base64
                result = base64.b64encode(md5_hash.digest()).decode('ascii')
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"MD5加密完成 ({output_format}格式)", data=result)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"MD5加密失败: {str(e)}")



@register_executor
class SHAEncryptExecutor(ModuleExecutor):
    """SHA加密模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "sha_encrypt"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_text = context.resolve_value(config.get("inputText", ""))
        sha_type = context.resolve_value(config.get("shaType", "sha256"))
        encoding = context.resolve_value(config.get("encoding", "utf-8"))
        output_format = context.resolve_value(config.get("outputFormat", "hex"))
        result_variable = config.get("resultVariable", "sha_hash")
        
        if not input_text:
            return ModuleResult(success=False, error="输入文本不能为空")
        
        try:
            # 选择SHA算法
            hash_func = getattr(hashlib, sha_type.lower(), hashlib.sha256)
            sha_hash = hash_func(input_text.encode(encoding))
            
            if output_format == "hex":
                result = sha_hash.hexdigest()
            else:  # base64
                import base64
                result = base64.b64encode(sha_hash.digest()).decode('ascii')
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"{sha_type.upper()}加密完成 ({output_format}格式)", data=result)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"SHA加密失败: {str(e)}")


@register_executor
class TimestampConverterExecutor(ModuleExecutor):
    """时间戳转换器模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "timestamp_converter"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        operation = context.resolve_value(config.get("operation", "to_timestamp"))
        input_value = context.resolve_value(config.get("inputValue", ""))
        timestamp_unit = context.resolve_value(config.get("timestampUnit", "seconds"))
        datetime_format = context.resolve_value(config.get("datetimeFormat", "%Y-%m-%d %H:%M:%S"))
        result_variable = config.get("resultVariable", "timestamp_result")
        
        try:
            if operation == "to_timestamp":
                # 日期时间转时间戳
                if not input_value:
                    # 如果没有输入，使用当前时间
                    dt = datetime.now()
                else:
                    dt = datetime.strptime(input_value, datetime_format)
                
                timestamp = dt.timestamp()
                if timestamp_unit == "milliseconds":
                    result = int(timestamp * 1000)
                else:
                    result = int(timestamp)
                
                msg = f"已转换为时间戳 ({timestamp_unit})"
            else:
                # 时间戳转日期时间
                if not input_value:
                    return ModuleResult(success=False, error="时间戳不能为空")
                
                timestamp = to_float({"value": input_value}, 0, context)
                if timestamp_unit == "milliseconds":
                    timestamp = timestamp / 1000
                
                dt = datetime.fromtimestamp(timestamp)
                result = dt.strftime(datetime_format)
                msg = "已转换为日期时间"
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=msg, data=result)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"时间戳转换失败: {str(e)}")



@register_executor
class RGBToHSVExecutor(ModuleExecutor):
    """RGB转HSV模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "rgb_to_hsv"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        r = to_int(config.get("r", 0), 0, context)
        g = to_int(config.get("g", 0), 0, context)
        b = to_int(config.get("b", 0), 0, context)
        result_variable = config.get("resultVariable", "hsv_color")
        
        try:
            import colorsys
            
            # RGB值范围0-255，需要归一化到0-1
            r_norm = r / 255.0
            g_norm = g / 255.0
            b_norm = b / 255.0
            
            # 转换为HSV
            h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
            
            # HSV值转换为常用格式：H(0-360), S(0-100), V(0-100)
            h_deg = int(h * 360)
            s_pct = int(s * 100)
            v_pct = int(v * 100)
            
            result = {
                "h": h_deg,
                "s": s_pct,
                "v": v_pct,
                "string": f"HSV({h_deg}, {s_pct}%, {v_pct}%)"
            }
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"RGB({r},{g},{b}) → {result['string']}", data=result)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"RGB转HSV失败: {str(e)}")


@register_executor
class RGBToCMYKExecutor(ModuleExecutor):
    """RGB转CMYK模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "rgb_to_cmyk"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        r = to_int(config.get("r", 0), 0, context)
        g = to_int(config.get("g", 0), 0, context)
        b = to_int(config.get("b", 0), 0, context)
        result_variable = config.get("resultVariable", "cmyk_color")
        
        try:
            # RGB值范围0-255，需要归一化到0-1
            r_norm = r / 255.0
            g_norm = g / 255.0
            b_norm = b / 255.0
            
            # 计算CMYK
            k = 1 - max(r_norm, g_norm, b_norm)
            
            if k == 1:
                c = m = y = 0
            else:
                c = (1 - r_norm - k) / (1 - k)
                m = (1 - g_norm - k) / (1 - k)
                y = (1 - b_norm - k) / (1 - k)
            
            # 转换为百分比
            c_pct = int(c * 100)
            m_pct = int(m * 100)
            y_pct = int(y * 100)
            k_pct = int(k * 100)
            
            result = {
                "c": c_pct,
                "m": m_pct,
                "y": y_pct,
                "k": k_pct,
                "string": f"CMYK({c_pct}%, {m_pct}%, {y_pct}%, {k_pct}%)"
            }
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"RGB({r},{g},{b}) → {result['string']}", data=result)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"RGB转CMYK失败: {str(e)}")



@register_executor
class HEXToCMYKExecutor(ModuleExecutor):
    """HEX转CMYK模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "hex_to_cmyk"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        hex_color = context.resolve_value(config.get("hexColor", ""))
        result_variable = config.get("resultVariable", "cmyk_color")
        
        if not hex_color:
            return ModuleResult(success=False, error="HEX颜色值不能为空")
        
        try:
            # 移除#号
            hex_color = hex_color.lstrip('#')
            
            # 解析HEX颜色
            if len(hex_color) == 3:
                # 短格式 #RGB -> #RRGGBB
                hex_color = ''.join([c*2 for c in hex_color])
            
            if len(hex_color) != 6:
                return ModuleResult(success=False, error="无效的HEX颜色格式")
            
            # 转换为RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # RGB归一化
            r_norm = r / 255.0
            g_norm = g / 255.0
            b_norm = b / 255.0
            
            # 计算CMYK
            k = 1 - max(r_norm, g_norm, b_norm)
            
            if k == 1:
                c = m = y = 0
            else:
                c = (1 - r_norm - k) / (1 - k)
                m = (1 - g_norm - k) / (1 - k)
                y = (1 - b_norm - k) / (1 - k)
            
            # 转换为百分比
            c_pct = int(c * 100)
            m_pct = int(m * 100)
            y_pct = int(y * 100)
            k_pct = int(k * 100)
            
            result = {
                "c": c_pct,
                "m": m_pct,
                "y": y_pct,
                "k": k_pct,
                "string": f"CMYK({c_pct}%, {m_pct}%, {y_pct}%, {k_pct}%)"
            }
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"#{hex_color.upper()} → {result['string']}", data=result)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"HEX转CMYK失败: {str(e)}")


@register_executor
class UUIDGeneratorExecutor(ModuleExecutor):
    """UUID生成器模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "uuid_generator"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        uuid_version = to_int(config.get("uuidVersion", 4), 4, context)
        uppercase_raw = config.get("uppercase", False)
        if isinstance(uppercase_raw, str):
            uppercase_raw = context.resolve_value(uppercase_raw)
        uppercase = uppercase_raw in [True, 'true', 'True', '1', 1]
        
        remove_hyphens_raw = config.get("removeHyphens", False)
        if isinstance(remove_hyphens_raw, str):
            remove_hyphens_raw = context.resolve_value(remove_hyphens_raw)
        remove_hyphens = remove_hyphens_raw in [True, 'true', 'True', '1', 1]
        
        result_variable = config.get("resultVariable", "generated_uuid")
        
        try:
            # 生成UUID
            if uuid_version == 1:
                generated_uuid = uuid.uuid1()
            elif uuid_version == 3:
                namespace = context.resolve_value(config.get("namespace", ""))
                name = context.resolve_value(config.get("name", ""))
                if not namespace or not name:
                    return ModuleResult(success=False, error="UUID v3需要namespace和name参数")
                ns = uuid.NAMESPACE_DNS if namespace == "dns" else uuid.NAMESPACE_URL
                generated_uuid = uuid.uuid3(ns, name)
            elif uuid_version == 5:
                namespace = context.resolve_value(config.get("namespace", ""))
                name = context.resolve_value(config.get("name", ""))
                if not namespace or not name:
                    return ModuleResult(success=False, error="UUID v5需要namespace和name参数")
                ns = uuid.NAMESPACE_DNS if namespace == "dns" else uuid.NAMESPACE_URL
                generated_uuid = uuid.uuid5(ns, name)
            else:  # UUID v4 (默认)
                generated_uuid = uuid.uuid4()
            
            result = str(generated_uuid)
            
            if remove_hyphens:
                result = result.replace('-', '')
            
            if uppercase:
                result = result.upper()
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"已生成UUID v{uuid_version}", data=result)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"UUID生成失败: {str(e)}")



@register_executor
class PrinterCallExecutor(ModuleExecutor):
    """打印机调用模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "printer_call"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        file_path = context.resolve_value(config.get("filePath", ""))
        printer_name = context.resolve_value(config.get("printerName", ""))
        copies = to_int(config.get("copies", 1), 1, context)
        color_mode = context.resolve_value(config.get("colorMode", "color"))
        duplex = context.resolve_value(config.get("duplex", "none"))
        orientation = context.resolve_value(config.get("orientation", "portrait"))
        paper_size = context.resolve_value(config.get("paperSize", "A4"))
        
        if not file_path:
            return ModuleResult(success=False, error="文件路径不能为空")
        
        try:
            import win32print
            import win32api
            from pathlib import Path
            
            file = Path(file_path)
            if not file.exists():
                return ModuleResult(success=False, error=f"文件不存在: {file_path}")
            
            # 获取默认打印机或指定打印机
            if not printer_name:
                printer_name = win32print.GetDefaultPrinter()
            
            # 验证打印机是否存在
            printers = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
            if printer_name not in printers:
                return ModuleResult(success=False, error=f"打印机不存在: {printer_name}")
            
            # 获取打印机句柄
            printer_handle = win32print.OpenPrinter(printer_name)
            
            try:
                # 获取打印机默认设置
                properties = win32print.GetPrinter(printer_handle, 2)
                pDevMode = properties["pDevMode"]
                
                # 设置打印份数
                pDevMode.Copies = copies
                
                # 设置颜色模式
                if color_mode == "grayscale":
                    pDevMode.Color = 2  # DMCOLOR_MONOCHROME
                else:
                    pDevMode.Color = 1  # DMCOLOR_COLOR
                
                # 设置双面打印
                if duplex == "long_edge":
                    pDevMode.Duplex = 2  # DMDUP_VERTICAL
                elif duplex == "short_edge":
                    pDevMode.Duplex = 3  # DMDUP_HORIZONTAL
                else:
                    pDevMode.Duplex = 1  # DMDUP_SIMPLEX
                
                # 设置纸张方向
                if orientation == "landscape":
                    pDevMode.Orientation = 2  # DMORIENT_LANDSCAPE
                else:
                    pDevMode.Orientation = 1  # DMORIENT_PORTRAIT
                
                # 设置纸张大小
                paper_sizes = {
                    "A4": 9,
                    "A3": 8,
                    "Letter": 1,
                    "Legal": 5,
                    "A5": 11,
                }
                if paper_size in paper_sizes:
                    pDevMode.PaperSize = paper_sizes[paper_size]
                
                # 应用设置
                properties["pDevMode"] = pDevMode
                win32print.SetPrinter(printer_handle, 2, properties, 0)
                
                # 执行打印
                win32api.ShellExecute(
                    0,
                    "print",
                    str(file),
                    f'/d:"{printer_name}"',
                    ".",
                    0
                )
                
                msg = f"已发送打印任务到 {printer_name} (份数: {copies})"
                return ModuleResult(success=True, message=msg)
            
            finally:
                win32print.ClosePrinter(printer_handle)
        
        except ImportError:
            return ModuleResult(success=False, error="缺少pywin32库，无法调用打印机")
        except Exception as e:
            return ModuleResult(success=False, error=f"打印失败: {str(e)}")
