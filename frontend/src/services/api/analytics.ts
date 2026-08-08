import client from './client';
import { ApiResponse } from '@/types/api';

export interface IDataPoint {
  date: string;
  value: number;
  unit: string;
  status: string;
  source_record_id: string;
}

export interface IParameterTrend {
  parameter_name: string;
  normalized_name: string;
  unit: string;
  latest_value: number;
  latest_date: string;
  direction: 'STABLE' | 'INCREASING' | 'DECREASING' | 'RAPIDLY_INCREASING' | 'RAPIDLY_DECREASING' | 'OSCILLATING' | 'OUTLIER' | 'REPEATED_ABNORMAL' | 'INSUFFICIENT_DATA';
  absolute_change: number;
  percentage_change: number;
  rate_of_change_per_day: number;
  observation_count: number;
  time_span_days: number;
  confidence: number;
  anomalies: string[];
  points: IDataPoint[];
}

export interface IAnalyticsOverview {
  patient_id: string;
  total_parameters_tracked: number;
  critical_anomalies_count?: number;
  active_anomalies?: string[];
  parameter_trends: IParameterTrend[];
}

export const analyticsApi = {
  getPatientTrends: (patientId: string) =>
    client.get<any, ApiResponse<IAnalyticsOverview>>(`/analytics/patients/${patientId}/trends`),

  getParameterHistory: (patientId: string, parameterName: string) =>
    client.get<any, ApiResponse<IParameterTrend>>(`/analytics/patients/${patientId}/parameters/${parameterName}`),
};
