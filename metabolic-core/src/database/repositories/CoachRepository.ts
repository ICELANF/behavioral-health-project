import { Repository, DataSource } from 'typeorm';
import { CoachProfileEntity } from '../entities/CoachProfile.entity';

/**
 * 教练档案仓储
 */
export class CoachRepository {
  private repository: Repository<CoachProfileEntity>;

  constructor(dataSource: DataSource) {
    this.repository = dataSource.getRepository(CoachProfileEntity);
  }

  async findById(coachId: string): Promise<CoachProfileEntity | null> {
    return this.repository.findOne({
      where: { coach_id: coachId },
      relations: ['completed_courses', 'passed_exams', 'agent_permissions', 'mentoring_records', 'cases'],
    });
  }

  async findByUserId(userId: string): Promise<CoachProfileEntity | null> {
    return this.repository.findOne({
      where: { user_id: userId },
      relations: ['completed_courses', 'passed_exams'],
    });
  }

  async findByLevel(level: string): Promise<CoachProfileEntity[]> {
    return this.repository.find({
      where: { level },
      relations: ['completed_courses', 'passed_exams'],
    });
  }

  async findAll(): Promise<CoachProfileEntity[]> {
    return this.repository.find({
      relations: ['completed_courses', 'passed_exams'],
    });
  }

  async create(profile: Partial<CoachProfileEntity>): Promise<CoachProfileEntity> {
    const entity = this.repository.create(profile);
    return this.repository.save(entity);
  }

  async update(coachId: string, updates: Partial<CoachProfileEntity>): Promise<CoachProfileEntity | null> {
    await this.repository.update({ coach_id: coachId }, updates);
    return this.findById(coachId);
  }

  async delete(coachId: string): Promise<boolean> {
    const result = await this.repository.delete({ coach_id: coachId });
    return (result.affected ?? 0) > 0;
  }
}
