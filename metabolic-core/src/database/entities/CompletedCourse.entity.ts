import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
} from 'typeorm';
import { CoachProfileEntity } from './CoachProfile.entity';

/**
 * 已完成课程记录实体
 */
@Entity('completed_courses')
export class CompletedCourseEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  @Index()
  coach_id: string;

  @Column({ type: 'varchar', length: 50 })
  @Index()
  course_id: string;

  @Column({ type: 'varchar', length: 255 })
  course_name: string;

  @Column({ type: 'varchar', length: 10 })
  level: string; // CertificationLevel

  @Column({ type: 'varchar', length: 50 })
  module_type: string; // knowledge | method | skill | value

  @Column({ type: 'decimal', precision: 5, scale: 2, nullable: true })
  score: number | null;

  @CreateDateColumn()
  completed_at: Date;

  @ManyToOne(() => CoachProfileEntity, (coach) => coach.completed_courses)
  @JoinColumn({ name: 'coach_id' })
  coach: CoachProfileEntity;
}
