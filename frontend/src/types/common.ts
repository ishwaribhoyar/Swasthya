export enum LoadingState {
  IDLE = 'idle',
  LOADING = 'loading',
  SUCCESS = 'success',
  ERROR = 'error',
}

export enum SortOrder {
  ASC = 'asc',
  DESC = 'desc',
}

export interface ISelectOption {
  label: string;
  value: string;
  disabled?: boolean;
}

export interface IBreadcrumb {
  label: string;
  href?: string;
}
