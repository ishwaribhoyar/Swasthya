import client from './client';
import { ApiResponse } from '@/types/api';
import {
  IDocument,
  IDocumentListItem,
  IDocumentProvenance,
  IBatchUploadSummary,
  IProcessingLog,
  IDocumentQueryParams,
} from '@/types/ingestion';

// Base URL for the backend — used for constructing direct file URLs
const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api/v1';

export const ingestionApi = {
  uploadBatch: async (patientId: string, files: File[]): Promise<ApiResponse<IBatchUploadSummary>> => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    return client.post(`/ingestion/patients/${patientId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  listDocuments: async (patientId: string, params?: IDocumentQueryParams): Promise<ApiResponse<IDocumentListItem[]>> =>
    client.get(`/ingestion/patients/${patientId}/documents`, { params }),

  getDocument: async (documentId: string): Promise<ApiResponse<IDocument>> =>
    client.get(`/ingestion/documents/${documentId}`),

  getDocumentProvenance: async (documentId: string): Promise<ApiResponse<IDocumentProvenance>> =>
    client.get(`/ingestion/documents/${documentId}/provenance`),

  getTimeline: async (documentId: string): Promise<ApiResponse<IProcessingLog[]>> =>
    client.get(`/ingestion/documents/${documentId}/timeline`),

  deleteDocument: async (documentId: string): Promise<void> =>
    client.delete(`/ingestion/documents/${documentId}`),

  retryDocument: async (documentId: string): Promise<any> =>
    client.post(`/ingestion/documents/${documentId}/retry`),

  /**
   * Returns the URL for the original file content endpoint.
   * The browser will stream this with the Authorization header via a
   * client-side fetch (for blob URL) since we cannot pass headers in
   * a native <img> or <object> src.
   */
  getContentUrl: (documentId: string): string =>
    `${API_BASE}/ingestion/documents/${documentId}/content`,

  /**
   * Fetch original file bytes as a Blob URL for rendering in the browser.
   * This is needed because <img src> / <object data> cannot send Authorization headers.
   */
  fetchContentBlob: async (documentId: string): Promise<string> => {
    // Use the same axios instance so auth headers are applied automatically
    const res = await client.get(`/ingestion/documents/${documentId}/content`, {
      responseType: 'blob',
    });
    return URL.createObjectURL(res as unknown as Blob);
  },
};
