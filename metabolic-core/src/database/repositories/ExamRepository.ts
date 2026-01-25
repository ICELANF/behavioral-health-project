import { Repository, DataSource, In } from 'typeorm';
import { ExamEntity } from '../entities/Exam.entity';
import { ExamResultEntity } from '../entities/ExamResult.entity';
import { QuestionEntity } from '../entities/Question.entity';

/**
 * 考试仓储
 */
export class ExamRepository {
  private examRepo: Repository<ExamEntity>;
  private resultRepo: Repository<ExamResultEntity>;
  private questionRepo: Repository<QuestionEntity>;

  constructor(dataSource: DataSource) {
    this.examRepo = dataSource.getRepository(ExamEntity);
    this.resultRepo = dataSource.getRepository(ExamResultEntity);
    this.questionRepo = dataSource.getRepository(QuestionEntity);
  }

  // Exam CRUD
  async findAllExams(filters?: { level?: string; exam_type?: string; status?: string }): Promise<ExamEntity[]> {
    const where: any = {};
    if (filters?.level) where.level = filters.level;
    if (filters?.exam_type) where.exam_type = filters.exam_type;
    if (filters?.status) where.status = filters.status;
    return this.examRepo.find({ where, order: { created_at: 'DESC' } });
  }

  async findExamById(examId: string): Promise<ExamEntity | null> {
    return this.examRepo.findOne({ where: { exam_id: examId } });
  }

  async createExam(exam: Partial<ExamEntity>): Promise<ExamEntity> {
    const entity = this.examRepo.create(exam);
    return this.examRepo.save(entity);
  }

  async updateExam(examId: string, updates: Partial<ExamEntity>): Promise<ExamEntity | null> {
    await this.examRepo.update({ exam_id: examId }, updates);
    return this.findExamById(examId);
  }

  async deleteExam(examId: string): Promise<boolean> {
    const result = await this.examRepo.delete({ exam_id: examId });
    return (result.affected ?? 0) > 0;
  }

  // Question operations
  async findQuestionsByIds(questionIds: string[]): Promise<QuestionEntity[]> {
    if (questionIds.length === 0) return [];
    return this.questionRepo.find({ where: { question_id: In(questionIds) } });
  }

  async findAllQuestions(filters?: { type?: string; level?: string; status?: string }): Promise<QuestionEntity[]> {
    const where: any = {};
    if (filters?.type) where.type = filters.type;
    if (filters?.level) where.level = filters.level;
    if (filters?.status) where.status = filters.status;
    return this.questionRepo.find({ where, order: { created_at: 'DESC' } });
  }

  async createQuestion(question: Partial<QuestionEntity>): Promise<QuestionEntity> {
    const entity = this.questionRepo.create(question);
    return this.questionRepo.save(entity);
  }

  async updateQuestion(questionId: string, updates: Partial<QuestionEntity>): Promise<QuestionEntity | null> {
    await this.questionRepo.update({ question_id: questionId }, updates);
    return this.questionRepo.findOne({ where: { question_id: questionId } });
  }

  async deleteQuestion(questionId: string): Promise<boolean> {
    const result = await this.questionRepo.delete({ question_id: questionId });
    return (result.affected ?? 0) > 0;
  }

  // Result operations
  async findResultsByExamId(examId: string): Promise<ExamResultEntity[]> {
    return this.resultRepo.find({
      where: { exam_id: examId },
      order: { submitted_at: 'DESC' },
    });
  }

  async findResultsByCoachId(coachId: string): Promise<ExamResultEntity[]> {
    return this.resultRepo.find({
      where: { coach_id: coachId },
      order: { submitted_at: 'DESC' },
    });
  }

  async createResult(result: Partial<ExamResultEntity>): Promise<ExamResultEntity> {
    const entity = this.resultRepo.create(result);
    return this.resultRepo.save(entity);
  }

  async getExamStatistics(examId: string): Promise<{
    totalAttempts: number;
    passCount: number;
    failCount: number;
    averageScore: number;
    highestScore: number;
    lowestScore: number;
  }> {
    const results = await this.resultRepo.find({ where: { exam_id: examId } });

    if (results.length === 0) {
      return {
        totalAttempts: 0,
        passCount: 0,
        failCount: 0,
        averageScore: 0,
        highestScore: 0,
        lowestScore: 0,
      };
    }

    const scores = results.map(r => Number(r.score));
    const passCount = results.filter(r => r.status === 'passed').length;

    return {
      totalAttempts: results.length,
      passCount,
      failCount: results.length - passCount,
      averageScore: scores.reduce((a, b) => a + b, 0) / scores.length,
      highestScore: Math.max(...scores),
      lowestScore: Math.min(...scores),
    };
  }
}
