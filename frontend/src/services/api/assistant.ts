import client from './client';
import { ApiResponse } from '@/types/api';

export interface ISourceCitation {
  doc_id: string;

  filename: string;
  category: string;
  header: string;
  snippet: string;
  relevance_score: number;
}

export interface IAIQueryResponse {
  id: string;
  patient_id: string;
  query: string;
  answer: string;
  confidence_score: number;
  sources: ISourceCitation[];
  audit_hash: string;
  created_at: string;
}

export const assistantApi = {
  query: async (patientId: string, query: string): Promise<ApiResponse<IAIQueryResponse>> =>
    client.post('/ai-copilot/query', { patient_id: patientId, query }),

  getHistory: async (patientId: string): Promise<ApiResponse<IAIQueryResponse[]>> =>
    client.get(`/ai-copilot/patients/${patientId}/history`),
};
