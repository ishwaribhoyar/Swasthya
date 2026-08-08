export type OrganStatus = 'OPTIMAL' | 'MILD_STRAIN' | 'MODERATE_IMPAIRMENT' | 'SEVERE_DYSFUNCTION';
export type AlertSeverity = 'CRITICAL' | 'HIGH' | 'MODERATE' | 'INFORMATIONAL';
export type LabStatus = 'NORMAL' | 'LOW' | 'HIGH' | 'CRITICAL_LOW' | 'CRITICAL_HIGH';

export interface ILabResult {
  id: string;
  patient_id: string;
  document_id?: string;
  test_name: string;
  test_code?: string;
  numeric_value: number;
  unit: string;
  ref_min?: number;
  ref_max?: number;
  status: LabStatus;
  confidence_score: number;
  tested_at: string;
}

export interface IVitalSign {
  id: string;
  patient_id: string;
  document_id?: string;
  sbp?: number;
  dbp?: number;
  heart_rate?: number;
  spo2?: number;
  respiratory_rate?: number;
  temperature_c?: number;
  bmi?: number;
  status: string;
  recorded_at: string;
}

export interface IOrganScore {
  id: string;
  patient_id: string;
  organ_system: string;
  score: number;
  status: OrganStatus;
  contributing_biomarkers?: string;
  rationale?: string;
  calculated_at: string;
}

export interface IClinicalAlert {
  id: string;
  patient_id: string;
  document_id?: string;
  alert_type: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  biomarker_name?: string;
  observed_value?: string;
  reference_range?: string;
  action_recommendation?: string;
  is_acknowledged: boolean;
  created_at: string;
}

export interface IClinicalOverview {
  patient_id: string;
  organ_scores: IOrganScore[];
  alerts: IClinicalAlert[];
  latest_labs: ILabResult[];
  latest_vitals?: IVitalSign;
  analyzed_documents_count: number;
}
