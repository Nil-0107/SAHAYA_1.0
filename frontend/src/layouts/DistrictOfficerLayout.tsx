import { BriefcaseBusiness, FileText, Landmark, Scale, UserPlus } from "lucide-react";
import { DashboardShell } from "../components/navigation/DashboardShell";

export function DistrictOfficerLayout() {
  return (
    <DashboardShell
      roleLabel="District Officer"
      items={[
        { label: "Assistance dashboard", to: "/district-officer", icon: Landmark },
        { label: "Authorised cases", to: "/district-officer#cases", icon: BriefcaseBusiness },
        { label: "Legal coordination", to: "/district-officer#coordination", icon: Scale },
        { label: "Documents", to: "/district-officer#documents", icon: FileText },
        { label: "Appoint counsellor", to: "/district-officer/operations", icon: UserPlus },
      ]}
    />
  );
}
