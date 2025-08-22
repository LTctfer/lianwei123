import nodemailer from 'nodemailer';
import { logger } from '../utils/logger';

export class EmailService {
  private transporter: nodemailer.Transporter;

  constructor() {
    this.transporter = nodemailer.createTransporter({
      host: process.env.SMTP_HOST || 'smtp.gmail.com',
      port: parseInt(process.env.SMTP_PORT || '587'),
      secure: false, // true for 465, false for other ports
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS,
      },
    });
  }

  // 发送邮箱验证邮件
  async sendVerificationEmail(email: string, username: string, token: string): Promise<void> {
    const verificationUrl = `${process.env.FRONTEND_URL}/verify-email?token=${token}`;
    
    const mailOptions = {
      from: `"${process.env.APP_NAME || '网站系统'}" <${process.env.SMTP_USER}>`,
      to: email,
      subject: '邮箱验证 - 请验证您的邮箱地址',
      html: `
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
          <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #333; margin-bottom: 10px;">邮箱验证</h1>
            <p style="color: #666; font-size: 16px;">感谢您注册我们的服务！</p>
          </div>
          
          <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <p style="margin: 0 0 15px 0; color: #333;">亲爱的 ${username}，</p>
            <p style="margin: 0 0 15px 0; color: #333;">
              为了确保您的账户安全，请点击下面的按钮验证您的邮箱地址：
            </p>
            
            <div style="text-align: center; margin: 25px 0;">
              <a href="${verificationUrl}" 
                 style="display: inline-block; padding: 12px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                验证邮箱
              </a>
            </div>
            
            <p style="margin: 15px 0 0 0; color: #666; font-size: 14px;">
              如果按钮无法点击，请复制以下链接到浏览器地址栏：<br>
              <a href="${verificationUrl}" style="color: #007bff; word-break: break-all;">${verificationUrl}</a>
            </p>
          </div>
          
          <div style="border-top: 1px solid #eee; padding-top: 20px; color: #666; font-size: 12px;">
            <p>此验证链接将在24小时后失效。</p>
            <p>如果您没有注册此账户，请忽略此邮件。</p>
            <p style="margin-top: 20px;">
              此邮件由系统自动发送，请勿回复。<br>
              如有疑问，请联系客服。
            </p>
          </div>
        </div>
      `
    };

    try {
      await this.transporter.sendMail(mailOptions);
      logger.info(`邮箱验证邮件已发送: ${email}`);
    } catch (error) {
      logger.error('发送邮箱验证邮件失败:', error);
      throw new Error('发送验证邮件失败');
    }
  }

  // 发送密码重置邮件
  async sendPasswordResetEmail(email: string, username: string, token: string): Promise<void> {
    const resetUrl = `${process.env.FRONTEND_URL}/reset-password?token=${token}`;
    
    const mailOptions = {
      from: `"${process.env.APP_NAME || '网站系统'}" <${process.env.SMTP_USER}>`,
      to: email,
      subject: '密码重置 - 重置您的账户密码',
      html: `
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
          <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #333; margin-bottom: 10px;">密码重置</h1>
            <p style="color: #666; font-size: 16px;">我们收到了您的密码重置请求</p>
          </div>
          
          <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <p style="margin: 0 0 15px 0; color: #333;">亲爱的 ${username}，</p>
            <p style="margin: 0 0 15px 0; color: #333;">
              我们收到了您的密码重置请求。如果这是您本人的操作，请点击下面的按钮重置密码：
            </p>
            
            <div style="text-align: center; margin: 25px 0;">
              <a href="${resetUrl}" 
                 style="display: inline-block; padding: 12px 30px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                重置密码
              </a>
            </div>
            
            <p style="margin: 15px 0 0 0; color: #666; font-size: 14px;">
              如果按钮无法点击，请复制以下链接到浏览器地址栏：<br>
              <a href="${resetUrl}" style="color: #dc3545; word-break: break-all;">${resetUrl}</a>
            </p>
          </div>
          
          <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p style="margin: 0; color: #856404; font-size: 14px;">
              <strong>安全提醒：</strong>此重置链接将在15分钟后失效。如果您没有请求重置密码，请忽略此邮件，您的账户仍然安全。
            </p>
          </div>
          
          <div style="border-top: 1px solid #eee; padding-top: 20px; color: #666; font-size: 12px;">
            <p>为了您的账户安全，请不要将此链接分享给他人。</p>
            <p style="margin-top: 20px;">
              此邮件由系统自动发送，请勿回复。<br>
              如有疑问，请联系客服。
            </p>
          </div>
        </div>
      `
    };

    try {
      await this.transporter.sendMail(mailOptions);
      logger.info(`密码重置邮件已发送: ${email}`);
    } catch (error) {
      logger.error('发送密码重置邮件失败:', error);
      throw new Error('发送重置邮件失败');
    }
  }

  // 发送欢迎邮件
  async sendWelcomeEmail(email: string, username: string): Promise<void> {
    const mailOptions = {
      from: `"${process.env.APP_NAME || '网站系统'}" <${process.env.SMTP_USER}>`,
      to: email,
      subject: '欢迎加入我们！',
      html: `
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
          <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #333; margin-bottom: 10px;">欢迎加入我们！</h1>
            <p style="color: #666; font-size: 16px;">感谢您成为我们的用户</p>
          </div>
          
          <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <p style="margin: 0 0 15px 0; color: #333;">亲爱的 ${username}，</p>
            <p style="margin: 0 0 15px 0; color: #333;">
              欢迎加入我们的平台！您的账户已经成功创建并验证。
            </p>
            <p style="margin: 0 0 15px 0; color: #333;">
              现在您可以开始探索我们的各种功能和服务了。
            </p>
            
            <div style="text-align: center; margin: 25px 0;">
              <a href="${process.env.FRONTEND_URL}" 
                 style="display: inline-block; padding: 12px 30px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                开始使用
              </a>
            </div>
          </div>
          
          <div style="border-top: 1px solid #eee; padding-top: 20px; color: #666; font-size: 12px;">
            <p>如果您在使用过程中遇到任何问题，请随时联系我们的客服团队。</p>
            <p style="margin-top: 20px;">
              此邮件由系统自动发送，请勿回复。<br>
              如有疑问，请联系客服。
            </p>
          </div>
        </div>
      `
    };

    try {
      await this.transporter.sendMail(mailOptions);
      logger.info(`欢迎邮件已发送: ${email}`);
    } catch (error) {
      logger.error('发送欢迎邮件失败:', error);
      throw new Error('发送欢迎邮件失败');
    }
  }

  // 测试邮件配置
  async testConnection(): Promise<boolean> {
    try {
      await this.transporter.verify();
      logger.info('邮件服务连接测试成功');
      return true;
    } catch (error) {
      logger.error('邮件服务连接测试失败:', error);
      return false;
    }
  }
}