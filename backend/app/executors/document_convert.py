"""文档转换模块执行器 - 基于Pandoc的文档格式转换"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int
from pathlib import Path
import asyncio


@register_executor
class MarkdownToHTMLExecutor(ModuleExecutor):
    """Markdown转HTML模块执行器"""

    @property
    def module_type(self) -> str:
        return "markdown_to_html"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        standalone = config.get("standalone", True)  # 是否生成完整HTML文档
        css_file = context.resolve_value(config.get("cssFile", ""))  # CSS样式文件
        template = context.resolve_value(config.get("template", ""))  # 模板文件
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")

        try:
            import pypandoc
            
            # 如果没有指定输出路径，生成默认路径
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.html'))
            
            # 构建额外参数
            extra_args = []
            if standalone:
                extra_args.append('--standalone')
            if css_file and Path(css_file).exists():
                extra_args.extend(['--css', css_file])
            if template and Path(template).exists():
                extra_args.extend(['--template', template])
            
            # 执行转换
            pypandoc.convert_file(
                input_path,
                'html',
                outputfile=output_path,
                extra_args=extra_args
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将Markdown转换为HTML: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"Markdown转HTML失败: {str(e)}")


@register_executor
class HTMLToMarkdownExecutor(ModuleExecutor):
    """HTML转Markdown模块执行器"""

    @property
    def module_type(self) -> str:
        return "html_to_markdown"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        wrap_text = config.get("wrapText", True)  # 是否自动换行
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")

        try:
            import pypandoc
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.md'))
            
            extra_args = []
            if wrap_text:
                extra_args.append('--wrap=auto')
            else:
                extra_args.append('--wrap=none')
            
            pypandoc.convert_file(
                input_path,
                'markdown',
                outputfile=output_path,
                extra_args=extra_args
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将HTML转换为Markdown: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"HTML转Markdown失败: {str(e)}")


@register_executor
class MarkdownToPDFExecutor(ModuleExecutor):
    """Markdown转PDF模块执行器"""

    @property
    def module_type(self) -> str:
        return "markdown_to_pdf"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        pdf_engine = context.resolve_value(config.get("pdfEngine", "pdflatex"))  # PDF引擎
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")

        try:
            import pypandoc
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.pdf'))
            
            pypandoc.convert_file(
                input_path,
                'pdf',
                outputfile=output_path,
                extra_args=[f'--pdf-engine={pdf_engine}']
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将Markdown转换为PDF: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc和LaTeX: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"Markdown转PDF失败: {str(e)}")


@register_executor
class MarkdownToDocxExecutor(ModuleExecutor):
    """Markdown转Word文档模块执行器"""

    @property
    def module_type(self) -> str:
        return "markdown_to_docx"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        reference_doc = context.resolve_value(config.get("referenceDoc", ""))  # 参考文档（样式模板）
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")

        try:
            import pypandoc
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.docx'))
            
            extra_args = []
            if reference_doc and Path(reference_doc).exists():
                extra_args.extend(['--reference-doc', reference_doc])
            
            pypandoc.convert_file(
                input_path,
                'docx',
                outputfile=output_path,
                extra_args=extra_args
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将Markdown转换为Word文档: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"Markdown转Word失败: {str(e)}")


@register_executor
class DocxToMarkdownExecutor(ModuleExecutor):
    """Word文档转Markdown模块执行器"""

    @property
    def module_type(self) -> str:
        return "docx_to_markdown"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        extract_media = config.get("extractMedia", True)  # 是否提取媒体文件
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")

        try:
            import pypandoc
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.md'))
            
            extra_args = []
            if extract_media:
                media_dir = Path(output_path).parent / f"{Path(output_path).stem}_media"
                extra_args.extend(['--extract-media', str(media_dir)])
            
            pypandoc.convert_file(
                input_path,
                'markdown',
                outputfile=output_path,
                extra_args=extra_args
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将Word文档转换为Markdown: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"Word转Markdown失败: {str(e)}")


@register_executor
class HTMLToDocxExecutor(ModuleExecutor):
    """HTML转Word文档模块执行器"""

    @property
    def module_type(self) -> str:
        return "html_to_docx"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")

        try:
            import pypandoc
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.docx'))
            
            pypandoc.convert_file(
                input_path,
                'docx',
                outputfile=output_path
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将HTML转换为Word文档: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"HTML转Word失败: {str(e)}")


@register_executor
class DocxToHTMLExecutor(ModuleExecutor):
    """Word文档转HTML模块执行器"""

    @property
    def module_type(self) -> str:
        return "docx_to_html"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        standalone = config.get("standalone", True)
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")

        try:
            import pypandoc
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.html'))
            
            extra_args = []
            if standalone:
                extra_args.append('--standalone')
            
            pypandoc.convert_file(
                input_path,
                'html',
                outputfile=output_path,
                extra_args=extra_args
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将Word文档转换为HTML: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"Word转HTML失败: {str(e)}")


@register_executor
class MarkdownToEPUBExecutor(ModuleExecutor):
    """Markdown转EPUB电子书模块执行器"""

    @property
    def module_type(self) -> str:
        return "markdown_to_epub"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        title = context.resolve_value(config.get("title", ""))
        author = context.resolve_value(config.get("author", ""))
        cover_image = context.resolve_value(config.get("coverImage", ""))
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")

        try:
            import pypandoc
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.epub'))
            
            extra_args = []
            if title:
                extra_args.extend(['--metadata', f'title={title}'])
            if author:
                extra_args.extend(['--metadata', f'author={author}'])
            if cover_image and Path(cover_image).exists():
                extra_args.extend(['--epub-cover-image', cover_image])
            
            pypandoc.convert_file(
                input_path,
                'epub',
                outputfile=output_path,
                extra_args=extra_args
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将Markdown转换为EPUB电子书: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"Markdown转EPUB失败: {str(e)}")


@register_executor
class EPUBToMarkdownExecutor(ModuleExecutor):
    """EPUB电子书转Markdown模块执行器"""

    @property
    def module_type(self) -> str:
        return "epub_to_markdown"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")

        try:
            import pypandoc
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.md'))
            
            pypandoc.convert_file(
                input_path,
                'markdown',
                outputfile=output_path
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将EPUB电子书转换为Markdown: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"EPUB转Markdown失败: {str(e)}")


@register_executor
class LaTeXToPDFExecutor(ModuleExecutor):
    """LaTeX转PDF模块执行器"""

    @property
    def module_type(self) -> str:
        return "latex_to_pdf"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        pdf_engine = context.resolve_value(config.get("pdfEngine", "pdflatex"))
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")

        try:
            import pypandoc
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.pdf'))
            
            pypandoc.convert_file(
                input_path,
                'pdf',
                outputfile=output_path,
                format='latex',
                extra_args=[f'--pdf-engine={pdf_engine}']
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将LaTeX转换为PDF: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc和LaTeX: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"LaTeX转PDF失败: {str(e)}")


@register_executor
class RSTToHTMLExecutor(ModuleExecutor):
    """reStructuredText转HTML模块执行器"""

    @property
    def module_type(self) -> str:
        return "rst_to_html"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        standalone = config.get("standalone", True)
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")

        try:
            import pypandoc
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.html'))
            
            extra_args = []
            if standalone:
                extra_args.append('--standalone')
            
            pypandoc.convert_file(
                input_path,
                'html',
                outputfile=output_path,
                format='rst',
                extra_args=extra_args
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将reStructuredText转换为HTML: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"RST转HTML失败: {str(e)}")


@register_executor
class OrgModeToHTMLExecutor(ModuleExecutor):
    """Org-mode转HTML模块执行器"""

    @property
    def module_type(self) -> str:
        return "org_to_html"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        standalone = config.get("standalone", True)
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")

        try:
            import pypandoc
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix('.html'))
            
            extra_args = []
            if standalone:
                extra_args.append('--standalone')
            
            pypandoc.convert_file(
                input_path,
                'html',
                outputfile=output_path,
                format='org',
                extra_args=extra_args
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将Org-mode转换为HTML: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"Org-mode转HTML失败: {str(e)}")


@register_executor
class UniversalDocumentConvertExecutor(ModuleExecutor):
    """通用文档转换模块执行器 - 支持Pandoc所有格式"""

    @property
    def module_type(self) -> str:
        return "universal_doc_convert"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        from_format = context.resolve_value(config.get("fromFormat", ""))  # 源格式
        to_format = context.resolve_value(config.get("toFormat", ""))  # 目标格式
        extra_options = context.resolve_value(config.get("extraOptions", ""))  # 额外选项
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")
        
        if not to_format:
            return ModuleResult(success=False, error="目标格式不能为空")

        try:
            import pypandoc
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.with_suffix(f'.{to_format}'))
            
            # 解析额外选项
            extra_args = []
            if extra_options:
                extra_args = extra_options.split()
            
            # 执行转换
            convert_kwargs = {
                'outputfile': output_path,
                'extra_args': extra_args
            }
            if from_format:
                convert_kwargs['format'] = from_format
            
            pypandoc.convert_file(
                input_path,
                to_format,
                **convert_kwargs
            )
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已将文档从 {from_format or '自动检测'} 转换为 {to_format}: {output_path}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(
                success=False,
                error="需要安装pypandoc库: pip install pypandoc，并安装Pandoc: https://pandoc.org/installing.html"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"文档转换失败: {str(e)}")
