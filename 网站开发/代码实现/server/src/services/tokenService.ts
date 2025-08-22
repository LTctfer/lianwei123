import jwt from 'jsonwebtoken';
import { CustomError } from '../middleware/errorHandler';

export class TokenService {
  private readonly jwtSecret: string;
  private readonly accessTokenExpiry: string;
  private readonly refreshTokenExpiry: string;

  constructor() {
    this.jwtSecret = process.env.JWT_SECRET || 'your-super-secret-jwt-key';
    this.accessTokenExpiry = process.env.JWT_EXPIRES_IN || '1h';
    this.refreshTokenExpiry = '7d';
  }

  // 生成访问令牌和刷新令牌
  generateTokens(userId: number): { accessToken: string; refreshToken: string } {
    const payload = { userId, type: 'access' };
    
    const accessToken = jwt.sign(payload, this.jwtSecret, {
      expiresIn: this.accessTokenExpiry,
      issuer: 'website-system',
      audience: 'website-users'
    });

    const refreshPayload = { userId, type: 'refresh' };
    const refreshToken = jwt.sign(refreshPayload, this.jwtSecret, {
      expiresIn: this.refreshTokenExpiry,
      issuer: 'website-system',
      audience: 'website-users'
    });

    return { accessToken, refreshToken };
  }

  // 生成邮箱验证令牌
  generateEmailVerificationToken(userId: number): string {
    const payload = { userId, type: 'email_verification' };
    
    return jwt.sign(payload, this.jwtSecret, {
      expiresIn: '24h',
      issuer: 'website-system',
      audience: 'website-users'
    });
  }

  // 生成密码重置令牌
  generatePasswordResetToken(userId: number): string {
    const payload = { userId, type: 'password_reset' };
    
    return jwt.sign(payload, this.jwtSecret, {
      expiresIn: '15m',
      issuer: 'website-system',
      audience: 'website-users'
    });
  }

  // 验证令牌
  verifyToken(token: string): any {
    try {
      return jwt.verify(token, this.jwtSecret, {
        issuer: 'website-system',
        audience: 'website-users'
      });
    } catch (error) {
      if (error instanceof jwt.TokenExpiredError) {
        throw new CustomError('令牌已过期', 401);
      }
      if (error instanceof jwt.JsonWebTokenError) {
        throw new CustomError('无效的令牌', 401);
      }
      throw error;
    }
  }

  // 解码令牌（不验证）
  decodeToken(token: string): any {
    return jwt.decode(token);
  }

  // 获取令牌剩余有效时间（秒）
  getTokenRemainingTime(token: string): number {
    try {
      const decoded = this.decodeToken(token);
      if (!decoded || !decoded.exp) {
        return 0;
      }
      
      const currentTime = Math.floor(Date.now() / 1000);
      const remainingTime = decoded.exp - currentTime;
      
      return Math.max(0, remainingTime);
    } catch (error) {
      return 0;
    }
  }

  // 检查令牌是否即将过期（30分钟内）
  isTokenExpiringSoon(token: string): boolean {
    const remainingTime = this.getTokenRemainingTime(token);
    return remainingTime > 0 && remainingTime < 30 * 60; // 30分钟
  }
}