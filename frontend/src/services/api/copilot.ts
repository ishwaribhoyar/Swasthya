import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import { ApiResponse } from '@/types/api';

export interface ISourceAttribution {
  record_id: string;
  title: string;
  event_date: string;
  document_type: string;
}

export interface IAmbiguousCandidate {
  id: string;
  mrn: string;
  name: string;
  date_of_birth: string;
  gender: string;
}

export interface IRAGAuditTrace {
  intent: string;
  retrieval_pathway: string;
  sources_count: number;
  confidence: string;
  grounding_passed: boolean;
  medical_safety_passed: boolean;
}

export interface IAICopilotChatRequest {
  message: string;
  patient_id?: string | null;
  conversation_id?: string | null;
}

export interface IAICopilotChatResponse {
  success: boolean;
  answer: string;
  patient_id?: string | null;
  patient_name?: string | null;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT';
  intent: string;
  sources: ISourceAttribution[];
  is_general_info?: boolean;
  ambiguous_candidates?: IAmbiguousCandidate[];
  audit_trace?: IRAGAuditTrace | null;
  disclaimer: string;
}

export const copilotApi = {
  chat: async (req: IAICopilotChatRequest): Promise<IAICopilotChatResponse> => {
    // apiClient interceptor already unwraps AxiosResponse.data -> res is ApiResponse<IAICopilotChatResponse>
    const res = await apiClient.post<ApiResponse<IAICopilotChatResponse>>(
      API_ENDPOINTS.AI_COPILOT.CHAT,
      req
    );
    return (res as unknown as ApiResponse<IAICopilotChatResponse>).data;
  },
};
