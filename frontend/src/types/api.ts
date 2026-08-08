export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
  request_id?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size?: number;
  pageSize?: number;
  pages?: number;
  totalPages?: number;
}

export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: unknown;
}

export interface RequestConfig {
  params?: Record<string, any>;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}
