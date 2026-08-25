import { render, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { useEffect, useRef } from 'react';
import { afterEach, beforeEach, vi } from 'vitest';

import { server } from '../test/server';
import { AuthProvider } from './providers/AuthProvider';
import { useAuth } from './providers/auth-context';

const posthogMock = vi.hoisted(() => ({
  capture: vi.fn(),
  identify: vi.fn(),
  register: vi.fn(),
  reset: vi.fn(),
  unregister: vi.fn(),
}));

vi.mock('posthog-js', () => ({
  default: posthogMock,
}));

vi.mock('../features/trip/pages/HomeScreen', () => ({
  default: function MockHomeScreen() {
    return <div>Home screen</div>;
  },
}));

vi.mock('../features/trip/pages/DayDetails', () => ({
  default: function MockDayDetails() {
    return <div>Day details</div>;
  },
}));

vi.mock('../features/trip/pages/PhaseDetails', () => ({
  default: function MockPhaseDetails() {
    return <div>Phase details</div>;
  },
}));

vi.mock('../features/recommendations/pages/RecommendationsScreen', () => ({
  default: function MockRecommendationsScreen() {
    return <div>Recommendations</div>;
  },
}));

vi.mock('../features/profile/pages/ProfileScreen', () => ({
  default: function MockProfileScreen() {
    return <div>Profile</div>;
  },
}));

vi.mock('../features/team/pages/InformationScreen', () => ({
  default: function MockInformationScreen() {
    return <div>Information</div>;
  },
}));

vi.mock('../features/notifications/pages/NotificationsScreen', () => ({
  default: function MockNotificationsScreen() {
    return <div>Notifications</div>;
  },
}));

vi.mock('../features/staff/pages/StaffScreen', () => ({
  default: function MockStaffScreen() {
    return <div>Staff screen</div>;
  },
}));

import App from './App';

const TRIP_ONE = {
  trip: {
    wetravel_trip_uuid: 'trip-001',
    title: 'Trip One',
    destination: 'Test',
    start_date: '2026-02-27',
    end_date: '2026-03-08',
    url: null,
    service_agreement_url: null,
    trip_mode: 'in-trip',
  },
};

const TRIP_TWO = {
  trip: {
    wetravel_trip_uuid: 'trip-002',
    title: 'Trip Two',
    destination: 'Test',
    start_date: '2026-04-01',
    end_date: '2026-04-10',
    url: null,
    service_agreement_url: null,
    trip_mode: 'pre-trip',
  },
};

const EMPTY_PHASES = {
  wetravel_trip_uuid: 'trip-001',
  phases: [],
  ideal_pace_phase_id: null,
};

const EMPTY_TRAVELERS = { travelers: [] };

function setAuthenticatedUser() {
  localStorage.setItem(
    'parrot_user',
    JSON.stringify({ userId: 'user-001', phone: '+15551111111', name: 'Alice', token: 'tok', role: 'traveler' })
  );
}

function setupTripHandlers(tripResponse: unknown = TRIP_ONE) {
  server.use(
    http.get('http://localhost:8000/me/trip', () => HttpResponse.json(tripResponse as Record<string, unknown>)),
    http.get('http://localhost:8000/me/trip/phases', () => HttpResponse.json(EMPTY_PHASES)),
    http.get('http://localhost:8000/me/trip/travelers', () => HttpResponse.json(EMPTY_TRAVELERS)),
    http.get('http://localhost:8000/me/announcements', () => HttpResponse.json({ announcements: [], unread_count: 0 })),
  );
}

function expectLastScreenViewPayload(expected: Record<string, unknown>) {
  const screenViews = posthogMock.capture.mock.calls.filter(([event]) => event === 'tela_visitada');
  expect(screenViews[screenViews.length - 1]).toEqual(['tela_visitada', expected]);
}

describe('PostHog screen tracking', () => {
  beforeEach(() => {
    localStorage.clear();
    posthogMock.capture.mockClear();
    posthogMock.identify.mockClear();
    posthogMock.register.mockClear();
    posthogMock.reset.mockClear();
    posthogMock.unregister.mockClear();
    setAuthenticatedUser();
  });

  afterEach(() => {
    localStorage.clear();
  });

  test('normalizes day routes and includes loaded trip context', async () => {
    setupTripHandlers();
    window.history.pushState({}, '', '/day/123');

    render(<App />);

    await waitFor(() => {
      expectLastScreenViewPayload({
        tela: '/day',
        day_id: '123',
        viagem_id: 'trip-001',
        modo_viagem: 'in-trip',
      });
    });
  });

  test('normalizes phase routes and includes loaded trip context', async () => {
    setupTripHandlers();
    window.history.pushState({}, '', '/phase/456');

    render(<App />);

    await waitFor(() => {
      expectLastScreenViewPayload({
        tela: '/phase',
        phase_id: '456',
        viagem_id: 'trip-001',
        modo_viagem: 'in-trip',
      });
    });
  });

  test('keeps static routes as the tela value and includes loaded trip context', async () => {
    setupTripHandlers();
    window.history.pushState({}, '', '/recommendations');

    render(<App />);

    await waitFor(() => {
      expectLastScreenViewPayload({
        tela: '/recommendations',
        viagem_id: 'trip-001',
        modo_viagem: 'in-trip',
      });
    });
  });

  test('does not keep previous trip context when there is no active trip', async () => {
    setupTripHandlers(TRIP_ONE);
    window.history.pushState({}, '', '/recommendations');

    const firstRender = render(<App />);

    await waitFor(() => {
      expectLastScreenViewPayload({
        tela: '/recommendations',
        viagem_id: 'trip-001',
        modo_viagem: 'in-trip',
      });
    });

    firstRender.unmount();
    posthogMock.capture.mockClear();
    setupTripHandlers({ trip: null });

    render(<App />);

    await waitFor(() => {
      expect(posthogMock.unregister).toHaveBeenCalledWith('viagem_id');
      expect(posthogMock.unregister).toHaveBeenCalledWith('modo_viagem');
      expectLastScreenViewPayload({ tela: '/recommendations' });
    });
  });

  test('replaces registered trip context when the active trip changes', async () => {
    setupTripHandlers(TRIP_TWO);
    window.history.pushState({}, '', '/recommendations');

    render(<App />);

    await waitFor(() => {
      expect(posthogMock.unregister).toHaveBeenCalledWith('viagem_id');
      expect(posthogMock.unregister).toHaveBeenCalledWith('modo_viagem');
      expect(posthogMock.register).toHaveBeenCalledWith({ viagem_id: 'trip-002', modo_viagem: 'pre-trip' });
      expectLastScreenViewPayload({
        tela: '/recommendations',
        viagem_id: 'trip-002',
        modo_viagem: 'pre-trip',
      });
    });
  });

  test('logout resets PostHog identity and registered properties', async () => {
    function LogoutProbe() {
      const { login, logout } = useAuth();
      const didRun = useRef(false);

      useEffect(() => {
        if (didRun.current) return;
        didRun.current = true;
        login('user-001', '+15551111111', 'Alice', 'tok', 'traveler');
        logout();
      }, [login, logout]);

      return null;
    }

    render(
      <AuthProvider>
        <LogoutProbe />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(posthogMock.identify).toHaveBeenCalledWith('user-001', {
        telefone: '+15551111111',
        nome: 'Alice',
        papel: 'traveler',
      });
      expect(posthogMock.reset).toHaveBeenCalled();
    });
  });
});
