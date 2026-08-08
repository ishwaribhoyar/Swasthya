export type DocumentCategory = 'lab' | 'prescription' | 'vitals' | 'note' | 'summary' | 'unclassified';
export type DocumentStatus = 'queued' | 'uploading' | 'processing' | 'completed' | 'failed' | 'duplicate' | 'cancelled';

export interface IProcessingLog {
  id: string;
  document_id: string;
  step_name: string;
  status: string;
  log_message?: string;
  duration_ms: number;
  timestamp: string;
}

export interface IDocument {
  id: string;
  patient_id: string;
  clinician_id: string;
  upload_job_id?: string;
  original_filename: string;
  file_type: string;
  mime_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  doc_category: DocumentCategory;
  status: DocumentStatus;
  parse_source?: string;
  confidence_score: number;
  extracted_text?: string;
  extracted_markdown?: string;
  extracted_html?: string;
  error_message?: string;

  processing_time_ms: number;
  created_at: string;
  updated_at: string;
}

export interface IDocumentListItem {
  id: string;
  patient_id: string;
  original_filename: string;
  file_type: string;
  mime_type: string;
  file_size_bytes: number;
  doc_category: DocumentCategory;
  status: DocumentStatus;
  parse_source?: string;
  confidence_score: number;
  processing_time_ms: number;
  created_at: string;
}

export interface IBatchUploadSummary {
  job_id: string;
  total_files: number;
  completed_files: number;
  duplicate_files: number;
  failed_files: number;
  average_confidence: number;
  total_processing_time_ms: number;
  documents: IDocument[];
}

export interface IDocumentQueryParams {
  search?: string;
  category?: string;
  status?: string;
  sort_by?: string;
}

/** Evidence provenance chain for a single source document. */
export interface IDocumentProvenance {
  document_id: string;
  patient_id: string;
  clinician_id: string;

  // File identity
  original_filename: string;
  mime_type: string;
  file_type: string;            // pdf | image | txt
  file_size_bytes: number;
  sha256_hash: string;

  // Clinical context
  doc_category: DocumentCategory;
  document_date?: string | null;
  uploaded_at: string;

  // Extraction provenance
  parse_source?: string | null; // sarvam_parse | sarvam_vision | pymupdf_fallback | direct_text
  confidence_score: number;
  processing_status: DocumentStatus;
  processing_time_ms: number;

  // File availability
  file_available: boolean;
  file_unavailable_reason?: string | null;

  // Evidence chain counts
  timeline_event_count: number;
  lab_result_count: number;
  parameter_history_count: number;
}
