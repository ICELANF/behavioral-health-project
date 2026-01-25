import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
} from 'typeorm';

/**
 * 题目实体 (题库)
 */
@Entity('questions')
export class QuestionEntity {
  @PrimaryGeneratedColumn('uuid')
  question_id: string;

  @Column({ type: 'text' })
  content: string;

  @Column({ type: 'varchar', length: 20 })
  @Index()
  type: string; // single | multiple | truefalse | short_answer

  @Column({ type: 'varchar', length: 10 })
  @Index()
  level: string; // L0-L4

  @Column({ type: 'int', default: 3 })
  difficulty: number; // 1-5

  @Column({ type: 'jsonb', nullable: true })
  options: string[] | null; // Array of options for choice questions

  @Column({ type: 'jsonb', nullable: true })
  answer: any; // number for single, number[] for multiple, boolean for truefalse, string for short_answer

  @Column({ type: 'text', nullable: true })
  explanation: string | null;

  @Column({ type: 'jsonb', default: [] })
  tags: string[];

  @Column({ type: 'varchar', length: 50, nullable: true })
  category: string | null; // knowledge | method | skill | value

  @Column({ type: 'int', default: 0 })
  use_count: number;

  @Column({ type: 'decimal', precision: 5, scale: 2, default: 1 })
  default_score: number;

  @Column({ type: 'varchar', length: 50, default: 'active' })
  @Index()
  status: string; // active | inactive

  @CreateDateColumn()
  created_at: Date;

  @UpdateDateColumn()
  updated_at: Date;
}
