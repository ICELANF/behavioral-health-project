import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
} from 'typeorm';

/**
 * 晋级申请实体
 */
@Entity('promotion_applications')
export class PromotionApplicationEntity {
  @PrimaryGeneratedColumn('uuid')
  application_id: string;

  @Column({ type: 'uuid' })
  @Index()
  coach_id: string;

  @Column({ type: 'varchar', length: 10 })
  current_level: string; // L0-L4

  @Column({ type: 'varchar', length: 10 })
  target_level: string; // L0-L4

  @Column({ type: 'varchar', length: 50, default: 'pending' })
  @Index()
  status: string; // pending | under_review | approved | rejected | need_supplement

  @Column({ type: 'jsonb', nullable: true })
  review_result: object | null; // { reviewer_id, reviewed_at, decision, comments, recommended_modules }

  @Column({ type: 'jsonb' })
  evidence: object; // { theory_scores, skill_scores, case_ids, platform_rating, additional_documents }

  @CreateDateColumn()
  submitted_at: Date;

  @UpdateDateColumn()
  updated_at: Date;
}
