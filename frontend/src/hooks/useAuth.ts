import { useAuthContext } from '@/contexts/AuthContext';

export const useAuth = () => {
  return useAuthContext();
};
