/**
 * Content Material Library - 内容素材库
 * 管理教育内容、话术模板、多媒体资源
 */

import { v4 as uuidv4 } from 'uuid';
import { BehaviorStage } from '../trajectory/TrajectorySchema';

/**
 * 内容类型
 */
export type ContentType =
  | 'article'         // 文章
  | 'video'           // 视频
  | 'audio'           // 音频
  | 'infographic'     // 信息图
  | 'checklist'       // 清单
  | 'template'        // 模板
  | 'script'          // 话术脚本
  | 'quiz'            // 测验
  | 'case_study';     // 案例

/**
 * 内容领域
 */
export type ContentDomain =
  | 'nutrition'       // 营养
  | 'exercise'        // 运动
  | 'medication'      // 用药
  | 'monitoring'      // 监测
  | 'psychology'      // 心理
  | 'complication'    // 并发症
  | 'lifestyle'       // 生活方式
  | 'general';        // 通用

/**
 * 难度级别
 */
export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced';

/**
 * 内容素材
 */
export interface ContentMaterial {
  /** 素材ID */
  content_id: string;
  /** 标题 */
  title: string;
  /** 摘要 */
  summary: string;
  /** 内容类型 */
  type: ContentType;
  /** 领域 */
  domain: ContentDomain;
  /** 难度级别 */
  difficulty: DifficultyLevel;
  /** 适用阶段 */
  applicable_stages: BehaviorStage[];
  /** 适用表型 */
  applicable_phenotypes?: string[];
  /** 内容正文 */
  body?: string;
  /** 媒体URL */
  media_url?: string;
  /** 时长(分钟) */
  duration_minutes?: number;
  /** 标签 */
  tags: string[];
  /** 关键词 */
  keywords: string[];
  /** 阅读/观看次数 */
  view_count: number;
  /** 点赞数 */
  like_count: number;
  /** 收藏数 */
  save_count: number;
  /** 版本 */
  version: string;
  /** 作者 */
  author?: string;
  /** 创建时间 */
  created_at: string;
  /** 更新时间 */
  updated_at?: string;
}

/**
 * 话术脚本
 */
export interface CoachingScript {
  /** 脚本ID */
  script_id: string;
  /** 脚本名称 */
  name: string;
  /** 场景 */
  scenario: string;
  /** 适用阶段 */
  stage: BehaviorStage;
  /** 目标 */
  objective: string;
  /** 话术内容 */
  content: {
    /** 开场白 */
    opening: string;
    /** 核心对话节点 */
    dialogue_nodes: {
      node_id: string;
      coach_says: string;
      expected_responses: {
        response_type: string;
        user_says: string;
        coach_reply: string;
      }[];
    }[];
    /** 结束语 */
    closing: string;
  };
  /** 注意事项 */
  notes?: string[];
  /** 示例对话 */
  example_dialogue?: string;
  /** 版本 */
  version: string;
}

/**
 * 推送消息模板
 */
export interface MessageTemplate {
  /** 模板ID */
  template_id: string;
  /** 模板名称 */
  name: string;
  /** 触发场景 */
  trigger_scenario: string;
  /** 消息类型 */
  message_type: 'reminder' | 'encouragement' | 'alert' | 'education' | 'celebration';
  /** 模板内容 */
  content: string;
  /** 变量占位符 */
  variables: string[];
  /** 适用时段 */
  applicable_time?: {
    start_hour: number;
    end_hour: number;
  };
  /** 优先级 */
  priority: 'low' | 'medium' | 'high';
}

/**
 * 预定义内容素材
 */
export const PREDEFINED_CONTENTS: ContentMaterial[] = [
  {
    content_id: 'CNT-001',
    title: '血糖波动的元凶：餐后血糖管理',
    summary: '了解餐后血糖升高的原因和应对策略',
    type: 'article',
    domain: 'nutrition',
    difficulty: 'beginner',
    applicable_stages: ['contemplation', 'preparation'],
    body: `
# 什么是餐后血糖？

餐后血糖是指进食后血糖的变化情况。对于糖尿病患者，餐后血糖控制尤为重要。

## 餐后血糖升高的原因

1. **碳水化合物摄入过多**：米饭、面条、馒头等主食含大量碳水化合物
2. **进食速度过快**：快速进食导致血糖快速升高
3. **缺乏餐后活动**：进食后立即休息使血糖难以下降

## 控制策略

### 调整进餐顺序
先吃蔬菜和蛋白质，最后吃主食，可有效降低餐后血糖峰值。

### 慢食习惯
每餐进食时间延长到20分钟以上，充分咀嚼。

### 餐后散步
餐后15-30分钟进行10-15分钟的轻度步行。
    `,
    tags: ['餐后血糖', '饮食控制', '基础知识'],
    keywords: ['餐后血糖', 'PPG', '进餐顺序', '慢食'],
    view_count: 0,
    like_count: 0,
    save_count: 0,
    version: '1.0',
    created_at: new Date().toISOString()
  },
  {
    content_id: 'CNT-002',
    title: '黎明现象：为什么早晨血糖会偏高？',
    summary: '解析黎明现象的机制和应对方法',
    type: 'article',
    domain: 'monitoring',
    difficulty: 'intermediate',
    applicable_stages: ['preparation', 'action'],
    applicable_phenotypes: ['PHE-002'],
    body: `
# 黎明现象

黎明现象是指凌晨3-8点血糖自然升高的现象。

## 原因

- 清晨时分，身体分泌较多升糖激素（如皮质醇、生长激素）
- 肝脏释放储存的葡萄糖
- 胰岛素作用相对减弱

## 与夜间低血糖的区别

| 特征 | 黎明现象 | 夜间低血糖反弹 |
|------|----------|----------------|
| 3AM血糖 | 正常 | 偏低(<3.9) |
| 原因 | 激素分泌 | 低血糖后反弹 |

## 应对策略

1. 睡前轻食（蛋白质+复合碳水）
2. 固定早餐时间
3. 药物调整（需咨询医生）
    `,
    tags: ['黎明现象', '空腹血糖', '监测'],
    keywords: ['黎明现象', 'dawn phenomenon', '清晨血糖'],
    view_count: 0,
    like_count: 0,
    save_count: 0,
    version: '1.0',
    created_at: new Date().toISOString()
  },
  {
    content_id: 'CNT-003',
    title: '运动与血糖：找到你的最佳运动处方',
    summary: '如何通过运动有效控制血糖',
    type: 'article',
    domain: 'exercise',
    difficulty: 'beginner',
    applicable_stages: ['preparation', 'action', 'maintenance'],
    body: `
# 运动对血糖的影响

运动是控制血糖的重要手段，能够提高胰岛素敏感性，帮助血糖进入细胞。

## 推荐运动类型

### 有氧运动
- 快走、慢跑、游泳、骑车
- 每周150分钟以上
- 强度：略微出汗、能正常交谈

### 抗阻运动
- 弹力带、哑铃、深蹲
- 每周2-3次
- 增加肌肉量，提高代谢

## 运动注意事项

1. **运动时机**：餐后1-2小时为佳
2. **血糖监测**：运动前后测血糖
3. **低血糖预防**：随身携带糖果
4. **循序渐进**：从低强度开始
    `,
    tags: ['运动', '血糖控制', '有氧运动', '抗阻运动'],
    keywords: ['运动处方', '有氧运动', '抗阻训练', '胰岛素敏感性'],
    view_count: 0,
    like_count: 0,
    save_count: 0,
    version: '1.0',
    created_at: new Date().toISOString()
  },
  {
    content_id: 'CNT-004',
    title: '压力与血糖的隐秘联系',
    summary: '了解压力如何影响血糖，学习压力管理技巧',
    type: 'article',
    domain: 'psychology',
    difficulty: 'intermediate',
    applicable_stages: ['contemplation', 'preparation', 'action'],
    applicable_phenotypes: ['PHE-005'],
    body: `
# 压力如何影响血糖？

当我们感到压力时，身体会释放应激激素（皮质醇、肾上腺素），这些激素会：

- 促进肝脏释放葡萄糖
- 降低胰岛素敏感性
- 导致血糖升高

## 识别压力信号

- 心跳加快
- 肌肉紧张
- 睡眠困难
- 情绪波动
- 食欲变化

## 压力管理技巧

### 4-7-8 呼吸法
1. 吸气4秒
2. 屏息7秒
3. 呼气8秒
4. 重复3-4次

### 正念练习
每天10分钟的正念冥想可显著降低压力水平。

### 社交支持
与家人朋友分享感受，参加病友互助小组。
    `,
    tags: ['压力', '心理健康', '应激', 'HRV'],
    keywords: ['压力管理', '应激激素', '正念', '呼吸练习'],
    view_count: 0,
    like_count: 0,
    save_count: 0,
    version: '1.0',
    created_at: new Date().toISOString()
  },
  {
    content_id: 'CNT-005',
    title: '睡眠质量与代谢健康',
    summary: '良好睡眠是血糖控制的基础',
    type: 'article',
    domain: 'lifestyle',
    difficulty: 'beginner',
    applicable_stages: ['preparation', 'action'],
    applicable_phenotypes: ['PHE-007'],
    body: `
# 睡眠与血糖的关系

研究表明，睡眠不足会：
- 降低胰岛素敏感性
- 增加食欲和饥饿感
- 影响次日血糖控制

## 理想睡眠时长

成年人建议每晚7-9小时优质睡眠。

## 提升睡眠质量的方法

### 建立睡眠规律
- 固定就寝和起床时间
- 周末不过度补觉

### 营造睡眠环境
- 黑暗、安静、凉爽
- 舒适的床品

### 睡前习惯
- 避免电子屏幕（蓝光）
- 避免咖啡因（下午2点后）
- 轻度拉伸或冥想
    `,
    tags: ['睡眠', '作息', '生活方式'],
    keywords: ['睡眠质量', '昼夜节律', '蓝光', '睡眠卫生'],
    view_count: 0,
    like_count: 0,
    save_count: 0,
    version: '1.0',
    created_at: new Date().toISOString()
  }
];

/**
 * 预定义话术脚本
 */
export const PREDEFINED_SCRIPTS: CoachingScript[] = [
  {
    script_id: 'SCR-001',
    name: '初次接触-建立信任',
    scenario: '新用户首次使用，建立信任关系',
    stage: 'precontemplation',
    objective: '建立信任，了解用户情况，避免说教',
    content: {
      opening: '您好！欢迎来到行健行为教练。我是您的健康管理伙伴。在开始之前，我想先了解一下您的情况，这样能更好地帮助您。您方便聊几分钟吗？',
      dialogue_nodes: [
        {
          node_id: 'node-1',
          coach_says: '请问您是通过什么渠道了解到我们的呢？是医生推荐，还是自己想要做些改变？',
          expected_responses: [
            {
              response_type: 'doctor_referral',
              user_says: '医生让我用的',
              coach_reply: '理解，医生建议使用说明他很关心您的健康。我们会配合医生的治疗方案，提供一些日常管理上的帮助。'
            },
            {
              response_type: 'self_motivated',
              user_says: '我自己想试试看',
              coach_reply: '非常好，主动寻求改变本身就是很棒的第一步。我很期待能陪您一起走这段路。'
            }
          ]
        },
        {
          node_id: 'node-2',
          coach_says: '目前您在血糖管理方面，觉得最困扰的是什么？',
          expected_responses: [
            {
              response_type: 'diet_struggle',
              user_says: '控制饮食太难了',
              coach_reply: '饮食确实是很多人觉得最难的部分。我们不会要求您一下子做很大改变，而是从一些小的、容易坚持的调整开始。'
            },
            {
              response_type: 'no_issue',
              user_says: '我觉得还好，没什么问题',
              coach_reply: '能这样想说明您心态很好。我们可以一起看看数据，也许能发现一些小的优化空间。'
            }
          ]
        }
      ],
      closing: '感谢您的分享。接下来我们会根据您的情况，提供一些个性化的建议。如果有任何问题，随时可以问我。'
    },
    notes: [
      '保持温和、不评判的态度',
      '多用开放式问题',
      '避免使用"必须"、"应该"等词汇',
      '认可用户的感受和努力'
    ],
    version: '1.0'
  },
  {
    script_id: 'SCR-002',
    name: '动机强化对话',
    scenario: '用户处于意向期，需要强化改变动机',
    stage: 'contemplation',
    objective: '探索改变的好处，识别和应对障碍',
    content: {
      opening: '我注意到您最近一直在关注血糖数据，看来您对自己的健康很上心。今天想和您聊聊关于改变的一些想法。',
      dialogue_nodes: [
        {
          node_id: 'node-1',
          coach_says: '如果血糖能够控制得更好，您觉得对您的生活会有什么改变？',
          expected_responses: [
            {
              response_type: 'health_concern',
              user_says: '不想以后有并发症',
              coach_reply: '预防并发症确实是非常重要的目标。您提到这个，说明您对长期健康有清晰的认识。'
            },
            {
              response_type: 'quality_of_life',
              user_says: '希望精力更好一些',
              coach_reply: '是的，稳定的血糖确实能让人感觉更有活力。您现在觉得精力不太好吗？'
            }
          ]
        },
        {
          node_id: 'node-2',
          coach_says: '在做出一些改变的过程中，您觉得最大的挑战可能是什么？',
          expected_responses: [
            {
              response_type: 'time',
              user_says: '太忙了，没时间',
              coach_reply: '时间确实是很多人面临的挑战。好消息是，很多有效的改变其实只需要很少的时间。我们可以一起找到适合您日程的方法。'
            },
            {
              response_type: 'willpower',
              user_says: '怕自己坚持不了',
              coach_reply: '担心坚持不了是很正常的想法。其实我们的方法不是靠意志力硬撑，而是通过小步骤和习惯设计，让改变变得更容易。'
            }
          ]
        }
      ],
      closing: '您提到的这些想法和顾虑都很重要。改变确实不容易，但每一小步都是进步。我会在这里支持您。'
    },
    notes: [
      '使用动机性访谈技巧',
      '引导用户自己说出改变的理由',
      '认可矛盾心理是正常的',
      '强调小步骤和可及性'
    ],
    version: '1.0'
  }
];

/**
 * 预定义消息模板
 */
export const PREDEFINED_TEMPLATES: MessageTemplate[] = [
  {
    template_id: 'TPL-001',
    name: '餐后散步提醒',
    trigger_scenario: '餐后30分钟',
    message_type: 'reminder',
    content: '吃完饭{duration}了，现在是散步的好时机！10分钟轻松走走，帮助血糖更平稳。',
    variables: ['duration'],
    applicable_time: { start_hour: 7, end_hour: 21 },
    priority: 'medium'
  },
  {
    template_id: 'TPL-002',
    name: '血糖改善鼓励',
    trigger_scenario: '检测到血糖改善趋势',
    message_type: 'encouragement',
    content: '太棒了！您这周的餐后血糖比上周下降了{improvement}%。您的努力正在看到成效！',
    variables: ['improvement'],
    priority: 'high'
  },
  {
    template_id: 'TPL-003',
    name: '夜间低血糖预警',
    trigger_scenario: '预测夜间可能发生低血糖',
    message_type: 'alert',
    content: '根据您今天的数据，夜间可能有低血糖风险。建议睡前补充少量点心（如一小杯牛奶+2片全麦饼干）。',
    variables: [],
    applicable_time: { start_hour: 20, end_hour: 23 },
    priority: 'high'
  },
  {
    template_id: 'TPL-004',
    name: '连续完成任务庆祝',
    trigger_scenario: '连续完成任务达到里程碑',
    message_type: 'celebration',
    content: '恭喜！您已经连续{days}天完成任务，这是一个了不起的成就！坚持就是胜利，继续加油！',
    variables: ['days'],
    priority: 'high'
  },
  {
    template_id: 'TPL-005',
    name: '每日小知识',
    trigger_scenario: '每日定时推送',
    message_type: 'education',
    content: '{tip}',
    variables: ['tip'],
    applicable_time: { start_hour: 8, end_hour: 20 },
    priority: 'low'
  }
];

/**
 * 内容素材服务
 */
export class ContentMaterialService {
  private contents: Map<string, ContentMaterial> = new Map();
  private scripts: Map<string, CoachingScript> = new Map();
  private templates: Map<string, MessageTemplate> = new Map();

  constructor() {
    // 加载预定义内容
    PREDEFINED_CONTENTS.forEach(c => {
      this.contents.set(c.content_id, c);
    });
    PREDEFINED_SCRIPTS.forEach(s => {
      this.scripts.set(s.script_id, s);
    });
    PREDEFINED_TEMPLATES.forEach(t => {
      this.templates.set(t.template_id, t);
    });
  }

  /**
   * 按条件搜索内容
   */
  searchContents(criteria: {
    type?: ContentType;
    domain?: ContentDomain;
    difficulty?: DifficultyLevel;
    stage?: BehaviorStage;
    phenotype?: string;
    keyword?: string;
  }): ContentMaterial[] {
    let results = Array.from(this.contents.values());

    if (criteria.type) {
      results = results.filter(c => c.type === criteria.type);
    }
    if (criteria.domain) {
      results = results.filter(c => c.domain === criteria.domain);
    }
    if (criteria.difficulty) {
      results = results.filter(c => c.difficulty === criteria.difficulty);
    }
    if (criteria.stage) {
      results = results.filter(c => c.applicable_stages.includes(criteria.stage!));
    }
    if (criteria.phenotype) {
      results = results.filter(c =>
        c.applicable_phenotypes?.includes(criteria.phenotype!) ?? false
      );
    }
    if (criteria.keyword) {
      const kw = criteria.keyword.toLowerCase();
      results = results.filter(c =>
        c.title.toLowerCase().includes(kw) ||
        c.keywords.some(k => k.toLowerCase().includes(kw)) ||
        c.tags.some(t => t.toLowerCase().includes(kw))
      );
    }

    return results;
  }

  /**
   * 推荐内容
   */
  recommendContents(
    stage: BehaviorStage,
    phenotypes: string[],
    limit: number = 5
  ): ContentMaterial[] {
    let results = Array.from(this.contents.values())
      .filter(c => c.applicable_stages.includes(stage));

    // 优先匹配表型
    const phenotypeMatched = results.filter(c =>
      c.applicable_phenotypes?.some(p => phenotypes.includes(p))
    );

    // 合并结果，表型匹配的优先
    const combined = [
      ...phenotypeMatched,
      ...results.filter(c => !phenotypeMatched.includes(c))
    ];

    return combined.slice(0, limit);
  }

  /**
   * 获取话术脚本
   */
  getScript(stage: BehaviorStage, scenario?: string): CoachingScript | undefined {
    for (const script of this.scripts.values()) {
      if (script.stage === stage) {
        if (!scenario || script.scenario.includes(scenario)) {
          return script;
        }
      }
    }
    return undefined;
  }

  /**
   * 获取消息模板并填充变量
   */
  fillTemplate(templateId: string, variables: Record<string, string>): string | null {
    const template = this.templates.get(templateId);
    if (!template) return null;

    let content = template.content;
    for (const [key, value] of Object.entries(variables)) {
      content = content.replace(`{${key}}`, value);
    }

    return content;
  }

  /**
   * 获取适用的消息模板
   */
  getApplicableTemplates(
    messageType: MessageTemplate['message_type'],
    hour?: number
  ): MessageTemplate[] {
    return Array.from(this.templates.values()).filter(t => {
      if (t.message_type !== messageType) return false;
      if (hour !== undefined && t.applicable_time) {
        if (hour < t.applicable_time.start_hour || hour > t.applicable_time.end_hour) {
          return false;
        }
      }
      return true;
    });
  }

  /**
   * 记录内容互动
   */
  recordInteraction(
    contentId: string,
    action: 'view' | 'like' | 'save'
  ): boolean {
    const content = this.contents.get(contentId);
    if (!content) return false;

    switch (action) {
      case 'view':
        content.view_count++;
        break;
      case 'like':
        content.like_count++;
        break;
      case 'save':
        content.save_count++;
        break;
    }

    return true;
  }

  /**
   * 注册新内容
   */
  registerContent(content: Omit<ContentMaterial, 'content_id' | 'view_count' | 'like_count' | 'save_count' | 'created_at'>): ContentMaterial {
    const newContent: ContentMaterial = {
      content_id: `CNT-${uuidv4().slice(0, 8).toUpperCase()}`,
      ...content,
      view_count: 0,
      like_count: 0,
      save_count: 0,
      created_at: new Date().toISOString()
    };
    this.contents.set(newContent.content_id, newContent);
    return newContent;
  }

  /**
   * 获取所有内容
   */
  getAllContents(): ContentMaterial[] {
    return Array.from(this.contents.values());
  }

  /**
   * 获取所有脚本
   */
  getAllScripts(): CoachingScript[] {
    return Array.from(this.scripts.values());
  }

  /**
   * 获取所有模板
   */
  getAllTemplates(): MessageTemplate[] {
    return Array.from(this.templates.values());
  }
}

// 导出单例
export const contentMaterialService = new ContentMaterialService();
