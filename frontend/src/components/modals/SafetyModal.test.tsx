import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SafetyModal } from "./SafetyModal";


describe("SafetyModal", () => {
  it("asks the immediate-danger question before showing help", async () => {
    const onClose = vi.fn();
    render(<SafetyModal open onClose={onClose} />);

    expect(screen.getByRole("heading", { name: "Are you in immediate danger?" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Immediate help" })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Yes, show immediate help" }));
    expect(screen.getByRole("heading", { name: "Immediate help" })).toBeInTheDocument();
    expect(screen.getByText(/location has not been shared/i)).toBeInTheDocument();
  });

  it("returns to normal support when the user selects No", async () => {
    const onClose = vi.fn();
    render(<SafetyModal open onClose={onClose} />);

    await userEvent.click(screen.getByRole("button", { name: "No, continue support" }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("heading", { name: "Immediate help" })).not.toBeInTheDocument();
  });

  it("supports back navigation from immediate help", async () => {
    render(<SafetyModal open onClose={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: "Yes, show immediate help" }));
    await userEvent.click(screen.getByRole("button", { name: "Back" }));

    expect(screen.getByRole("heading", { name: "Are you in immediate danger?" })).toBeInTheDocument();
  });

  it("keeps the dialog scrollable on small screens", () => {
    render(<SafetyModal open onClose={vi.fn()} />);
    const dialog = screen.getByRole("dialog");
    expect(dialog.className).toContain("max-h-[calc(100vh-2rem)]");
    expect(dialog.className).toContain("overflow-y-auto");
  });
});
