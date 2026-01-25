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
 * 带教记录实体
 */
@Entity('mentoring_records')
export class MentoringRecordEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  @Index()
  supervisor_id: string; // coach_id of the supervisor/mentor

  @Column({ type: 'varchar', length: 255 })
  mentee_id: string;

  @Column({ type: 'varchar', length: 255 })
  mentee_name: string;

  @Column({ type: 'date' })
  start_date: Date;

  @Column({ type: 'date', nullable: true })
  end_date: Date | null;

  @Column({ type: 'varchar', length: 20, nullable: true })
  outcome: string | null; // promoted | ongoing | dropped

  @Column({ type: 'text', nullable: true })
  supervisor_notes: string | null;

  @CreateDateColumn()
  created_at: Date;

  @ManyToOne(() => CoachProfileEntity, (coach) => coach.mentoring_records)
  @JoinColumn({ name: 'supervisor_id' })
  supervisor: CoachProfileEntity;
}
