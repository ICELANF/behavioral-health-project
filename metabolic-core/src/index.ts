/**
 * Metabolic Core - 行健行为教练代谢慢病行为健康决策系统内核
 *
 * 模块结构:
 * - Signal: 设备信号处理
 * - Trajectory: 行为轨迹建模
 * - Libraries: 知识库集合
 * - Registry: 知识注册中心
 * - Orchestrator: 决策编排器
 */

// Signal Layer
export * from './signal';

// Trajectory Layer
export * from './trajectory';

// Libraries Layer
export * from './libraries';

// Registry Layer
export * from './registry';

// Orchestrator Layer
export * from './orchestrator';

// Version
export const VERSION = '1.0.0';
export const PROJECT_NAME = '行健行为教练';
