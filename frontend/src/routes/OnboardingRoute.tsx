import { Navigate, Outlet } from "react-router-dom";
import { postAuthenticationPath } from "../config/demoAuth";
import { useAuth } from "../context/AuthContext";

export function OnboardingRoute({ step }: { step: "profile" | "dashboard" }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;

  if (step === "profile" && user.profile_completed) return <Navigate to={postAuthenticationPath(user)} replace />;
  if (step === "dashboard" && !user.profile_completed) return <Navigate to="/profile/setup" replace />;
  return <Outlet />;
}
