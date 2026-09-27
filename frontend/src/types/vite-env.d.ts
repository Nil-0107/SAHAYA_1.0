/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_IMMEDIATE_HELP_RESOURCES?: string;
  readonly VITE_DEMO_AUTH_ENABLED?: string;
  readonly VITE_DEMO_VICTIM_EMAIL?: string;
  readonly VITE_DEMO_VICTIM_PASSWORD?: string;
  readonly VITE_DEMO_COUNSELLOR_EMAIL?: string;
  readonly VITE_DEMO_COUNSELLOR_PASSWORD?: string;
  readonly VITE_DEMO_DISTRICT_EMAIL?: string;
  readonly VITE_DEMO_DISTRICT_PASSWORD?: string;
  readonly VITE_DEMO_ADMIN_EMAIL?: string;
  readonly VITE_DEMO_ADMIN_PASSWORD?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
