"""元素选择器核心类 - 使用子进程方式"""
import asyncio
import subprocess
import sys
import json
from pathlib import Path


class ElementPicker:
    def __init__(self):
        self.is_active = False
        self._process = None
        self._selected_element = None
        self._similar_elements = None
        self._url = ""
        self._error = None
        self._reader_task = None

    async def _read_output(self):
        """读取子进程输出"""
        while self._process and self._process.stdout:
            try:
                loop = asyncio.get_running_loop()
                line = await loop.run_in_executor(
                    None, self._process.stdout.readline
                )
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("type") == "selected" and data.get("data"):
                        self._selected_element = data["data"]
                    elif data.get("type") == "similar" and data.get("data"):
                        self._similar_elements = data["data"]
                    elif data.get("status") == "closed":
                        self.is_active = False
                        break
                except json.JSONDecodeError:
                    pass
            except Exception as e:
                print(f"[ElementPicker] Read error: {e}")
                break

    async def start(self, url, on_element_selected=None):
        if self.is_active:
            raise Exception("已在运行")
        
        self._url = url
        self._selected_element = None
        self._similar_elements = None
        self._error = None
        
        # 启动子进程
        script_path = Path(__file__).parent / "picker_process.py"
        
        try:
            self._process = subprocess.Popen(
                [sys.executable, str(script_path), url],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            self.is_active = True
            
            # 启动输出读取任务
            self._reader_task = asyncio.create_task(self._read_output())
            
            # 等待浏览器启动
            await asyncio.sleep(0.5)
            
        except Exception as e:
            self._error = str(e)
            self.is_active = False
            raise

    async def get_selected_element(self):
        if self._process and self._process.stdin:
            try:
                self._process.stdin.write(json.dumps({"action": "get_selected"}) + "\n")
                self._process.stdin.flush()
                await asyncio.sleep(0.1)
            except:
                pass
        
        result = self._selected_element
        if result:
            self._selected_element = None
        return result

    async def get_similar_elements(self):
        if self._process and self._process.stdin:
            try:
                self._process.stdin.write(json.dumps({"action": "get_similar"}) + "\n")
                self._process.stdin.flush()
                await asyncio.sleep(0.1)
            except:
                pass
        
        result = self._similar_elements
        if result:
            self._similar_elements = None
        return result

    async def stop(self):
        if self._process:
            try:
                self._process.stdin.write(json.dumps({"action": "quit"}) + "\n")
                self._process.stdin.flush()
            except:
                pass
            
            try:
                self._process.terminate()
                self._process.wait(timeout=3)
            except:
                try:
                    self._process.kill()
                except:
                    pass
            
            self._process = None
        
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None
        
        self.is_active = False
