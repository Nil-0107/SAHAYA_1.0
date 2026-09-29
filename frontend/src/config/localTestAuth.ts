import type { UserRole } from "../types";

export interface LocalTestAccount {
  role: UserRole;
  label: string;
  identifier: string;
  password: string;
}

const configuredAccounts: LocalTestAccount[] = [
  {
    role: "victim",
    label: "Victim / User",
    identifier: import.meta.env.VITE_LOCAL_TEST_VICTIM_EMAIL ?? "",
    password: import.meta.env.VITE_LOCAL_TEST_VICTIM_PASSWORD ?? "",
  },
  {
    role: "counsellor",
    label: "Psychologist / Counsellor",
    identifier: import.meta.env.VITE_LOCAL_TEST_COUNSELLOR_EMAIL ?? "",
    password: import.meta.env.VITE_LOCAL_TEST_COUNSELLOR_PASSWORD ?? "",
  },
  {
    role: "district_admin",
    label: "District Administrator",
    identifier: import.meta.env.VITE_LOCAL_TEST_DISTRICT_EMAIL ?? "",
    password: import.meta.env.VITE_LOCAL_TEST_DISTRICT_PASSWORD ?? "",
  },
  {
    role: "state_admin",
    label: "State Administrator",
    identifier: import.meta.env.VITE_LOCAL_TEST_STATE_ADMIN_EMAIL ?? "",
    password: import.meta.env.VITE_LOCAL_TEST_STATE_ADMIN_PASSWORD ?? "",
  },
  {
    role: "national_admin",
    label: "National Administrator",
    identifier: import.meta.env.VITE_LOCAL_TEST_NATIONAL_ADMIN_EMAIL ?? "",
    password: import.meta.env.VITE_LOCAL_TEST_NATIONAL_ADMIN_PASSWORD ?? "",
  },
];

export const localTestAuthEnabled =
  import.meta.env.DEV && import.meta.env.VITE_LOCAL_ROLE_LOGIN_ENABLED === "true";

export const localTestAccounts = localTestAuthEnabled
  ? configuredAccounts.filter((account) => account.identifier && account.password)
  : [];
