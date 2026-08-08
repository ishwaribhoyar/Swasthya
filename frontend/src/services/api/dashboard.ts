import client from './client';
import { ApiResponse } from '@/types/api';

export interface IDashboardOverview {
  total_patients: number;
  active_patients: number;
  documents_processed: number;
  critical_alerts: number;
  new_this_month: number;
}

export interface ITrendPoint {
  date: string;
  count: number;
}

export interface ICategoryPoint {
  name: string;
  value: number;
  color: string;
}

export const dashboardApi = {
  getOverview: async (): Promise<ApiResponse<IDashboardOverview>> =>
    client.get('/dashboard/overview'),

  getAdmissionsTrend: async (days = 30): Promise<ApiResponse<ITrendPoint[]>> =>
    client.get('/dashboard/admissions-trend', { params: { days } }),

  getDocumentCategories: async (): Promise<ApiResponse<ICategoryPoint[]>> =>
    client.get('/dashboard/document-categories'),
};
