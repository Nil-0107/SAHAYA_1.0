import { AxiosError, type AxiosAdapter, type AxiosResponse, type InternalAxiosRequestConfig } from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, authRefreshClient, clearAuthSession, setAccessToken, setAuthSessionListener, type AuthSessionListener } from "./api";
import type { AuthSession } from "./authApi";

const originalApiAdapter = api.defaults.adapter;
const originalRefreshAdapter = authRefreshClient.defaults.adapter;

const refreshedSession: AuthSession = {
  access_token: "new-access-token",
  token_type: "bearer",
  expires_in: 900,
  user: {
    id: 1,
    phone: "+919876543210",
    email: "user@example.invalid",
    role: "victim",
    status: "active",
    phone_verified_at: "2026-09-25T08:00:00Z",
    profile_completed: true,
    is_demo: false,
  },
};

function axiosResponse<T>(config: InternalAxiosRequestConfig, data: T, status = 200): AxiosResponse<T> {
  return { data, status, statusText: "OK", headers: {}, config };
}

function unauthorized(config: InternalAxiosRequestConfig) {
  return new AxiosError("expired", "ERR_BAD_REQUEST", config, undefined, {
    status: 401,
    data: { error: { code: "TOKEN_EXPIRED" } },
    statusText: "Unauthorized",
    headers: {},
    config,
  } as never);
}

beforeEach(() => {
  setAccessToken("expired-access-token");
  setAuthSessionListener(null);
});

afterEach(() => {
  api.defaults.adapter = originalApiAdapter;
  authRefreshClient.defaults.adapter = originalRefreshAdapter;
  clearAuthSession();
  setAuthSessionListener(null);
});

describe("API session recovery", () => {
  it("refreshes once after a 401 and retries the protected request", async () => {
    let protectedAttempts = 0;
    let refreshAttempts = 0;
    const listener: AuthSessionListener = { onSessionRefreshed: vi.fn() };
    setAuthSessionListener(listener);
    (api.defaults.adapter as AxiosAdapter) = vi.fn(async (config) => {
      protectedAttempts += 1;
      if (protectedAttempts === 1) throw unauthorized(config);
      return axiosResponse(config, { ok: true });
    });
    (authRefreshClient.defaults.adapter as AxiosAdapter) = vi.fn(async (config) => {
      refreshAttempts += 1;
      return axiosResponse(config, refreshedSession);
    });

    const result = await api.get<{ ok: boolean }>("/me");

    expect(result.data.ok).toBe(true);
    expect(protectedAttempts).toBe(2);
    expect(refreshAttempts).toBe(1);
    expect(listener.onSessionRefreshed).toHaveBeenCalledWith(refreshedSession);
  });

  it("clears authentication when the refresh session is rejected", async () => {
    const listener: AuthSessionListener = { onSessionExpired: vi.fn() };
    setAuthSessionListener(listener);
    api.defaults.adapter = vi.fn(async (config) => { throw unauthorized(config); });
    authRefreshClient.defaults.adapter = vi.fn(async (config) => { throw unauthorized(config); });

    await expect(api.get("/me")).rejects.toBeInstanceOf(AxiosError);
    expect(listener.onSessionExpired).toHaveBeenCalledTimes(1);
  });

  it("does not refresh a request after the session was explicitly cleared", async () => {
    let refreshAttempts = 0;
    api.defaults.adapter = vi.fn(async (config) => { throw unauthorized(config); });
    authRefreshClient.defaults.adapter = vi.fn(async () => {
      refreshAttempts += 1;
      return axiosResponse({} as InternalAxiosRequestConfig, refreshedSession);
    });

    const request = api.get("/me");
    await Promise.resolve();
    clearAuthSession();
    await expect(request).rejects.toBeInstanceOf(AxiosError);
    expect(refreshAttempts).toBe(0);
  });
});
