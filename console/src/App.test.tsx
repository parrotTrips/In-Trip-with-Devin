import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

import App from './App';

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  vi.stubEnv('VITE_ENABLE_CONSOLE_LOCAL', 'false');
  vi.stubEnv('VITE_GOOGLE_CLIENT_ID', 'client.apps.googleusercontent.com');
});

test('shows the login screen when nobody is signed in', () => {
  render(<App />);
  expect(screen.getByText('Parrot Trips — Console')).toBeInTheDocument();
});
