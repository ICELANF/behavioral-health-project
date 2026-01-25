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
 * Agent权限实体
 */
@Entity('agent_permissions')
export class AgentPermissionEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'uuid' })
  @Index()
  coach_id: string;

  @Column({ type: 'varchar', length: 100 })
  agent_type: string;

  @Column({ type: 'varchar', length: 20 })
  permission_level: string; // read | execute | configure

  @CreateDateColumn()
  granted_at: Date;

  @ManyToOne(() => CoachProfileEntity, (coach) => coach.agent_permissions)
  @JoinColumn({ name: 'coach_id' })
  coach: CoachProfileEntity;
}
