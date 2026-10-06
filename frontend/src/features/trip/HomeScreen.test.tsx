import { render, screen, within } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, vi } from 'vitest';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { TripProvider } from '../../app/providers/TripProvider';
import { server } from '../../test/server';
import HomeScreen from './pages/HomeScreen';

const TRIP_UUID = 'test-trip-001';
const USER_ID = 'traveler-001';

function makePhase({
  id,
  title,
  sortOrder,
  icon = 'passport',
  phaseType = 'pre-trip',
  startsAt = null,
}: {
  id: string;
  title: string;
  sortOrder: number;
  icon?: string;
  phaseType?: 'pre-trip' | 'in-trip';
  startsAt?: string | null;
}) {
  return {
    id,
    phase_type: phaseType,
    title,
    subtitle: null,
    icon,
    short_description: `${title} details`,
    detailed_description: null,
    sort_order: sortOrder,
    starts_at: startsAt,
    is_locked_by_default: false,
    checklist_items: [],
    links: [],
  };
}

function setupHandlers({
  idealPacePhaseId = null,
  currentPhaseId = 'phase-001',
  phases = [makePhase({ id: 'phase-001', title: 'Passport', sortOrder: 0 })],
  completedPhaseIds = [],
  tripMode = 'pre-trip',
}: {
  idealPacePhaseId?: string | null;
  currentPhaseId?: string | null;
  completedPhaseIds?: string[];
  tripMode?: 'pre-trip' | 'in-trip';
  phases?: Array<{
    id: string;
    phase_type: string;
    title: string;
    subtitle: string | null;
    icon: string | null;
    short_description: string | null;
    detailed_description: string | null;
    sort_order: number;
    starts_at: string | null;
    is_locked_by_default: boolean;
    checklist_items: unknown[];
    links: unknown[];
  }>;
} = {}) {
  server.use(
    http.get('http://localhost:8000/me/trip', () =>
      HttpResponse.json({
        trip: {
          wetravel_trip_uuid: TRIP_UUID,
          title: 'Peru Adventure',
          destination: 'Peru',
          start_date: '2026-02-27',
          end_date: '2026-03-08',
          url: null,
          service_agreement_url: null,
          trip_mode: tripMode,
        },
      })
    ),
    http.get('http://localhost:8000/me/trip/phases', () =>
      HttpResponse.json({
        wetravel_trip_uuid: TRIP_UUID,
        phases,
        ideal_pace_phase_id: idealPacePhaseId,
        completed_phase_ids: completedPhaseIds,
      })
    ),
    http.get('http://localhost:8000/me/trip/travelers', () =>
      HttpResponse.json({
        travelers: [
          {
            id: USER_ID,
            name: 'Alice Traveler',
            phone: '+15550000001',
            current_phase_id: currentPhaseId,
          },
        ],
      })
    ),
  );
}

describe('HomeScreen', () => {
  afterEach(() => {
    Reflect.deleteProperty(window.HTMLElement.prototype, 'scrollIntoView');
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({
        userId: USER_ID,
        phone: '+15550000001',
        name: 'Alice Traveler',
        token: 'tok',
        role: 'traveler',
        tripId: TRIP_UUID,
        activeTrip: null,
      })
    );
    setupHandlers();
  });

  test('shows the trip title only in the app header', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <TripProvider>
            <Routes>
              <Route path="/" element={<HomeScreen />} />
            </Routes>
          </TripProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findAllByText('Peru Adventure')).toHaveLength(1);
    expect(screen.queryByRole('heading', { name: 'My QR Code' })).not.toBeInTheDocument();
  });

  test('shows the date on in-trip day cards only', async () => {
    setupHandlers({
      phases: [
        makePhase({ id: 'phase-001', title: 'Passport', sortOrder: 0 }),
        makePhase({
          id: 'day-001',
          title: 'Day 1',
          sortOrder: 1,
          phaseType: 'in-trip',
          startsAt: '2026-09-08T03:00:00Z',
        }),
      ],
    });

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <TripProvider>
            <Routes>
              <Route path="/" element={<HomeScreen />} />
            </Routes>
          </TripProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Tue • Sep 08')).toBeInTheDocument();
    expect(screen.queryAllByText(/•/)).toHaveLength(1);
  });

  test('keeps the journey summary sticky below the app header', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <TripProvider>
            <Routes>
              <Route path="/" element={<HomeScreen />} />
            </Routes>
          </TripProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('Passport');

    expect(screen.getByTestId('journey-sticky-header')).toHaveClass('sticky', 'top-14');
  });

  test('centers the current phase after the journey loads', async () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(window.HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: scrollIntoView,
    });
    setupHandlers({
      currentPhaseId: 'phase-003',
      phases: [
        makePhase({ id: 'phase-001', title: 'Passport', sortOrder: 0 }),
        makePhase({ id: 'phase-002', title: 'Packing', sortOrder: 1, icon: 'luggage' }),
        makePhase({ id: 'phase-003', title: 'Airport', sortOrder: 2, icon: 'plane' }),
      ],
    });

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <TripProvider>
            <Routes>
              <Route path="/" element={<HomeScreen />} />
            </Routes>
          </TripProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('Airport');

    expect(scrollIntoView).toHaveBeenCalledWith({ block: 'center', inline: 'nearest' });
  });

  test('groups parrot and completed check in one card badge container', async () => {
    setupHandlers({ idealPacePhaseId: 'phase-001', currentPhaseId: 'phase-999', completedPhaseIds: ['phase-001'] });

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <TripProvider>
            <Routes>
              <Route path="/" element={<HomeScreen />} />
            </Routes>
          </TripProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('Passport');

    const badgeGroup = screen.getByTestId('phase-card-badges');
    expect(badgeGroup).toContainElement(screen.getByTestId('phase-parrot-badge'));
    expect(badgeGroup).toContainElement(screen.getByTestId('phase-completed-badge'));
  });

  test('marks each completed phase even when an earlier phase is still open', async () => {
    setupHandlers({
      currentPhaseId: 'phase-001',
      completedPhaseIds: ['phase-003'],
      phases: [
        makePhase({ id: 'phase-001', title: 'Passport', sortOrder: 0 }),
        makePhase({ id: 'phase-002', title: 'Vaccines', sortOrder: 1 }),
        makePhase({ id: 'phase-003', title: 'Packing', sortOrder: 2 }),
      ],
    });

    renderHome();

    const packing = (await screen.findByText('Packing')).closest('button') as HTMLElement;
    expect(within(packing).getByTestId('phase-completed-badge')).toBeInTheDocument();
    const vaccines = screen.getByText('Vaccines').closest('button') as HTMLElement;
    expect(within(vaccines).queryByTestId('phase-completed-badge')).not.toBeInTheDocument();
    expect(screen.getAllByTestId('phase-completed-badge')).toHaveLength(1);
  });

  test('shows unfinished pre-trip phases as pending during the trip', async () => {
    setupHandlers({
      tripMode: 'in-trip',
      currentPhaseId: 'day-001',
      completedPhaseIds: ['phase-002'],
      phases: [
        makePhase({ id: 'phase-001', title: 'Passport', sortOrder: 0 }),
        makePhase({ id: 'phase-002', title: 'Vaccines', sortOrder: 1 }),
        makePhase({ id: 'day-001', title: 'Day 1', sortOrder: 2, phaseType: 'in-trip', startsAt: '2026-02-27T03:00:00Z' }),
      ],
    });

    renderHome();

    const passport = (await screen.findByText('Passport')).closest('button') as HTMLElement;
    expect(within(passport).getByTestId('phase-pending-badge')).toHaveTextContent(/pending/i);
    const vaccines = screen.getByText('Vaccines').closest('button') as HTMLElement;
    expect(within(vaccines).getByTestId('phase-completed-badge')).toBeInTheDocument();
    expect(within(vaccines).queryByTestId('phase-pending-badge')).not.toBeInTheDocument();
    const day = screen.getByText('Day 1').closest('button') as HTMLElement;
    expect(within(day).queryByTestId('phase-pending-badge')).not.toBeInTheDocument();
  });
});

function renderHome() {
  render(
    <MemoryRouter initialEntries={['/']}>
      <AuthProvider>
        <TripProvider>
          <Routes>
            <Route path="/" element={<HomeScreen />} />
          </Routes>
        </TripProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}
