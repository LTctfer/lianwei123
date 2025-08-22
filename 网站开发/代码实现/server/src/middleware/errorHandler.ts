import { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger';

export interface AppError extends Error {
  statusCode?: number;
  isOperational?: boolean;
}

export class CustomError extends Error implements AppError {
  statusCode: number;
  isOperational: boolean;

  constructor(message: string, statusCode: number = 500) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = true;

    Error.captureStackTrace(this, this.constructor);
  }
}

export const createError = (message: string, statusCode: number = 500): CustomError => {
  return new CustomError(message, statusCode);
};

export const errorHandler = (
  error: AppError,
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  let { statusCode = 500, message } = error;

  // 记录错误日志
  logger.error({
    error: {
      message: error.message,
      stack: error.stack,
      statusCode
    },
    request: {
      method: req.method,
      url: req.url,
      ip: req.ip,
      userAgent: req.get('User-Agent')
    }
  });

  // Prisma错误处理
  if (error.name === 'PrismaClientKnownRequestError') {
    const prismaError = error as any;
    switch (prismaError.code) {
      case 'P2002':
        statusCode = 409;
        message = '数据已存在，请检查唯一字段';
        break;
      case 'P2025':
        statusCode = 404;
        message = '记录不存在';
        break;
      case 'P2003':
        statusCode = 400;
        message = '外键约束失败';
        break;
      default:
        statusCode = 400;
        message = '数据库操作失败';
    }
  }

  // JWT错误处理
  if (error.name === 'JsonWebTokenError') {
    statusCode = 401;
    message = '无效的访问令牌';
  }

  if (error.name === 'TokenExpiredError') {
    statusCode = 401;
    message = '访问令牌已过期';
  }

  // 验证错误处理
  if (error.name === 'ValidationError') {
    statusCode = 400;
    message = '数据验证失败';
  }

  // 生产环境不暴露详细错误信息
  if (process.env.NODE_ENV === 'production' && !error.isOperational) {
    message = '服务器内部错误';
  }

  res.status(statusCode).json({
    success: false,
    error: {
      message,
      ...(process.env.NODE_ENV === 'development' && {
        stack: error.stack,
        details: error
      })
    },
    timestamp: new Date().toISOString(),
    path: req.path
  });
};

// 异步错误处理包装器
export const asyncHandler = (fn: Function) => {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};

// 404错误处理
export const notFound = (req: Request, res: Response, next: NextFunction) => {
  const error = new CustomError(`路径 ${req.originalUrl} 不存在`, 404);
  next(error);
};