import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToMany,
  Index,
} from 'typeorm';
import { CompletedCourseEntity } from './CompletedCourse.entity';
import { PassedExamEntity } from './PassedExam.entity';
import { AgentPermissionEntity } from './AgentPermission.entity';
import { MentoringRecordEntity } from './MentoringRecord.entity';
import { CoachCaseEntity } from './CoachCase.entity';

/**
 * 教练档案实体
 */
@Entity('coach_profiles')
export class CoachProfileEntity {
  @PrimaryGeneratedColumn('uuid')
  coach_id: string;

  @Column({ type: 'varchar', length: 255 })
  @Index()
  user_id: string;

  @Column({ type: 'varchar', length: 255 })
  name: string;

  @Column({ type: 'varchar', length: 10, default: 'L0' })
  @Index()
  level: string; // CertificationLevel

  @Column({ type: 'jsonb', default: [] })
  specialty_tags: string[]; // SpecialtyTag[]

  @Column({ type: 'jsonb' })
  competency: object; // CoachCompetencyModel

  @Column({ type: 'decimal', precision: 5, scale: 2, default: 0 })
  quality_score: number;

  @Column({ type: 'varchar', length: 10, default: 'C' })
  platform_rating: string; // S, A+, A, A-, B+, B, B-, C, D

  @Column({ type: 'jsonb', default: [] })
  serviceable_risk_levels: string[]; // 'low' | 'medium' | 'high'

  @Column({ type: 'decimal', precision: 3, scale: 2, default: 0 })
  revenue_share_ratio: number;

  @Column({ type: 'varchar', length: 50, default: 'active' })
  @Index()
  status: string; // active | inactive | suspended | pending_review

  @CreateDateColumn()
  registered_at: Date;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  level_achieved_at: Date;

  @UpdateDateColumn()
  updated_at: Date;

  // Relations
  @OneToMany(() => CompletedCourseEntity, (course) => course.coach)
  completed_courses: CompletedCourseEntity[];

  @OneToMany(() => PassedExamEntity, (exam) => exam.coach)
  passed_exams: PassedExamEntity[];

  @OneToMany(() => AgentPermissionEntity, (perm) => perm.coach)
  agent_permissions: AgentPermissionEntity[];

  @OneToMany(() => MentoringRecordEntity, (record) => record.supervisor)
  mentoring_records: MentoringRecordEntity[];

  @OneToMany(() => CoachCaseEntity, (c) => c.coach)
  cases: CoachCaseEntity[];
}
