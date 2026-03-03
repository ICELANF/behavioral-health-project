/**
 * 评估工具注册表 — 量表 + 问卷统一入口
 *
 * 量表（scale）: 静态定义，key = ttm7/big5/... ，由 assessment-assignments 分配
 * 问卷（survey）: 动态从 /api/v1/surveys?status=published 加载，由 surveys/{id}/assign 分配
 *
 * 两个分配入口（detail.vue 分配弹窗 / assessment/index.vue 批次分配）
 * 均从此文件导入，保证内容一致。
 */

import { SCALES_REGISTRY, SCALE_PACKS, estimateTime, SCALE_NAME_MAP } from './scales'
import type { ScaleDef } from './scales'
import { httpReq as http } from '@/api/request'

// ─── 统一工具定义 ──────────────────────────────────────────────────────────────

export interface ToolDef {
  key: string
  type: 'scale' | 'survey'
  label: string
  shortLabel: string
  desc: string
  time: number          // 预估完成分钟
  tags: string[]
  // survey 专属
  surveyId?: number
  shortCode?: string
}

// ─── 静态量表工具（来自 scales.ts） ───────────────────────────────────────────

export const SCALE_TOOLS: ToolDef[] = SCALES_REGISTRY.map((s: ScaleDef) => ({
  key:        s.key,
  type:       'scale' as const,
  label:      s.label,
  shortLabel: s.shortLabel,
  desc:       s.desc,
  time:       s.time,
  tags:       s.tags,
}))

// ─── 动态问卷工具（从 API 加载） ──────────────────────────────────────────────

export async function loadSurveyTools(): Promise<ToolDef[]> {
  try {
    const res = await http<any>('/api/v1/surveys?status=published&limit=50')
    const surveys: any[] = res.surveys || res.items || (Array.isArray(res) ? res : [])
    return surveys.map(s => ({
      key:        'survey_' + s.id,
      type:       'survey' as const,
      label:      s.title,
      shortLabel: s.title.slice(0, 8),
      desc:       s.description || `${s.survey_type || '通用'}问卷`,
      time:       s.settings?.estimated_minutes
                    ?? (Math.round((s.avg_duration || 300) / 60) || 5),
      tags:       [s.survey_type || 'general'],
      surveyId:   s.id,
      shortCode:  s.short_code,
    }))
  } catch {
    return []
  }
}

// ─── 向下兼容 re-export ─────────────────────────────────────────────────────

export { SCALES_REGISTRY, SCALE_PACKS, estimateTime, SCALE_NAME_MAP }
export type { ScaleDef }
