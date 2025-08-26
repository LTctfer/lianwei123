# MCP浏览器控制服务器安装指南

## 环境要求

- Node.js 18.0.0 或更高版本
- npm 或 yarn 包管理器
- Windows 10/11 或 macOS/Linux

## 安装步骤

### 1. 安装Node.js

#### Windows系统
**方法一：官网下载**
1. 访问 [Node.js官网](https://nodejs.org/)
2. 下载LTS版本（推荐）
3. 运行安装程序，按默认设置安装

**方法二：使用包管理器**
```powershell
# 使用winget安装
winget install OpenJS.NodeJS

# 或使用chocolatey安装
choco install nodejs
```

#### macOS系统
```bash
# 使用Homebrew安装
brew install node

# 或使用官网下载安装包
```

#### Linux系统
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
sudo yum install -y nodejs
```

### 2. 验证安装

安装完成后，重新打开终端并验证：

```bash
node --version
npm --version
```

应该看到类似输出：
```
v18.17.0
9.6.7
```

### 3. 安装项目依赖

```bash
cd mcp文件
npm install
```

### 4. 安装Playwright浏览器

```bash
# 安装Playwright浏览器
npx playwright install
```

## 构建和运行

### 构建项目
```bash
npm run build
```

### 启动MCP服务器
```bash
npm start
```

### 开发模式运行
```bash
npm run dev
```

## 测试MCP服务器

### 基本连接测试
MCP服务器通过stdio协议通信，可以使用以下方式测试：

```bash
# 启动服务器并测试基本功能
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | npm start
```

### 使用MCP客户端测试
如果您有MCP客户端（如Claude Desktop），可以在配置中添加：

```json
{
  "mcpServers": {
    "browser-control": {
      "command": "node",
      "args": ["dist/server.js"],
      "cwd": "path/to/mcp文件"
    }
  }
}
```

## 故障排除

### 常见问题

1. **Node.js未找到**
   - 确保Node.js已正确安装
   - 重启终端或重新登录
   - 检查PATH环境变量

2. **依赖安装失败**
   ```bash
   # 清理npm缓存
   npm cache clean --force
   
   # 删除node_modules重新安装
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Playwright安装失败**
   ```bash
   # 手动安装浏览器
   npx playwright install chromium
   ```

4. **权限问题（Linux/macOS）**
   ```bash
   # 使用sudo安装全局包
   sudo npm install -g npm@latest
   ```

### 日志调试

启动服务器时会在stderr输出日志信息：
```bash
npm run dev 2> debug.log
```

## 下一步

安装完成后，您可以：
1. 阅读 [README.md](./README.md) 了解详细使用方法
2. 查看工具列表和参数说明
3. 在MCP客户端中配置和使用浏览器控制功能

## 技术支持

如果遇到问题，请检查：
- Node.js版本是否符合要求
- 网络连接是否正常
- 防火墙设置是否阻止了依赖下载