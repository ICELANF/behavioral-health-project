import {
  Entity,
  PrimaryColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
} from 'typeorm';

/**
 * 课程定义实体 (主数据)
 */
@Entity('courses')
export class CourseEntity {
  @PrimaryColumn({ type: 'varchar', length: 50 })
  course_id: string;

  @Column({ type: 'varchar', length: 255 })
  course_name: string;

  @Column({ type: 'varchar', length: 10 })
  @Index()
  level: string; // L0-L4

  @Column({ type: 'varchar', length: 50 })
  @Index()
  module_type: string; // knowledge | method | skill | value

  @Column({ type: 'text' })
  description: string;

  @Column({ type: 'int' })
  duration_minutes: number;

  @Column({ type: 'varchar', length: 50 })
  content_format: string; // video | interactive | case_study | simulation

  @Column({ type: 'jsonb', default: [] })
  prerequisites: string[]; // Array of course_ids

  @Column({ type: 'jsonb', default: [] })
  learning_objectives: string[];

  @Column({ type: 'jsonb', default: [] })
  assessment_criteria: string[];

  @Column({ type: 'varchar', length: 500, nullable: true })
  cover_image: string | null;

  @Column({ type: 'varchar', length: 50, default: 'published' })
  status: string; // draft | published | archived

  @Column({ type: 'int', default: 0 })
  sort_order: number;

  @CreateDateColumn()
  created_at: Date;

  @UpdateDateColumn()
  updated_at: Date;
}
