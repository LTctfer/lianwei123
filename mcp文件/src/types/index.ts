import { z } from 'zod';

// 浏览器配置类型
export const BrowserConfigSchema = z.object({
  headless: z.boolean().default(true),
  viewport: z.object({
    width: z.number().default(1280),
    height: z.number().default(720)
  }).optional(),
  timeout: z.number().default(30000),
  userAgent: z.string().optional()
});

export type BrowserConfig = z.infer<typeof BrowserConfigSchema>;

// 导航工具参数
export const NavigateArgsSchema = z.object({
  url: z.string().url(),
  waitUntil: z.enum(['load', 'domcontentloaded', 'networkidle']).default('load')
});

export type NavigateArgs = z.infer<typeof NavigateArgsSchema>;

// 点击工具参数
export const ClickArgsSchema = z.object({
  selector: z.string(),
  timeout: z.number().default(5000),
  force: z.boolean().default(false)
});

export type ClickArgs = z.infer<typeof ClickArgsSchema>;

// 输入工具参数
export const TypeArgsSchema = z.object({
  selector: z.string(),
  text: z.string(),
  delay: z.number().default(0),
  clear: z.boolean().default(true)
});

export type TypeArgs = z.infer<typeof TypeArgsSchema>;

// 截图工具参数
export const ScreenshotArgsSchema = z.object({
  fullPage: z.boolean().default(false),
  quality: z.number().min(0).max(100).default(80),
  type: z.enum(['png', 'jpeg']).default('png')
});

export type ScreenshotArgs = z.infer<typeof ScreenshotArgsSchema>;

// 获取文本工具参数
export const GetTextArgsSchema = z.object({
  selector: z.string(),
  timeout: z.number().default(5000)
});

export type GetTextArgs = z.infer<typeof GetTextArgsSchema>;

// 获取属性工具参数
export const GetAttributeArgsSchema = z.object({
  selector: z.string(),
  attribute: z.string(),
  timeout: z.number().default(5000)
});

export type GetAttributeArgs = z.infer<typeof GetAttributeArgsSchema>;

// 工具响应类型
export interface ToolResponse {
  success: boolean;
  data?: any;
  error?: string;
  timestamp: string;
}

// 浏览器会话状态
export interface BrowserSession {
  id: string;
  browser: any;
  page: any;
  createdAt: Date;
  lastUsed: Date;
}