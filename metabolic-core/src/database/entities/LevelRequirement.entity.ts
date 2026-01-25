import {
  Entity,
  PrimaryColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm';

/**
 * 等级要求定义实体 (配置数据)
 */
@Entity('level_requirements')
export class LevelRequirementEntity {
  @PrimaryColumn({ type: 'varchar', length: 10 })
  level: string; // L0-L4

  @Column({ type: 'varchar', length: 100 })
  name: string;

  @Column({ type: 'text' })
  description: string;

  @Column({ type: 'jsonb', default: [] })
  required_courses: object[]; // Array of { module_type, course_ids[] }

  @Column({ type: 'jsonb', default: [] })
  required_exams: object[]; // Array of { exam_type, min_score, weight_percent }

  @Column({ type: 'jsonb' })
  practice_requirements: object; // { min_cases, min_completed_paths, min_followup_months, min_improved_cases }

  @Column({ type: 'varchar', length: 10, nullable: true })
  min_platform_rating: string | null; // S, A+, A, etc.

  @Column({ type: 'jsonb', nullable: true })
  mentoring_requirements: object | null; // { min_mentees }

  @Column({ type: 'jsonb', default: [] })
  granted_permissions: object[]; // Array of { agent_type, permission_level }

  @Column({ type: 'jsonb', default: [] })
  serviceable_risk_levels: string[]; // low | medium | high

  @Column({ type: 'decimal', precision: 3, scale: 2 })
  revenue_share_ratio: number;

  @CreateDateColumn()
  created_at: Date;

  @UpdateDateColumn()
  updated_at: Date;
}
