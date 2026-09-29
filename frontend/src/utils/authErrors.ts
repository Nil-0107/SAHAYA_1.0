import { isAxiosError } from "axios";

const messages: Record<string, string> = {
  INVALID_CREDENTIALS: "The mobile/email or password is incorrect.",
  ACCOUNT_MOBILE_NOT_VERIFIED: "Verify your account mobile before continuing.",
  ACCOUNT_ONBOARDING_INCOMPLETE: "Complete account verification and profile setup before continuing.",
  PROFILE_INCOMPLETE: "Complete your profile before opening the dashboard.",
  DUPLICATE_ACCOUNT: "An account already exists for this mobile or email.",
  OTP_INVALID: "That verification code is incorrect or no longer valid.",
  OTP_EXPIRED: "That verification code has expired. Request a new code.",
  OTP_RESEND_RATE_LIMITED: "Please wait before requesting another code.",
  OTP_RATE_LIMITED: "Too many verification requests. Please try again later.",
  OTP_TEMPORARILY_BLOCKED: "Verification is temporarily blocked. Please try again later.",
  OTP_VERIFY_RATE_LIMITED: "Too many incorrect attempts. Request a new code later.",
  OTP_PROVIDER_UNAVAILABLE: "Verification is temporarily unavailable. Please try again later.",
  CHECKIN_ANALYSIS_UNAVAILABLE: "Check-in analysis is temporarily unavailable. Your message was not saved.",
  CHECKIN_SAVE_FAILED: "The check-in could not be saved. Please try again.",
  TOKEN_EXPIRED: "Your session has expired. Please sign in again.",
  SESSION_REVOKED: "Your session has ended. Please sign in again.",
  REFRESH_TOKEN_REQUIRED: "Your session has expired. Please sign in again.",
  REFRESH_TOKEN_EXPIRED: "Your session has expired. Please sign in again.",
  INVALID_REFRESH_TOKEN: "Your session has expired. Please sign in again.",
  AUTHENTICATION_REQUIRED: "Please sign in to continue.",
  ACCOUNT_UNAVAILABLE: "This account is not available. Contact support.",
};

export function authErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError(error)) {
    const code = error.response?.data?.error?.code;
    if (typeof code === "string" && messages[code]) return messages[code];
    const message = error.response?.data?.error?.message;
    if (typeof message === "string" && message.length < 180) return message;
    if (error.response?.status === 401 || error.response?.status === 403) {
      return "Authentication is required to continue. Please sign in again.";
    }
    if (error.response?.status === 422 || error.response?.status === 400) {
      return "The request could not be validated. Please check the entered information.";
    }
    if (error.response?.status && error.response.status >= 500) {
      return "The service is temporarily unavailable. Please try again.";
    }
    if (!error.response) {
      return "The service could not be reached. Check your connection and try again.";
    }
  }
  return fallback;
}
