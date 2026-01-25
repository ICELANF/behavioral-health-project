import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  Index,
} from 'typeorm';

/**
 * 智能陪练会话实体
 */
@Entity('training_sessions')
export class TrainingSessionEntity {
  @PrimaryGeneratedColumn('uuid')
  session_id: string;

  @Column({ type: 'uuid' })
  @Index()
  coach_id: string;

  @Column({ type: 'varchar', length: 50 })
  session_type: string; // ai_simulation | resistance_scenario | dialogue_practice | path_review

  @Column({ type: 'jsonb' })
  scenario: object; // { scenario_id, scenario_name, difficulty, client_profile, presenting_issue, expected_approach }

  @Column({ type: 'jsonb', default: [] })
  dialogue_turns: object[]; // Array of { turn, speaker, content, timestamp }

  @Column({ type: 'jsonb', nullable: true })
  ai_feedback: object | null; // { overall_score, strengths, improvements, specific_feedback }

  @Column({ type: 'varchar', length: 50, default: 'in_progress' })
  @Index()
  status: string; // in_progress | completed | abandoned

  @CreateDateColumn()
  started_at: Date;

  @Column({ type: 'timestamp', nullable: true })
  completed_at: Date | null;
}
