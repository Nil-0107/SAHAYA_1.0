import { describe, expect, it } from "vitest";
import { parseImmediateHelpResources } from "./immediateHelp";

describe("immediate help resource configuration", () => {
  it("returns no resources when none are configured", () => {
    expect(parseImmediateHelpResources(undefined)).toEqual([]);
    expect(parseImmediateHelpResources("[]")).toEqual([]);
  });

  it("accepts only explicitly configured safe resources", () => {
    expect(parseImmediateHelpResources(JSON.stringify([
      { label: "Configured local resource", description: "Verified resource", href: "https://example.invalid/help" },
      { label: "Unsafe resource", href: "javascript:alert(1)" },
    ]))).toEqual([
      { label: "Configured local resource", description: "Verified resource", href: "https://example.invalid/help" },
    ]);
  });
});
