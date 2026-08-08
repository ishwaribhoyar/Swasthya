export interface IUser {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  avatar?: string;
}

export interface IAuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface ILoginRequest {
  email: string;
  password?: string;
}

export interface IRegisterRequest {
  firstName: string;
  lastName: string;
  email: string;
  password?: string;
}

export interface IAuthState {
  user: IUser | null;
  tokens: IAuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
