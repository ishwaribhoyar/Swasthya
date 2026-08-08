import client from './client';
import { ApiResponse } from '@/types/api';

// ── Observation (single clinical measurement) ──────────────────────────────
export interface IClinicalObservation {
  name: string;
  value: number | null;
  value_str: string;
  unit: string;
  status: 'NORMAL' | 'HIGH' | 'LOW' | 'CRITICAL_HIGH' | 'CRITICAL_LOW' | 'UNKNOWN';
  reference_range?: string | null;
  category: 'lab' | 'vitals' | 'medicine';
}

// ── One encounter (reconstructed from one document) ────────────────────────
export interface IClinicalEncounter {
  id: string;
  event_date: string;
  display_date: string;
  event_type: string;
  document_type: string;
  title: string;
  summary?: string | null;
  processing_incomplete: boolean;
  processing_reason?: string | null;
  date_priority_source: string;
  confidence: number;
  observations: IClinicalObservation[];
  record_id?: string | null;
}

// ── Visit group (all encounters on one calendar date) ──────────────────────
export interface IVisitGroup {
  visit_date: string;
  display_date: string;
  day_label: string;
  event_count: number;
  observation_count: number;
  incomplete_count: number;
  categories: string[];
  encounters: IClinicalEncounter[];
}

// ── Timeline statistics header ─────────────────────────────────────────────
export interface ITimelineStats {
  total_events: number;
  first_record: string | null;
  latest_record: string | null;
  lab_count: number;
  vitals_count: number;
  prescription_count: number;
  note_count: number;
}

export interface ITimelineQueryParams {
  search?: string;
  doc_type?: string;
}

export const timelineApi = {
  getPatientTimeline: (patientId: string, params?: ITimelineQueryParams) =>
    client.get<any, ApiResponse<IVisitGroup[]>>(`/timeline/patients/${patientId}`, { params }),

  getTimelineStats: (patientId: string) =>
    client.get<any, ApiResponse<ITimelineStats>>(`/timeline/patients/${patientId}/stats`),
};
