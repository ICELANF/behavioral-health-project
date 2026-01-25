import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  Index,
} from 'typeorm';

/**
 * 考试结果详情实体 (包含逐题答案)
 */
@Entity('exam_results')
export class ExamResultEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  @Index()
  coach_id: string;

  @Column({ type: 'varchar', length: 50 })
  @Index()
  exam_id: string;

  @Column({ type: 'varchar', length: 255 })
  exam_name: string;

  @Column({ type: 'int', default: 1 })
  attempt_number: number;

  @Column({ type: 'decimal', precision: 5, scale: 2 })
  score: number;

  @Column({ type: 'decimal', precision: 5, scale: 2 })
  passing_score: number;

  @Column({ type: 'varchar', length: 20 })
  status: string; // passed | failed

  @Column({ type: 'jsonb', default: [] })
  answers: object[]; // Array of { question_id, user_answer, correct_answer, is_correct, score_earned }

  @Column({ type: 'int' })
  duration_seconds: number;

  @CreateDateColumn()
  started_at: Date;

  @Column({ type: 'timestamp' })
  submitted_at: Date;

  // Anti-cheat related fields
  @Column({ type: 'int', default: 0 })
  violation_count: number;

  @Column({ type: 'jsonb', default: [] })
  violations: object[]; // Array of violation records

  @Column({ type: 'int', default: 100 })
  integrity_score: number;

  @Column({ type: 'varchar', length: 50, default: 'valid' })
  review_status: string; // valid | flagged | invalidated
}
