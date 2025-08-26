# MCP浏览器控制服务器

一个基于MCP（Model Context Protocol）协议的浏览器自动化控制服务器，为AI智能体提供完整的浏览器操作能力。

## 功能特性

- 🌐 **网页导航控制** - 支持页面跳转、前进后退、刷新等操作
- 🖱️ **元素交互操作** - 实现点击、输入、选择等用户交互模拟
- 📝 **表单自动填写** - 智能识别表单字段并执行自动化填写
- 📊 **数据抓取提取** - 提供页面内容、元素属性、截图等数据获取
- 🔌 **MCP协议集成** - 完整实现MCP工具注册、调用和响应机制
- 🔄 **会话状态管理** - 维护浏览器实例和页面状态的生命周期

## 技术栈

- **后端**: Node.js + TypeScript + MCP SDK
- **浏览器引擎**: Playwright (支持 Chromium、Firefox、Safari)
- **数据验证**: Zod Schema
- **协议**: MCP (Model Context Protocol)

## 安装依赖

```bash
cd mcp文件
npm install
```

## 构建项目

```bash
npm run build
```

## 启动服务器

```bash
npm start
```

或开发模式：

```bash
npm run dev
```

## 可用工具

### 导航工具

#### `browser_navigate`
导航到指定URL
```json
{
  "url": "https://example.com",
  "waitUntil": "load"
}
```

#### `browser_back`
浏览器后退
```json
{}
```

#### `browser_forward`
浏览器前进
```json
{}
```

#### `browser_refresh`
刷新页面
```json
{}
```

### 交互工具

#### `browser_click`
点击页面元素
```json
{
  "selector": "#submit-button",
  "timeout": 5000,
  "force": false
}
```

#### `browser_type`
在元素中输入文本
```json
{
  "selector": "#username",
  "text": "用户名",
  "delay": 100,
  "clear": true
}
```

### 数据工具

#### `browser_screenshot`
截取页面截图
```json
{
  "fullPage": false,
  "quality": 80,
  "type": "png"
}
```

#### `browser_get_text`
获取元素文本内容
```json
{
  "selector": ".title",
  "timeout": 5000
}
```

#### `browser_get_attribute`
获取元素属性值
```json
{
  "selector": "#link",
  "attribute": "href",
  "timeout": 5000
}
```

## 使用示例

### 基本网页操作
```javascript
// 导航到网页
await callTool('browser_navigate', {
  url: 'https://example.com'
});

// 点击登录按钮
await callTool('browser_click', {
  selector: '#login-button'
});

// 输入用户名
await callTool('browser_type', {
  selector: '#username',
  text: 'myusername'
});

// 获取页面标题
await callTool('browser_get_text', {
  selector: 'h1'
});
```

### 表单自动填写
```javascript
// 填写注册表单
await callTool('browser_type', {
  selector: '#email',
  text: 'user@example.com'
});

await callTool('browser_type', {
  selector: '#password',
  text: 'securepassword'
});

await callTool('browser_click', {
  selector: '#register-button'
});
```

### 数据抓取
```javascript
// 截取页面截图
await callTool('browser_screenshot', {
  fullPage: true,
  type: 'png'
});

// 获取链接地址
await callTool('browser_get_attribute', {
  selector: 'a.download-link',
  attribute: 'href'
});
```

## 配置选项

可以通过修改 `BrowserConfig` 来自定义浏览器行为：

```typescript
const config: BrowserConfig = {
  headless: true,           // 无头模式
  viewport: {               // 视窗大小
    width: 1280,
    height: 720
  },
  timeout: 30000,          // 默认超时时间
  userAgent: 'custom-ua'   // 自定义用户代理
};
```

## 错误处理

所有工具调用都会返回标准化的响应格式：

```typescript
interface ToolResponse {
  success: boolean;
  data?: any;
  error?: string;
  timestamp: string;
}
```

成功响应示例：
```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "title": "Example Domain",
    "message": "成功导航到 https://example.com"
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

错误响应示例：
```json
{
  "success": false,
  "error": "导航失败: net::ERR_NAME_NOT_RESOLVED",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## 安全考虑

- 建议在受控环境中运行
- 可以通过配置限制访问的域名
- 定期清理浏览器会话和缓存
- 监控资源使用情况

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！