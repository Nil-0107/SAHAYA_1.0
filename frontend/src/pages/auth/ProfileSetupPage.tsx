import { useEffect, useState, type FormEvent } from "react";
import { CheckCircle2, ContactRound, Languages, MapPin, ShieldCheck } from "lucide-react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button } from "../../components/common/Button";
import { Card } from "../../components/common/Card";
import { ErrorState, InlineAlert, LoadingState } from "../../components/feedback/FeedbackStates";
import { FormField, SelectInput, TextArea, TextInput } from "../../components/forms/FormField";
import { postAuthenticationPath } from "../../config/authRouting";
import { useAuth } from "../../context/AuthContext";
import { profileApi } from "../../services/profileApi";
import type { ProfileSetupPayload } from "../../types/profile";
import { authErrorMessage } from "../../utils/authErrors";
import { AuthProgress } from "./SignupPage";

const blankForm = {
  full_name: "",
  display_name: "",
  preferred_language: "English",
  city_or_district: "",
  emergency_contact_name: "",
  emergency_contact_phone: "",
  safe_contact_method: "",
  address: "",
  case_reference: "",
  relationship_to_case: "",
  role_in_case: "",
};

export function ProfileSetupPage() {
  const navigate = useNavigate();
  const { user, isLoading: sessionLoading, refreshUser, pendingFullName, clearPendingFullName } = useAuth();
  const [form, setForm] = useState({ ...blankForm, full_name: pendingFullName, display_name: pendingFullName });
  const [consent, setConsent] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user?.phone_verified_at) return;
    let active = true;
    profileApi
      .get()
      .then((response) => {
        if (!active || !response.profile) return;
        const profile = response.profile;
        setForm({
          full_name: profile.full_name,
          display_name: profile.display_name,
          preferred_language: profile.preferred_language,
          city_or_district: profile.city_or_district,
          emergency_contact_name: profile.emergency_contact_name ?? "",
          emergency_contact_phone: profile.emergency_contact_phone ?? "",
          safe_contact_method: profile.safe_contact_method ?? "",
          address: profile.address ?? "",
          case_reference: profile.case_reference ?? "",
          relationship_to_case: profile.relationship_to_case ?? "",
          role_in_case: profile.role_in_case ?? "",
        });
        setConsent(true);
      })
      .catch((caught) => {
        if (active) setLoadError(authErrorMessage(caught, "Unable to load profile information."));
      })
      .finally(() => {
        if (active) setLoadingProfile(false);
      });
    return () => { active = false; };
  }, [user?.phone_verified_at]);

  if (sessionLoading) return <LoadingState label="Restoring your secure session…" />;
  if (!user) return <Navigate to="/login" replace />;

  if (user.profile_completed) return <Navigate to={postAuthenticationPath(user)} replace />;

  const updateField = (field: keyof typeof blankForm, value: string) => setForm((current) => ({ ...current, [field]: value }));
  const hasEmergencyContact = Boolean(form.emergency_contact_name && form.emergency_contact_phone);

  const submitProfile = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    if (!consent) return setError("Consent is required to complete profile setup.");
    if (Boolean(form.emergency_contact_name) !== Boolean(form.emergency_contact_phone)) {
      return setError("Emergency contact name and phone must be provided together.");
    }
    if (hasEmergencyContact && form.emergency_contact_phone && !/^[6-9]\d{9}$/.test(form.emergency_contact_phone)) {
      return setError("Emergency contact phone must be a valid 10-digit mobile number.");
    }
    setSubmitting(true);
    try {
      const payload: ProfileSetupPayload = {
        full_name: form.full_name.trim(),
        display_name: form.display_name.trim(),
        preferred_language: form.preferred_language,
        city_or_district: form.city_or_district.trim(),
        emergency_contact_name: form.emergency_contact_name || undefined,
        emergency_contact_phone: form.emergency_contact_phone || undefined,
        safe_contact_method: hasEmergencyContact ? form.safe_contact_method || undefined : undefined,
        address: form.address || undefined,
        case_reference: form.case_reference || undefined,
        relationship_to_case: form.relationship_to_case || undefined,
        role_in_case: form.role_in_case || undefined,
        consent: true,
      };
      await profileApi.setup(payload);
      clearPendingFullName();
      const updatedUser = await refreshUser();
      navigate(postAuthenticationPath(updatedUser), { replace: true });
    } catch (caught) {
      setError(authErrorMessage(caught, "Profile setup failed. Please try again."));
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingProfile) return <LoadingState label="Loading profile setup…" />;

  return (
    <section className="mx-auto max-w-3xl">
      <AuthProgress current={2} />
      <Card className="mt-5 p-6 sm:p-8">
        <div className="text-center">
          <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-sahaya-50 text-sahaya-700"><CheckCircle2 size={23} /></span>
          <p className="mt-4 text-[11px] font-extrabold uppercase tracking-[.16em] text-sahaya-700">One-time setup</p>
          <h1 className="mt-2 text-3xl font-extrabold text-slate-900">Finish your profile</h1>
          <p className="mt-2 text-sm leading-6 text-slate-500">This setup is completed once. Your account mobile was provided during registration and is not an emergency contact.</p>
        </div>

        <div className="mt-5 flex items-start gap-3 rounded-2xl border border-teal-200 bg-teal-50 p-4">
          <ShieldCheck className="mt-0.5 shrink-0 text-emerald-700" size={19} />
          <div><p className="text-xs font-extrabold uppercase tracking-wider text-sahaya-800">Account mobile · Registered</p><p className="mt-1 text-sm font-bold text-sahaya-950">{user.phone}</p><p className="mt-1 text-[11px] text-sahaya-900">This is your own account number and is not an emergency contact.</p></div>
        </div>

        {loadError ? <div className="mt-5"><ErrorState message={loadError} onRetry={() => window.location.reload()} /></div> : null}

        <form className="mt-6 grid gap-5" onSubmit={submitProfile}>
          <fieldset>
            <legend className="flex items-center gap-2 text-sm font-extrabold text-slate-900"><ContactRound size={17} className="text-sahaya-700" /> Basic profile</legend>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <FormField label="Full name"><TextInput required autoComplete="name" maxLength={120} value={form.full_name} onChange={(event) => updateField("full_name", event.target.value)} /></FormField>
              <FormField label="Display name"><TextInput required autoComplete="nickname" maxLength={80} value={form.display_name} onChange={(event) => updateField("display_name", event.target.value)} /></FormField>
              <FormField label="Preferred language">
                <SelectInput required value={form.preferred_language} onChange={(event) => updateField("preferred_language", event.target.value)}>
                  <option>English</option><option>Hindi</option><option>বাংলা</option><option>मराठी</option><option>தமிழ்</option><option>తెలుగు</option><option>ಕನ್ನಡ</option><option>Malayalam</option><option>Gujarati</option><option>Punjabi</option><option>Odia</option><option>Assamese</option><option>Urdu</option>
                </SelectInput>
              </FormField>
              <FormField label="City / district">
                <div className="relative"><MapPin size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" /><TextInput required maxLength={100} className="pl-9" value={form.city_or_district} onChange={(event) => updateField("city_or_district", event.target.value)} /></div>
              </FormField>
            </div>
          </fieldset>

          <fieldset className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
            <legend className="flex items-center gap-2 px-1 text-sm font-extrabold text-amber-950"><ContactRound size={17} /> Emergency contact · Optional</legend>
            <p className="text-[11px] leading-5 text-amber-900">This unverified contact is separate from your account mobile. Leave blank if you do not want to provide one.</p>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <FormField label="Contact name"><TextInput autoComplete="off" maxLength={120} value={form.emergency_contact_name} onChange={(event) => updateField("emergency_contact_name", event.target.value)} /></FormField>
              <FormField label="Contact phone"><TextInput inputMode="numeric" maxLength={10} value={form.emergency_contact_phone} onChange={(event) => updateField("emergency_contact_phone", event.target.value.replace(/\D/g, ""))} /></FormField>
              <div className="sm:col-span-2">
                <FormField label="Safe contact method" hint={hasEmergencyContact ? "Optional instructions for a safe time or method" : "Available after a contact name and phone are provided"}>
                  <TextInput disabled={!hasEmergencyContact} maxLength={160} placeholder="For example: phone after 6 PM" value={form.safe_contact_method} onChange={(event) => updateField("safe_contact_method", event.target.value)} />
                </FormField>
              </div>
            </div>
          </fieldset>

          <details className="rounded-2xl border border-slate-200 p-4">
            <summary className="cursor-pointer text-sm font-extrabold text-slate-800">Optional case context</summary>
            <p className="mt-2 text-[11px] leading-5 text-slate-500">These fields do not create a case or contact an officer.</p>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <FormField label="Address"><TextInput autoComplete="street-address" value={form.address} onChange={(event) => updateField("address", event.target.value)} /></FormField>
              <FormField label="Case reference"><TextInput value={form.case_reference} onChange={(event) => updateField("case_reference", event.target.value)} /></FormField>
              <FormField label="Relationship to case"><TextInput value={form.relationship_to_case} onChange={(event) => updateField("relationship_to_case", event.target.value)} /></FormField>
              <FormField label="Role in case"><TextInput value={form.role_in_case} onChange={(event) => updateField("role_in_case", event.target.value)} /></FormField>
            </div>
          </details>

          <label className="flex items-start gap-2 text-xs leading-5 text-slate-700">
            <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} className="mt-1 h-4 w-4 accent-sahaya-700" />
            I consent to this one-time profile setup and confirm that the emergency contact is optional and separate from my account mobile.
          </label>
          {error ? <InlineAlert>{error}</InlineAlert> : null}
          <Button type="submit" loading={submitting} icon={<Languages size={17} />}>Finish account setup</Button>
        </form>
      </Card>
    </section>
  );
}
