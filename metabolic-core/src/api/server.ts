/**
 * API Server - Express服务器
 * 启动HTTP服务，提供REST API访问
 */

import express from 'express';
import cors from 'cors';
import routes from './routes';

const app = express();
const PORT = process.env.PORT || 8002;

// 中间件
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// API路由
app.use('/api', routes);

// 根路由
app.get('/', (req, res) => {
  res.json({
    name: 'Metabolic Core API',
    project: '行健行为教练',
    version: '1.0.0',
    description: '代谢慢病行为健康决策系统内核',
    endpoints: {
      health: '/api/health',
      status: '/api/status',
      signals: 'POST /api/signals',
      dashboard: 'GET /api/dashboard/:userId',
      interventions: 'POST /api/interventions/generate',
      knowledge: 'GET /api/knowledge/search',
      phenotypes: 'GET /api/phenotypes',
      playbooks: 'GET /api/playbooks',
      content: 'GET /api/content',
      resources: 'GET /api/resources'
    }
  });
});

// OpenAPI工具描述（供Dify使用）
app.get('/openapi-tools.json', (req, res) => {
  res.json({
    openapi: '3.0.0',
    info: {
      title: 'Metabolic Core API',
      version: '1.0.0',
      description: '行健行为教练代谢慢病行为健康决策系统内核API'
    },
    servers: [
      { url: `http://localhost:${PORT}` }
    ],
    paths: {
      '/api/signals': {
        post: {
          operationId: 'processSignals',
          summary: '处理设备信号数据',
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  required: ['user_id', 'signals'],
                  properties: {
                    user_id: { type: 'string' },
                    signals: {
                      type: 'array',
                      items: {
                        type: 'object',
                        properties: {
                          device_type: { type: 'string' },
                          metric: { type: 'string' },
                          value: { type: 'number' },
                          timestamp: { type: 'string' }
                        }
                      }
                    }
                  }
                }
              }
            }
          },
          responses: {
            '200': { description: '信号处理结果' }
          }
        }
      },
      '/api/dashboard/{userId}': {
        get: {
          operationId: 'getDashboard',
          summary: '获取用户仪表盘',
          parameters: [
            {
              name: 'userId',
              in: 'path',
              required: true,
              schema: { type: 'string' }
            }
          ],
          responses: {
            '200': { description: '用户仪表盘数据' }
          }
        }
      },
      '/api/context/{userId}': {
        get: {
          operationId: 'getConversationContext',
          summary: '获取对话上下文',
          parameters: [
            {
              name: 'userId',
              in: 'path',
              required: true,
              schema: { type: 'string' }
            }
          ],
          responses: {
            '200': { description: '对话上下文数据' }
          }
        }
      },
      '/api/interventions/generate': {
        post: {
          operationId: 'generateIntervention',
          summary: '生成干预计划',
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  required: ['user_id'],
                  properties: {
                    user_id: { type: 'string' },
                    stage_indicators: {
                      type: 'object',
                      properties: {
                        awareness_score: { type: 'number' },
                        motivation_score: { type: 'number' },
                        self_efficacy_score: { type: 'number' },
                        action_frequency: { type: 'number' },
                        days_maintained: { type: 'number' }
                      }
                    }
                  }
                }
              }
            }
          },
          responses: {
            '200': { description: '干预计划摘要' }
          }
        }
      },
      '/api/knowledge/search': {
        get: {
          operationId: 'searchKnowledge',
          summary: '搜索知识库',
          parameters: [
            { name: 'keyword', in: 'query', schema: { type: 'string' } },
            { name: 'types', in: 'query', schema: { type: 'string' } },
            { name: 'tags', in: 'query', schema: { type: 'string' } },
            { name: 'limit', in: 'query', schema: { type: 'integer' } }
          ],
          responses: {
            '200': { description: '搜索结果' }
          }
        }
      },
      '/api/phenotypes': {
        get: {
          operationId: 'getPhenotypes',
          summary: '获取所有表型',
          responses: {
            '200': { description: '表型列表' }
          }
        }
      },
      '/api/playbooks': {
        get: {
          operationId: 'getPlaybooks',
          summary: '获取所有干预剧本',
          responses: {
            '200': { description: '剧本列表' }
          }
        }
      },
      '/api/content/recommend': {
        get: {
          operationId: 'recommendContent',
          summary: '推荐内容',
          parameters: [
            { name: 'stage', in: 'query', required: true, schema: { type: 'string' } },
            { name: 'phenotypes', in: 'query', schema: { type: 'string' } },
            { name: 'limit', in: 'query', schema: { type: 'integer' } }
          ],
          responses: {
            '200': { description: '推荐内容列表' }
          }
        }
      },
      '/api/resources/recommend': {
        get: {
          operationId: 'recommendResources',
          summary: '推荐商业资源',
          parameters: [
            { name: 'phenotypes', in: 'query', required: true, schema: { type: 'string' } },
            { name: 'limit', in: 'query', schema: { type: 'integer' } }
          ],
          responses: {
            '200': { description: '推荐资源列表' }
          }
        }
      }
    }
  });
});

// 错误处理
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Error:', err);
  res.status(500).json({
    success: false,
    error: 'Internal server error',
    message: err.message
  });
});

// 启动服务器
export function startServer(): void {
  app.listen(PORT, () => {
    console.log(`
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     行健行为教练 - Metabolic Core API                        ║
║                                                              ║
║     Server running on http://localhost:${PORT}                 ║
║                                                              ║
║     Endpoints:                                               ║
║     - Health:      GET  /api/health                          ║
║     - Status:      GET  /api/status                          ║
║     - Signals:     POST /api/signals                         ║
║     - Dashboard:   GET  /api/dashboard/:userId               ║
║     - Intervention: POST /api/interventions/generate         ║
║     - Knowledge:   GET  /api/knowledge/search                ║
║                                                              ║
║     OpenAPI:       GET  /openapi-tools.json                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    `);
  });
}

export { app };
