import { useEffect, useRef, useState } from "react";
import { ArrowLeft, CheckCircle2, Clock3, LockKeyhole, MessageSquareText, RotateCcw } from "lucide-react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button } from "../../components/common/Button";
import { Card } from "../../components/common/Card";
import { InlineAlert, LoadingState } from "../../components/feedback/FeedbackStates";
import { FormField, TextInput } from "../../components/forms/FormField";
import { postAuthenticationPath } from "../../config/demoAuth";
import { useAuth } from "../../context/AuthContext";
import { authApi } from "../../services/authApi";
import { authErrorMessage } from "../../utils/authErrors";
import { AuthProgress } from "./SignupPage";

export function AccountVerificationPage() {
  const navigate = useNavigate();
  const { user, isLoading, refreshUser, logout } = useAuth();
  const [status, setStatus] = useState("Sending a verification code to your account mobile…");
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [resending, setResending] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const started = useRef(false);

  useEffect(() => {
    if (!user || user.phone_verified_at || started.current) return;
    started.current = true;
    void authApi
      .startOtp(user.phone)
      .then((result) => setStatus(result.message))
      .catch((caught) => {
        setError(authErrorMessage(caught, "Unable to send the verification code."));
        setStatus("Verification needs attention before you can continue.");
      });
  }, [user]);

  if (isLoading) return <LoadingState label="Restoring your secure session…" />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.phone_verified_at || user.profile_completed) {
    return <Navigate to={postAuthenticationPath(user)} replace />;
  }

  const resend = async () => {
    setError("");
    setResending(true);
    try {
      const result = await authApi.resendOtp(user.phone);
      setStatus(result.message);
    } catch (caught) {
      setError(authErrorMessage(caught, "Unable to resend the verification code."));
    } finally {
      setResending(false);
    }
  };

  const verify = async () => {
    setError("");
    if (!/^\d{6}$/.test(otp)) {
      setError("Enter the complete 6-digit verification code.");
      return;
    }
    setVerifying(true);
    try {
      await authApi.verifyOtp(user.phone, otp);
      const updatedUser = await refreshUser();
      navigate(postAuthenticationPath(updatedUser), { replace: true });
    } catch (caught) {
      setError(authErrorMessage(caught, "Account verification failed."));
    } finally {
      setVerifying(false);
    }
  };

  const leave = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <section className="mx-auto max-w-xl">
      <AuthProgress current={2} />
      <Card className="mt-5 p-6 sm:p-8">
        <div className="text-center">
          <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-saathi-50 text-saathi-700"><MessageSquareText size={23} /></span>
          <p className="mt-4 text-[11px] font-extrabold uppercase tracking-[.16em] text-saathi-700">Account verification</p>
          <h1 className="mt-2 text-3xl font-extrabold text-slate-900">Verify your mobile</h1>
          <p className="mt-2 text-sm leading-6 text-slate-500">We sent a 6-digit code by SMS to your account mobile.</p>
        </div>

        <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-center">
          <p className="text-[10px] font-extrabold uppercase tracking-[.14em] text-emerald-800">Account mobile</p>
          <p className="mt-1 text-lg font-extrabold text-emerald-950">{maskPhone(user.phone)}</p>
          <p className="mt-1 text-[11px] text-emerald-800">Your optional emergency contact is separate and is not verified here.</p>
        </div>

        <div className="mt-5 grid gap-4">
          <FormField label="6-digit verification code" hint="The code expires after a limited time and can be used only a limited number of times.">
            <TextInput
              value={otp}
              onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 6))}
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              placeholder="••••••"
              className="text-center text-xl font-black tracking-[0.55em]"
              aria-label="6-digit verification code"
            />
          </FormField>
          <p className="flex items-center justify-center gap-2 text-center text-xs text-slate-500"><Clock3 size={14} /> Codes expire and are invalidated after successful use.</p>
          <p aria-live="polite" className="text-center text-xs font-bold text-slate-600">{status}</p>
          {error ? <InlineAlert>{error}</InlineAlert> : null}
          <Button className="w-full" loading={verifying} onClick={() => void verify()} icon={<CheckCircle2 size={17} />}>Verify account mobile</Button>
          <Button className="w-full" variant="secondary" loading={resending} onClick={() => void resend()} icon={<RotateCcw size={16} />}>Resend code</Button>
        </div>

        <div className="mt-5 flex items-center gap-2 rounded-xl bg-slate-50 p-3 text-[11px] leading-5 text-slate-500"><LockKeyhole size={15} className="shrink-0" /> Twilio delivers the SMS. The FastAPI backend generates and verifies the time-based code; Twilio credentials never reach the browser.</div>
        <Button className="mt-5 w-full" variant="ghost" onClick={() => void leave()} icon={<ArrowLeft size={15} />}>Account created? Sign in later</Button>
      </Card>
    </section>
  );
}

function maskPhone(phone: string): string {
  if (phone.length < 6) return phone;
  return `${phone.slice(0, 3)}••••${phone.slice(-3)}`;
}

