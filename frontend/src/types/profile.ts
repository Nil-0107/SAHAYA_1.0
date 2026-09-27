export interface AccountMobileStatus {
  phone: string;
  verified: boolean;
  verified_at: string | null;
}

export interface ProfileData {
  id: number;
  full_name: string;
  display_name: string;
  preferred_language: string;
  city_or_district: string;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  safe_contact_method: string | null;
  address: string | null;
  case_reference: string | null;
  relationship_to_case: string | null;
  role_in_case: string | null;
  consent_at: string;
}

export interface ProfileResponse {
  account_mobile: AccountMobileStatus;
  profile: ProfileData | null;
  profile_completed: boolean;
}

export interface ProfileSetupPayload {
  full_name: string;
  display_name: string;
  preferred_language: string;
  city_or_district: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  safe_contact_method?: string;
  address?: string;
  case_reference?: string;
  relationship_to_case?: string;
  role_in_case?: string;
  consent: true;
}
