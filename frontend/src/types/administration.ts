import type { UserRole, UserStatus } from ".";

export interface AdministrativeUnit {
  id: number;
  name: string;
  unit_type: "national" | "state" | "district";
  parent_id: number | null;
  is_demo: boolean;
}

export interface AdministrativeAccount {
  id: number;
  full_name: string;
  display_name: string;
  email: string | null;
  phone: string;
  role: UserRole;
  status: UserStatus;
  state_id: number | null;
  district_id: number | null;
  state_name: string | null;
  district_name: string | null;
  created_by_user_id: number | null;
  created_role: UserRole | null;
  appointed_by_user_id: number | null;
  appointed_at: string | null;
  created_at: string;
  is_demo: boolean;
}
