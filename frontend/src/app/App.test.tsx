import { render, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, vi } from 'vitest';

import { server } from '../test/server';
import App from './App';

const MOCK_TRIP = {
  trip: { wetravel_trip_uuid: 'test-001', title: 'Test Trip', destination: 'Test', start_date: '2026-02-27', end_date: '2026-03-08', url: null },
};
const MOCK_PHASES = {
  wetravel_trip_uuid: 'test-001',
  phases: [
    { id: 'ph-1', phase_type: 'pre-trip', title: 'Visa', subtitle: null, icon: 'passport', short_description: 'Visa', detailed_description: null, sort_order: 0, starts_at: null, is_locked_by_default: false, checklist_items: [], links: [] },
  ],
};
const MOCK_TRAVELERS = { travelers: [] };

function setupTripHandlers() {
  server.use(
    http.get('http://localhost:8000/me/trip', () => HttpResponse.json(MOCK_TRIP)),
    http.get('http://localhost:8000/me/trip/phases', () => HttpResponse.json(MOCK_PHASES)),
    http.get('http://localhost:8000/me/trip/travelers', () => HttpResponse.json(MOCK_TRAVELERS)),
  );
}

describe('App composition', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllEnvs();
    setupTripHandlers();
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

  test('renders main routes when the user is authenticated', async () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'uid-1', phone: '+15551111111', name: 'Alice', token: 'tok', role: 'traveler' })
    );
    window.history.pushState({}, '', '/');

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Trip Progress')).toBeInTheDocument();
    });
    expect(screen.getByText('Map')).toBeInTheDocument();
    expect(screen.getByText('My Profile')).toBeInTheDocument();
    expect(screen.queryByText('Secret Missions')).not.toBeInTheDocument();
    expect(screen.queryByText('Sharing XP')).not.toBeInTheDocument();
  });

  test('renders main routes when dev auto-login is enabled', async () => {
    vi.stubEnv('VITE_DEV_AUTO_LOGIN', 'true');
    vi.stubEnv('VITE_DEV_USER_ID', 'uid-7');
    vi.stubEnv('VITE_DEV_USER_PHONE', '+15557777777');
    vi.stubEnv('VITE_DEV_USER_NAME', 'Dev Traveler');

    window.history.pushState({}, '', '/');

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Trip Progress')).toBeInTheDocument();
    });
    expect(screen.getByText('Map')).toBeInTheDocument();
    expect(screen.getByText('My Profile')).toBeInTheDocument();
    expect(screen.queryByText('Secret Missions')).not.toBeInTheDocument();
    expect(screen.queryByText('Sharing XP')).not.toBeInTheDocument();
  });
});
