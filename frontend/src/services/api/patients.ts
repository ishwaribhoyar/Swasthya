import client from './client';
import { ApiResponse, PaginatedResponse } from '@/types/api';
import {
  IPatient,
  IPatientListItem,
  IPatientCreate,
  IPatientUpdate,
  IPatientStatistics,
  IPatientQueryParams,
} from '@/types/patients';

export const patientsApi = {
  list: async (params?: IPatientQueryParams): Promise<ApiResponse<PaginatedResponse<IPatientListItem>>> => {
    return client.get('/patients', { params });
  },

  getById: async (id: string): Promise<ApiResponse<IPatient>> => {
    return client.get(`/patients/${id}`);
  },

  create: async (data: IPatientCreate): Promise<ApiResponse<IPatient>> => {
    return client.post('/patients', data);
  },

  update: async (id: string, data: IPatientUpdate): Promise<ApiResponse<IPatient>> => {
    return client.patch(`/patients/${id}`, data);
  },

  archive: async (id: string): Promise<ApiResponse<IPatient>> => {
    return client.delete(`/patients/${id}`);
  },

  restore: async (id: string): Promise<ApiResponse<IPatient>> => {
    return client.post(`/patients/${id}/restore`);
  },

  getStatistics: async (): Promise<ApiResponse<IPatientStatistics>> => {
    return client.get('/patients/statistics');
  },

  search: async (q: string): Promise<ApiResponse<IPatientListItem[]>> => {
    return client.get('/patients/search/global', { params: { q } });
  },
};

