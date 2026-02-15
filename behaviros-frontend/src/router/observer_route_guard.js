/**
 * 观察员分层前端路由守卫
 * 契约来源: Sheet③ A节 + Sheet⑤ 服务权益矩阵
 *
 * 三层访问控制:
 *   PUBLIC   → 免注册游客可见
 *   OBSERVER → 注册观察员可见 (部分带体验版限制)
 *   GROWER+  → 成长者及以上可见
 */

// ─────────────────────────────────────────
// 1. 路由元数据定义 (route meta)
// ─────────────────────────────────────────

/**
 * 在路由配置中使用 meta.accessTier 标记访问层级:
 *
 * {
 *   path: '/content/public',
 *   component: PublicContent,
 *   meta: { accessTier: 'public' }
 * },
 * {
 *   path: '/assessment/trial',
 *   component: TrialAssessment,
 *   meta: { accessTier: 'observer', trialType: 'assessment' }
 * },
 * {
 *   path: '/chat/trial',
 *   component: TrialChat,
 *   meta: { accessTier: 'observer', trialType: 'chat' }
 * },
 * {
 *   path: '/assessment/full',
 *   component: FullAssessment,
 *   meta: { accessTier: 'grower' }
 * }
 */

// ─────────────────────────────────────────
// 2. 角色层级映射 (对齐 Sheet① role_level)
// ─────────────────────────────────────────

const ROLE_LEVELS = {
  admin: 99,
  supervisor: 98,
  observer: 1,
  grower: 2,
  sharer: 3,
  coach: 4,
  senior_coach: 5,
  master: 6,
};

const TIER_MIN_LEVEL = {
  public: 0,       // 任何人
  observer: 1,     // 注册观察员+
  grower: 2,       // 成长者+
  sharer: 3,       // 分享者+
  coach: 4,        // 教练+
  senior_coach: 5, // 促进师+
  master: 6,       // 大师+
  admin: 99,       // 管理员
};

// ─────────────────────────────────────────
// 3. 体验版状态管理 (Pinia Store)
// ─────────────────────────────────────────

/**
 * stores/trialStore.js
 */
export const useTrialStore = () => {
  // 如果使用 Pinia:
  // import { defineStore } from 'pinia';
  // export const useTrialStore = defineStore('trial', { ... });

  // 简化版: 使用 reactive state
  const state = {
    assessmentUsed: 0,
    assessmentLimit: 1,
    chatRoundsUsed: 0,
    chatRoundsLimit: 3,
    loaded: false,
  };

  const canDoTrialAssessment = () =>
    state.assessmentUsed < state.assessmentLimit;

  const canDoTrialChat = () =>
    state.chatRoundsUsed < state.chatRoundsLimit;

  const remainingChatRounds = () =>
    Math.max(0, state.chatRoundsLimit - state.chatRoundsUsed);

  const loadTrialStatus = async () => {
    try {
      const [assessRes, chatRes] = await Promise.all([
        fetch('/api/v1/trial/assessment/status'),
        fetch('/api/v1/trial/chat/status'),
      ]);
      if (assessRes.ok) {
        const data = await assessRes.json();
        state.assessmentUsed = data.used;
        state.assessmentLimit = data.limit;
      }
      if (chatRes.ok) {
        const data = await chatRes.json();
        state.chatRoundsUsed = data.used;
        state.chatRoundsLimit = data.limit;
      }
      state.loaded = true;
    } catch (e) {
      console.warn('[TrialStore] 加载体验版状态失败:', e);
    }
  };

  return {
    state,
    canDoTrialAssessment,
    canDoTrialChat,
    remainingChatRounds,
    loadTrialStatus,
  };
};


// ─────────────────────────────────────────
// 4. Vue Router 全局守卫
// ─────────────────────────────────────────

/**
 * router/guards/observerTieringGuard.js
 *
 * 安装方式:
 *   import { createObserverGuard } from './guards/observerTieringGuard';
 *   router.beforeEach(createObserverGuard(authStore, trialStore));
 */
export function createObserverGuard(authStore, trialStore) {
  return async (to, from, next) => {
    const requiredTier = to.meta?.accessTier || 'public';
    const trialType = to.meta?.trialType;

    // 1. 公开路由 → 直接放行
    if (requiredTier === 'public') {
      return next();
    }

    // 2. 未登录 → 引导注册
    if (!authStore.isAuthenticated) {
      return next({
        name: 'Register',
        query: {
          redirect: to.fullPath,
          hint: 'register_unlock',  // 转化钩子: "注册解锁更多"
        },
      });
    }

    const userRole = authStore.user?.role?.toLowerCase() || 'observer';
    const userLevel = ROLE_LEVELS[userRole] || 0;
    const requiredLevel = TIER_MIN_LEVEL[requiredTier] || 0;

    // 3. 角色层级不足 → 引导升级
    if (userLevel < requiredLevel) {
      return next({
        name: 'UpgradePrompt',
        query: {
          required: requiredTier,
          current: userRole,
          redirect: to.fullPath,
        },
      });
    }

    // 4. 体验版路由 → 检查使用额度
    if (trialType && userLevel === 1) {
      // 仅观察员需要检查体验版限制; 成长者+不受限
      if (!trialStore.state.loaded) {
        await trialStore.loadTrialStatus();
      }

      if (trialType === 'assessment' && !trialStore.canDoTrialAssessment()) {
        return next({
          name: 'TrialExhausted',
          query: {
            type: 'assessment',
            redirect: to.fullPath,
            hint: '成为成长者获取完整服务',  // Sheet③ 转化路径
          },
        });
      }

      if (trialType === 'chat' && !trialStore.canDoTrialChat()) {
        return next({
          name: 'TrialExhausted',
          query: {
            type: 'chat',
            redirect: to.fullPath,
            hint: '注册解锁完整AI服务',  // Sheet③ 转化路径
          },
        });
      }
    }

    // 5. 全部检查通过 → 放行
    return next();
  };
}


// ─────────────────────────────────────────
// 5. 转化引导页面路由配置
// ─────────────────────────────────────────

export const observerTieringRoutes = [
  {
    path: '/upgrade-prompt',
    name: 'UpgradePrompt',
    component: () => import('@/views/observer/UpgradePrompt.vue'),
    meta: { accessTier: 'public', layout: 'minimal' },
  },
  {
    path: '/trial-exhausted',
    name: 'TrialExhausted',
    component: () => import('@/views/observer/TrialExhausted.vue'),
    meta: { accessTier: 'observer', layout: 'minimal' },
  },
];


// ─────────────────────────────────────────
// 6. API 端点: 体验版状态查询
// ─────────────────────────────────────────

/**
 * 后端对应端点 (已在 observer_access_middleware.py 中实现):
 *
 * GET /v1/trial/assessment/status
 *   → { used: 0, limit: 1, remaining: 1, allowed: true }
 *
 * GET /v1/trial/chat/status
 *   → { used: 2, limit: 3, remaining: 1, allowed: true }
 *
 * POST /v1/trial/assessment/consume
 *   → { success: true, remaining: 0 }
 *
 * POST /v1/trial/chat/consume
 *   → { success: true, remaining: 2 }
 */
