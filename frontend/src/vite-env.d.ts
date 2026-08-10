/// <reference types="vite/client" />
/// <reference types="vitest/globals" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_SENTRY_DSN: string;
  readonly VITE_POSTHOG_KEY: string;
  readonly VITE_DEV_AUTO_LOGIN: string;
  readonly VITE_DEV_USER_ID: string;
  readonly VITE_DEV_USER_ROLE: string;
  readonly VITE_DEV_USER_PHONE: string;
  readonly VITE_DEV_USER_NAME: string;
  readonly VITE_DEV_TOKEN: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
