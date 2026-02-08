"""元素选择器服务"""
import asyncio
import threading
import time
import traceback
from typing import Optional


PICKER_SCRIPT = '''(function() {
    if (window.__elementPickerActive) return;
    window.__elementPickerActive = true;
    var highlightBox = document.createElement("div");
    highlightBox.style.cssText = "position:fixed;pointer-events:none;border:3px solid #3b82f6;background:rgba(59,130,246,0.2);z-index:999999;border-radius:4px;display:none;";
    document.body.appendChild(highlightBox);
    var tooltip = document.createElement("div");
    tooltip.style.cssText = "position:fixed;top:10px;left:50%;transform:translateX(-50%);background:#1e40af;color:white;padding:12px 24px;border-radius:8px;font-size:14px;z-index:999999;";
    tooltip.textContent = "Ctrl+点击选择元素";
    document.body.appendChild(tooltip);
    var isCtrlPressed = false;
    document.addEventListener("keydown", function(e) {
        if (e.key === "Control") {
            isCtrlPressed = true;
            highlightBox.style.borderColor = "#22c55e";
            highlightBox.style.background = "rgba(34,197,94,0.2)";
            tooltip.textContent = "点击选择元素";
            tooltip.style.background = "#059669";
        }
    }, true);
    document.addEventListener("keyup", function(e) {
        if (e.key === "Control") {
            isCtrlPressed = false;
            highlightBox.style.borderColor = "#3b82f6";
            highlightBox.style.background = "rgba(59,130,246,0.2)";
            tooltip.textContent = "Ctrl+点击选择元素";
            tooltip.style.background = "#1e40af";
        }
    }, true);
    function getSelector(el) {
        if (el.id) return "#" + CSS.escape(el.id);
        if (el.className && typeof el.className === "string") {
            var cls = el.className.trim().split(/\\s+/)[0];
            if (cls && document.querySelectorAll("." + CSS.escape(cls)).length === 1) {
                return "." + CSS.escape(cls);
            }
        }
        var path = [];
        while (el && el !== document.body) {
            var parent = el.parentElement;
            if (!parent) break;
            var idx = Array.from(parent.children).indexOf(el) + 1;
            path.unshift(el.tagName.toLowerCase() + ":nth-child(" + idx + ")");
            el = parent;
        }
        return path.join(" > ");
    }
    document.addEventListener("mousemove", function(e) {
        var el = document.elementFromPoint(e.clientX, e.clientY);
        if (!el) return;
        var rect = el.getBoundingClientRect();
        highlightBox.style.left = rect.left + "px";
        highlightBox.style.top = rect.top + "px";
        highlightBox.style.width = rect.width + "px";
        highlightBox.style.height = rect.height + "px";
        highlightBox.style.display = "block";
    }, true);
    document.addEventListener("click", function(e) {
        if (!isCtrlPressed && !e.ctrlKey) return;
        e.preventDefault();
        e.stopPropagation();
        var el = document.elementFromPoint(e.clientX, e.clientY);
        if (!el) return;
        var sel = getSelector(el);
        var rect = el.getBoundingClientRect();
        window.__elementPickerResult = {
            selector: sel,
            tagName: el.tagName.toLowerCase(),
            text: (el.textContent || "").substring(0, 100).trim(),
            attributes: { id: el.id || "", className: el.className || "" },
            rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
        };
        tooltip.textContent = "已选择: " + sel.substring(0, 40);
        tooltip.style.background = "#059669";
    }, true);
})();'''


class ElementPicker:
    def __init__(self):
        self.is_active = False
        self._selected_element = None
        self._similar_elements = None
        self._thread = None
        self._stop_event = threading.Event()
        self._url = ""
        self._error = None

    def _run_picker(self):
        from playwright.sync_api import sync_playwright
        print(f"[ElementPicker] Starting: {self._url}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, channel='msedge')  # 元素选择器必须有头模式
                page = browser.new_page()
                page.goto(self._url, timeout=30000)
                page.evaluate(PICKER_SCRIPT)
                print("[ElementPicker] Script injected")
                while not self._stop_event.is_set():
                    try:
                        result = page.evaluate("window.__elementPickerResult")
                        if result:
                            self._selected_element = result
                            page.evaluate("window.__elementPickerResult = null")
                        time.sleep(0.3)
                    except:
                        break
                browser.close()
        except Exception as e:
            self._error = str(e)
            traceback.print_exc()
        finally:
            self.is_active = False

    async def start(self, url, on_element_selected=None):
        if self.is_active:
            raise Exception("已在运行")
        self._url = url
        self._selected_element = None
        self._error = None
        self._stop_event.clear()
        self.is_active = True
        self._thread = threading.Thread(target=self._run_picker, daemon=True)
        self._thread.start()
        await asyncio.sleep(1.0)
        if self._error:
            self.is_active = False
            raise Exception(self._error)

    async def get_selected_element(self):
        result = self._selected_element
        if result:
            self._selected_element = None
        return result

    async def get_similar_elements(self):
        result = self._similar_elements
        if result:
            self._similar_elements = None
        return result

    async def stop(self):
        self._stop_event.set()
        self.is_active = False


class SelectorGenerator:
    @staticmethod
    def generate_selector(info):
        if info.get('selector'):
            return info['selector']
        return info.get('tagName', 'div')
