import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuth } from "../context/AuthContext";
import type { AuthUser, UserRole } from "../types";
import { OnboardingRoute } from "./OnboardingRoute";
import { ProtectedRoute } from "./ProtectedRoute";
import { RoleRoute } from "./RoleRoute";

vi.mock("../context/AuthContext", () => ({ useAuth: vi.fn() }));

function user(role: UserRole, overrides: Partial<AuthUser> = {}): AuthUser {
  return {
    id: 1,
    phone: "+919876543210",
    email: "user@example.invalid",
    role,
    status: "active",
    phone_verified_at: "2026-09-25T08:00:00Z",
    profile_completed: true,
    is_demo: false,
    ...overrides,
  };
}

function renderProtected(path: string, currentUser: AuthUser | null) {
  vi.mocked(useAuth).mockReturnValue({
    user: currentUser,
    isLoading: false,
    sessionExpired: false,
  } as ReturnType<typeof useAuth>);
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/login" element={<div>login page</div>} />
        <Route element={<ProtectedRoute />}>
          <Route path="*" element={<div>private page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

function renderOnboarding(path: string, currentUser: AuthUser, step: "profile" | "dashboard") {
  vi.mocked(useAuth).mockReturnValue({ user: currentUser, isLoading: false } as ReturnType<typeof useAuth>);
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/profile/setup" element={<div>profile page</div>} />
        <Route element={<OnboardingRoute step={step} />}>
          <Route path={path} element={<div>onboarding page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("authentication route gates", () => {
  it("redirects an unauthenticated protected request to login", () => {
    renderProtected("/victim", null);
    expect(screen.getByText("login page")).toBeInTheDocument();
  });

  it("redirects an incomplete account to profile setup", () => {
    renderOnboarding("/victim", user("victim", { phone_verified_at: new Date().toISOString(), profile_completed: false }), "dashboard");
    expect(screen.getByText("profile page")).toBeInTheDocument();
  });

  it("redirects a verified but incomplete profile to setup", () => {
    renderOnboarding("/victim", user("victim", { profile_completed: false }), "dashboard");
    expect(screen.getByText("profile page")).toBeInTheDocument();
  });

  it.each([
    ["victim", "/victim"],
    ["counsellor", "/counsellor"],
    ["district_admin", "/district-officer"],
    ["state_admin", "/state-admin"],
    ["national_admin", "/national-admin"],
  ] as Array<[UserRole, string]>)("allows the completed %s account to reach %s", (role, path) => {
    vi.mocked(useAuth).mockReturnValue({ user: user(role), isLoading: false } as ReturnType<typeof useAuth>);
    render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/forbidden" element={<div>forbidden page</div>} />
          <Route element={<OnboardingRoute step="dashboard" />}>
            <Route element={<RoleRoute allowedRoles={[role]} />}>
              <Route path={path} element={<div>{role} dashboard</div>} />
            </Route>
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText(`${role} dashboard`)).toBeInTheDocument();
  });

  it("blocks a valid account from another role's frontend route", () => {
    vi.mocked(useAuth).mockReturnValue({ user: user("victim"), isLoading: false } as ReturnType<typeof useAuth>);
    render(
      <MemoryRouter initialEntries={["/national-admin"]}>
        <Routes>
          <Route path="/forbidden" element={<div>forbidden page</div>} />
          <Route element={<OnboardingRoute step="dashboard" />}>
            <Route element={<RoleRoute allowedRoles={["national_admin"]} />}>
              <Route path="/national-admin" element={<div>admin dashboard</div>} />
            </Route>
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("forbidden page")).toBeInTheDocument();
  });
});
