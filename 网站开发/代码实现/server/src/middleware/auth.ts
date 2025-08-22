import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { PrismaClient } from '@prisma/client';
import { logger } from '../utils/logger';

const prisma = new PrismaClient();

// 扩展Request接口以包含用户信息
declare global {
  namespace Express {
    interface Request {
      user?: {
        id: number;
        username: string;
        email: string;
        role: string;
      };
    }
  }
}

// JWT Token验证中间件
export const authenticateToken = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

    if (!token) {
      return res.status(401).json({
        error: '访问令牌缺失',
        code: 'TOKEN_MISSING'
      });
    }

    // 验证JWT token
    const decoded = jwt.verify(token, process.env.JWT_SECRET!) as any;
    
    // 从数据库获取用户信息
    const user = await prisma.user.findUnique({
      where: { id: decoded.userId },
      select: {
        id: true,
        username: true,
        email: true,
        role: true,
        status: true
      }
    });

    if (!user) {
      return res.status(401).json({
        error: '用户不存在',
        code: 'USER_NOT_FOUND'
      });
    }

    if (user.status !== 'ACTIVE') {
      return res.status(401).json({
        error: '账户已被禁用',
        code: 'ACCOUNT_DISABLED'
      });
    }

    // 将用户信息添加到请求对象
    req.user = {
      id: user.id,
      username: user.username,
      email: user.email,
      role: user.role
    };

    next();
  } catch (error) {
    logger.error('Token验证失败:', error);
    
    if (error instanceof jwt.JsonWebTokenError) {
      return res.status(401).json({
        error: '无效的访问令牌',
        code: 'INVALID_TOKEN'
      });
    }

    if (error instanceof jwt.TokenExpiredError) {
      return res.status(401).json({
        error: '访问令牌已过期',
        code: 'TOKEN_EXPIRED'
      });
    }

    return res.status(500).json({
      error: '服务器内部错误',
      code: 'INTERNAL_ERROR'
    });
  }
};

// 可选的Token验证中间件（用于不强制登录的接口）
export const optionalAuth = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (token) {
      const decoded = jwt.verify(token, process.env.JWT_SECRET!) as any;
      const user = await prisma.user.findUnique({
        where: { id: decoded.userId },
        select: {
          id: true,
          username: true,
          email: true,
          role: true,
          status: true
        }
      });

      if (user && user.status === 'ACTIVE') {
        req.user = {
          id: user.id,
          username: user.username,
          email: user.email,
          role: user.role
        };
      }
    }

    next();
  } catch (error) {
    // 可选认证失败时不返回错误，继续执行
    next();
  }
};

// 权限检查中间件
export const requireRole = (roles: string[]) => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({
        error: '需要登录',
        code: 'LOGIN_REQUIRED'
      });
    }

    if (!roles.includes(req.user.role)) {
      return res.status(403).json({
        error: '权限不足',
        code: 'INSUFFICIENT_PERMISSIONS'
      });
    }

    next();
  };
};

// 管理员权限检查
export const requireAdmin = requireRole(['ADMIN']);

// 版主权限检查
export const requireModerator = requireRole(['ADMIN', 'MODERATOR']);

// 资源所有者检查中间件
export const requireOwnership = (resourceField: string = 'userId') => {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (!req.user) {
        return res.status(401).json({
          error: '需要登录',
          code: 'LOGIN_REQUIRED'
        });
      }

      // 管理员可以访问所有资源
      if (req.user.role === 'ADMIN') {
        return next();
      }

      const resourceId = req.params.id;
      if (!resourceId) {
        return res.status(400).json({
          error: '资源ID缺失',
          code: 'RESOURCE_ID_MISSING'
        });
      }

      // 这里需要根据具体的资源类型来检查所有权
      // 示例：检查订单所有权
      if (req.route.path.includes('/orders/')) {
        const order = await prisma.order.findUnique({
          where: { id: parseInt(resourceId) },
          select: { userId: true }
        });

        if (!order || order.userId !== req.user.id) {
          return res.status(403).json({
            error: '无权访问此资源',
            code: 'ACCESS_DENIED'
          });
        }
      }

      next();
    } catch (error) {
      logger.error('所有权检查失败:', error);
      return res.status(500).json({
        error: '服务器内部错误',
        code: 'INTERNAL_ERROR'
      });
    }
  };
};

// API密钥验证中间件（用于第三方集成）
export const authenticateApiKey = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const apiKey = req.headers['x-api-key'] as string;

    if (!apiKey) {
      return res.status(401).json({
        error: 'API密钥缺失',
        code: 'API_KEY_MISSING'
      });
    }

    // 验证API密钥（这里可以从数据库或配置中验证）
    const validApiKeys = process.env.VALID_API_KEYS?.split(',') || [];
    
    if (!validApiKeys.includes(apiKey)) {
      return res.status(401).json({
        error: '无效的API密钥',
        code: 'INVALID_API_KEY'
      });
    }

    next();
  } catch (error) {
    logger.error('API密钥验证失败:', error);
    return res.status(500).json({
      error: '服务器内部错误',
      code: 'INTERNAL_ERROR'
    });
  }
};