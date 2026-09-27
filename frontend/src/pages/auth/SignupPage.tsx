import { useMemo, useState, type FormEvent } from "react";
import { Check, Eye, EyeOff, ShieldCheck } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../../components/common/Button";
import { Card } from "../../components/common/Card";
import { InlineAlert } from "../../components/feedback/FeedbackStates";
import { FormField, TextInput } from "../../components/forms/FormField";
import { useAuth } from "../../context/AuthContext";
import { authApi, type AuthSession } from "../../services/authApi";
import { authErrorMessage } from "../../utils/authErrors";

export function SignupPage() {
  const navigate = useNavigate();
  const { adoptSignup } = useAuth();
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const passwordChecks = useMemo(
    () => [
      password.length >= 8,
      /[a-z]/.test(password),
      /[A-Z]/.test(password),
      /\d/.test(password),
      /[^A-Za-z0-9]/.test(password),
    ],
    [password],
  );
  const passwordScore = passwordChecks.filter(Boolean).length;

  const submitSignup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    if (!/^[6-9]\d{9}$/.test(phone)) {
      setError("Enter a valid 10-digit account mobile number.");
      return;
    }
    if (!dateOfBirth) {
      setError("Enter your date of birth.");
      return;
    }
    if (passwordScore < 5) {
      setError("Use at least 8 characters with uppercase, lowercase, number and symbol.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setSubmitting(true);
    try {
      const result = await authApi.signup({ phone: `+91${phone}`, email: email || null, password, date_of_birth: dateOfBirth, role: "victim" });
      const session: AuthSession = {
        access_token: result.access_token,
        token_type: result.token_type,
        expires_in: result.expires_in,
        user: result.user,
      };
      adoptSignup(session, fullName);
      navigate("/profile/setup", { replace: true });
    } catch (caught) {
      setError(authErrorMessage(caught, "Account creation failed. Please try again."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mx-auto max-w-2xl">
      <AuthProgress current={1} />
      <Card className="mt-5 p-6 sm:p-8">
        <p className="text-[11px] font-extrabold uppercase tracking-[.16em] text-saathi-700">Account details</p>
        <h1 className="mt-2 text-3xl font-extrabold text-slate-900">Create your account</h1>
        <p className="mt-2 text-sm leading-6 text-slate-500">You are creating a Victim / User account. Your account mobile is used as your account contact number. It is not your emergency contact.</p>

        <form className="mt-6 grid gap-4" onSubmit={submitSignup}>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField label="Full name">
              <TextInput required autoComplete="name" maxLength={120} value={fullName} onChange={(event) => setFullName(event.target.value)} />
            </FormField>
            <FormField label="Account mobile" hint="10-digit Indian mobile number">
              <div className="flex overflow-hidden rounded-[10px] border border-slate-300 bg-white focus-within:border-saathi-500 focus-within:ring-2 focus-within:ring-teal-100">
                <span className="grid min-w-14 place-items-center border-r border-slate-200 bg-slate-50 px-3 text-sm font-bold text-slate-600">+91</span>
                <TextInput required inputMode="numeric" maxLength={10} autoComplete="tel-national" value={phone} onChange={(event) => setPhone(event.target.value.replace(/\D/g, ""))} className="border-0 focus:ring-0" />
              </div>
            </FormField>
          </div>
          <FormField label="Date of birth" hint="Used for account registration. It is not an emergency-contact field.">
            <TextInput required type="date" max={new Date().toISOString().slice(0, 10)} value={dateOfBirth} onChange={(event) => setDateOfBirth(event.target.value)} />
          </FormField>
          <FormField label="Email address" hint="Optional">
            <TextInput type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </FormField>
          <FormField label="Password">
            <div className="relative">
              <TextInput required type={showPassword ? "text" : "password"} autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} className="pr-12" />
              <button type="button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword((current) => !current)} className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-2 text-saathi-700 focus:outline-none focus:ring-2 focus:ring-saathi-500">
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
            <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[10px] font-bold text-slate-500">
              {["8+ characters", "Lowercase", "Uppercase", "Number", "Symbol"].map((label, index) => <span key={label} className={passwordChecks[index] ? "text-emerald-700" : ""}>{passwordChecks[index] ? "✓" : "○"} {label}</span>)}
            </div>
          </FormField>
          <FormField label="Confirm password">
            <TextInput required type={showPassword ? "text" : "password"} autoComplete="new-password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} />
          </FormField>
          {error ? <InlineAlert>{error}</InlineAlert> : null}
          <Button type="submit" loading={submitting}>Create account & continue</Button>
          <p className="flex items-center justify-center gap-2 text-center text-[11px] leading-5 text-slate-500"><ShieldCheck size={14} /> Your password is never stored in browser storage.</p>
        </form>
        <p className="mt-5 text-center text-xs text-slate-500">Already have an account? <Link to="/login" className="font-extrabold text-saathi-700">Log in</Link></p>
      </Card>
    </section>
  );
}

export function AuthProgress({ current }: { current: 1 | 2 }) {
  const steps = ["Account", "Profile"];
  return (
    <ol className="mx-auto flex max-w-md items-center" aria-label="Account setup progress">
      {steps.map((step, index) => {
        const number = index + 1;
        const complete = number < current;
        const active = number === current;
        return (
          <li key={step} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-1">
              <span aria-current={active ? "step" : undefined} className={`grid h-8 w-8 place-items-center rounded-full text-xs font-extrabold ${complete ? "bg-emerald-600 text-white" : active ? "bg-saathi-900 text-white" : "border border-slate-300 bg-white text-slate-400"}`}>
                {complete ? <Check size={14} /> : number}
              </span>
              <span className={`text-[10px] font-extrabold ${active ? "text-saathi-900" : "text-slate-400"}`}>{step}</span>
            </div>
            {number < steps.length ? <span aria-hidden="true" className={`mx-2 mb-5 h-px flex-1 ${complete ? "bg-emerald-500" : "bg-slate-200"}`} /> : null}
          </li>
        );
      })}
    </ol>
  );
}
