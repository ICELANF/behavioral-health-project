/**
 * Knowledge Registry - 知识注册中心
 * 统一管理所有知识库的注册、索引和查询
 */

import { v4 as uuidv4 } from 'uuid';

/**
 * 知识类型
 */
export type KnowledgeType =
  | 'phenotype'
  | 'intervention'
  | 'behavior_stage'
  | 'survey'
  | 'content'
  | 'resource'
  | 'training'
  | 'prompt';

/**
 * 知识条目元数据
 */
export interface KnowledgeMetadata {
  /** 条目ID */
  id: string;
  /** 类型 */
  type: KnowledgeType;
  /** 名称 */
  name: string;
  /** 描述 */
  description?: string;
  /** 标签 */
  tags: string[];
  /** 关键词 */
  keywords: string[];
  /** 版本 */
  version: string;
  /** 创建时间 */
  created_at: string;
  /** 更新时间 */
  updated_at?: string;
  /** 引用来源 */
  source_library: string;
  /** 相关条目 */
  related_ids?: string[];
  /** 使用次数 */
  usage_count: number;
  /** 评分 */
  rating?: number;
}

/**
 * 知识索引
 */
export interface KnowledgeIndex {
  /** 按类型索引 */
  byType: Map<KnowledgeType, Set<string>>;
  /** 按标签索引 */
  byTag: Map<string, Set<string>>;
  /** 按关键词索引 */
  byKeyword: Map<string, Set<string>>;
  /** 全文搜索索引 */
  fullText: Map<string, string[]>; // id -> searchable terms
}

/**
 * 搜索查询
 */
export interface SearchQuery {
  /** 关键词 */
  keyword?: string;
  /** 类型过滤 */
  types?: KnowledgeType[];
  /** 标签过滤 */
  tags?: string[];
  /** 最低评分 */
  minRating?: number;
  /** 排序方式 */
  sortBy?: 'relevance' | 'usage' | 'rating' | 'date';
  /** 分页 */
  limit?: number;
  offset?: number;
}

/**
 * 搜索结果
 */
export interface SearchResult {
  /** 条目ID */
  id: string;
  /** 元数据 */
  metadata: KnowledgeMetadata;
  /** 相关度分数 */
  relevance_score: number;
  /** 匹配片段 */
  matched_snippets?: string[];
}

/**
 * 知识注册中心
 */
export class KnowledgeRegistry {
  private entries: Map<string, KnowledgeMetadata> = new Map();
  private index: KnowledgeIndex = {
    byType: new Map(),
    byTag: new Map(),
    byKeyword: new Map(),
    fullText: new Map()
  };

  /**
   * 注册知识条目
   */
  register(
    type: KnowledgeType,
    id: string,
    name: string,
    options: {
      description?: string;
      tags?: string[];
      keywords?: string[];
      version?: string;
      source_library: string;
      related_ids?: string[];
    }
  ): KnowledgeMetadata {
    const metadata: KnowledgeMetadata = {
      id,
      type,
      name,
      description: options.description,
      tags: options.tags || [],
      keywords: options.keywords || [],
      version: options.version || '1.0',
      created_at: new Date().toISOString(),
      source_library: options.source_library,
      related_ids: options.related_ids,
      usage_count: 0
    };

    this.entries.set(id, metadata);
    this.updateIndex(metadata);

    return metadata;
  }

  /**
   * 更新索引
   */
  private updateIndex(metadata: KnowledgeMetadata): void {
    // 按类型索引
    if (!this.index.byType.has(metadata.type)) {
      this.index.byType.set(metadata.type, new Set());
    }
    this.index.byType.get(metadata.type)!.add(metadata.id);

    // 按标签索引
    for (const tag of metadata.tags) {
      const normalizedTag = tag.toLowerCase();
      if (!this.index.byTag.has(normalizedTag)) {
        this.index.byTag.set(normalizedTag, new Set());
      }
      this.index.byTag.get(normalizedTag)!.add(metadata.id);
    }

    // 按关键词索引
    for (const keyword of metadata.keywords) {
      const normalizedKeyword = keyword.toLowerCase();
      if (!this.index.byKeyword.has(normalizedKeyword)) {
        this.index.byKeyword.set(normalizedKeyword, new Set());
      }
      this.index.byKeyword.get(normalizedKeyword)!.add(metadata.id);
    }

    // 全文搜索索引
    const searchTerms = [
      metadata.name,
      metadata.description || '',
      ...metadata.tags,
      ...metadata.keywords
    ].map(s => s.toLowerCase());
    this.index.fullText.set(metadata.id, searchTerms);
  }

  /**
   * 搜索知识
   */
  search(query: SearchQuery): SearchResult[] {
    let candidateIds: Set<string> | null = null;

    // 按类型过滤
    if (query.types && query.types.length > 0) {
      candidateIds = new Set();
      for (const type of query.types) {
        const typeIds = this.index.byType.get(type);
        if (typeIds) {
          typeIds.forEach(id => candidateIds!.add(id));
        }
      }
    }

    // 按标签过滤
    if (query.tags && query.tags.length > 0) {
      const tagIds = new Set<string>();
      for (const tag of query.tags) {
        const ids = this.index.byTag.get(tag.toLowerCase());
        if (ids) {
          ids.forEach(id => tagIds.add(id));
        }
      }
      if (candidateIds === null) {
        candidateIds = tagIds;
      } else {
        candidateIds = new Set([...candidateIds].filter(id => tagIds.has(id)));
      }
    }

    // 如果没有过滤条件，使用所有条目
    if (candidateIds === null) {
      candidateIds = new Set(this.entries.keys());
    }

    // 构建结果
    let results: SearchResult[] = [];

    for (const id of candidateIds) {
      const metadata = this.entries.get(id);
      if (!metadata) continue;

      // 最低评分过滤
      if (query.minRating && (!metadata.rating || metadata.rating < query.minRating)) {
        continue;
      }

      // 计算相关度
      let relevanceScore = 1;
      const matchedSnippets: string[] = [];

      if (query.keyword) {
        const searchTerms = this.index.fullText.get(id) || [];
        const keyword = query.keyword.toLowerCase();
        const matchCount = searchTerms.filter(term => term.includes(keyword)).length;

        if (matchCount === 0) continue;

        relevanceScore = matchCount / searchTerms.length;
        matchedSnippets.push(...searchTerms.filter(term => term.includes(keyword)));
      }

      results.push({
        id,
        metadata,
        relevance_score: relevanceScore,
        matched_snippets: matchedSnippets.length > 0 ? matchedSnippets : undefined
      });
    }

    // 排序
    switch (query.sortBy) {
      case 'usage':
        results.sort((a, b) => b.metadata.usage_count - a.metadata.usage_count);
        break;
      case 'rating':
        results.sort((a, b) => (b.metadata.rating || 0) - (a.metadata.rating || 0));
        break;
      case 'date':
        results.sort((a, b) =>
          new Date(b.metadata.created_at).getTime() - new Date(a.metadata.created_at).getTime()
        );
        break;
      case 'relevance':
      default:
        results.sort((a, b) => b.relevance_score - a.relevance_score);
        break;
    }

    // 分页
    const offset = query.offset || 0;
    const limit = query.limit || 20;
    results = results.slice(offset, offset + limit);

    return results;
  }

  /**
   * 获取条目
   */
  get(id: string): KnowledgeMetadata | undefined {
    return this.entries.get(id);
  }

  /**
   * 按类型获取所有条目
   */
  getByType(type: KnowledgeType): KnowledgeMetadata[] {
    const ids = this.index.byType.get(type);
    if (!ids) return [];

    return Array.from(ids)
      .map(id => this.entries.get(id))
      .filter((m): m is KnowledgeMetadata => m !== undefined);
  }

  /**
   * 更新条目
   */
  update(id: string, updates: Partial<KnowledgeMetadata>): boolean {
    const existing = this.entries.get(id);
    if (!existing) return false;

    const updated = {
      ...existing,
      ...updates,
      id: existing.id, // 保持ID不变
      updated_at: new Date().toISOString()
    };

    this.entries.set(id, updated);

    // 如果标签或关键词变化，重建索引
    if (updates.tags || updates.keywords) {
      this.rebuildIndexForEntry(updated);
    }

    return true;
  }

  /**
   * 重建单条目索引
   */
  private rebuildIndexForEntry(metadata: KnowledgeMetadata): void {
    // 从旧索引中移除
    this.index.byTag.forEach((ids, tag) => ids.delete(metadata.id));
    this.index.byKeyword.forEach((ids, keyword) => ids.delete(metadata.id));

    // 重新添加到索引
    for (const tag of metadata.tags) {
      const normalizedTag = tag.toLowerCase();
      if (!this.index.byTag.has(normalizedTag)) {
        this.index.byTag.set(normalizedTag, new Set());
      }
      this.index.byTag.get(normalizedTag)!.add(metadata.id);
    }

    for (const keyword of metadata.keywords) {
      const normalizedKeyword = keyword.toLowerCase();
      if (!this.index.byKeyword.has(normalizedKeyword)) {
        this.index.byKeyword.set(normalizedKeyword, new Set());
      }
      this.index.byKeyword.get(normalizedKeyword)!.add(metadata.id);
    }

    // 更新全文索引
    const searchTerms = [
      metadata.name,
      metadata.description || '',
      ...metadata.tags,
      ...metadata.keywords
    ].map(s => s.toLowerCase());
    this.index.fullText.set(metadata.id, searchTerms);
  }

  /**
   * 记录使用
   */
  recordUsage(id: string): void {
    const metadata = this.entries.get(id);
    if (metadata) {
      metadata.usage_count++;
    }
  }

  /**
   * 更新评分
   */
  updateRating(id: string, rating: number): void {
    const metadata = this.entries.get(id);
    if (metadata) {
      metadata.rating = rating;
    }
  }

  /**
   * 删除条目
   */
  delete(id: string): boolean {
    const metadata = this.entries.get(id);
    if (!metadata) return false;

    // 从索引中移除
    this.index.byType.get(metadata.type)?.delete(id);
    this.index.byTag.forEach(ids => ids.delete(id));
    this.index.byKeyword.forEach(ids => ids.delete(id));
    this.index.fullText.delete(id);

    // 删除条目
    this.entries.delete(id);

    return true;
  }

  /**
   * 获取统计信息
   */
  getStats(): {
    totalEntries: number;
    byType: Record<string, number>;
    topTags: { tag: string; count: number }[];
    avgRating: number;
  } {
    const byType: Record<string, number> = {};
    for (const [type, ids] of this.index.byType.entries()) {
      byType[type] = ids.size;
    }

    const tagCounts: { tag: string; count: number }[] = [];
    for (const [tag, ids] of this.index.byTag.entries()) {
      tagCounts.push({ tag, count: ids.size });
    }
    tagCounts.sort((a, b) => b.count - a.count);

    let ratingSum = 0;
    let ratingCount = 0;
    for (const metadata of this.entries.values()) {
      if (metadata.rating !== undefined) {
        ratingSum += metadata.rating;
        ratingCount++;
      }
    }

    return {
      totalEntries: this.entries.size,
      byType,
      topTags: tagCounts.slice(0, 10),
      avgRating: ratingCount > 0 ? ratingSum / ratingCount : 0
    };
  }

  /**
   * 获取相关知识
   */
  getRelated(id: string, limit: number = 5): KnowledgeMetadata[] {
    const metadata = this.entries.get(id);
    if (!metadata) return [];

    // 通过标签和关键词找相关条目
    const relatedIds = new Map<string, number>(); // id -> score

    for (const tag of metadata.tags) {
      const ids = this.index.byTag.get(tag.toLowerCase());
      if (ids) {
        ids.forEach(relId => {
          if (relId !== id) {
            relatedIds.set(relId, (relatedIds.get(relId) || 0) + 2);
          }
        });
      }
    }

    for (const keyword of metadata.keywords) {
      const ids = this.index.byKeyword.get(keyword.toLowerCase());
      if (ids) {
        ids.forEach(relId => {
          if (relId !== id) {
            relatedIds.set(relId, (relatedIds.get(relId) || 0) + 1);
          }
        });
      }
    }

    // 排序并返回
    const sorted = Array.from(relatedIds.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, limit)
      .map(([relId]) => this.entries.get(relId))
      .filter((m): m is KnowledgeMetadata => m !== undefined);

    return sorted;
  }
}

// 导出单例
export const knowledgeRegistry = new KnowledgeRegistry();
