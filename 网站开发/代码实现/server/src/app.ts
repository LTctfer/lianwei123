import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import { PrismaClient } from '@prisma/client';
import Redis from 'ioredis';
import dotenv from 'dotenv';
import path from 'path';

// 导入路由
import authRoutes from './routes/auth';
import userRoutes from './routes/users';
import productRoutes from './routes/products';
import orderRoutes from './routes/orders';
import cartRoutes from './routes/cart';
import commentRoutes from './routes/comments';
import cmsRoutes from './routes/cms';
import analyticsRoutes from './routes/analytics';
import uploadRoutes from './routes/upload';

// 导入中间件
import { errorHandler } from './middleware/errorHandler';
import { logger } from './utils/logger';
import { authenticateToken } from './middleware/auth';

// 加载环境变量
dotenv.config();

const app = express();
const PORT = process.env.PORT || 8000;

// 初始化数据库连接
export const prisma = new PrismaClient();

// 初始化Redis连接
export const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD || undefined,
  retryDelayOnFailover: 100,
  maxRetriesPerRequest: 3,
});

// 基础中间件
app.use(helmet()); // 安全头
app.use(compression()); // 压缩响应
app.use(cors({
  origin: process.env.NODE_ENV === 'production' 
    ? ['https://yourdomain.com'] 
    : ['http://localhost:3000'],
  credentials: true
}));

// 限流中间件
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW || '15') * 60 * 1000, // 15分钟
  max: parseInt(process.env.RATE_LIMIT_MAX || '100'), // 限制每个IP 100次请求
  message: {
    error: '请求过于频繁，请稍后再试'
  }
});
app.use('/api', limiter);

// 解析中间件
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 静态文件服务
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// 请求日志
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path} - ${req.ip}`);
  next();
});

// API路由
app.use('/api/auth', authRoutes);
app.use('/api/users', authenticateToken, userRoutes);
app.use('/api/products', productRoutes);
app.use('/api/orders', authenticateToken, orderRoutes);
app.use('/api/cart', authenticateToken, cartRoutes);
app.use('/api/comments', commentRoutes);
app.use('/api/cms', cmsRoutes);
app.use('/api/analytics', analyticsRoutes);
app.use('/api/upload', authenticateToken, uploadRoutes);

// 健康检查
app.get('/health', async (req, res) => {
  try {
    // 检查数据库连接
    await prisma.$queryRaw`SELECT 1`;
    
    // 检查Redis连接
    await redis.ping();
    
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      database: 'connected',
      redis: 'connected'
    });
  } catch (error) {
    logger.error('Health check failed:', error);
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: 'Service unavailable'
    });
  }
});

// API文档
app.get('/api-docs', (req, res) => {
  res.json({
    title: '网站系统 API 文档',
    version: '1.0.0',
    description: '完整的网站系统API接口文档',
    endpoints: {
      auth: '/api/auth - 用户认证相关接口',
      users: '/api/users - 用户管理接口',
      products: '/api/products - 产品管理接口',
      orders: '/api/orders - 订单管理接口',
      cart: '/api/cart - 购物车接口',
      comments: '/api/comments - 评论接口',
      cms: '/api/cms - 内容管理接口',
      analytics: '/api/analytics - 数据分析接口',
      upload: '/api/upload - 文件上传接口'
    }
  });
});

// 404处理
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'API接口不存在',
    path: req.originalUrl
  });
});

// 错误处理中间件
app.use(errorHandler);

// 优雅关闭
process.on('SIGTERM', async () => {
  logger.info('收到SIGTERM信号，开始优雅关闭...');
  
  // 关闭数据库连接
  await prisma.$disconnect();
  
  // 关闭Redis连接
  redis.disconnect();
  
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('收到SIGINT信号，开始优雅关闭...');
  
  await prisma.$disconnect();
  redis.disconnect();
  
  process.exit(0);
});

// 启动服务器
app.listen(PORT, () => {
  logger.info(`服务器启动成功，端口: ${PORT}`);
  logger.info(`API文档: http://localhost:${PORT}/api-docs`);
  logger.info(`健康检查: http://localhost:${PORT}/health`);
});

export default app;