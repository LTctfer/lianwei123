import { chromium, Browser, Page, BrowserContext } from 'playwright';
import {
  BrowserConfig,
  BrowserSession,
  NavigateArgs,
  ClickArgs,
  TypeArgs,
  ScreenshotArgs,
  GetTextArgs,
  GetAttributeArgs,
  ToolResponse
} from '../types/index.js';

export class BrowserManager {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;
  private session: BrowserSession | null = null;

  constructor(private config: BrowserConfig = {
    headless: true,
    viewport: { width: 1280, height: 720 },
    timeout: 30000
  }) {}

  private async ensureBrowser(): Promise<void> {
    if (!this.browser) {
      this.browser = await chromium.launch({
        headless: this.config.headless,
        timeout: this.config.timeout
      });

      this.context = await this.browser.newContext({
        viewport: this.config.viewport,
        userAgent: this.config.userAgent
      });

      this.page = await this.context.newPage();
      
      // 设置默认超时
      this.page.setDefaultTimeout(this.config.timeout);
      this.page.setDefaultNavigationTimeout(this.config.timeout);

      this.session = {
        id: `session_${Date.now()}`,
        browser: this.browser,
        page: this.page,
        createdAt: new Date(),
        lastUsed: new Date()
      };

      console.error(`浏览器会话已创建: ${this.session.id}`);
    }

    if (this.session) {
      this.session.lastUsed = new Date();
    }
  }

  async navigate(args: NavigateArgs): Promise<ToolResponse> {
    try {
      await this.ensureBrowser();
      
      if (!this.page) {
        throw new Error('页面未初始化');
      }

      console.error(`导航到: ${args.url}`);
      await this.page.goto(args.url, { 
        waitUntil: args.waitUntil,
        timeout: this.config.timeout 
      });

      const currentUrl = this.page.url();
      const title = await this.page.title();

      return {
        success: true,
        data: {
          url: currentUrl,
          title: title,
          message: `成功导航到 ${currentUrl}`
        },
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      return {
        success: false,
        error: `导航失败: ${error instanceof Error ? error.message : String(error)}`,
        timestamp: new Date().toISOString()
      };
    }
  }

  async click(args: ClickArgs): Promise<ToolResponse> {
    try {
      await this.ensureBrowser();
      
      if (!this.page) {
        throw new Error('页面未初始化');
      }

      console.error(`点击元素: ${args.selector}`);
      
      // 等待元素可见
      await this.page.waitForSelector(args.selector, { 
        timeout: args.timeout,
        state: 'visible'
      });

      // 执行点击
      await this.page.click(args.selector, { 
        force: args.force,
        timeout: args.timeout
      });

      return {
        success: true,
        data: {
          selector: args.selector,
          message: `成功点击元素 ${args.selector}`
        },
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      return {
        success: false,
        error: `点击失败: ${error instanceof Error ? error.message : String(error)}`,
        timestamp: new Date().toISOString()
      };
    }
  }

  async type(args: TypeArgs): Promise<ToolResponse> {
    try {
      await this.ensureBrowser();
      
      if (!this.page) {
        throw new Error('页面未初始化');
      }

      console.error(`在元素中输入文本: ${args.selector}`);
      
      // 等待元素可见
      await this.page.waitForSelector(args.selector, { 
        timeout: 5000,
        state: 'visible'
      });

      // 清空输入框（如果需要）
      if (args.clear) {
        await this.page.fill(args.selector, '');
      }

      // 输入文本
      await this.page.type(args.selector, args.text, { 
        delay: args.delay 
      });

      return {
        success: true,
        data: {
          selector: args.selector,
          text: args.text,
          message: `成功在 ${args.selector} 中输入文本`
        },
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      return {
        success: false,
        error: `输入失败: ${error instanceof Error ? error.message : String(error)}`,
        timestamp: new Date().toISOString()
      };
    }
  }

  async screenshot(args: ScreenshotArgs): Promise<ToolResponse> {
    try {
      await this.ensureBrowser();
      
      if (!this.page) {
        throw new Error('页面未初始化');
      }

      console.error('截取页面截图');
      
      const screenshot = await this.page.screenshot({
        fullPage: args.fullPage,
        quality: args.type === 'jpeg' ? args.quality : undefined,
        type: args.type
      });

      // 将截图转换为base64
      const base64Screenshot = screenshot.toString('base64');

      return {
        success: true,
        data: {
          screenshot: `data:image/${args.type};base64,${base64Screenshot}`,
          type: args.type,
          fullPage: args.fullPage,
          message: '截图成功'
        },
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      return {
        success: false,
        error: `截图失败: ${error instanceof Error ? error.message : String(error)}`,
        timestamp: new Date().toISOString()
      };
    }
  }

  async getText(args: GetTextArgs): Promise<ToolResponse> {
    try {
      await this.ensureBrowser();
      
      if (!this.page) {
        throw new Error('页面未初始化');
      }

      console.error(`获取元素文本: ${args.selector}`);
      
      // 等待元素存在
      await this.page.waitForSelector(args.selector, { 
        timeout: args.timeout 
      });

      const text = await this.page.textContent(args.selector);

      return {
        success: true,
        data: {
          selector: args.selector,
          text: text || '',
          message: `成功获取 ${args.selector} 的文本内容`
        },
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      return {
        success: false,
        error: `获取文本失败: ${error instanceof Error ? error.message : String(error)}`,
        timestamp: new Date().toISOString()
      };
    }
  }

  async getAttribute(args: GetAttributeArgs): Promise<ToolResponse> {
    try {
      await this.ensureBrowser();
      
      if (!this.page) {
        throw new Error('页面未初始化');
      }

      console.error(`获取元素属性: ${args.selector}.${args.attribute}`);
      
      // 等待元素存在
      await this.page.waitForSelector(args.selector, { 
        timeout: args.timeout 
      });

      const value = await this.page.getAttribute(args.selector, args.attribute);

      return {
        success: true,
        data: {
          selector: args.selector,
          attribute: args.attribute,
          value: value || '',
          message: `成功获取 ${args.selector} 的 ${args.attribute} 属性`
        },
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      return {
        success: false,
        error: `获取属性失败: ${error instanceof Error ? error.message : String(error)}`,
        timestamp: new Date().toISOString()
      };
    }
  }

  async back(): Promise<ToolResponse> {
    try {
      await this.ensureBrowser();
      
      if (!this.page) {
        throw new Error('页面未初始化');
      }

      console.error('浏览器后退');
      await this.page.goBack({ waitUntil: 'load' });

      return {
        success: true,
        data: {
          url: this.page.url(),
          message: '成功后退到上一页'
        },
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      return {
        success: false,
        error: `后退失败: ${error instanceof Error ? error.message : String(error)}`,
        timestamp: new Date().toISOString()
      };
    }
  }

  async forward(): Promise<ToolResponse> {
    try {
      await this.ensureBrowser();
      
      if (!this.page) {
        throw new Error('页面未初始化');
      }

      console.error('浏览器前进');
      await this.page.goForward({ waitUntil: 'load' });

      return {
        success: true,
        data: {
          url: this.page.url(),
          message: '成功前进到下一页'
        },
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      return {
        success: false,
        error: `前进失败: ${error instanceof Error ? error.message : String(error)}`,
        timestamp: new Date().toISOString()
      };
    }
  }

  async refresh(): Promise<ToolResponse> {
    try {
      await this.ensureBrowser();
      
      if (!this.page) {
        throw new Error('页面未初始化');
      }

      console.error('刷新页面');
      await this.page.reload({ waitUntil: 'load' });

      return {
        success: true,
        data: {
          url: this.page.url(),
          message: '页面刷新成功'
        },
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      return {
        success: false,
        error: `刷新失败: ${error instanceof Error ? error.message : String(error)}`,
        timestamp: new Date().toISOString()
      };
    }
  }

  async cleanup(): Promise<void> {
    try {
      if (this.page) {
        await this.page.close();
        this.page = null;
      }

      if (this.context) {
        await this.context.close();
        this.context = null;
      }

      if (this.browser) {
        await this.browser.close();
        this.browser = null;
      }

      this.session = null;
      console.error('浏览器资源已清理');

    } catch (error) {
      console.error('清理浏览器资源时出错:', error);
    }
  }
}