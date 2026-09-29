import { AxiosError } from "axios";
import { describe, expect, it } from "vitest";
import { authErrorMessage } from "./authErrors";

function responseError(status: number, code: string, message: string): AxiosError {
  return new AxiosError(
    message,
    "ERR_BAD_REQUEST",
    undefined,
    undefined,
    {
      status,
      data: { error: { code, message } },
      statusText: "Error",
      headers: {},
      config: {},
    } as never,
  );
}

describe("shared API error messages", () => {
  it("keeps authentication failures in the authentication category", () => {
    expect(authErrorMessage(responseError(401, "TOKEN_EXPIRED", "expired"), "fallback")).toBe(
      "Your session has expired. Please sign in again.",
    );
  });

  it("reports server failures as service failures", () => {
    expect(authErrorMessage(responseError(503, "SERVICE_UNAVAILABLE", "unavailable"), "fallback")).toBe(
      "unavailable",
    );
  });

  it("reports network failures as connectivity failures", () => {
    expect(authErrorMessage(new AxiosError("Network Error", "ERR_NETWORK"), "fallback")).toBe(
      "The service could not be reached. Check your connection and try again.",
    );
  });

  it("preserves validation messages", () => {
    expect(authErrorMessage(responseError(422, "VALIDATION_ERROR", "Request validation failed"), "fallback")).toBe(
      "Request validation failed",
    );
  });
});
