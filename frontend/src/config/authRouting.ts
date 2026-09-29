import type { AuthUser, UserRole } from "../types";

export function postAuthenticationPath(user: Pick<AuthUser, "role" | "profile_completed">): string {
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
