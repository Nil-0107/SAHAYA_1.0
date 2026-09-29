/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_IMMEDIATE_HELP_RESOURCES?: string;
  readonly VITE_LOCAL_ROLE_LOGIN_ENABLED?: string;
  readonly VITE_LOCAL_TEST_VICTIM_EMAIL?: string;
  readonly VITE_LOCAL_TEST_VICTIM_PASSWORD?: string;
  readonly VITE_LOCAL_TEST_COUNSELLOR_EMAIL?: string;
  readonly VITE_LOCAL_TEST_COUNSELLOR_PASSWORD?: string;
  readonly VITE_LOCAL_TEST_DISTRICT_EMAIL?: string;
  readonly VITE_LOCAL_TEST_DISTRICT_PASSWORD?: string;
  readonly VITE_LOCAL_TEST_STATE_ADMIN_EMAIL?: string;
  readonly VITE_LOCAL_TEST_STATE_ADMIN_PASSWORD?: string;
  readonly VITE_LOCAL_TEST_NATIONAL_ADMIN_EMAIL?: string;
  readonly VITE_LOCAL_TEST_NATIONAL_ADMIN_PASSWORD?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
