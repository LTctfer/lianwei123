#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { BrowserManager } from './browser/manager.js';
import { 
  NavigateArgsSchema,
  ClickArgsSchema,
  TypeArgsSchema,
  ScreenshotArgsSchema,
  GetTextArgsSchema,
  GetAttributeArgsSchema,
  ToolResponse
} from './types/index.js';

class MCPBrowserServer {
  private server: Server;
  private browserManager: BrowserManager;

  constructor() {
    this.server = new Server(
      {
        name: 'mcp-browser-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.browserManager = new BrowserManager();
    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  private setupToolHandlers() {
    // 列出所有可用工具
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'browser_navigate',
            description: '导航到指定URL',
            inputSchema: {
              type: 'object',
              properties: {
                url: {
                  type: 'string',
                  format: 'uri',
                  description: '要导航到的URL地址'
                },
                waitUntil: {
                  type: 'string',
                  enum: ['load', 'domcontentloaded', 'networkidle'],
                  default: 'load',
                  description: '等待页面加载状态'
                }
              },
              required: ['url']
            }
          },
          {
            name: 'browser_click',
            description: '点击页面元素',
            inputSchema: {
              type: 'object',
              properties: {
                selector: {
                  type: 'string',
                  description: 'CSS选择器或XPath'
                },
                timeout: {
                  type: 'number',
                  default: 5000,
                  description: '超时时间（毫秒）'
                },
                force: {
                  type: 'boolean',
                  default: false,
                  description: '是否强制点击'
                }
              },
              required: ['selector']
            }
          },
          {
            name: 'browser_type',
            description: '在元素中输入文本',
            inputSchema: {
              type: 'object',
              properties: {
                selector: {
                  type: 'string',
                  description: 'CSS选择器或XPath'
                },
                text: {
                  type: 'string',
                  description: '要输入的文本'
                },
                delay: {
                  type: 'number',
                  default: 0,
                  description: '输入延迟（毫秒）'
                },
                clear: {
                  type: 'boolean',
                  default: true,
                  description: '是否先清空输入框'
                }
              },
              required: ['selector', 'text']
            }
          },
          {
            name: 'browser_screenshot',
            description: '截取页面截图',
            inputSchema: {
              type: 'object',
              properties: {
                fullPage: {
                  type: 'boolean',
                  default: false,
                  description: '是否截取整个页面'
                },
                quality: {
                  type: 'number',
                  minimum: 0,
                  maximum: 100,
                  default: 80,
                  description: '图片质量（0-100）'
                },
                type: {
                  type: 'string',
                  enum: ['png', 'jpeg'],
                  default: 'png',
                  description: '图片格式'
                }
              }
            }
          },
          {
            name: 'browser_get_text',
            description: '获取元素文本内容',
            inputSchema: {
              type: 'object',
              properties: {
                selector: {
                  type: 'string',
                  description: 'CSS选择器或XPath'
                },
                timeout: {
                  type: 'number',
                  default: 5000,
                  description: '超时时间（毫秒）'
                }
              },
              required: ['selector']
            }
          },
          {
            name: 'browser_get_attribute',
            description: '获取元素属性值',
            inputSchema: {
              type: 'object',
              properties: {
                selector: {
                  type: 'string',
                  description: 'CSS选择器或XPath'
                },
                attribute: {
                  type: 'string',
                  description: '属性名称'
                },
                timeout: {
                  type: 'number',
                  default: 5000,
                  description: '超时时间（毫秒）'
                }
              },
              required: ['selector', 'attribute']
            }
          },
          {
            name: 'browser_back',
            description: '浏览器后退',
            inputSchema: {
              type: 'object',
              properties: {}
            }
          },
          {
            name: 'browser_forward',
            description: '浏览器前进',
            inputSchema: {
              type: 'object',
              properties: {}
            }
          },
          {
            name: 'browser_refresh',
            description: '刷新页面',
            inputSchema: {
              type: 'object',
              properties: {}
            }
          }
        ] as Tool[]
      };
    });

    // 处理工具调用
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        let result: ToolResponse;

        switch (name) {
          case 'browser_navigate':
            const navigateArgs = NavigateArgsSchema.parse(args);
            result = await this.browserManager.navigate(navigateArgs);
            break;

          case 'browser_click':
            const clickArgs = ClickArgsSchema.parse(args);
            result = await this.browserManager.click(clickArgs);
            break;

          case 'browser_type':
            const typeArgs = TypeArgsSchema.parse(args);
            result = await this.browserManager.type(typeArgs);
            break;

          case 'browser_screenshot':
            const screenshotArgs = ScreenshotArgsSchema.parse(args);
            result = await this.browserManager.screenshot(screenshotArgs);
            break;

          case 'browser_get_text':
            const getTextArgs = GetTextArgsSchema.parse(args);
            result = await this.browserManager.getText(getTextArgs);
            break;

          case 'browser_get_attribute':
            const getAttributeArgs = GetAttributeArgsSchema.parse(args);
            result = await this.browserManager.getAttribute(getAttributeArgs);
            break;

          case 'browser_back':
            result = await this.browserManager.back();
            break;

          case 'browser_forward':
            result = await this.browserManager.forward();
            break;

          case 'browser_refresh':
            result = await this.browserManager.refresh();
            break;

          default:
            throw new Error(`未知工具: ${name}`);
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2)
            }
          ]
        };

      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: false,
                error: errorMessage,
                timestamp: new Date().toISOString()
              }, null, 2)
            }
          ],
          isError: true
        };
      }
    });
  }

  private setupErrorHandling() {
    this.server.onerror = (error) => {
      console.error('[MCP服务器错误]', error);
    };

    process.on('SIGINT', async () => {
      await this.cleanup();
      process.exit(0);
    });

    process.on('SIGTERM', async () => {
      await this.cleanup();
      process.exit(0);
    });
  }

  private async cleanup() {
    console.log('正在清理资源...');
    await this.browserManager.cleanup();
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('MCP浏览器服务器已启动');
  }
}

// 启动服务器
const server = new MCPBrowserServer();
server.run().catch(console.error);