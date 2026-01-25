import {
  Entity,
  PrimaryColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
} from 'typeorm';

/**
 * 考试定义实体 (主数据)
 */
@Entity('exams')
export class ExamEntity {
  @PrimaryColumn({ type: 'varchar', length: 50 })
  exam_id: string;

  @Column({ type: 'varchar', length: 255 })
  exam_name: string;

  @Column({ type: 'varchar', length: 10 })
  @Index()
  level: string; // L0-L4

  @Column({ type: 'varchar', length: 50 })
  @Index()
  exam_type: string; // theory | case_simulation | dialogue_assessment | specialty

  @Column({ type: 'decimal', precision: 5, scale: 2 })
  passing_score: number;

  @Column({ type: 'decimal', precision: 5, scale: 2 })
  weight_percent: number;

  @Column({ type: 'int', nullable: true })
  duration_minutes: number | null;

  @Column({ type: 'int', nullable: true })
  questions_count: number | null;

  @Column({ type: 'varchar', length: 50, nullable: true })
  specialty: string | null; // SpecialtyTag

  @Column({ type: 'text', nullable: true })
  description: string | null;

  @Column({ type: 'text', nullable: true })
  instructions: string | null;

  @Column({ type: 'jsonb', default: [] })
  question_ids: string[]; // References to questions

  @Column({ type: 'varchar', length: 50, default: 'draft' })
  @Index()
  status: string; // draft | published | archived

  @Column({ type: 'int', default: 1 })
  max_attempts: number;

  @Column({ type: 'boolean', default: true })
  allow_retry: boolean;

  @CreateDateColumn()
  created_at: Date;

  @UpdateDateColumn()
  updated_at: Date;
}
