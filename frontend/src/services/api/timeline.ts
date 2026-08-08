import client from './client';
import { ApiResponse } from '@/types/api';

export interface ITimelineEvent {
  id: string;
  patient_id: string;
  source_record_id: string;
  event_date: string;
  event_date_type: string;
  event_date_confidence: number;
  event_type: string;
  document_type: string;
  title: string;
  summary: string;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface IVisitGroup {
  visit_date: string;
  visit_title: string;
  events: ITimelineEvent[];
  event_count: number;
}

export interface ITimelineQueryParams {
  search?: string;
  doc_type?: string;
  event_type?: string;
  from_date?: string;
  to_date?: string;
  sort_order?: 'asc' | 'desc';
}

export const timelineApi = {
  getPatientTimeline: (patientId: string, params?: ITimelineQueryParams) =>
    client.get<any, ApiResponse<IVisitGroup[]>>(`/timeline/patients/${patientId}`, { params }),

  getEventDetails: (patientId: string, eventId: string) =>
    client.get<any, ApiResponse<ITimelineEvent>>(`/timeline/patients/${patientId}/${eventId}`),
};
