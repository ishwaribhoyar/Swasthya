export type BloodGroup = 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-';
export type Gender = 'male' | 'female' | 'other';

export interface IPatient {
  id: string;
  clinician_id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  age: number;
  gender: Gender;
  phone?: string;
  email?: string;
  blood_group?: BloodGroup;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  address?: string;
  allergies?: string;
  chronic_conditions?: string;
  notes?: string;
  is_active: boolean;
  archived_at?: string;
  created_at: string;
  updated_at: string;
}

export interface IPatientListItem {
  id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  age: number;
  gender: Gender;
  phone?: string;
  blood_group?: BloodGroup;
  emergency_contact_name?: string;
  is_active: boolean;
  archived_at?: string;
  created_at: string;
  updated_at: string;
  last_document_at?: string | null;
  risk_status?: 'NORMAL' | 'HIGH' | 'CRITICAL' | 'MODERATE' | null;
}

export interface IPatientCreate {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: Gender;
  phone?: string;
  email?: string;
  blood_group?: BloodGroup;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  address?: string;
  allergies?: string;
  chronic_conditions?: string;
  notes?: string;
}

export interface IPatientUpdate {
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  gender?: Gender;
  phone?: string;
  email?: string;
  blood_group?: BloodGroup;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  address?: string;
  allergies?: string;
  chronic_conditions?: string;
  notes?: string;
}

export interface IPatientStatistics {
  total_patients: number;
  active_patients: number;
  archived_patients: number;
  new_this_month: number;
  gender_distribution: Record<string, number>;
  blood_group_distribution: Record<string, number>;
  age_distribution: Record<string, number>;
}

export interface IPatientQueryParams {
  search?: string;
  gender?: string;
  blood_group?: string;
  include_archived?: boolean;
  sort_by?: string;
  page?: number;
  page_size?: number;
}
