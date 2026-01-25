/**
 * Library Manager - 知识库统一管理器
 * 协调各知识库的加载、同步和访问
 */

import { knowledgeRegistry, KnowledgeType, KnowledgeMetadata } from './KnowledgeRegistry';
import {
  phenotypeMappingService,
  PhenotypeMapping,
  PREDEFINED_PHENOTYPES
} from '../libraries/PhenotypeMapping';
import {
  interventionPlaybookService,
  InterventionPlaybook,
  InterventionLever,
  PREDEFINED_PLAYBOOKS,
  PREDEFINED_LEVERS
} from '../libraries/InterventionPlaybook';
import {
  behaviorChangeEngineService,
  StageProfile,
  STAGE_PROFILES
} from '../libraries/BehaviorChangeEngine';
import {
  assessmentSurveyService,
  SurveyDefinition,
  PREDEFINED_SURVEYS
} from '../libraries/AssessmentSurvey';
import {
  contentMaterialService,
  ContentMaterial,
  CoachingScript,
  PREDEFINED_CONTENTS,
  PREDEFINED_SCRIPTS
} from '../libraries/ContentMaterial';
import {
  commercialResourceService,
  CommercialResource,
  PREDEFINED_RESOURCES
} from '../libraries/CommercialResource';
import {
  coachTrainingService,
  TrainingModule,
  CaseStudy,
  AIPromptTemplate,
  PREDEFINED_MODULES,
  PREDEFINED_CASES,
  PREDEFINED_PROMPTS
} from '../libraries/CoachTraining';

/**
 * 库加载状态
 */
export interface LibraryStatus {
  name: string;
  loaded: boolean;
  entryCount: number;
  lastSyncTime?: string;
  error?: string;
}

/**
 * 知识库统一管理器
 */
export class LibraryManager {
  private initialized: boolean = false;
  private libraryStatus: Map<string, LibraryStatus> = new Map();

  /**
   * 初始化所有知识库
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    console.log('Initializing Knowledge Libraries...');

    try {
      // 加载表型库
      await this.loadPhenotypeLibrary();

      // 加载干预剧本库
      await this.loadInterventionLibrary();

      // 加载行为改变阶段库
      await this.loadBehaviorChangeLibrary();

      // 加载评估问卷库
      await this.loadSurveyLibrary();

      // 加载内容素材库
      await this.loadContentLibrary();

      // 加载商业资源库
      await this.loadCommercialLibrary();

      // 加载教练训练库
      await this.loadTrainingLibrary();

      this.initialized = true;
      console.log('All Knowledge Libraries initialized successfully.');

    } catch (error) {
      console.error('Failed to initialize libraries:', error);
      throw error;
    }
  }

  /**
   * 加载表型库
   */
  private async loadPhenotypeLibrary(): Promise<void> {
    const libraryName = 'phenotype';

    try {
      PREDEFINED_PHENOTYPES.forEach(phenotype => {
        knowledgeRegistry.register('phenotype', phenotype.mapping_id, phenotype.phenotype_name, {
          description: phenotype.description,
          tags: [phenotype.category, phenotype.risk_level],
          keywords: [...phenotype.detected_patterns, ...phenotype.probable_behaviors],
          version: phenotype.version,
          source_library: libraryName
        });
      });

      this.libraryStatus.set(libraryName, {
        name: 'Phenotype Mapping Library',
        loaded: true,
        entryCount: PREDEFINED_PHENOTYPES.length,
        lastSyncTime: new Date().toISOString()
      });

    } catch (error) {
      this.libraryStatus.set(libraryName, {
        name: 'Phenotype Mapping Library',
        loaded: false,
        entryCount: 0,
        error: String(error)
      });
      throw error;
    }
  }

  /**
   * 加载干预剧本库
   */
  private async loadInterventionLibrary(): Promise<void> {
    const libraryName = 'intervention';

    try {
      // 注册剧本
      PREDEFINED_PLAYBOOKS.forEach(playbook => {
        knowledgeRegistry.register('intervention', playbook.playbook_id, playbook.name, {
          description: `干预周期: ${playbook.expected_duration_days}天`,
          tags: playbook.applicable_stages,
          keywords: playbook.target_phenotypes,
          version: playbook.version,
          source_library: libraryName,
          related_ids: playbook.target_phenotypes
        });
      });

      // 注册杠杆
      PREDEFINED_LEVERS.forEach(lever => {
        knowledgeRegistry.register('intervention', lever.lever_id, lever.name, {
          description: lever.description,
          tags: [lever.domain, lever.intensity],
          keywords: lever.expected_outcomes,
          version: '1.0',
          source_library: libraryName
        });
      });

      this.libraryStatus.set(libraryName, {
        name: 'Intervention Playbook Library',
        loaded: true,
        entryCount: PREDEFINED_PLAYBOOKS.length + PREDEFINED_LEVERS.length,
        lastSyncTime: new Date().toISOString()
      });

    } catch (error) {
      this.libraryStatus.set(libraryName, {
        name: 'Intervention Playbook Library',
        loaded: false,
        entryCount: 0,
        error: String(error)
      });
      throw error;
    }
  }

  /**
   * 加载行为改变阶段库
   */
  private async loadBehaviorChangeLibrary(): Promise<void> {
    const libraryName = 'behavior_stage';

    try {
      STAGE_PROFILES.forEach(profile => {
        knowledgeRegistry.register('behavior_stage', `STAGE-${profile.stage}`, profile.name_zh, {
          description: profile.description,
          tags: [...profile.recommended_strategies.slice(0, 3)],
          keywords: [...profile.characteristics, ...profile.advancement_criteria],
          version: '1.0',
          source_library: libraryName
        });
      });

      this.libraryStatus.set(libraryName, {
        name: 'Behavior Change Engine Library',
        loaded: true,
        entryCount: STAGE_PROFILES.length,
        lastSyncTime: new Date().toISOString()
      });

    } catch (error) {
      this.libraryStatus.set(libraryName, {
        name: 'Behavior Change Engine Library',
        loaded: false,
        entryCount: 0,
        error: String(error)
      });
      throw error;
    }
  }

  /**
   * 加载评估问卷库
   */
  private async loadSurveyLibrary(): Promise<void> {
    const libraryName = 'survey';

    try {
      PREDEFINED_SURVEYS.forEach(survey => {
        knowledgeRegistry.register('survey', survey.survey_id, survey.name, {
          description: survey.description,
          tags: [survey.type],
          keywords: survey.dimensions?.map(d => d.name) || [],
          version: survey.version,
          source_library: libraryName
        });
      });

      this.libraryStatus.set(libraryName, {
        name: 'Assessment Survey Library',
        loaded: true,
        entryCount: PREDEFINED_SURVEYS.length,
        lastSyncTime: new Date().toISOString()
      });

    } catch (error) {
      this.libraryStatus.set(libraryName, {
        name: 'Assessment Survey Library',
        loaded: false,
        entryCount: 0,
        error: String(error)
      });
      throw error;
    }
  }

  /**
   * 加载内容素材库
   */
  private async loadContentLibrary(): Promise<void> {
    const libraryName = 'content';

    try {
      PREDEFINED_CONTENTS.forEach(content => {
        knowledgeRegistry.register('content', content.content_id, content.title, {
          description: content.summary,
          tags: content.tags,
          keywords: content.keywords,
          version: content.version,
          source_library: libraryName
        });
      });

      PREDEFINED_SCRIPTS.forEach(script => {
        knowledgeRegistry.register('content', script.script_id, script.name, {
          description: script.scenario,
          tags: [script.stage, 'script'],
          keywords: [script.objective],
          version: script.version,
          source_library: libraryName
        });
      });

      this.libraryStatus.set(libraryName, {
        name: 'Content Material Library',
        loaded: true,
        entryCount: PREDEFINED_CONTENTS.length + PREDEFINED_SCRIPTS.length,
        lastSyncTime: new Date().toISOString()
      });

    } catch (error) {
      this.libraryStatus.set(libraryName, {
        name: 'Content Material Library',
        loaded: false,
        entryCount: 0,
        error: String(error)
      });
      throw error;
    }
  }

  /**
   * 加载商业资源库
   */
  private async loadCommercialLibrary(): Promise<void> {
    const libraryName = 'resource';

    try {
      PREDEFINED_RESOURCES.forEach(resource => {
        knowledgeRegistry.register('resource', resource.resource_id, resource.name, {
          description: resource.description,
          tags: [resource.type, resource.category],
          keywords: resource.key_benefits,
          version: '1.0',
          source_library: libraryName,
          related_ids: resource.applicable_phenotypes
        });
      });

      this.libraryStatus.set(libraryName, {
        name: 'Commercial Resource Library',
        loaded: true,
        entryCount: PREDEFINED_RESOURCES.length,
        lastSyncTime: new Date().toISOString()
      });

    } catch (error) {
      this.libraryStatus.set(libraryName, {
        name: 'Commercial Resource Library',
        loaded: false,
        entryCount: 0,
        error: String(error)
      });
      throw error;
    }
  }

  /**
   * 加载教练训练库
   */
  private async loadTrainingLibrary(): Promise<void> {
    const libraryName = 'training';

    try {
      PREDEFINED_MODULES.forEach(module => {
        knowledgeRegistry.register('training', module.module_id, module.name, {
          description: module.description,
          tags: [module.domain, module.difficulty],
          keywords: module.learning_objectives,
          version: module.version,
          source_library: libraryName,
          related_ids: module.prerequisites
        });
      });

      PREDEFINED_CASES.forEach(caseStudy => {
        knowledgeRegistry.register('training', caseStudy.case_id, caseStudy.name, {
          description: caseStudy.background.slice(0, 100),
          tags: [caseStudy.type, caseStudy.stage],
          keywords: caseStudy.learning_points,
          version: '1.0',
          source_library: libraryName,
          related_ids: caseStudy.phenotypes
        });
      });

      PREDEFINED_PROMPTS.forEach(prompt => {
        knowledgeRegistry.register('prompt', prompt.template_id, prompt.name, {
          description: prompt.scenario,
          tags: ['ai_prompt', prompt.stage || 'all'],
          keywords: prompt.variables,
          version: prompt.version,
          source_library: libraryName
        });
      });

      this.libraryStatus.set(libraryName, {
        name: 'Coach Training Library',
        loaded: true,
        entryCount: PREDEFINED_MODULES.length + PREDEFINED_CASES.length + PREDEFINED_PROMPTS.length,
        lastSyncTime: new Date().toISOString()
      });

    } catch (error) {
      this.libraryStatus.set(libraryName, {
        name: 'Coach Training Library',
        loaded: false,
        entryCount: 0,
        error: String(error)
      });
      throw error;
    }
  }

  /**
   * 获取所有库状态
   */
  getLibraryStatus(): LibraryStatus[] {
    return Array.from(this.libraryStatus.values());
  }

  /**
   * 获取总体统计
   */
  getOverallStats(): {
    totalLibraries: number;
    loadedLibraries: number;
    totalEntries: number;
    registryStats: ReturnType<typeof knowledgeRegistry.getStats>;
  } {
    const statuses = Array.from(this.libraryStatus.values());

    return {
      totalLibraries: statuses.length,
      loadedLibraries: statuses.filter(s => s.loaded).length,
      totalEntries: statuses.reduce((sum, s) => sum + s.entryCount, 0),
      registryStats: knowledgeRegistry.getStats()
    };
  }

  /**
   * 统一搜索接口
   */
  search(query: {
    keyword?: string;
    types?: KnowledgeType[];
    tags?: string[];
    limit?: number;
  }): KnowledgeMetadata[] {
    if (!this.initialized) {
      throw new Error('Library Manager not initialized. Call initialize() first.');
    }

    const results = knowledgeRegistry.search({
      keyword: query.keyword,
      types: query.types,
      tags: query.tags,
      limit: query.limit || 20
    });

    return results.map(r => r.metadata);
  }

  /**
   * 获取表型服务
   */
  getPhenotypeService() {
    return phenotypeMappingService;
  }

  /**
   * 获取干预服务
   */
  getInterventionService() {
    return interventionPlaybookService;
  }

  /**
   * 获取行为改变服务
   */
  getBehaviorChangeService() {
    return behaviorChangeEngineService;
  }

  /**
   * 获取评估服务
   */
  getAssessmentService() {
    return assessmentSurveyService;
  }

  /**
   * 获取内容服务
   */
  getContentService() {
    return contentMaterialService;
  }

  /**
   * 获取商业资源服务
   */
  getCommercialService() {
    return commercialResourceService;
  }

  /**
   * 获取训练服务
   */
  getTrainingService() {
    return coachTrainingService;
  }

  /**
   * 检查是否已初始化
   */
  isInitialized(): boolean {
    return this.initialized;
  }

  /**
   * 重新加载指定库
   */
  async reloadLibrary(libraryName: string): Promise<void> {
    switch (libraryName) {
      case 'phenotype':
        await this.loadPhenotypeLibrary();
        break;
      case 'intervention':
        await this.loadInterventionLibrary();
        break;
      case 'behavior_stage':
        await this.loadBehaviorChangeLibrary();
        break;
      case 'survey':
        await this.loadSurveyLibrary();
        break;
      case 'content':
        await this.loadContentLibrary();
        break;
      case 'resource':
        await this.loadCommercialLibrary();
        break;
      case 'training':
        await this.loadTrainingLibrary();
        break;
      default:
        throw new Error(`Unknown library: ${libraryName}`);
    }
  }
}

// 导出单例
export const libraryManager = new LibraryManager();
