import { BrainCircuit, BriefcaseBusiness, HeartHandshake, Home, LineChart, NotebookPen, Scale, ShieldCheck } from "lucide-react";
import { DashboardShell } from "../components/navigation/DashboardShell";

export function VictimLayout() {
  return (
    <DashboardShell
      roleLabel="Victim / User"
      items={[
        { label: "Overview", to: "/victim", icon: Home },
        { label: "Well-being check", to: "/victim#check-in", icon: NotebookPen },
        { label: "AI support", to: "/victim#ai-support", icon: BrainCircuit },
        { label: "My case & documents", to: "/victim#my-case", icon: BriefcaseBusiness },
        { label: "My progress", to: "/victim#my-progress", icon: LineChart },
        { label: "My summary", to: "/victim#my-summary", icon: ShieldCheck },
        { label: "Legal assistance", to: "/victim#legal-assistance", icon: Scale },
        { label: "Support", to: "/victim#support", icon: HeartHandshake },
      ]}
    />
  );
}
