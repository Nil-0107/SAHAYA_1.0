import { BarChart3, Bell, Building2, ListChecks, ScrollText, Settings2 } from "lucide-react";
import { DashboardShell } from "../components/navigation/DashboardShell";
import { useAuth } from "../context/AuthContext";

export function AdminLayout() {
  const { user } = useAuth();
  const national = user?.role === "national_admin";
  const base = national ? "/national-admin" : "/state-admin";
  return (
    <DashboardShell
      roleLabel={national ? "National Administrator" : "State Administrator"}
      items={[
        { label: "Programme overview", to: base, icon: BarChart3 },
        { label: national ? "State administrators" : "District administrators", to: `${base}/operations`, icon: Building2 },
        { label: "Priority queue", to: `${base}#queue`, icon: ListChecks },
        { label: "Notifications", to: `${base}#notifications`, icon: Bell },
        { label: "Audit log", to: `${base}#audit`, icon: ScrollText },
        { label: "System settings", to: `${base}#settings`, icon: Settings2 },
      ]}
    />
  );
}
