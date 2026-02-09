import request from './request'

const BASE = '/v1/tenants'

export interface DocumentCreateData {
  title: string
  raw_content?: string
  author?: string
  domain_id?: string
  priority?: number
  evidence_tier?: string
  content_type?: string
  published_date?: string
  expires_at?: string
}

export interface DocumentUpdateData {
  title?: string
  raw_content?: string
  domain_id?: string
  priority?: number
  evidence_tier?: string
  content_type?: string
  published_date?: string
  expires_at?: string
}

export interface DocumentFilters {
  status?: string
  domain?: string
  keyword?: string
}

export const expertContentAPI = {
  // 知识文档
  listDocuments(tenantId: string, filters?: DocumentFilters) {
    return request.get(`${BASE}/${tenantId}/content/documents`, { params: filters })
  },
  getDocument(tenantId: string, docId: number) {
    return request.get(`${BASE}/${tenantId}/content/documents/${docId}`)
  },
  createDocument(tenantId: string, data: DocumentCreateData) {
    return request.post(`${BASE}/${tenantId}/content/documents`, data)
  },
  updateDocument(tenantId: string, docId: number, data: DocumentUpdateData) {
    return request.put(`${BASE}/${tenantId}/content/documents/${docId}`, data)
  },
  publishDocument(tenantId: string, docId: number) {
    return request.post(`${BASE}/${tenantId}/content/documents/${docId}/publish`)
  },
  unpublishDocument(tenantId: string, docId: number) {
    return request.post(`${BASE}/${tenantId}/content/documents/${docId}/unpublish`)
  },
  deleteDocument(tenantId: string, docId: number) {
    return request.delete(`${BASE}/${tenantId}/content/documents/${docId}`)
  },
  // 挑战活动
  listChallenges(tenantId: string) {
    return request.get(`${BASE}/${tenantId}/content/challenges`)
  },
}
