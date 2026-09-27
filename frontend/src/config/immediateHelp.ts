export interface ImmediateHelpResource {
  label: string;
  description?: string;
  href?: string;
}

function isSafeHref(href: string): boolean {
  return href.startsWith("https://") || href.startsWith("http://") || href.startsWith("tel:");
}

export function parseImmediateHelpResources(raw: string | undefined): ImmediateHelpResource[] {
  if (!raw) return [];
  try {
    const value: unknown = JSON.parse(raw);
    if (!Array.isArray(value)) return [];
    return value.flatMap((item) => {
      if (!item || typeof item !== "object") return [];
      const record = item as Record<string, unknown>;
      const label = typeof record.label === "string" ? record.label.trim() : "";
      const description = typeof record.description === "string" ? record.description.trim() : "";
      const href = typeof record.href === "string" ? record.href.trim() : "";
      if (!label || (href && !isSafeHref(href))) return [];
      return [{ label, ...(description ? { description } : {}), ...(href ? { href } : {}) }];
    });
  } catch {
    return [];
  }
}

export const immediateHelpResources = parseImmediateHelpResources(
  import.meta.env.VITE_IMMEDIATE_HELP_RESOURCES,
);
