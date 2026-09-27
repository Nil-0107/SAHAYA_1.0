import { Card } from "../components/common/Card";
import { ForbiddenState } from "../components/feedback/FeedbackStates";

export function ForbiddenPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-saathi-50 p-5">
      <Card className="w-full max-w-lg p-6"><ForbiddenState /></Card>
    </main>
  );
}
