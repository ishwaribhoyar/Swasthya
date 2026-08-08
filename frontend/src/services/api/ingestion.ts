import client from './client';
import { ApiResponse } from '@/types/api';
import {
  IDocument,
  IDocumentListItem,
  IBatchUploadSummary,
  IProcessingLog,
  IDocumentQueryParams,
} from '@/types/ingestion';

export const ingestionApi = {
  uploadBatch: async (patientId: string, files: File[]): Promise<ApiResponse<IBatchUploadSummary>> => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    return client.post(`/ingestion/patients/${patientId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  listDocuments: async (patientId: string, params?: IDocumentQueryParams): Promise<ApiResponse<IDocumentListItem[]>> => {
    return client.get(`/ingestion/patients/${patientId}/documents`, { params });
  },

  getDocument: async (documentId: string): Promise<ApiResponse<IDocument>> => {
    return client.get(`/ingestion/documents/${documentId}`);
  },

  getTimeline: async (documentId: string): Promise<ApiResponse<IProcessingLog[]>> => {
    return client.get(`/ingestion/documents/${documentId}/timeline`);
  },

  deleteDocument: async (documentId: string): Promise<void> => {
    return client.delete(`/ingestion/documents/${documentId}`);
  },

  retryDocument: async (documentId: string): Promise<any> =>
    client.post(`/ingestion/documents/${documentId}/retry`),
};
