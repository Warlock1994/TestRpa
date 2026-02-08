export const selectorGuideContent = `# 🎯 选择器完全指南

CSS选择器是网页自动化的核心技能。本章从入门到精通，全面讲解选择器的使用方法。

---

## 📌 什么是选择器？

选择器是用来定位网页元素的"地址"。就像快递需要地址才能送到，自动化操作也需要选择器才能找到目标元素。

**示例**：
\`\`\`html
<button id="submit-btn" class="btn primary">提交</button>
\`\`\`

可以用以下选择器定位这个按钮：
- \`#submit-btn\` - 通过ID
- \`.btn\` - 通过类名
- \`button\` - 通过标签名

---

## 🎓 基础选择器

### 1. ID选择器（#）

通过元素的 \`id\` 属性定位，**最稳定**的选择方式。

**语法**：\`#id名称\`

**示例**：
\`\`\`html
<input id="username" type="text">
<button id="login-btn">登录</button>
\`\`\`

选择器：
- \`#username\` - 选择用户名输入框
- \`#login-btn\` - 选择登录按钮

**特点**：
- ✅ 最稳定，ID通常不会变
- ✅ 唯一性，一个页面ID不重复
- ❌ 不是所有元素都有ID

---

### 2. 类选择器（.）

通过元素的 \`class\` 属性定位。

**语法**：\`.类名\`

**示例**：
\`\`\`html
<div class="product-item">商品1</div>
<div class="product-item">商品2</div>
<button class="btn btn-primary">按钮</button>
\`\`\`

选择器：
- \`.product-item\` - 选择所有商品项（多个）
- \`.btn\` - 选择所有按钮
- \`.btn-primary\` - 选择主要按钮

**多类名选择**：
\`\`\`
.btn.btn-primary  → 同时有btn和btn-primary类的元素
\`\`\`

---

### 3. 标签选择器

通过HTML标签名定位。

**语法**：\`标签名\`

**示例**：
- \`input\` - 所有输入框
- \`button\` - 所有按钮
- \`a\` - 所有链接
- \`img\` - 所有图片
- \`div\` - 所有div

**特点**：
- ✅ 简单直接
- ❌ 通常会选中多个元素
- ❌ 不够精确

---

### 4. 属性选择器（[]）

通过元素的属性定位，非常强大。

**语法**：

| 语法 | 说明 |
|------|------|
| \`[attr]\` | 有这个属性 |
| \`[attr="value"]\` | 属性等于某值 |
| \`[attr^="value"]\` | 属性以某值开头 |
| \`[attr$="value"]\` | 属性以某值结尾 |
| \`[attr*="value"]\` | 属性包含某值 |

**示例**：
\`\`\`html
<input type="text" name="username" placeholder="请输入用户名">
<input type="password" name="password">
<a href="https://example.com" target="_blank">链接</a>
<div data-id="123" data-type="product">商品</div>
\`\`\`

选择器：
- \`[type="text"]\` - 文本输入框
- \`[type="password"]\` - 密码输入框
- \`[name="username"]\` - name为username的元素
- \`[href^="https"]\` - https开头的链接
- \`[href$=".pdf"]\` - 以.pdf结尾的链接
- \`[data-id="123"]\` - data-id为123的元素
- \`[data-type*="prod"]\` - data-type包含prod的元素

---

## 🔗 组合选择器

### 1. 后代选择器（空格）

选择某元素内部的元素。

**语法**：\`祖先 后代\`

**示例**：
\`\`\`html
<div class="container">
  <ul class="list">
    <li>项目1</li>
    <li>项目2</li>
  </ul>
</div>
\`\`\`

- \`.container li\` - container内的所有li
- \`.list li\` - list内的所有li

---

### 2. 子元素选择器（>）

只选择直接子元素。

**语法**：\`父元素 > 子元素\`

**示例**：
\`\`\`html
<ul class="menu">
  <li>一级菜单
    <ul>
      <li>二级菜单</li>
    </ul>
  </li>
</ul>
\`\`\`

- \`.menu li\` - 所有li（包括二级）
- \`.menu > li\` - 只有一级li

---

### 3. 相邻兄弟选择器（+）

选择紧跟在某元素后面的元素。

**语法**：\`元素1 + 元素2\`

**示例**：
\`\`\`html
<h2>标题</h2>
<p>第一段</p>
<p>第二段</p>
\`\`\`

- \`h2 + p\` - 紧跟h2后面的p（第一段）

---

### 4. 通用兄弟选择器（~）

选择某元素后面的所有兄弟元素。

**语法**：\`元素1 ~ 元素2\`

- \`h2 ~ p\` - h2后面的所有p

---

## 🎯 伪类选择器

### 位置伪类

| 选择器 | 说明 |
|--------|------|
| \`:first-child\` | 第一个子元素 |
| \`:last-child\` | 最后一个子元素 |
| \`:nth-child(n)\` | 第n个子元素 |
| \`:nth-child(odd)\` | 奇数位置的子元素 |
| \`:nth-child(even)\` | 偶数位置的子元素 |
| \`:nth-last-child(n)\` | 倒数第n个子元素 |

**示例**：
\`\`\`html
<ul>
  <li>项目1</li>
  <li>项目2</li>
  <li>项目3</li>
  <li>项目4</li>
</ul>
\`\`\`

- \`li:first-child\` - 项目1
- \`li:last-child\` - 项目4
- \`li:nth-child(2)\` - 项目2
- \`li:nth-child(odd)\` - 项目1、项目3

### 类型伪类

| 选择器 | 说明 |
|--------|------|
| \`:first-of-type\` | 同类型中的第一个 |
| \`:last-of-type\` | 同类型中的最后一个 |
| \`:nth-of-type(n)\` | 同类型中的第n个 |

### 状态伪类

| 选择器 | 说明 |
|--------|------|
| \`:hover\` | 鼠标悬停 |
| \`:focus\` | 获得焦点 |
| \`:checked\` | 被选中（复选框/单选框） |
| \`:disabled\` | 被禁用 |
| \`:enabled\` | 可用状态 |

### 否定伪类

\`:not(选择器)\` - 排除某些元素

**示例**：
- \`input:not([type="hidden"])\` - 非隐藏的输入框
- \`li:not(:first-child)\` - 除了第一个的所有li

---

## 🛠️ 实战技巧

### 1. 可视化选择元素

**Ctrl+点击** 选择器按钮，可以在网页上直接点选元素，自动生成选择器。

### 2. 浏览器调试选择器

1. 按 **F12** 打开开发者工具
2. 切换到 **Console** 标签
3. 输入测试代码：

\`\`\`javascript
// 测试选择器是否正确
document.querySelector('你的选择器')

// 查看选中了多少个元素
document.querySelectorAll('你的选择器').length
\`\`\`

### 3. 在Elements面板搜索

1. 按 **F12** 打开开发者工具
2. 切换到 **Elements** 标签
3. 按 **Ctrl+F** 搜索
4. 输入选择器，会高亮匹配的元素

---

## 📋 常见场景选择器

### 表单元素

\`\`\`
用户名输入框：#username 或 input[name="username"]
密码输入框：#password 或 input[type="password"]
登录按钮：#login-btn 或 button[type="submit"]
搜索框：#search 或 input[placeholder*="搜索"]
\`\`\`

### 列表元素

\`\`\`
所有列表项：.list-item 或 ul > li
第一个列表项：.list-item:first-child
最后一个列表项：.list-item:last-child
第3个列表项：.list-item:nth-child(3)
\`\`\`

### 表格元素

\`\`\`
表格：table 或 .data-table
表头：thead th
表格行：tbody tr
第2行：tbody tr:nth-child(2)
第3列：tbody td:nth-child(3)
\`\`\`

### 导航菜单

\`\`\`
导航栏：nav 或 .navbar
菜单项：.nav-item 或 nav a
当前激活项：.nav-item.active
\`\`\`

### 弹窗/对话框

\`\`\`
弹窗容器：.modal 或 [role="dialog"]
关闭按钮：.modal .close 或 .modal-close
确认按钮：.modal .btn-confirm
\`\`\`

---

## ⚠️ 常见问题

### 1. 选择器找不到元素

**可能原因**：
- 元素在 iframe 中
- 元素是动态加载的
- 选择器写错了

**解决方法**：
- 检查是否需要切换到 iframe
- 添加等待元素模块
- 使用浏览器调试确认选择器

### 2. 选择器选中多个元素

**解决方法**：
- 添加更多限定条件
- 使用 :nth-child 指定位置
- 使用更具体的父元素

### 3. 选择器不稳定

**原因**：使用了动态生成的类名或ID

**解决方法**：
- 使用属性选择器 \`[data-xxx]\`
- 使用文本内容定位
- 使用相对位置定位

---

## 💡 选择器优先级建议

1. **首选 ID 选择器**：\`#login-btn\`
2. **次选 唯一类名**：\`.submit-button\`
3. **再选 属性选择器**：\`[data-action="submit"]\`
4. **最后 组合选择器**：\`.form .btn:last-child\`

**原则**：
- 越简单越好
- 越稳定越好
- 避免过长的选择器链`
