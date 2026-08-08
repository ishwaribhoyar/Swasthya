import client from './client';
import { ApiResponse } from '@/types/api';

export interface IPrescriptionMedicine {
  id: string;
  prescription_id: string;
  patient_id: string;
  clinician_id: string;
  medicine_name: string;
  strength?: string;
  dose?: string;
  frequency?: string;
  route?: string;
  duration_days?: number;
  instructions?: string;
  created_at: string;
}

export interface IPrescription {
  id: string;
  patient_id: string;
  clinician_id: string;
  document_id?: string;
  prescribed_by?: string;
  prescription_date: string;
  notes?: string;
  medicines: IPrescriptionMedicine[];
  created_at: string;
}

export interface IMedicineSummary {
  medicine_name: string;
  times_prescribed: number;
  first_prescribed_date: string;
  latest_prescribed_date: string;
  latest_strength?: string;
  latest_dose?: string;
  latest_frequency?: string;
  latest_route?: string;
  status: string;
}

export interface IMedicineHistory {
  medicine_name: string;
  total_prescriptions: number;
  first_prescribed: string;
  latest_prescribed: string;
  prescription_events: IPrescriptionMedicine[];
}

export const medicineApi = {
  getPrescriptions: (patientId: string) =>
    client.get<any, ApiResponse<IPrescription[]>>(`/medicine-engine/patients/${patientId}/prescriptions`),

  getMedicineSummary: (patientId: string) =>
    client.get<any, ApiResponse<IMedicineSummary[]>>(`/medicine-engine/patients/${patientId}/medicines`),

  getMedicineHistory: (patientId: string, name: string) =>
    client.get<any, ApiResponse<IMedicineHistory>>(`/medicine-engine/patients/${patientId}/medicines/history?name=${encodeURIComponent(name)}`),
};
