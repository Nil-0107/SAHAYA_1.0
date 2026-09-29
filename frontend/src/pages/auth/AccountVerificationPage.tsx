import { Navigate } from "react-router-dom";
import { LoadingState } from "../../components/feedback/FeedbackStates";
import { postAuthenticationPath } from "../../config/authRouting";
import { useAuth } from "../../context/AuthContext";

/** Compatibility entry for older links; the current backend verifies mobile during signup. */
export function AccountVerificationPage() {
  const { user, isLoading } = useAuth();
  if (isLoading) return <LoadingState label="Restoring your secure session…" />;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={postAuthenticationPath(user)} replace />;
}
