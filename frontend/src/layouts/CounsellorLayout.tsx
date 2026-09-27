import { ClipboardCheck, HeartHandshake, Inbox, UsersRound } from "lucide-react";
import { DashboardShell } from "../components/navigation/DashboardShell";

export function CounsellorLayout() {
  return (
    <DashboardShell
      roleLabel="Psychologist / Counsellor"
      items={[
        { label: "Care dashboard", to: "/counsellor", icon: Inbox },
        { label: "Assigned people", to: "/counsellor#assigned", icon: UsersRound },
        { label: "Follow-up", to: "/counsellor#follow-up", icon: HeartHandshake },
        { label: "Support actions", to: "/counsellor#actions", icon: ClipboardCheck },
      ]}
    />
  );
}
