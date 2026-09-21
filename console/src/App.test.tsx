import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';

import App from './App';

beforeEach(() => {
  localStorage.clear();
  // The local .env sets VITE_DEV_AUTO_LOGIN; pin it off so tests do not
  // depend on the developer's machine.
  vi.stubEnv('VITE_DEV_AUTO_LOGIN', '');
});

test('shows the login screen when nobody is signed in', () => {
  render(<App />);
  expect(screen.getByText('Parrot Trips — Console')).toBeInTheDocument();
});
