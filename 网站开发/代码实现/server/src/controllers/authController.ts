import { Request, Response } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { PrismaClient } from '@prisma/client';
import { CustomError } from '../middleware/errorHandler';
import { logger } from '../utils/logger';
import { EmailService } from '../services/emailService';
import { TokenService } from '../services/tokenService';
import { redis } from '../app';

const prisma = new PrismaClient();
const emailService = new EmailService();
const tokenService = new TokenService();

export class AuthController {
  // 用户注册
  async register(req: Request, res: Response): Promise<void> {
    const { username, email, password, phone } = req.body;

    try {
      // 检查用户是否已存在
      const existingUser = await prisma.user.findFirst({
        where: {
          OR: [
            { email },
            { username }
          ]
        }
      });

      if (existingUser) {
        if (existingUser.email === email) {
          throw new CustomError('邮箱已被注册', 409);
        }
        if (existingUser.username === username) {
          throw new CustomError('用户名已被使用', 409);
        }
      }

      // 加密密码
      const saltRounds = parseInt(process.env.BCRYPT_ROUNDS || '12');
      const hashedPassword = await bcrypt.hash(password, saltRounds);

      // 创建用户
      const user = await prisma.user.create({
        data: {
          username,
          email,
          password: hashedPassword,
          phone,
          status: 'ACTIVE'
        },
        select: {
          id: true,
          username: true,
          email: true,
          phone: true,
          role: true,
          status: true,
          emailVerified: true,
          createdAt: true
        }
      });

      // 生成邮箱验证令牌
      const verificationToken = tokenService.generateEmailVerificationToken(user.id);
      
      // 发送验证邮件
      await emailService.sendVerificationEmail(email, username, verificationToken);

      // 生成访问令牌
      const { accessToken, refreshToken } = tokenService.generateTokens(user.id);

      // 存储刷新令牌到Redis
      await redis.setex(`refresh_token:${user.id}`, 7 * 24 * 60 * 60, refreshToken);

      logger.info(`用户注册成功: ${email}`);

      res.status(201).json({
        success: true,
        message: '注册成功，请查收验证邮件',
        data: {
          user,
          accessToken,
          refreshToken
        }
      });
    } catch (error) {
      logger.error('用户注册失败:', error);
      throw error;
    }
  }

  // 用户登录
  async login(req: Request, res: Response): Promise<void> {
    const { email, password } = req.body;

    try {
      // 查找用户
      const user = await prisma.user.findUnique({
        where: { email },
        include: {
          profile: true
        }
      });

      if (!user) {
        throw new CustomError('邮箱或密码错误', 401);
      }

      // 检查用户状态
      if (user.status === 'BANNED') {
        throw new CustomError('账户已被封禁', 403);
      }

      if (user.status === 'INACTIVE') {
        throw new CustomError('账户已被停用', 403);
      }

      // 验证密码
      const isPasswordValid = await bcrypt.compare(password, user.password);
      if (!isPasswordValid) {
        throw new CustomError('邮箱或密码错误', 401);
      }

      // 生成访问令牌
      const { accessToken, refreshToken } = tokenService.generateTokens(user.id);

      // 存储刷新令牌到Redis
      await redis.setex(`refresh_token:${user.id}`, 7 * 24 * 60 * 60, refreshToken);

      // 更新最后登录时间
      await prisma.user.update({
        where: { id: user.id },
        data: { updatedAt: new Date() }
      });

      // 返回用户信息（不包含密码）
      const { password: _, ...userWithoutPassword } = user;

      logger.info(`用户登录成功: ${email}`);

      res.json({
        success: true,
        message: '登录成功',
        data: {
          user: userWithoutPassword,
          accessToken,
          refreshToken
        }
      });
    } catch (error) {
      logger.error('用户登录失败:', error);
      throw error;
    }
  }

  // 用户登出
  async logout(req: Request, res: Response): Promise<void> {
    try {
      const userId = (req as any).user?.id;
      
      if (userId) {
        // 删除Redis中的刷新令牌
        await redis.del(`refresh_token:${userId}`);
        
        // 将访问令牌加入黑名单
        const token = req.headers.authorization?.replace('Bearer ', '');
        if (token) {
          const decoded = jwt.decode(token) as any;
          const expiresIn = decoded.exp - Math.floor(Date.now() / 1000);
          if (expiresIn > 0) {
            await redis.setex(`blacklist:${token}`, expiresIn, 'true');
          }
        }
      }

      res.json({
        success: true,
        message: '登出成功'
      });
    } catch (error) {
      logger.error('用户登出失败:', error);
      throw error;
    }
  }

  // 刷新访问令牌
  async refreshToken(req: Request, res: Response): Promise<void> {
    const { refreshToken } = req.body;

    try {
      if (!refreshToken) {
        throw new CustomError('刷新令牌不能为空', 400);
      }

      // 验证刷新令牌
      const decoded = jwt.verify(refreshToken, process.env.JWT_SECRET!) as any;
      const userId = decoded.userId;

      // 检查Redis中的刷新令牌
      const storedToken = await redis.get(`refresh_token:${userId}`);
      if (storedToken !== refreshToken) {
        throw new CustomError('刷新令牌无效', 401);
      }

      // 检查用户是否存在
      const user = await prisma.user.findUnique({
        where: { id: userId },
        select: {
          id: true,
          username: true,
          email: true,
          role: true,
          status: true
        }
      });

      if (!user || user.status !== 'ACTIVE') {
        throw new CustomError('用户不存在或已被禁用', 401);
      }

      // 生成新的访问令牌
      const { accessToken, refreshToken: newRefreshToken } = tokenService.generateTokens(userId);

      // 更新Redis中的刷新令牌
      await redis.setex(`refresh_token:${userId}`, 7 * 24 * 60 * 60, newRefreshToken);

      res.json({
        success: true,
        message: '令牌刷新成功',
        data: {
          accessToken,
          refreshToken: newRefreshToken
        }
      });
    } catch (error) {
      logger.error('刷新令牌失败:', error);
      if (error instanceof jwt.JsonWebTokenError) {
        throw new CustomError('刷新令牌无效', 401);
      }
      throw error;
    }
  }

  // 忘记密码
  async forgotPassword(req: Request, res: Response): Promise<void> {
    const { email } = req.body;

    try {
      const user = await prisma.user.findUnique({
        where: { email }
      });

      if (!user) {
        throw new CustomError('用户不存在', 404);
      }

      // 生成重置密码令牌
      const resetToken = tokenService.generatePasswordResetToken(user.id);

      // 存储重置令牌到Redis（15分钟有效期）
      await redis.setex(`reset_token:${user.id}`, 15 * 60, resetToken);

      // 发送重置密码邮件
      await emailService.sendPasswordResetEmail(email, user.username, resetToken);

      logger.info(`密码重置邮件已发送: ${email}`);

      res.json({
        success: true,
        message: '重置密码邮件已发送，请查收邮件'
      });
    } catch (error) {
      logger.error('发送重置密码邮件失败:', error);
      throw error;
    }
  }

  // 重置密码
  async resetPassword(req: Request, res: Response): Promise<void> {
    const { token, password, confirmPassword } = req.body;

    try {
      if (password !== confirmPassword) {
        throw new CustomError('两次输入的密码不一致', 400);
      }

      // 验证重置令牌
      const decoded = jwt.verify(token, process.env.JWT_SECRET!) as any;
      const userId = decoded.userId;

      // 检查Redis中的重置令牌
      const storedToken = await redis.get(`reset_token:${userId}`);
      if (storedToken !== token) {
        throw new CustomError('重置令牌无效或已过期', 400);
      }

      // 加密新密码
      const saltRounds = parseInt(process.env.BCRYPT_ROUNDS || '12');
      const hashedPassword = await bcrypt.hash(password, saltRounds);

      // 更新用户密码
      await prisma.user.update({
        where: { id: userId },
        data: { password: hashedPassword }
      });

      // 删除重置令牌
      await redis.del(`reset_token:${userId}`);

      // 删除所有刷新令牌（强制重新登录）
      await redis.del(`refresh_token:${userId}`);

      logger.info(`用户密码重置成功: ${userId}`);

      res.json({
        success: true,
        message: '密码重置成功，请重新登录'
      });
    } catch (error) {
      logger.error('重置密码失败:', error);
      if (error instanceof jwt.JsonWebTokenError) {
        throw new CustomError('重置令牌无效或已过期', 400);
      }
      throw error;
    }
  }

  // 验证邮箱
  async verifyEmail(req: Request, res: Response): Promise<void> {
    const { token } = req.body;

    try {
      // 验证邮箱验证令牌
      const decoded = jwt.verify(token, process.env.JWT_SECRET!) as any;
      const userId = decoded.userId;

      // 更新用户邮箱验证状态
      const user = await prisma.user.update({
        where: { id: userId },
        data: { emailVerified: true },
        select: {
          id: true,
          username: true,
          email: true,
          emailVerified: true
        }
      });

      logger.info(`用户邮箱验证成功: ${user.email}`);

      res.json({
        success: true,
        message: '邮箱验证成功',
        data: { user }
      });
    } catch (error) {
      logger.error('邮箱验证失败:', error);
      if (error instanceof jwt.JsonWebTokenError) {
        throw new CustomError('验证令牌无效或已过期', 400);
      }
      throw error;
    }
  }
}