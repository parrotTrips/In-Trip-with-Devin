/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_GOOGLE_CLIENT_ID: string;
  readonly VITE_ALLOWED_EMAIL_DOMAIN: string;
  readonly VITE_ENABLE_CONSOLE_LOCAL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
