import type { AuthUser, UserRole } from "../types";
import { api } from "./api";

export interface SignupPayload {
  phone: string;
  email?: string | null;
  password: string;
  date_of_birth: string;
  role?: UserRole;
}

export interface LoginPayload {
  identifier: string;
  password: string;
}

export interface AuthSession {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: AuthUser;
}

export const authApi = {
  async signup(payload: SignupPayload) {
    const { data } = await api.post("/auth/signup", payload);
    return data as {
      message: string;
      user: AuthUser;
      verification_required: boolean;
      access_token: string;
      token_type: "bearer";
      expires_in: number;
    };
  },

  async login(payload: LoginPayload): Promise<AuthSession> {
    const { data } = await api.post<AuthSession>("/auth/login", payload);
    return data;
  },

  async refresh(): Promise<AuthSession> {
    const { data } = await api.post<AuthSession>("/auth/refresh");
    return data;
  },

  async me(): Promise<AuthUser> {
    const { data } = await api.get<AuthUser>("/me");
    return data;
  },

  async logout(): Promise<void> {
    await api.post("/auth/logout");
  },
};
