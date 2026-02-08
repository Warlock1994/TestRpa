"""高级模块执行器 - advanced_email"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
import asyncio
import re


@register_executor
class SendEmailExecutor(ModuleExecutor):
    """发送邮件模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "send_email"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        sender_email = context.resolve_value(config.get('senderEmail', ''))
        auth_code = context.resolve_value(config.get('authCode', ''))
        recipient_email = context.resolve_value(config.get('recipientEmail', ''))
        email_subject = context.resolve_value(config.get('emailSubject', ''))
        email_content = context.resolve_value(config.get('emailContent', ''))
        
        if not sender_email:
            return ModuleResult(success=False, error="发件人邮箱不能为空")
        
        if not auth_code:
            return ModuleResult(success=False, error="授权码不能为空")
        
        if not recipient_email:
            return ModuleResult(success=False, error="收件人邮箱不能为空")
        
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = email_subject or '(无标题)'
            
            msg.attach(MIMEText(email_content or '', 'plain', 'utf-8'))
            
            # 使用线程池执行同步SMTP操作
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._send_email_sync, sender_email, auth_code, recipient_email, msg)
            
            return ModuleResult(
                success=True, 
                message=f"邮件已发送至: {recipient_email}",
                data={'recipient': recipient_email, 'subject': email_subject}
            )
        
        except smtplib.SMTPAuthenticationError:
            return ModuleResult(success=False, error="邮箱认证失败，请检查邮箱地址和授权码")
        except Exception as e:
            return ModuleResult(success=False, error=f"发送邮件失败: {str(e)}")
    
    def _send_email_sync(self, sender_email, auth_code, recipient_email, msg):
        import smtplib
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(sender_email, auth_code)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()