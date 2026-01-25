/**
 * API Routes - REST API路由定义
 * 提供HTTP接口访问metabolic-core功能
 */

import express, { Request, Response, NextFunction } from 'express';
import { orchestrator } from '../orchestrator/Orchestrator';
import { RawSignalInput } from '../signal/SignalNormalizationService';
import { libraryManager } from '../registry/LibraryManager';
import { knowledgeRegistry } from '../registry/KnowledgeRegistry';
import { certificationService, LEVEL_REQUIREMENTS, PREDEFINED_COURSES, PREDEFINED_EXAMS } from '../certification/CertificationService';
import { promotionEngine } from '../certification/PromotionEngine';
import { CertificationLevel, SpecialtyTag } from '../certification/CertificationSchema';

const router = express.Router();

/**
 * 中间件：确保系统已初始化
 */
const ensureInitialized = async (req: Request, res: Response, next: NextFunction) => {
  try {
    await orchestrator.initialize();
    next();
  } catch (error) {
    res.status(503).json({
      success: false,
      error: 'System initialization failed',
      message: String(error)
    });
  }
};

router.use(ensureInitialized);

// ============ 系统状态 ============

/**
 * GET /api/status
 * 获取系统状态
 */
router.get('/status', (req: Request, res: Response) => {
  const status = orchestrator.getSystemStatus();
  res.json({
    success: true,
    data: status
  });
});

/**
 * GET /api/health
 * 健康检查
 */
router.get('/health', (req: Request, res: Response) => {
  res.json({
    success: true,
    status: 'healthy',
    timestamp: new Date().toISOString()
  });
});

// ============ 信号处理 ============

/**
 * POST /api/signals
 * 处理设备信号数据
 */
router.post('/signals', (req: Request, res: Response) => {
  const { user_id, signals } = req.body as {
    user_id: string;
    signals: RawSignalInput[];
  };

  if (!user_id || !signals || !Array.isArray(signals)) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: user_id, signals'
    });
  }

  const result = orchestrator.processSignals(user_id, signals);
  res.json(result);
});

// ============ 用户会话 ============

/**
 * POST /api/sessions
 * 创建用户会话
 */
router.post('/sessions', (req: Request, res: Response) => {
  const { user_id } = req.body;

  if (!user_id) {
    return res.status(400).json({
      success: false,
      error: 'Missing required field: user_id'
    });
  }

  const session = orchestrator.createSession(user_id);
  res.json({
    success: true,
    data: session
  });
});

/**
 * GET /api/dashboard/:userId
 * 获取用户仪表盘
 */
router.get('/dashboard/:userId', (req: Request, res: Response) => {
  const { userId } = req.params;
  const dashboard = orchestrator.getDashboard(userId);

  res.json({
    success: true,
    data: dashboard
  });
});

/**
 * GET /api/context/:userId
 * 获取对话上下文
 */
router.get('/context/:userId', (req: Request, res: Response) => {
  const { userId } = req.params;
  const context = orchestrator.getConversationContext(userId);

  res.json({
    success: true,
    data: context
  });
});

// ============ 干预计划 ============

/**
 * POST /api/interventions/generate
 * 生成干预计划
 */
router.post('/interventions/generate', (req: Request, res: Response) => {
  const { user_id, stage_indicators } = req.body;

  if (!user_id) {
    return res.status(400).json({
      success: false,
      error: 'Missing required field: user_id'
    });
  }

  const plan = orchestrator.generateIntervention(user_id, stage_indicators);

  if (!plan) {
    return res.status(404).json({
      success: false,
      error: 'No trajectory data found for user. Process signals first.'
    });
  }

  res.json({
    success: true,
    data: plan
  });
});

/**
 * POST /api/interventions/activate
 * 激活干预计划
 */
router.post('/interventions/activate', (req: Request, res: Response) => {
  const { user_id, playbook_id } = req.body;

  if (!user_id || !playbook_id) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: user_id, playbook_id'
    });
  }

  const plan = orchestrator.activateInterventionPlan(user_id, playbook_id);

  if (!plan) {
    return res.status(404).json({
      success: false,
      error: 'Playbook not found'
    });
  }

  res.json({
    success: true,
    data: plan
  });
});

// ============ 用户反馈 ============

/**
 * POST /api/feedback
 * 处理用户反馈
 */
router.post('/feedback', (req: Request, res: Response) => {
  const { user_id, feedback } = req.body;

  if (!user_id || !feedback) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: user_id, feedback'
    });
  }

  const result = orchestrator.processFeedback(user_id, {
    ...feedback,
    timestamp: feedback.timestamp || new Date().toISOString()
  });

  res.json({
    success: result,
    message: result ? 'Feedback processed' : 'Failed to process feedback'
  });
});

// ============ 行为锁定 ============

/**
 * POST /api/behavior-locks
 * 创建行为锁定
 */
router.post('/behavior-locks', (req: Request, res: Response) => {
  const {
    user_id,
    behavior_name,
    category,
    trigger_cue,
    execution_time,
    reward
  } = req.body;

  if (!user_id || !behavior_name || !category || !trigger_cue) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: user_id, behavior_name, category, trigger_cue'
    });
  }

  const lock = orchestrator.createBehaviorLock(
    user_id,
    behavior_name,
    category,
    trigger_cue,
    execution_time,
    reward
  );

  res.json({
    success: true,
    data: lock
  });
});

// ============ 知识搜索 ============

/**
 * GET /api/knowledge/search
 * 搜索知识库
 */
router.get('/knowledge/search', (req: Request, res: Response) => {
  const { keyword, types, tags, limit } = req.query;

  const results = libraryManager.search({
    keyword: keyword as string,
    types: types ? (types as string).split(',') as any : undefined,
    tags: tags ? (tags as string).split(',') : undefined,
    limit: limit ? parseInt(limit as string) : undefined
  });

  res.json({
    success: true,
    data: results
  });
});

/**
 * GET /api/knowledge/:id
 * 获取知识条目
 */
router.get('/knowledge/:id', (req: Request, res: Response) => {
  const { id } = req.params;
  const entry = knowledgeRegistry.get(id);

  if (!entry) {
    return res.status(404).json({
      success: false,
      error: 'Knowledge entry not found'
    });
  }

  // 记录使用
  knowledgeRegistry.recordUsage(id);

  res.json({
    success: true,
    data: entry
  });
});

/**
 * GET /api/knowledge/:id/related
 * 获取相关知识
 */
router.get('/knowledge/:id/related', (req: Request, res: Response) => {
  const { id } = req.params;
  const { limit } = req.query;

  const related = knowledgeRegistry.getRelated(
    id,
    limit ? parseInt(limit as string) : 5
  );

  res.json({
    success: true,
    data: related
  });
});

// ============ 内容服务 ============

/**
 * GET /api/content
 * 搜索内容
 */
router.get('/content', (req: Request, res: Response) => {
  const { type, domain, difficulty, stage, keyword } = req.query;

  const contentService = libraryManager.getContentService();
  const results = contentService.searchContents({
    type: type as any,
    domain: domain as any,
    difficulty: difficulty as any,
    stage: stage as any,
    keyword: keyword as string
  });

  res.json({
    success: true,
    data: results
  });
});

/**
 * GET /api/content/recommend
 * 推荐内容
 */
router.get('/content/recommend', (req: Request, res: Response) => {
  const { stage, phenotypes, limit } = req.query;

  if (!stage) {
    return res.status(400).json({
      success: false,
      error: 'Missing required field: stage'
    });
  }

  const contentService = libraryManager.getContentService();
  const results = contentService.recommendContents(
    stage as any,
    phenotypes ? (phenotypes as string).split(',') : [],
    limit ? parseInt(limit as string) : 5
  );

  res.json({
    success: true,
    data: results
  });
});

// ============ 商业资源 ============

/**
 * GET /api/resources
 * 搜索商业资源
 */
router.get('/resources', (req: Request, res: Response) => {
  const { type, category, phenotype, maxPrice } = req.query;

  const resourceService = libraryManager.getCommercialService();
  const results = resourceService.searchResources({
    type: type as any,
    category: category as any,
    phenotype: phenotype as string,
    maxPrice: maxPrice ? parseFloat(maxPrice as string) : undefined
  });

  res.json({
    success: true,
    data: results
  });
});

/**
 * GET /api/resources/recommend
 * 推荐资源
 */
router.get('/resources/recommend', (req: Request, res: Response) => {
  const { phenotypes, limit } = req.query;

  if (!phenotypes) {
    return res.status(400).json({
      success: false,
      error: 'Missing required field: phenotypes'
    });
  }

  const resourceService = libraryManager.getCommercialService();
  const results = resourceService.recommendByPhenotypes(
    (phenotypes as string).split(','),
    limit ? parseInt(limit as string) : 5
  );

  res.json({
    success: true,
    data: results
  });
});

// ============ 表型服务 ============

/**
 * GET /api/phenotypes
 * 获取所有表型
 */
router.get('/phenotypes', (req: Request, res: Response) => {
  const phenotypeService = libraryManager.getPhenotypeService();
  const phenotypes = phenotypeService.getAllPhenotypes();

  res.json({
    success: true,
    data: phenotypes
  });
});

/**
 * GET /api/phenotypes/:category
 * 按类别获取表型
 */
router.get('/phenotypes/category/:category', (req: Request, res: Response) => {
  const { category } = req.params;

  const phenotypeService = libraryManager.getPhenotypeService();
  const phenotypes = phenotypeService.getPhenotypesByCategory(category as any);

  res.json({
    success: true,
    data: phenotypes
  });
});

// ============ 干预剧本 ============

/**
 * GET /api/playbooks
 * 获取所有剧本
 */
router.get('/playbooks', (req: Request, res: Response) => {
  const interventionService = libraryManager.getInterventionService();
  const playbooks = interventionService.getAllPlaybooks();

  res.json({
    success: true,
    data: playbooks
  });
});

/**
 * GET /api/levers
 * 获取所有干预杠杆
 */
router.get('/levers', (req: Request, res: Response) => {
  const interventionService = libraryManager.getInterventionService();
  const levers = interventionService.getAllLevers();

  res.json({
    success: true,
    data: levers
  });
});

// ============ 训练服务 ============

/**
 * GET /api/training/modules
 * 获取训练模块
 */
router.get('/training/modules', (req: Request, res: Response) => {
  const trainingService = libraryManager.getTrainingService();
  const modules = trainingService.getAllModules();

  res.json({
    success: true,
    data: modules
  });
});

/**
 * GET /api/training/cases
 * 获取案例
 */
router.get('/training/cases', (req: Request, res: Response) => {
  const { phenotypes, stage, limit } = req.query;

  const trainingService = libraryManager.getTrainingService();
  const cases = trainingService.getRelatedCases(
    phenotypes ? (phenotypes as string).split(',') : undefined,
    stage as any,
    limit ? parseInt(limit as string) : 5
  );

  res.json({
    success: true,
    data: cases
  });
});

/**
 * GET /api/training/prompts
 * 获取AI提示模板
 */
router.get('/training/prompts', (req: Request, res: Response) => {
  const trainingService = libraryManager.getTrainingService();
  const prompts = trainingService.getAllPromptTemplates();

  res.json({
    success: true,
    data: prompts
  });
});

// ============ 教练认证体系 ============

/**
 * GET /api/certification/levels
 * 获取所有认证等级要求
 */
router.get('/certification/levels', (req: Request, res: Response) => {
  res.json({
    success: true,
    data: LEVEL_REQUIREMENTS
  });
});

/**
 * GET /api/certification/levels/:level
 * 获取指定等级要求
 */
router.get('/certification/levels/:level', (req: Request, res: Response) => {
  const { level } = req.params;
  const requirement = LEVEL_REQUIREMENTS.find(r => r.level === level);

  if (!requirement) {
    return res.status(404).json({
      success: false,
      error: 'Level not found'
    });
  }

  res.json({
    success: true,
    data: requirement
  });
});

/**
 * POST /api/certification/coaches
 * 创建教练档案
 */
router.post('/certification/coaches', (req: Request, res: Response) => {
  const { user_id, name } = req.body;

  if (!user_id || !name) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: user_id, name'
    });
  }

  const profile = certificationService.createCoachProfile(user_id, name);

  res.json({
    success: true,
    data: profile
  });
});

/**
 * GET /api/certification/coaches
 * 获取所有教练
 */
router.get('/certification/coaches', (req: Request, res: Response) => {
  const { level } = req.query;

  let coaches;
  if (level) {
    coaches = certificationService.getCoachesByLevel(level as CertificationLevel);
  } else {
    coaches = certificationService.getAllCoaches();
  }

  res.json({
    success: true,
    data: coaches
  });
});

/**
 * GET /api/certification/coaches/:coachId
 * 获取教练档案
 */
router.get('/certification/coaches/:coachId', (req: Request, res: Response) => {
  const { coachId } = req.params;
  const profile = certificationService.getCoachProfile(coachId);

  if (!profile) {
    return res.status(404).json({
      success: false,
      error: 'Coach profile not found'
    });
  }

  res.json({
    success: true,
    data: profile
  });
});

/**
 * GET /api/certification/coaches/:coachId/cases
 * 获取教练案例
 */
router.get('/certification/coaches/:coachId/cases', (req: Request, res: Response) => {
  const { coachId } = req.params;
  const cases = certificationService.getCoachCases(coachId);

  res.json({
    success: true,
    data: cases
  });
});

/**
 * POST /api/certification/coaches/:coachId/courses
 * 完成课程
 */
router.post('/certification/coaches/:coachId/courses', (req: Request, res: Response) => {
  const { coachId } = req.params;
  const { course_id, score } = req.body;

  if (!course_id) {
    return res.status(400).json({
      success: false,
      error: 'Missing required field: course_id'
    });
  }

  const success = certificationService.completeCourse(coachId, course_id, score);

  if (!success) {
    return res.status(400).json({
      success: false,
      error: 'Failed to complete course. Check prerequisites or course ID.'
    });
  }

  res.json({
    success: true,
    message: 'Course completed successfully'
  });
});

/**
 * POST /api/certification/coaches/:coachId/exams
 * 通过考试
 */
router.post('/certification/coaches/:coachId/exams', (req: Request, res: Response) => {
  const { coachId } = req.params;
  const { exam_id, score } = req.body;

  if (!exam_id || score === undefined) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: exam_id, score'
    });
  }

  const success = certificationService.passExam(coachId, exam_id, score);

  if (!success) {
    return res.status(400).json({
      success: false,
      error: 'Failed to pass exam. Score below passing threshold or invalid exam ID.'
    });
  }

  res.json({
    success: true,
    message: 'Exam passed successfully'
  });
});

/**
 * POST /api/certification/coaches/:coachId/cases
 * 创建案例
 */
router.post('/certification/coaches/:coachId/cases', (req: Request, res: Response) => {
  const { coachId } = req.params;
  const { client_user_id, risk_type } = req.body;

  if (!client_user_id || !risk_type) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: client_user_id, risk_type'
    });
  }

  const coachCase = certificationService.createCase(coachId, client_user_id, risk_type);

  if (!coachCase) {
    return res.status(400).json({
      success: false,
      error: 'Failed to create case. Coach may not have permission for this risk type.'
    });
  }

  res.json({
    success: true,
    data: coachCase
  });
});

/**
 * GET /api/certification/coaches/:coachId/evaluate
 * 评估教练晋级资格
 */
router.get('/certification/coaches/:coachId/evaluate', (req: Request, res: Response) => {
  const { coachId } = req.params;
  const profile = certificationService.getCoachProfile(coachId);

  if (!profile) {
    return res.status(404).json({
      success: false,
      error: 'Coach profile not found'
    });
  }

  const evaluation = promotionEngine.evaluate(profile);

  res.json({
    success: true,
    data: evaluation
  });
});

/**
 * POST /api/certification/coaches/:coachId/promote
 * 执行教练晋级
 */
router.post('/certification/coaches/:coachId/promote', (req: Request, res: Response) => {
  const { coachId } = req.params;

  const result = promotionEngine.promote(coachId);

  if (!result.success) {
    return res.status(400).json({
      success: false,
      error: result.message
    });
  }

  res.json({
    success: true,
    message: result.message,
    new_level: result.new_level
  });
});

/**
 * GET /api/certification/courses
 * 获取所有课程
 */
router.get('/certification/courses', (req: Request, res: Response) => {
  const { level } = req.query;

  let courses;
  if (level) {
    courses = certificationService.getCoursesByLevel(level as CertificationLevel);
  } else {
    courses = certificationService.getAllCourses();
  }

  res.json({
    success: true,
    data: courses
  });
});

/**
 * GET /api/certification/exams
 * 获取所有考试
 */
router.get('/certification/exams', (req: Request, res: Response) => {
  const { level } = req.query;

  let exams;
  if (level) {
    exams = certificationService.getExamsByLevel(level as CertificationLevel);
  } else {
    exams = certificationService.getAllExams();
  }

  res.json({
    success: true,
    data: exams
  });
});

/**
 * POST /api/certification/training-sessions
 * 创建训练会话
 */
router.post('/certification/training-sessions', (req: Request, res: Response) => {
  const { coach_id, session_type, scenario } = req.body;

  if (!coach_id || !session_type || !scenario) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: coach_id, session_type, scenario'
    });
  }

  const session = certificationService.createTrainingSession(coach_id, session_type, scenario);

  res.json({
    success: true,
    data: session
  });
});

// ============ 认证鉴权 ============

import { authService } from '../auth/AuthService';
import { permissionService } from '../permission/PermissionService';
import { agentOrchestrator } from '../agent/AgentOrchestrator';

/**
 * POST /api/auth/login
 * 用户登录
 */
router.post('/auth/login', (req: Request, res: Response) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: username, password'
    });
  }

  const result = authService.login({ username, password });

  if (!result.success) {
    return res.status(401).json(result);
  }

  res.json(result);
});

/**
 * POST /api/auth/refresh
 * 刷新Token
 */
router.post('/auth/refresh', (req: Request, res: Response) => {
  const { refresh_token } = req.body;

  if (!refresh_token) {
    return res.status(400).json({
      success: false,
      error: 'Missing required field: refresh_token'
    });
  }

  const result = authService.refreshToken(refresh_token);

  if (!result.success) {
    return res.status(401).json(result);
  }

  res.json(result);
});

/**
 * POST /api/auth/logout
 * 用户登出
 */
router.post('/auth/logout', (req: Request, res: Response) => {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (token) {
    authService.logout(token);
  }

  res.json({
    success: true,
    message: 'Logged out successfully'
  });
});

/**
 * GET /api/auth/profile
 * 获取当前用户信息
 */
router.get('/auth/profile', (req: Request, res: Response) => {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (!token) {
    return res.status(401).json({
      success: false,
      error: 'No token provided'
    });
  }

  const user = authService.getUserByToken(token);

  if (!user) {
    return res.status(401).json({
      success: false,
      error: 'Invalid or expired token'
    });
  }

  res.json({
    success: true,
    data: user
  });
});

/**
 * POST /api/auth/register
 * 用户注册
 */
router.post('/auth/register', (req: Request, res: Response) => {
  const { username, email, password, phone, name } = req.body;

  if (!username || !email || !password) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: username, email, password'
    });
  }

  try {
    const account = authService.createAccount({
      username,
      email,
      password,
      phone,
      name
    });

    res.json({
      success: true,
      data: {
        user_id: account.user_id,
        username: account.username,
        email: account.email,
        role: account.role
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: String(error)
    });
  }
});

// ============ 权限服务 ============

/**
 * POST /api/permission/check
 * 检查权限
 */
router.post('/permission/check', (req: Request, res: Response) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  const { resource, action, context } = req.body;

  if (!token) {
    return res.status(401).json({
      success: false,
      error: 'No token provided'
    });
  }

  const user = authService.getUserByToken(token);
  if (!user) {
    return res.status(401).json({
      success: false,
      error: 'Invalid token'
    });
  }

  const result = permissionService.check({
    user,
    resource,
    action,
    context
  });

  res.json({
    success: true,
    data: result
  });
});

/**
 * GET /api/permission/rules
 * 获取所有权限规则
 */
router.get('/permission/rules', (req: Request, res: Response) => {
  const rules = permissionService.getAllRules();

  res.json({
    success: true,
    data: rules
  });
});

// ============ Agent服务 ============

/**
 * POST /api/agent/run
 * 执行Agent任务
 */
router.post('/agent/run', async (req: Request, res: Response) => {
  const { agent_type, user_id, context, expected_output, priority, coach_id } = req.body;

  if (!agent_type || !user_id || !context || !expected_output) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: agent_type, user_id, context, expected_output'
    });
  }

  try {
    const task = agentOrchestrator.createTask(
      agent_type,
      user_id,
      context,
      expected_output,
      { priority, coachId: coach_id }
    );

    const output = await agentOrchestrator.runTask(task.task_id);

    res.json({
      success: true,
      data: output
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: String(error)
    });
  }
});

/**
 * POST /api/agent/feedback
 * 提交Agent反馈
 */
router.post('/agent/feedback', (req: Request, res: Response) => {
  const { task_id, reviewer_id, reviewer_role, feedback_type, rating, comment, modifications } = req.body;

  if (!task_id || !reviewer_id || !reviewer_role || !feedback_type) {
    return res.status(400).json({
      success: false,
      error: 'Missing required fields: task_id, reviewer_id, reviewer_role, feedback_type'
    });
  }

  try {
    const feedback = agentOrchestrator.submitFeedback(
      task_id,
      reviewer_id,
      reviewer_role,
      feedback_type,
      { rating, comment, modifications }
    );

    res.json({
      success: true,
      data: feedback
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: String(error)
    });
  }
});

/**
 * GET /api/agent/history
 * 获取Agent执行历史
 */
router.get('/agent/history', (req: Request, res: Response) => {
  const { agent_id, user_id, status, limit } = req.query;

  const history = agentOrchestrator.getExecutionHistory({
    agentId: agent_id as string,
    userId: user_id as string,
    status: status as string,
    limit: limit ? parseInt(limit as string) : undefined
  });

  res.json({
    success: true,
    data: history
  });
});

/**
 * GET /api/agent/pending-reviews
 * 获取待审核任务
 */
router.get('/agent/pending-reviews', (req: Request, res: Response) => {
  const reviews = agentOrchestrator.getPendingReviews();

  res.json({
    success: true,
    data: reviews
  });
});

/**
 * GET /api/agent/list
 * 获取Agent列表
 */
router.get('/agent/list', (req: Request, res: Response) => {
  const agents = agentOrchestrator.getAgents();

  res.json({
    success: true,
    data: agents
  });
});

/**
 * GET /api/agent/stats/:agentId
 * 获取Agent统计
 */
router.get('/agent/stats/:agentId', (req: Request, res: Response) => {
  const { agentId } = req.params;
  const stats = agentOrchestrator.getAgentStats(agentId);

  res.json({
    success: true,
    data: stats
  });
});

// ============ 教练服务 ============

/**
 * GET /api/coach/students
 * 获取教练学员列表
 */
router.get('/coach/students', (req: Request, res: Response) => {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (!token) {
    return res.status(401).json({
      success: false,
      error: 'No token provided'
    });
  }

  const user = authService.getUserByToken(token);
  if (!user) {
    return res.status(401).json({
      success: false,
      error: 'Invalid token'
    });
  }

  // 检查权限
  const permResult = permissionService.check({
    user,
    resource: 'coach_students',
    action: 'view'
  });

  if (!permResult.allowed) {
    return res.status(403).json({
      success: false,
      error: permResult.reason
    });
  }

  // 返回模拟学员数据
  res.json({
    success: true,
    data: [
      {
        user_id: 'student-001',
        name: '张三',
        risk_level: 'medium',
        behavior_stage: 'action',
        last_active: new Date().toISOString(),
        tasks_completed: 12,
        tasks_pending: 3
      },
      {
        user_id: 'student-002',
        name: '李四',
        risk_level: 'low',
        behavior_stage: 'maintenance',
        last_active: new Date().toISOString(),
        tasks_completed: 28,
        tasks_pending: 1
      }
    ]
  });
});

/**
 * POST /api/coach/submit-plan
 * 提交干预方案
 */
router.post('/coach/submit-plan', (req: Request, res: Response) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  const { user_id, plan } = req.body;

  if (!token) {
    return res.status(401).json({
      success: false,
      error: 'No token provided'
    });
  }

  const user = authService.getUserByToken(token);
  if (!user) {
    return res.status(401).json({
      success: false,
      error: 'Invalid token'
    });
  }

  // 检查权限
  const permResult = permissionService.check({
    user,
    resource: 'intervention_plan',
    action: 'create'
  });

  if (!permResult.allowed) {
    return res.status(403).json({
      success: false,
      error: permResult.reason
    });
  }

  res.json({
    success: true,
    data: {
      plan_id: 'plan-' + Date.now(),
      user_id,
      plan,
      status: 'pending_review',
      submitted_at: new Date().toISOString()
    }
  });
});

/**
 * GET /api/coach/review-agent
 * 获取待审核的Agent建议
 */
router.get('/coach/review-agent', (req: Request, res: Response) => {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (!token) {
    return res.status(401).json({
      success: false,
      error: 'No token provided'
    });
  }

  const user = authService.getUserByToken(token);
  if (!user) {
    return res.status(401).json({
      success: false,
      error: 'Invalid token'
    });
  }

  const reviews = agentOrchestrator.getPendingReviews();

  res.json({
    success: true,
    data: reviews
  });
});

export default router;
