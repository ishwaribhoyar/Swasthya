export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    ME: '/auth/me',
    REFRESH: '/auth/refresh',
  },
  PATIENTS: {
    LIST: '/patients',
    DETAIL: (id: string) => `/patients/${id}`,
    RECORDS: (id: string) => `/patients/${id}/records`,
  },
  TIMELINE: {
    LIST: '/timeline',
  },
  ANALYTICS: {
    DASHBOARD: '/analytics/dashboard',
  },
  ASSISTANT: {
    CHAT: '/ai-copilot/chat',
  },
  AI_COPILOT: {
    CHAT: '/ai-copilot/chat',
  },
} as const;
