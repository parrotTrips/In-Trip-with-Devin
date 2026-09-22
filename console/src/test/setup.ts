import '@testing-library/jest-dom';
import { beforeEach, vi } from 'vitest';

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  vi.stubEnv('VITE_ALLOWED_EMAIL_DOMAIN', 'parrottrips.com');
  vi.stubEnv('VITE_ENABLE_CONSOLE_LOCAL', 'true');
});
