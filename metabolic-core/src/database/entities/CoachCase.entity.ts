import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
} from 'typeorm';
import { CoachProfileEntity } from './CoachProfile.entity';

/**
 * 教练案例实体
 */
@Entity('coach_cases')
export class CoachCaseEntity {
  @PrimaryGeneratedColumn('uuid')
  case_id: string;

  @Column({ type: 'uuid' })
  @Index()
  coach_id: string;

  @Column({ type: 'varchar', length: 255 })
  @Index()
  user_id: string; // Client user_id

  @Column({ type: 'varchar', length: 20 })
  risk_type: string; // low | medium | high

  @Column({ type: 'jsonb', default: [] })
  primary_issues: string[];

  @Column({ type: 'jsonb' })
  intervention_path: object; // { path_id, path_name, duration_days, phases[] }

  @Column({ type: 'jsonb', default: [] })
  outcome_metrics: object[]; // Array of { metric, baseline, final, improvement_percent }

  @Column({ type: 'decimal', precision: 5, scale: 2, nullable: true })
  supervisor_score: number | null;

  @Column({ type: 'text', nullable: true })
  supervisor_comments: string | null;

  @Column({ type: 'varchar', length: 50, default: 'ongoing' })
  @Index()
  status: string; // ongoing | completed | abandoned

  @Column({ type: 'date' })
  start_date: Date;

  @Column({ type: 'date', nullable: true })
  end_date: Date | null;

  @Column({ type: 'int', nullable: true })
  followup_months: number | null;

  @Column({ type: 'decimal', precision: 5, scale: 2, nullable: true })
  dialogue_quality_score: number | null;

  @Column({ type: 'decimal', precision: 5, scale: 2, nullable: true })
  client_satisfaction: number | null;

  @CreateDateColumn()
  created_at: Date;

  @UpdateDateColumn()
  updated_at: Date;

  @ManyToOne(() => CoachProfileEntity, (coach) => coach.cases)
  @JoinColumn({ name: 'coach_id' })
  coach: CoachProfileEntity;
}
