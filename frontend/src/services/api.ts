import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { API_BASE_URL } from "../config";
import type { AuthSession } from "./authApi";

let accessToken: string | null = null;
let refreshPromise: Promise<AuthSession> | null = null;
let sessionListener: AuthSessionListener | null = null;
let authGeneration = 0;

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _authRetry?: boolean;
  _authGeneration?: number;
}

export interface AuthSessionListener {
  onSessionRefreshed?: (session: AuthSession) => void;
  onSessionExpired?: () => void;
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

export const authRefreshClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  (config as RetryableRequestConfig)._authGeneration = authGeneration;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const request = error.config as RetryableRequestConfig | undefined;
    if (error.response?.status !== 401 || !request || isAuthEntryRequest(request.url)) {
      return Promise.reject(error);
    }
    if (request._authGeneration !== authGeneration) return Promise.reject(error);

    if (!request._authRetry) {
      try {
        const session = await refreshSession();
        request._authRetry = true;
        request.headers.Authorization = `Bearer ${session.access_token}`;
        return api.request(request);
      } catch {
        return Promise.reject(error);
      }
    }

    expireSession();
    return Promise.reject(error);
  },
);

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function setAuthSessionListener(listener: AuthSessionListener | null): void {
  sessionListener = listener;
}

export function clearAccessToken(): void {
  accessToken = null;
}

export function clearAuthSession(): void {
  authGeneration += 1;
  accessToken = null;
  refreshPromise = null;
}

function refreshSession(): Promise<AuthSession> {
  if (!refreshPromise) {
    const generation = authGeneration;
    refreshPromise = authRefreshClient
      .post<AuthSession>("/auth/refresh")
      .then(({ data }) => {
        if (generation !== authGeneration) throw new Error("Stale authentication refresh");
        setAccessToken(data.access_token);
        sessionListener?.onSessionRefreshed?.(data);
        return data;
      })
      .catch((error: unknown) => {
        if (generation === authGeneration) expireSession();
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

function expireSession(): void {
  setAccessToken(null);
  sessionListener?.onSessionExpired?.();
}

function isAuthEntryRequest(url: string | undefined): boolean {
  if (!url) return false;
  return ["/auth/login", "/auth/signup", "/auth/refresh", "/auth/logout"].some((path) => url.endsWith(path));
}
