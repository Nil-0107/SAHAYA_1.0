import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AxiosError } from "axios";
import { AuthProvider, useAuth } from "./AuthContext";
import type { AuthUser } from "../types";

const mocks = vi.hoisted(() => ({
  refresh: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  setAccessToken: vi.fn(),
  clearAuthSession: vi.fn(),
  setAuthSessionListener: vi.fn(),
}));

vi.mock("../services/authApi", () => ({
  authApi: {
    refresh: mocks.refresh,
    login: mocks.login,
    logout: mocks.logout,
    me: vi.fn(),
  },
}));

vi.mock("../services/api", () => ({
  setAccessToken: mocks.setAccessToken,
  clearAuthSession: mocks.clearAuthSession,
  setAuthSessionListener: mocks.setAuthSessionListener,
}));

const user: AuthUser = {
  id: 7,
  phone: "+919876543210",
  email: "user@example.invalid",
  role: "victim",
  status: "active",
  phone_verified_at: "2026-09-25T08:00:00Z",
  profile_completed: true,
  is_demo: false,
};

const session = {
  access_token: "short-lived-access-token",
  token_type: "bearer" as const,
  expires_in: 900,
  user,
};

function unauthorized() {
  return new AxiosError("expired", "ERR_BAD_REQUEST", undefined, undefined, {
    status: 401,
    data: {},
    statusText: "Unauthorized",
    headers: {},
    config: {},
  } as never);
}

function Probe() {
  const auth = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(auth.isLoading)}</span>
      <span data-testid="user">{auth.user?.role ?? "anonymous"}</span>
      <span data-testid="expired">{String(auth.sessionExpired)}</span>
      <button onClick={() => void auth.login({ identifier: user.email ?? "+919876543210", password: "ValidPass!123" })}>login</button>
      <button onClick={() => void auth.logout()}>logout</button>
    </div>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage.clear();
  mocks.refresh.mockRejectedValue(unauthorized());
  mocks.logout.mockResolvedValue(undefined);
  mocks.setAuthSessionListener.mockImplementation(() => undefined);
});

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
});

describe("AuthContext", () => {
  it("restores a session from the HttpOnly refresh cookie on startup", async () => {
    window.localStorage.setItem("sahaya_session_present", "1");
    mocks.refresh.mockResolvedValue(session);
    render(<AuthProvider><Probe /></AuthProvider>);

    expect(screen.getByTestId("loading")).toHaveTextContent("true");
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("victim"));
    expect(mocks.refresh).toHaveBeenCalledTimes(1);
    expect(mocks.setAccessToken).toHaveBeenCalledWith(session.access_token);
  });

  it("clears an expired session and exposes the expired state", async () => {
    window.localStorage.setItem("sahaya_session_present", "1");
    let listener: { onSessionExpired?: () => void } | undefined;
    mocks.setAuthSessionListener.mockImplementation((next: typeof listener) => { listener = next; });
    mocks.refresh.mockResolvedValue(session);
    render(<AuthProvider><Probe /></AuthProvider>);
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("victim"));

    act(() => listener?.onSessionExpired?.());
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("anonymous"));
    expect(screen.getByTestId("expired")).toHaveTextContent("true");
    expect(mocks.clearAuthSession).toHaveBeenCalled();
  });

  it("logs in through the real auth client contract and stores no password in state", async () => {
    mocks.login.mockResolvedValue(session);
    render(<AuthProvider><Probe /></AuthProvider>);
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("anonymous"));

    await userEvent.click(screen.getByRole("button", { name: "login" }));
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("victim"));
    expect(mocks.login).toHaveBeenCalledWith({ identifier: user.email, password: "ValidPass!123" });
  });

  it("clears local authentication state on logout", async () => {
    window.localStorage.setItem("sahaya_session_present", "1");
    mocks.refresh.mockResolvedValue(session);
    render(<AuthProvider><Probe /></AuthProvider>);
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("victim"));

    await userEvent.click(screen.getByRole("button", { name: "logout" }));
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("anonymous"));
    expect(mocks.logout).toHaveBeenCalledTimes(1);
    expect(mocks.clearAuthSession).toHaveBeenCalled();
  });
});
