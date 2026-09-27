import { Navigate, Outlet, useLocation } from "react-router-dom";
import { LoadingState } from "../components/feedback/FeedbackStates";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute() {
  const { user, isLoading, sessionExpired } = useAuth();
  const location = useLocation();
  if (isLoading) return <LoadingState label="Restoring your secure session…" />;
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location, reason: sessionExpired ? "session-expired" : undefined }} />;
  }
  return <Outlet />;
}
