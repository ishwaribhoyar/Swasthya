export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  PATIENTS: '/patients',
  PATIENT_DETAIL: (id: string) => `/patients/${id}`,
  TIMELINE: '/timeline',
  ANALYTICS: '/analytics',
  ASSISTANT: '/assistant',
  SETTINGS: '/settings',
} as const;

export const APP_NAME = 'ClinIQ';
export const APP_VERSION = '1.0.0';

export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE: 10,
  OPTIONS: [10, 20, 50, 100],
} as const;
