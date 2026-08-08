import client from './client';
import { ApiResponse } from '@/types/api';
import {
  IClinicalAlert,
  IClinicalOverview,
  ILabResult,
  IOrganScore,
  IVitalSign,
} from '@/types/clinical';

export const clinicalApi = {
  analyze: async (patientId: string): Promise<ApiResponse<IClinicalOverview>> => {
    return client.post(`/clinical/patients/${patientId}/analyze`);
  },

  getOverview: async (patientId: string): Promise<ApiResponse<IClinicalOverview>> => {
    return client.get(`/clinical/patients/${patientId}/overview`);
  },

  listLabs: async (patientId: string, status?: string): Promise<ApiResponse<ILabResult[]>> => {
    return client.get(`/clinical/patients/${patientId}/labs`, { params: { status } });
  },

  listVitals: async (patientId: string): Promise<ApiResponse<IVitalSign[]>> => {
    return client.get(`/clinical/patients/${patientId}/vitals`);
  },

  getOrganScores: async (patientId: string): Promise<ApiResponse<IOrganScore[]>> => {
    return client.get(`/clinical/patients/${patientId}/organ-scores`);
  },

  listAlerts: async (patientId: string, severity?: string): Promise<ApiResponse<IClinicalAlert[]>> => {
    return client.get(`/clinical/patients/${patientId}/alerts`, { params: { severity } });
  },

  acknowledgeAlert: async (alertId: string): Promise<ApiResponse<IClinicalAlert>> => {
    return client.post(`/clinical/alerts/${alertId}/acknowledge`);
  },
};
