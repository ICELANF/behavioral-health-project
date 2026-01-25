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
 * 已通过考试记录实体
 */
@Entity('passed_exams')
export class PassedExamEntity {
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

  @Column({ type: 'varchar', length: 10 })
  level: string; // CertificationLevel

  @Column({ type: 'varchar', length: 50 })
  exam_type: string; // theory | case_simulation | dialogue_assessment | specialty

  @Column({ type: 'decimal', precision: 5, scale: 2 })
  score: number;

  @CreateDateColumn()
  passed_at: Date;

  @ManyToOne(() => CoachProfileEntity, (coach) => coach.passed_exams)
  @JoinColumn({ name: 'coach_id' })
  coach: CoachProfileEntity;
}
