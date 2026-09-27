export type UserRole =
  | "victim"
  | "counsellor"
  | "district_admin"
  | "state_admin"
  | "national_admin";

export type UserStatus =
  | "pending_verification"
  | "active"
  | "suspended"
  | "disabled";

export interface AuthUser {
  id: number;
  phone: string;
  email: string | null;
  role: UserRole;
  state_id?: number | null;
  district_id?: number | null;
  status: UserStatus;
  phone_verified_at: string | null;
  profile_completed: boolean;
  is_demo: boolean;
}
