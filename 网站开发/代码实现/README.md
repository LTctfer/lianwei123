# 网站系统代码实现

## 项目概述

这是一个完整的现代化网站系统，基于设计文档实现，包含以下核心功能：

- 用户认证系统
- 产品展示与搜索
- 购物车与支付
- 内容管理系统
- 用户社区
- 数据分析平台

## 技术栈

### 前端
- React 18 + TypeScript
- Ant Design + Tailwind CSS
- Redux Toolkit
- React Router v6
- Vite

### 后端
- Node.js + Express + TypeScript
- MySQL + Prisma ORM
- Redis
- JWT认证
- Multer文件上传

## 项目结构

```
代码实现/
├── client/                 # 前端代码
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── pages/         # 页面
│   │   ├── store/         # 状态管理
│   │   ├── services/      # API服务
│   │   └── utils/         # 工具函数
│   ├── public/            # 静态资源
│   └── package.json
├── server/                # 后端代码
│   ├── src/
│   │   ├── controllers/   # 控制器
│   │   ├── models/        # 数据模型
│   │   ├── routes/        # 路由
│   │   ├── middleware/    # 中间件
│   │   ├── services/      # 业务服务
│   │   └── utils/         # 工具函数
│   ├── prisma/            # 数据库配置
│   └── package.json
├── docs/                  # 文档
├── docker-compose.yml     # Docker配置
└── package.json          # 根配置
```

## 快速开始

### 1. 环境准备
```bash
# 安装Node.js 18+
# 安装MySQL 8.0+
# 安装Redis 6.0+
```

### 2. 项目安装
```bash
# 克隆项目
git clone <repository-url>
cd 网站开发/代码实现

# 安装所有依赖
npm run setup
```

### 3. 环境配置
```bash
# 复制环境配置文件
cp server/.env.example server/.env

# 编辑配置文件
vim server/.env
```

### 4. 数据库初始化
```bash
# 运行数据库迁移
npm run migrate

# 填充初始数据
npm run seed
```

### 5. 启动服务
```bash
# 开发模式启动
npm run dev

# 生产模式启动
npm run build
npm start
```

### 6. 访问应用
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- 管理后台: http://localhost:3000/admin

## 开发指南

### 代码规范
- 使用TypeScript进行类型检查
- 遵循ESLint配置规范
- 编写单元测试
- 提交前运行lint检查

### Git工作流
```bash
# 创建功能分支
git checkout -b feature/new-feature

# 提交代码
git add .
git commit -m "feat: 添加新功能"

# 推送分支
git push origin feature/new-feature
```

### 测试
```bash
# 运行测试
npm test

# 生成覆盖率报告
npm run test:coverage
```

## 部署

### Docker部署
```bash
# 构建并启动
docker-compose up -d

# 查看状态
docker-compose ps
```

### 手动部署
```bash
# 构建前端
npm run build

# 启动后端
npm start
```

## API文档

API文档可在以下地址查看：
- 开发环境: http://localhost:8000/api-docs
- 生产环境: https://api.example.com/api-docs

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

MIT License