import type { AuthUser, UserRole } from "../types";

export interface DemoLoginPersona {
  role: UserRole;
  label: string;
  email: string;
  password: string;
}

const configuredPersonas: DemoLoginPersona[] = [
  {
    role: "victim",
    label: "Victim / User",
    email: import.meta.env.VITE_DEMO_VICTIM_EMAIL ?? "",
    password: import.meta.env.VITE_DEMO_VICTIM_PASSWORD ?? "",
  },
  {
    role: "counsellor",
    label: "Psychologist / Counsellor",
    email: import.meta.env.VITE_DEMO_COUNSELLOR_EMAIL ?? "",
    password: import.meta.env.VITE_DEMO_COUNSELLOR_PASSWORD ?? "",
  },
  {
    role: "district_admin",
    label: "District Administrator",
    email: import.meta.env.VITE_DEMO_DISTRICT_EMAIL ?? "",
    password: import.meta.env.VITE_DEMO_DISTRICT_PASSWORD ?? "",
  },
  {
    role: "state_admin",
    label: "State Administrator",
    email: import.meta.env.VITE_DEMO_STATE_ADMIN_EMAIL ?? import.meta.env.VITE_DEMO_ADMIN_EMAIL ?? "",
    password: import.meta.env.VITE_DEMO_STATE_ADMIN_PASSWORD ?? import.meta.env.VITE_DEMO_ADMIN_PASSWORD ?? "",
  },
  {
    role: "national_admin",
    label: "National Administrator",
    email: import.meta.env.VITE_DEMO_NATIONAL_ADMIN_EMAIL ?? "",
    password: import.meta.env.VITE_DEMO_NATIONAL_ADMIN_PASSWORD ?? "",
  },
];

export const demoLoginEnabled =
  import.meta.env.DEV && import.meta.env.VITE_DEMO_AUTH_ENABLED === "true";

export const demoLoginPersonas = demoLoginEnabled
  ? configuredPersonas.filter((persona) => persona.email && persona.password)
  : [];

export function postAuthenticationPath(user: Pick<AuthUser, "role" | "phone_verified_at" | "profile_completed">): string {
  if (!user.profile_completed) return "/profile/setup";
  return postLoginPath(user.role);
}

export function postLoginPath(role: UserRole): string {
  switch (role) {
    case "victim":
      return "/victim";
    case "counsellor":
      return "/counsellor";
    case "district_admin":
      return "/district-officer";
    case "state_admin":
      return "/state-admin";
    case "national_admin":
      return "/national-admin";
  }
}
