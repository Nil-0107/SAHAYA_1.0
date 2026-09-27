import { useState, type FormEvent } from "react";
import { Eye, EyeOff, LockKeyhole, ShieldCheck } from "lucide-react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { Button } from "../../components/common/Button";
import { Card } from "../../components/common/Card";
import { InlineAlert } from "../../components/feedback/FeedbackStates";
import { FormField, TextInput } from "../../components/forms/FormField";
import {
  demoLoginEnabled,
  demoLoginPersonas,
  postAuthenticationPath,
  type DemoLoginPersona,
} from "../../config/demoAuth";
import { useAuth } from "../../context/AuthContext";
import { DemoLoginSelector } from "../../features/auth/DemoLoginSelector";
import { authErrorMessage } from "../../utils/authErrors";

interface LoginLocationState {
  from?: { pathname?: string };
  reason?: "session-expired";
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, login, sessionExpired, bootstrapError, dismissAuthError } = useAuth();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const locationState = location.state as LoginLocationState | null;

  if (user) return <Navigate to={postAuthenticationPath(user)} replace />;

  const selectPersona = (persona: DemoLoginPersona) => {
    setIdentifier(persona.email);
    setPassword(persona.password);
    setError("");
  };

  const submitLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      const authenticatedUser = await login({ identifier: identifier.trim(), password });
      const nextPath = postAuthenticationPath(authenticatedUser);
      const intendedPath = (location.state as LoginLocationState | null)?.from?.pathname;
      const onboardingComplete = Boolean(authenticatedUser.phone_verified_at && authenticatedUser.profile_completed);
      navigate(onboardingComplete && intendedPath?.startsWith("/") ? intendedPath : nextPath, { replace: true });
    } catch (caught) {
      setError(authErrorMessage(caught, "Login failed. Please try again."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="grid items-stretch gap-6 lg:grid-cols-[1fr_450px]">
      <div className="relative hidden overflow-hidden rounded-[28px] bg-saathi-900 p-10 text-white shadow-card lg:flex lg:flex-col lg:justify-between">
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-teal-400/10" />
        <div className="relative">
          <p className="text-[11px] font-extrabold uppercase tracking-[.16em] text-teal-200">Secure access</p>
          <h1 className="mt-4 max-w-lg text-4xl font-black leading-tight">Continue your support journey securely.</h1>
          <p className="mt-4 max-w-lg text-sm leading-7 text-teal-50/80">Use your registered account mobile or email. Normal login never sends an OTP.</p>
        </div>
        <div className="relative grid gap-3 text-xs font-bold text-teal-50/80">
          <p className="flex items-center gap-2"><ShieldCheck size={16} /> Authoritative role assignment</p>
          <p className="flex items-center gap-2"><LockKeyhole size={16} /> Short-lived secure session</p>
        </div>
      </div>

      <Card className="w-full p-6 sm:p-8">
        <p className="text-[11px] font-extrabold uppercase tracking-[.16em] text-saathi-700">Welcome back</p>
        <h1 className="mt-2 text-2xl font-extrabold text-slate-900">Log in to SAATHI</h1>
        <p className="mt-2 text-sm leading-6 text-slate-500">New users create a Victim / User account first.</p>

        {sessionExpired || locationState?.reason === "session-expired" ? (
          <div className="mt-4"><InlineAlert tone="info">Your session has expired. Please sign in again.</InlineAlert></div>
        ) : null}
        {bootstrapError ? (
          <div className="mt-4 flex items-start gap-2">
            <div className="flex-1"><InlineAlert>{bootstrapError}</InlineAlert></div>
            <button type="button" className="rounded-lg px-2 text-xs font-extrabold text-slate-500" onClick={dismissAuthError}>Dismiss</button>
          </div>
        ) : null}

        <form className="mt-6 grid gap-4" onSubmit={submitLogin}>
          <FormField label="Registered mobile or email">
            <TextInput
              value={identifier}
              onChange={(event) => setIdentifier(event.target.value)}
              autoComplete="username"
              required
              maxLength={160}
              placeholder="Mobile number or email"
            />
          </FormField>
          <FormField label="Password">
            <div className="relative">
              <TextInput
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                required
                className="pr-12"
              />
              <button
                type="button"
                aria-label={showPassword ? "Hide password" : "Show password"}
                onClick={() => setShowPassword((current) => !current)}
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-2 text-saathi-700 focus:outline-none focus:ring-2 focus:ring-saathi-500"
              >
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
          </FormField>
          {error ? <InlineAlert>{error}</InlineAlert> : null}
          <Button type="submit" loading={isSubmitting}>Log in securely</Button>
        </form>

        <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-3 text-center text-xs text-slate-500">
          Do not have an account? <Link to="/signup/role" className="font-extrabold text-saathi-700">Create one</Link>
        </div>

        {demoLoginEnabled ? (
          <div className="mt-5">
            <DemoLoginSelector personas={demoLoginPersonas} onSelect={selectPersona} />
          </div>
        ) : null}
      </Card>
    </section>
  );
}
