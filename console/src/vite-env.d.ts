/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_DEV_AUTO_LOGIN: string;
  readonly VITE_DEV_TOKEN: string;
  readonly VITE_DEV_USER_ID: string;
  readonly VITE_DEV_USER_PHONE: string;
  readonly VITE_DEV_USER_NAME: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
