export type Stage = 'AWARENESS' | 'ACTION' | 'STABILIZATION' | 'RELAPSE';

export type CompletionState = 'PENDING' | 'DONE' | 'ATTEMPTED' | 'SKIPPED';

export interface StageConfig {
  label: string;
  description: string;
  taskTitle: string;
  gradientFrom: string;
  gradientTo: string;
  textColor: string;
  icon: string;
}

export const STAGE_CONFIG: Record<Stage, StageConfig> = {
  AWARENESS: {
    label: '觉察者',
    description: '看见，就是改变的开始。',
    taskTitle: '今天只需要记录，不需要改变',
    gradientFrom: '#7dd3fc',
    gradientTo: '#38bdf8',
    textColor: '#0c4a6e',
    icon: '👁️',
  },
  ACTION: {
    label: '行动者',
    description: '你正在真实的生活中迈出步伐。',
    taskTitle: '今天只做这一件事',
    gradientFrom: '#6ee7b7',
    gradientTo: '#34d399',
    textColor: '#065f46',
    icon: '🚀',
  },
  STABILIZATION: {
    label: '稳定者',
    description: '节奏感比爆发力更重要。',
    taskTitle: '保持你的节奏',
    gradientFrom: '#60a5fa',
    gradientTo: '#3b82f6',
    textColor: '#1e40af',
    icon: '⚖️',
  },
  RELAPSE: {
    label: '调整者',
    description: '暂停是为了更好地出发。',
    taskTitle: '做一件最小的事来找回感觉',
    gradientFrom: '#fcd34d',
    gradientTo: '#fbbf24',
    textColor: '#92400e',
    icon: '🔄',
  }
};
