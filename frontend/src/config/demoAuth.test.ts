import { beforeEach, describe, expect, it, vi } from "vitest";
import type { UserRole } from "../types";

const personaCases: Array<[UserRole, string]> = [
  ["victim", "/victim"],
  ["counsellor", "/counsellor"],
  ["district_admin", "/district-officer"],
  ["state_admin", "/state-admin"],
  ["national_admin", "/national-admin"],
];

beforeEach(() => {
  vi.resetModules();
  vi.unstubAllEnvs();
  vi.stubEnv("VITE_DEMO_AUTH_ENABLED", "true");
  vi.stubEnv("VITE_DEMO_VICTIM_EMAIL", "victim@example.invalid");
  vi.stubEnv("VITE_DEMO_VICTIM_PASSWORD", "VictimOnly!1");
  vi.stubEnv("VITE_DEMO_COUNSELLOR_EMAIL", "counsellor@example.invalid");
  vi.stubEnv("VITE_DEMO_COUNSELLOR_PASSWORD", "CounsellorOnly!1");
  vi.stubEnv("VITE_DEMO_DISTRICT_EMAIL", "district@example.invalid");
  vi.stubEnv("VITE_DEMO_DISTRICT_PASSWORD", "DistrictOnly!1");
  vi.stubEnv("VITE_DEMO_STATE_ADMIN_EMAIL", "state@example.invalid");
  vi.stubEnv("VITE_DEMO_STATE_ADMIN_PASSWORD", "StateOnly!1");
  vi.stubEnv("VITE_DEMO_NATIONAL_ADMIN_EMAIL", "national@example.invalid");
  vi.stubEnv("VITE_DEMO_NATIONAL_ADMIN_PASSWORD", "NationalOnly!1");
});

describe("demo login routing", () => {
  it.each(personaCases)("routes %s to %s", async (role, expectedPath) => {
    const { postLoginPath } = await import("./demoAuth");
    expect(postLoginPath(role)).toBe(expectedPath);
  });

  it("routes completed demo personas directly to dashboards", async () => {
    const { postAuthenticationPath } = await import("./demoAuth");
    for (const [role, expectedPath] of personaCases) {
      expect(
        postAuthenticationPath({
          role,
          phone_verified_at: "2026-09-20T08:00:00Z",
          profile_completed: true,
        }),
      ).toBe(expectedPath);
    }
  });

  it("routes new users through profile setup", async () => {
    const { postAuthenticationPath } = await import("./demoAuth");
    expect(
      postAuthenticationPath({
        role: "victim",
        phone_verified_at: "2026-09-25T08:00:00Z",
        profile_completed: false,
      }),
    ).toBe("/profile/setup");
    expect(
      postAuthenticationPath({
        role: "victim",
        phone_verified_at: "2026-09-25T08:00:00Z",
        profile_completed: false,
      }),
    ).toBe("/profile/setup");
  });

  it("provides five independently credentialed development personas", async () => {
    const { demoLoginEnabled, demoLoginPersonas } = await import("./demoAuth");
    expect(demoLoginEnabled).toBe(true);
    expect(demoLoginPersonas.map((persona) => persona.role)).toEqual([
      "victim",
      "counsellor",
      "district_admin",
      "state_admin",
      "national_admin",
    ]);
    expect(new Set(demoLoginPersonas.map((persona) => persona.password)).size).toBe(5);
  });
});
