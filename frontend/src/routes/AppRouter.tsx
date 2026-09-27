import { Route, Routes } from "react-router-dom";
import { AdminLayout } from "../layouts/AdminLayout";
import { AuthLayout } from "../layouts/AuthLayout";
import { CounsellorLayout } from "../layouts/CounsellorLayout";
import { DistrictOfficerLayout } from "../layouts/DistrictOfficerLayout";
import { PublicLayout } from "../layouts/PublicLayout";
import { VictimLayout } from "../layouts/VictimLayout";
import { LoginPage } from "../pages/auth/LoginPage";
import { ProfileSetupPage } from "../pages/auth/ProfileSetupPage";
import { RoleSelectionPage } from "../pages/auth/RoleSelectionPage";
import { SignupPage } from "../pages/auth/SignupPage";
import { AdminDashboardPage } from "../pages/admin/DashboardPage";
import { AdminOperationsPage } from "../pages/admin/AdminOperationsPage";
import { CounsellorDashboardPage } from "../pages/counsellor/DashboardPage";
import { DistrictDashboardPage } from "../pages/district-officer/DashboardPage";
import { ForbiddenPage } from "../pages/ForbiddenPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { LandingPage } from "../pages/public/LandingPage";
import { VictimDashboardPage } from "../pages/victim/DashboardPage";
import { OnboardingRoute } from "./OnboardingRoute";
import { ProtectedRoute } from "./ProtectedRoute";
import { RoleRoute } from "./RoleRoute";

export function AppRouter() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<LandingPage />} />
      </Route>

      <Route element={<AuthLayout />}>
        <Route path="login" element={<LoginPage />} />
        <Route path="signup/role" element={<RoleSelectionPage />} />
        <Route path="signup" element={<SignupPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<OnboardingRoute step="profile" />}>
            <Route path="profile/setup" element={<ProfileSetupPage />} />
          </Route>
        </Route>
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<OnboardingRoute step="dashboard" />}>
          <Route element={<RoleRoute allowedRoles={["victim"]} />}>
            <Route element={<VictimLayout />}>
              <Route path="victim" element={<VictimDashboardPage />} />
            </Route>
          </Route>
          <Route element={<RoleRoute allowedRoles={["counsellor"]} />}>
            <Route element={<CounsellorLayout />}>
              <Route path="counsellor" element={<CounsellorDashboardPage />} />
            </Route>
          </Route>
          <Route element={<RoleRoute allowedRoles={["district_admin"]} />}>
            <Route element={<DistrictOfficerLayout />}>
              <Route path="district-officer" element={<DistrictDashboardPage />} />
              <Route path="district-officer/operations" element={<AdminOperationsPage />} />
            </Route>
          </Route>
          <Route element={<RoleRoute allowedRoles={["state_admin", "national_admin"]} />}>
            <Route element={<AdminLayout />}>
              <Route path="state-admin" element={<AdminDashboardPage />} />
              <Route path="state-admin/operations" element={<AdminOperationsPage />} />
              <Route path="national-admin" element={<AdminDashboardPage />} />
              <Route path="national-admin/operations" element={<AdminOperationsPage />} />
            </Route>
          </Route>
        </Route>
      </Route>

      <Route path="forbidden" element={<ForbiddenPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
