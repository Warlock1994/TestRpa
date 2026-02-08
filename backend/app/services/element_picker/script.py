"""元素选择器注入脚本"""

PICKER_SCRIPT = """(function() {
    // 防止重复注入
    if (window.__elementPickerActive) {
        console.log('[ElementPicker] Already active');
        return;
    }
    window.__elementPickerActive = true;
    console.log('[ElementPicker] Initializing...');
    
    // 创建高亮框
    var box = document.createElement('div');
    box.id = '__element_picker_box';
    box.style.cssText = 'position:fixed;pointer-events:none;border:3px solid #3b82f6;background:rgba(59,130,246,0.2);z-index:2147483647;border-radius:4px;display:none;transition:all 0.1s;';
    document.body.appendChild(box);
    
    // 创建提示条
    var tip = document.createElement('div');
    tip.id = '__element_picker_tip';
    tip.style.cssText = 'position:fixed;top:10px;left:50%;transform:translateX(-50%);background:#1e40af;color:white;padding:10px 20px;border-radius:8px;font-size:14px;z-index:2147483647;font-family:sans-serif;box-shadow:0 4px 12px rgba(0,0,0,0.3);';
    tip.textContent = 'Ctrl+点击选择元素 | Alt+点击选择相似元素';
    document.body.appendChild(tip);
    
    console.log('[ElementPicker] UI created');
    
    // 生成选择器
    function getSelector(el) {
        if (!el || el === document.body || el === document.documentElement) {
            return 'body';
        }
        
        // 优先使用 id
        if (el.id) {
            return '#' + el.id;
        }
        
        // 使用 class
        if (el.className && typeof el.className === 'string') {
            var classes = el.className.trim().split(/\\s+/);
            for (var i = 0; i < classes.length; i++) {
                if (classes[i] && classes[i].length < 50) {
                    var sel = el.tagName.toLowerCase() + '.' + classes[i];
                    try {
                        if (document.querySelectorAll(sel).length === 1) {
                            return sel;
                        }
                    } catch(e) {}
                }
            }
        }

        // 使用路径
        var path = [];
        var current = el;
        while (current && current !== document.body && path.length < 5) {
            var tag = current.tagName.toLowerCase();
            var parent = current.parentElement;
            if (parent) {
                var siblings = Array.from(parent.children).filter(function(c) {
                    return c.tagName === current.tagName;
                });
                if (siblings.length > 1) {
                    var idx = siblings.indexOf(current) + 1;
                    tag += ':nth-of-type(' + idx + ')';
                }
            }
            path.unshift(tag);
            current = parent;
        }
        return path.join(' > ');
    }
    
    // 查找相似元素
    function findSimilar(el) {
        var tag = el.tagName;
        var parent = el.parentElement;
        if (!parent) return [el];
        
        // 同父元素下相同标签
        var siblings = Array.from(parent.children).filter(function(c) {
            return c.tagName === tag;
        });
        if (siblings.length > 1 && siblings.length <= 50) {
            return siblings;
        }
        return [el];
    }
    
    // 鼠标移动高亮
    document.addEventListener('mousemove', function(e) {
        var el = document.elementFromPoint(e.clientX, e.clientY);
        if (!el || el === tip || el === box || el.id === '__element_picker_tip' || el.id === '__element_picker_box') {
            return;
        }
        var rect = el.getBoundingClientRect();
        box.style.left = rect.left + 'px';
        box.style.top = rect.top + 'px';
        box.style.width = rect.width + 'px';
        box.style.height = rect.height + 'px';
        box.style.display = 'block';
    }, true);
    
    // 点击选择
    document.addEventListener('click', function(e) {
        // 只响应 Ctrl 或 Alt 点击
        if (!e.ctrlKey && !e.altKey) {
            return;
        }
        
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        
        var el = document.elementFromPoint(e.clientX, e.clientY);
        if (!el || el === tip || el === box) {
            return;
        }
        
        console.log('[ElementPicker] Click detected, ctrl:', e.ctrlKey, 'alt:', e.altKey);
        
        if (e.altKey) {
            // Alt+点击：选择相似元素
            var similar = findSimilar(el);
            var selector = getSelector(el);
            
            // 生成带 {index} 的模式
            var parent = el.parentElement;
            if (parent && similar.length > 1) {
                var parentSel = getSelector(parent);
                var tag = el.tagName.toLowerCase();
                selector = parentSel + ' > ' + tag + ':nth-of-type({index})';
            }
            
            window.__elementPickerSimilar = {
                pattern: selector,
                count: similar.length,
                indices: similar.map(function(s, i) { return i + 1; }),
                minIndex: 1,
                maxIndex: similar.length
            };
            
            tip.textContent = '已选择 ' + similar.length + ' 个相似元素';
            tip.style.background = '#059669';
            console.log('[ElementPicker] Similar selected:', selector, 'count:', similar.length);
        } else if (e.ctrlKey) {
            // Ctrl+点击：选择单个元素
            var selector = getSelector(el);
            var rect = el.getBoundingClientRect();
            
            window.__elementPickerResult = {
                selector: selector,
                tagName: el.tagName.toLowerCase(),
                text: (el.textContent || '').substring(0, 100).trim(),
                attributes: { id: el.id || '', className: el.className || '' },
                rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
            };
            
            tip.textContent = '已选择: ' + selector;
            tip.style.background = '#059669';
            console.log('[ElementPicker] Element selected:', selector);
        }
    }, true);
    
    console.log('[ElementPicker] Ready!');
})();"""
