import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, vi } from 'vitest';

import App from './App';
import { server } from '../test/server';

describe('App composition', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllEnvs();
  });

  afterEach(() => {
    localStorage.clear();
    vi.unstubAllEnvs();
  });

  test('renders login when there is no authenticated user', () => {
    window.history.pushState({}, '', '/');

    render(<App />);

    expect(screen.getByText('Welcome, Traveler!')).toBeInTheDocument();
  });

  test('renders main routes when the user is authenticated', () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15551111111', name: 'Alice' })
    );
    window.history.pushState({}, '', '/');
    server.use(
      http.get('http://localhost:8000/notifications/:userId/count', () =>
        HttpResponse.json({ unread_count: 0 })
      )
    );

    render(<App />);

    expect(screen.getByText('Trip Progress')).toBeInTheDocument();
    expect(screen.getByText('Map')).toBeInTheDocument();
  });

  test('renders main routes when dev auto-login is enabled', () => {
    vi.stubEnv('VITE_DEV_AUTO_LOGIN', 'true');
    vi.stubEnv('VITE_DEV_USER_ID', '7');
    vi.stubEnv('VITE_DEV_USER_PHONE', '+15557777777');
    vi.stubEnv('VITE_DEV_USER_NAME', 'Dev Traveler');

    window.history.pushState({}, '', '/');
    server.use(
      http.get('http://localhost:8000/notifications/:userId/count', () =>
        HttpResponse.json({ unread_count: 0 })
      )
    );

    render(<App />);

    expect(screen.getByText('Trip Progress')).toBeInTheDocument();
    expect(screen.getByText('Map')).toBeInTheDocument();
  });
});
