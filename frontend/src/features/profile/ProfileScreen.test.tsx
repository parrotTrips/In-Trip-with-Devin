import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, vi } from 'vitest';

import App from '../../app/App';
import { AuthProvider } from '../../app/providers/AuthProvider';
import { TripContext } from '../../app/providers/trip-context';
import { server } from '../../test/server';
import type { TripChoice } from '../auth/services/auth-api';
import ProfileScreen from './pages/ProfileScreen';

// Pin "today" so the calendar opens on a known month; only Date is faked.
function freezeToday() {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-10-01T12:00:00'));
}

afterEach(() => {
  vi.useRealTimers();
});

async function pickDate(field: HTMLElement, day: RegExp) {
  await userEvent.click(field);
  await userEvent.click(await screen.findByRole('button', { name: day }));
}

async function pickTime(field: HTMLElement, label: string) {
  await userEvent.click(field);
  const listbox = await screen.findByRole('listbox');
  await userEvent.click(within(listbox).getByRole('option', { name: label }));
}

const SWITCH_TRIP_CURRENT: TripChoice = {
  trip_id: 'trip-001',
  title: 'Trip One',
  destination: 'Rio de Janeiro',
  start_date: '2026-02-27',
  end_date: '2026-03-08',
  role: 'traveler',
  is_current: true,
};

const SWITCH_TRIP_OTHER: TripChoice = {
  trip_id: 'trip-002',
  title: 'Trip Two',
  destination: 'Lisbon',
  start_date: '2026-06-01',
  end_date: '2026-06-10',
  role: 'traveler',
  is_current: false,
};

function setUpSwitcherSession() {
  localStorage.setItem(
    'parrot_user',
    JSON.stringify({
      userId: 'traveler-1',
      phone: '+15550000001',
      name: 'Alice',
      token: 'tok',
      role: 'traveler',
      tripId: 'trip-001',
      activeTrip: SWITCH_TRIP_CURRENT,
      canSwitchTrips: true,
    })
  );
}

function setUpSwitcherAppHandlers() {
  server.use(
    http.get('http://localhost:8000/me/trip', () =>
      HttpResponse.json({
        trip: {
          wetravel_trip_uuid: 'trip-001',
          title: 'Trip One',
          destination: 'Rio de Janeiro',
          start_date: '2026-02-27',
          end_date: '2026-03-08',
          url: null,
          service_agreement_url: null,
          trip_mode: 'in-trip',
        },
      })
    ),
    http.get('http://localhost:8000/me/trip/phases', () =>
      HttpResponse.json({ wetravel_trip_uuid: 'trip-001', phases: [], ideal_pace_phase_id: null })
    ),
    http.get('http://localhost:8000/me/trip/travelers', () => HttpResponse.json({ travelers: [] })),
    http.get('http://localhost:8000/me/announcements', () =>
      HttpResponse.json({ announcements: [], unread_count: 0 })
    ),
    http.get('http://localhost:8000/profile/traveler-1', () =>
      HttpResponse.json({
        user_id: 'traveler-1',
        phone: '+15550000001',
        name: 'Alice',
        profile: { preferred_name: 'Alice', email: 'alice@example.com' },
        roommate: null,
      })
    ),
    http.get('http://localhost:8000/me/qr-code', () =>
      HttpResponse.json({
        trip_uuid: 'trip-001',
        trip_traveler_id: 'trip-traveler-001',
        qr_payload: 'parrot-trip-checkin:trip-001:trip-traveler-001',
      })
    )
  );
}

describe('ProfileScreen', () => {
  test('loads and saves the profile data', async () => {
    let savedPayload: Record<string, unknown> | null = null;

    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice', token: 'tok', role: 'traveler', tripId: 'trip-001', activeTrip: null, canSwitchTrips: false })
    );

    server.use(
      http.get('http://localhost:8000/profile/1', () =>
        HttpResponse.json({
          user_id: 1,
          phone: '+15550000001',
          name: 'Alice',
          profile: {
            preferred_name: 'Alice',
            email: 'alice@example.com',
          },
          roommate: null,
        })
      ),
      http.get('http://localhost:8000/trip/ross26/travelers', () =>
        HttpResponse.json({ trip_id: 'ross26', travelers: [] })
      ),
      http.get('http://localhost:8000/me/qr-code', () =>
        HttpResponse.json({
          trip_uuid: 'test-trip-001',
          trip_traveler_id: 'trip-traveler-001',
          qr_payload: 'parrot-trip-checkin:test-trip-001:trip-traveler-001',
        })
      ),
      http.put('http://localhost:8000/profile/1', async ({ request }) => {
        savedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ message: 'Profile updated' });
      })
    );

    render(
      <MemoryRouter>
        <AuthProvider>
          <ProfileScreen />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('My Profile');
    await userEvent.click(screen.getByRole('button', { name: /registration details/i }));
    const packagesButton = screen.getByRole('button', { name: /packages/i });
    expect(packagesButton).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /service agreement/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /esim/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /roommate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /flight information/i })).not.toBeInTheDocument();
    const preferredNameInput = await screen.findByLabelText('Preferred Name');
    expect(preferredNameInput).toHaveValue('Alice');

    await userEvent.click(packagesButton);
    const managePaymentsLink = screen.getByRole('link', { name: /manage my payments/i });
    expect(managePaymentsLink).toHaveAttribute('href', 'https://www.wetravel.com/');
    const packageTransferLink = screen.getByRole('link', { name: /transfer or cancel your package/i });
    expect(packageTransferLink).toHaveAttribute(
      'href',
      'https://package-transfer-116789457910.southamerica-east1.run.app'
    );

    await userEvent.clear(preferredNameInput);
    await userEvent.type(preferredNameInput, 'Bea');

    // Date of birth can be filled from an empty value, one part at a time.
    await userEvent.selectOptions(screen.getByLabelText('Day'), '15');
    await userEvent.selectOptions(screen.getByLabelText('Month'), 'March');
    expect(screen.getByLabelText('Day')).toHaveValue('15');
    await userEvent.selectOptions(screen.getByLabelText('Year'), '1990');

    // Health and dietary info is a single free-text question, no yes/no gate.
    expect(screen.queryByLabelText(/^dietary restrictions\?$/i)).not.toBeInTheDocument();
    const healthField = screen.getByLabelText(
      'Do you have any dietary restrictions or other health conditions we should know about?'
    );
    expect(healthField.tagName).toBe('TEXTAREA');
    await userEvent.type(healthField, 'Vegetarian{enter}Peanut allergy');

    expect(screen.queryByText(/plus one/i)).not.toBeInTheDocument();

    expect(screen.queryByRole('button', { name: /save profile/i })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(savedPayload).toMatchObject({
        preferred_name: 'Bea',
        email: 'alice@example.com',
        dob: '1990-03-15',
        dietary_restrictions_desc: 'Vegetarian\nPeanut allergy',
      });
    });
    expect(savedPayload).not.toHaveProperty('dietary_restrictions_yn');
    expect(savedPayload).not.toHaveProperty('plus_one_yn');
    expect(savedPayload).not.toHaveProperty('plus_one_name');
    expect(savedPayload).not.toHaveProperty('plus_one_email');
  });

  test('shows the saved date of birth and health info when returning to the profile', async () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice', token: 'tok', role: 'traveler', tripId: 'trip-001', activeTrip: null, canSwitchTrips: false })
    );

    server.use(
      http.get('http://localhost:8000/profile/1', () =>
        HttpResponse.json({
          user_id: 1,
          phone: '+15550000001',
          name: 'Alice',
          profile: {
            preferred_name: 'Alice',
            dob: '1985-07-04',
            dietary_restrictions_desc: 'Lactose intolerant',
          },
          roommate: null,
        })
      ),
      http.get('http://localhost:8000/me/qr-code', () =>
        HttpResponse.json({
          trip_uuid: 'test-trip-001',
          trip_traveler_id: 'trip-traveler-001',
          qr_payload: 'parrot-trip-checkin:test-trip-001:trip-traveler-001',
        })
      ),
    );

    render(
      <MemoryRouter>
        <AuthProvider>
          <ProfileScreen />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('My Profile');
    await userEvent.click(screen.getByRole('button', { name: /registration details/i }));

    expect(await screen.findByLabelText('Day')).toHaveValue('04');
    expect(screen.getByLabelText('Month')).toHaveValue('07');
    expect(screen.getByLabelText('Year')).toHaveValue('1985');
    expect(
      screen.getByLabelText('Do you have any dietary restrictions or other health conditions we should know about?')
    ).toHaveValue('Lactose intolerant');
  });

  test('saves pre departure information without duplicating registration fields', async () => {
    freezeToday();
    let savedPayload: Record<string, unknown> | null = null;

    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice', token: 'tok', role: 'traveler', tripId: 'trip-001', activeTrip: null, canSwitchTrips: false })
    );

    server.use(
      http.get('http://localhost:8000/profile/1', () =>
        HttpResponse.json({
          user_id: 1,
          phone: '+15550000001',
          name: 'Alice',
          profile: {
            preferred_name: 'Alice',
            email: 'alice@example.com',
            visa_status: 'Not yet, I already started my visa process but don\'t have one yet',
            arrival_time: '14:32',
            departure_time: '25:61',
          },
          roommate: null,
        })
      ),
      http.get('http://localhost:8000/me/qr-code', () =>
        HttpResponse.json({
          trip_uuid: 'test-trip-001',
          trip_traveler_id: 'trip-traveler-001',
          qr_payload: 'parrot-trip-checkin:test-trip-001:trip-traveler-001',
        })
      ),
      http.put('http://localhost:8000/profile/1', async ({ request }) => {
        savedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ message: 'Profile updated' });
      })
    );

    render(
      <MemoryRouter>
        <AuthProvider>
          <ProfileScreen />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('My Profile');
    await userEvent.click(screen.getByRole('button', { name: /pre departure information/i }));
    const preDepartureContainer = screen
      .getByRole('button', { name: /pre departure information/i })
      .closest('.bg-white') as HTMLElement;

    expect(within(preDepartureContainer).queryByLabelText(/passport number/i)).not.toBeInTheDocument();
    expect(within(preDepartureContainer).queryByLabelText(/dietary restrictions/i)).not.toBeInTheDocument();
    expect(within(preDepartureContainer).queryByLabelText(/^email$/i)).not.toBeInTheDocument();

    fireEvent.change(within(preDepartureContainer).getByLabelText(/visa status/i), {
      target: { value: 'I am not sure and I need orientation about it' },
    });
    expect(within(preDepartureContainer).getByTestId('arrival-date-time-grid')).toHaveClass('grid-cols-1', 'sm:grid-cols-2');
    expect(within(preDepartureContainer).getByTestId('departure-date-time-grid')).toHaveClass('grid-cols-1', 'sm:grid-cols-2');

    const arrivalDate = within(preDepartureContainer).getByLabelText(/arrival date/i);
    const arrivalTime = within(preDepartureContainer).getByLabelText(/arrival time/i);
    const departureDate = within(preDepartureContainer).getByLabelText(/departure date/i);
    const departureTime = within(preDepartureContainer).getByLabelText(/departure time/i);

    expect(arrivalDate).toHaveTextContent(/select date/i);
    expect(arrivalTime).toHaveTextContent('2:32 PM');
    expect(departureTime).toHaveTextContent('Existing value: 25:61');

    await userEvent.click(arrivalTime);
    const arrivalList = screen.getByRole('listbox', { name: /arrival time options/i });
    expect(arrivalList).toHaveClass('max-h-60', 'overflow-y-auto');
    expect(within(arrivalList).getByRole('option', { name: '2:32 PM' })).toHaveAttribute('aria-selected', 'true');
    expect(within(arrivalList).getByRole('option', { name: '2:30 PM' })).toHaveAttribute('aria-selected', 'false');
    expect(within(arrivalList).queryByRole('option', { name: '2:31 PM' })).not.toBeInTheDocument();
    await userEvent.keyboard('{Escape}');
    expect(screen.queryByRole('listbox', { name: /arrival time options/i })).not.toBeInTheDocument();

    await userEvent.click(departureTime);
    const departureList = screen.getByRole('listbox', { name: /departure time options/i });
    expect(within(departureList).getByRole('option', { name: '12:00 AM' })).toBeInTheDocument();
    expect(within(departureList).getByRole('option', { name: '11:55 PM' })).toBeInTheDocument();
    expect(within(departureList).getByRole('option', { name: 'Existing value: 25:61' })).toHaveAttribute('aria-selected', 'true');
    await userEvent.keyboard('{Escape}');

    const helpCases = [
      {
        field: /Early Check-in Preference/i,
        button: /more information about check-in times/i,
        text: /Hotels usually have a 2 PM check-in time/i,
      },
      {
        field: /Instagram Handle/i,
        button: /more information about social media/i,
        text: /We will be posting moments of the trip in our Instagram account/i,
      },
      {
        field: /Home Address/i,
        button: /more information about hotel registration/i,
        text: /Some hotels ask for this info on the check in/i,
      },
    ];

    for (const helpCase of helpCases) {
      const field = within(preDepartureContainer).getByLabelText(helpCase.field);
      const button = within(preDepartureContainer).getByRole('button', { name: helpCase.button });
      expect(button).toHaveAttribute('aria-expanded', 'false');
      const helpText = within(preDepartureContainer).getByText(helpCase.text);
      const helpPanel = helpText.parentElement?.parentElement;
      expect(helpPanel).not.toBeVisible();
      expect(button.getAttribute('aria-controls')).toBe(helpPanel?.id);
      expect(field.parentElement?.nextElementSibling).toBe(button.parentElement);
      fireEvent.click(button);
      expect(button).toHaveAttribute('aria-expanded', 'true');
      expect(helpPanel).toBeVisible();
      expect(button.getAttribute('aria-controls')).toBe(helpPanel?.id);
    }

    await pickDate(arrivalDate, /October 3rd, 2026/);
    expect(arrivalDate).toHaveTextContent('Oct 03, 2026');
    await pickTime(arrivalTime, '2:30 PM');
    expect(arrivalTime).toHaveTextContent('2:30 PM');
    fireEvent.change(within(preDepartureContainer).getByLabelText(/arrival airport and flight/i), { target: { value: 'GRU, AA 1234' } });
    await pickDate(departureDate, /October 12th, 2026/);
    await pickTime(departureTime, '9:45 PM');
    fireEvent.change(within(preDepartureContainer).getByLabelText(/departure airport and flight/i), { target: { value: 'GIG, LA 4567' } });
    fireEvent.change(within(preDepartureContainer).getByLabelText(/checked bags/i), { target: { value: '1 checked bag is all I need' } });
    fireEvent.change(within(preDepartureContainer).getByLabelText(/Need help with early arrival or longer stay/i), { target: { value: 'No, thanks' } });
    fireEvent.change(within(preDepartureContainer).getByLabelText(/Early Check-in Preference/i), { target: { value: "I’ll arrive after the check-in time." } });
    fireEvent.change(within(preDepartureContainer).getByLabelText(/travel insurance status/i), { target: { value: 'Already hired one' } });
    fireEvent.change(within(preDepartureContainer).getByLabelText(/Medical Coverage in Brazil/i), { target: { value: 'Yes' } });
    fireEvent.change(within(preDepartureContainer).getByLabelText(/insurance provider/i), { target: { value: 'SafetyWing' } });
    fireEvent.change(within(preDepartureContainer).getByLabelText(/policy number/i), { target: { value: 'POL-123' } });
    fireEvent.change(within(preDepartureContainer).getByLabelText(/Do you know who you will share the room with/i), { target: { value: 'I am staying in an individual room' } });
    fireEvent.change(within(preDepartureContainer).getByLabelText(/Room Configuration/i), { target: { value: 'One double bed (for two people)' } });
    fireEvent.change(within(preDepartureContainer).getByLabelText(/emergency contact/i), { target: { value: 'Maria +5511999999999' } });

    expect(within(preDepartureContainer).queryByLabelText(/Trip Mood/i)).not.toBeInTheDocument();
    expect(within(preDepartureContainer).queryByLabelText(/Social Topic/i)).not.toBeInTheDocument();
    expect(within(preDepartureContainer).queryByLabelText(/Always Up For/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(savedPayload).toMatchObject({
        email: 'alice@example.com',
        visa_status: 'I am not sure and I need orientation about it',
        arrival_date: '2026-10-03',
        arrival_time: '14:30',
        arrival_flight: 'GRU, AA 1234',
        departure_date: '2026-10-12',
        departure_time: '21:45',
        departure_flight: 'GIG, LA 4567',
        checked_bags: '1 checked bag is all I need',
        extended_stay_help: 'No, thanks',
        early_check_in_preference: "I’ll arrive after the check-in time.",
        travel_insurance_status: 'Already hired one',
        travel_insurance_brazil_medical_coverage: 'Yes',
        travel_insurance_provider: 'SafetyWing',
        travel_insurance_policy_number: 'POL-123',
        roommate_status: 'I am staying in an individual room',
        room_configuration: 'One double bed (for two people)',
        emergency_contact: 'Maria +5511999999999',
      });
    });
  });

  test('preserves an existing off-grid arrival time when saving without changing it', async () => {
    let savedPayload: Record<string, unknown> | null = null;

    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice', token: 'tok', role: 'traveler', tripId: 'trip-001', activeTrip: null, canSwitchTrips: false })
    );

    server.use(
      http.get('http://localhost:8000/profile/1', () =>
        HttpResponse.json({
          user_id: 1,
          phone: '+15550000001',
          name: 'Alice',
          profile: {
            preferred_name: 'Alice',
            email: 'alice@example.com',
            visa_status: 'Yes, I already have a visa / I can enter Brazil without a visa',
            arrival_date: '2026-10-03',
            arrival_time: '14:32',
            arrival_flight: 'GRU, AA 1234',
            checked_bags: 'No checked bags, I travel light',
            extended_stay_help: 'No, thanks',
            early_check_in_preference: 'I’ll arrive after the check-in time.',
            departure_date: '2026-10-12',
            departure_flight: 'GIG, LA 4567',
            travel_insurance_status: 'Already hired one',
            travel_insurance_brazil_medical_coverage: 'Yes',
            travel_insurance_provider: 'SafetyWing',
            travel_insurance_policy_number: 'POL-123',
            roommate_status: 'I am staying in an individual room',
            room_configuration: 'One double bed (for two people)',
            emergency_contact: 'Maria +5511999999999',
          },
          roommate: null,
        })
      ),
      http.get('http://localhost:8000/me/qr-code', () =>
        HttpResponse.json({
          trip_uuid: 'test-trip-001',
          trip_traveler_id: 'trip-traveler-001',
          qr_payload: 'parrot-trip-checkin:test-trip-001:trip-traveler-001',
        })
      ),
      http.put('http://localhost:8000/profile/1', async ({ request }) => {
        savedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ message: 'Profile updated' });
      })
    );

    render(
      <MemoryRouter>
        <AuthProvider>
          <ProfileScreen />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('My Profile');
    await userEvent.click(screen.getByRole('button', { name: /pre departure information/i }));
    const arrivalTime = screen.getByLabelText(/arrival time/i);
    expect(arrivalTime).toHaveTextContent('2:32 PM');

    await userEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(savedPayload).toMatchObject({ arrival_time: '14:32' });
    });
  });

  test('opens pre departure information from a section deep link', async () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice', token: 'tok', role: 'traveler', tripId: 'trip-001', activeTrip: null, canSwitchTrips: false })
    );

    server.use(
      http.get('http://localhost:8000/profile/1', () =>
        HttpResponse.json({
          user_id: 1,
          phone: '+15550000001',
          name: 'Alice',
          profile: {
            preferred_name: 'Alice',
            email: 'alice@example.com',
          },
          roommate: null,
        })
      ),
      http.get('http://localhost:8000/me/qr-code', () =>
        HttpResponse.json({
          trip_uuid: 'test-trip-001',
          trip_traveler_id: 'trip-traveler-001',
          qr_payload: 'parrot-trip-checkin:test-trip-001:trip-traveler-001',
        })
      )
    );

    render(
      <MemoryRouter initialEntries={['/profile?section=pre-departure']}>
        <AuthProvider>
          <ProfileScreen />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('My Profile');

    const preDepartureContainer = screen
      .getByRole('button', { name: /pre departure information/i })
      .closest('.bg-white') as HTMLElement;
    expect(within(preDepartureContainer).getByLabelText(/visa status/i)).toBeInTheDocument();
  });

  test('requires visible pre departure fields and selects roommate from trip travelers', async () => {
    freezeToday();
    let savedPayload: Record<string, unknown> | null = null;

    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'traveler-1', phone: '+15550000001', name: 'Alice', token: 'tok', role: 'traveler', tripId: 'trip-001', activeTrip: null, canSwitchTrips: false })
    );

    server.use(
      http.get('http://localhost:8000/profile/traveler-1', () =>
        HttpResponse.json({
          user_id: 'traveler-1',
          phone: '+15550000001',
          name: 'Alice',
          profile: {
            preferred_name: 'Alice',
            email: 'alice@example.com',
          },
          roommate: null,
        })
      ),
      http.get('http://localhost:8000/me/qr-code', () =>
        HttpResponse.json({
          trip_uuid: 'test-trip-001',
          trip_traveler_id: 'trip-traveler-001',
          qr_payload: 'parrot-trip-checkin:test-trip-001:trip-traveler-001',
        })
      ),
      http.put('http://localhost:8000/profile/traveler-1', async ({ request }) => {
        savedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ message: 'Profile updated' });
      })
    );

    render(
      <MemoryRouter>
        <AuthProvider>
          <TripContext.Provider
            value={{
              tripInfo: null,
              phases: [],
              travelers: [
                { id: 'traveler-1', name: 'Alice', phone: '+15550000001', current_phase_id: null },
                { id: 'traveler-3', name: 'Zoe Rivera', phone: '+15550000003', current_phase_id: null },
                { id: 'traveler-2', name: 'Bea Santos', phone: '+15550000002', current_phase_id: null },
                { id: 'traveler-4', name: 'Ana Baker', phone: '+15550000004', current_phase_id: null },
              ],
              idealPacePhaseId: null,
              loading: false,
              error: null,
              refetch: () => {},
            }}
          >
            <ProfileScreen />
          </TripContext.Provider>
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('My Profile');
    await userEvent.click(screen.getByRole('button', { name: /pre departure information/i }));
    const preDepartureContainer = screen
      .getByRole('button', { name: /pre departure information/i })
      .closest('.bg-white') as HTMLElement;

    await userEvent.click(screen.getByRole('button', { name: /save changes/i }));
    expect(await within(preDepartureContainer).findByText(/Visa Status is required/i)).toBeInTheDocument();
    expect(savedPayload).toBeNull();

    await userEvent.selectOptions(
      within(preDepartureContainer).getByLabelText(/visa status/i),
      'Yes, I already have a visa / I can enter Brazil without a visa'
    );
    await pickDate(within(preDepartureContainer).getByLabelText(/arrival date/i), /October 3rd, 2026/);
    await userEvent.type(within(preDepartureContainer).getByLabelText(/arrival airport and flight/i), 'GRU, AA 1234');
    await pickDate(within(preDepartureContainer).getByLabelText(/departure date/i), /October 12th, 2026/);
    await userEvent.type(within(preDepartureContainer).getByLabelText(/departure airport and flight/i), 'GIG, LA 4567');
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/checked bags/i), 'No checked bags, I travel light');
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/travel insurance status/i), 'Already hired one');
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/medical coverage in Brazil/i), 'Yes');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/insurance provider/i), 'SafetyWing');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/policy number/i), 'POL-123');
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/do you know who you will share the room with/i), 'Yes');
    const roommateInput = within(preDepartureContainer).getByLabelText(/requested roommate/i);
    await userEvent.click(roommateInput);
    const roommateList = within(preDepartureContainer).getByRole('listbox', { name: /requested roommate suggestions/i });
    expect(within(roommateList).getAllByRole('option').map(option => option.textContent)).toEqual([
      'Ana Baker',
      'Bea Santos',
      'Zoe Rivera',
    ]);
    await userEvent.type(roommateInput, 'bea');
    await userEvent.click(within(roommateList).getByRole('option', { name: 'Bea Santos' }));
    expect(within(preDepartureContainer).queryByLabelText(/roommate gender preference/i)).not.toBeInTheDocument();
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/room configuration/i), 'Two twin beds (one single bed each)');
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/need help with early arrival or longer stay/i), 'No, thanks');
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/early check-in preference/i), "I’ll arrive after the check-in time.");
    await userEvent.type(within(preDepartureContainer).getByLabelText(/emergency contact/i), 'Maria +5511999999999');

    await userEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(savedPayload).toMatchObject({
        roommate_status: 'Yes',
        roommate_user_id: 'traveler-2',
      });
      expect(savedPayload).not.toHaveProperty('roommate_email');
      expect(savedPayload).not.toHaveProperty('trip_mood');
      expect(savedPayload).not.toHaveProperty('social_topic');
      expect(savedPayload).not.toHaveProperty('always_up_for');
    });

    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/do you know who you will share the room with/i), 'No, please match me with someone.');
    expect(within(preDepartureContainer).queryByLabelText(/requested roommate/i)).not.toBeInTheDocument();
    expect(within(preDepartureContainer).getByLabelText(/roommate gender preference/i)).toBeInTheDocument();
  });

  test('offers Trocar de viagem, refreshes memberships fresh, and opens the selector without OTP', async () => {
    let tripsRequests = 0;
    let lastAuthHeader: string | null = null;
    setUpSwitcherSession();
    window.history.pushState({}, '', '/profile');
    setUpSwitcherAppHandlers();
    server.use(
      http.get('http://localhost:8000/auth/trips', ({ request }) => {
        tripsRequests += 1;
        lastAuthHeader = request.headers.get('authorization');
        return HttpResponse.json({ trips: [SWITCH_TRIP_CURRENT, SWITCH_TRIP_OTHER] });
      })
    );

    render(<App />);

    const switchButton = await screen.findByRole('button', { name: /trocar de viagem/i });
    await userEvent.click(switchButton);

    await screen.findByText('Escolha sua viagem');
    expect(tripsRequests).toBe(1);
    expect(lastAuthHeader).toBe('Bearer tok');
    expect(screen.getByText('Trip Two')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument();
    // No OTP step is shown — the switcher opens directly from the profile.
    expect(screen.queryByPlaceholderText('Phone number')).not.toBeInTheDocument();
    expect(screen.queryByText('Verification Code')).not.toBeInTheDocument();
  });

  test('hides Trocar de viagem when only one trip is eligible', async () => {
    setUpSwitcherSession();
    const stored = JSON.parse(localStorage.getItem('parrot_user')!);
    localStorage.setItem('parrot_user', JSON.stringify({ ...stored, canSwitchTrips: false }));
    window.history.pushState({}, '', '/profile');
    setUpSwitcherAppHandlers();

    render(<App />);

    await screen.findByRole('heading', { name: 'My Profile' });
    expect(screen.queryByRole('button', { name: /trocar de viagem/i })).not.toBeInTheDocument();
  });

  test('cancelling the switcher returns to the exact previous session untouched', async () => {
    setUpSwitcherSession();
    window.history.pushState({}, '', '/profile');
    setUpSwitcherAppHandlers();
    server.use(
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({ trips: [SWITCH_TRIP_CURRENT, SWITCH_TRIP_OTHER] })
      )
    );

    render(<App />);

    await userEvent.click(await screen.findByRole('button', { name: /trocar de viagem/i }));
    await screen.findByText('Escolha sua viagem');

    await userEvent.click(screen.getByRole('button', { name: /cancelar/i }));

    expect(screen.queryByText('Escolha sua viagem')).not.toBeInTheDocument();
    await screen.findByRole('heading', { name: 'My Profile' });
    expect(JSON.parse(localStorage.getItem('parrot_user')!)).toMatchObject({
      userId: 'traveler-1',
      token: 'tok',
      tripId: 'trip-001',
    });
  });

  test('keeps the current session if selecting a new trip fails', async () => {
    setUpSwitcherSession();
    window.history.pushState({}, '', '/profile');
    setUpSwitcherAppHandlers();
    server.use(
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({ trips: [SWITCH_TRIP_CURRENT, SWITCH_TRIP_OTHER] })
      ),
      http.post('http://localhost:8000/auth/select-trip', () =>
        HttpResponse.json({ detail: 'Trip no longer available' }, { status: 409 })
      )
    );

    render(<App />);

    await userEvent.click(await screen.findByRole('button', { name: /trocar de viagem/i }));
    await screen.findByText('Escolha sua viagem');

    await userEvent.click(screen.getByText('Trip Two').closest('button')!);

    await screen.findByRole('alert');
    expect(screen.getByText('Escolha sua viagem')).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem('parrot_user')!)).toMatchObject({
      userId: 'traveler-1',
      token: 'tok',
      tripId: 'trip-001',
    });
  });

  test('offers a Cancelar option while the switcher is still loading trips', async () => {
    setUpSwitcherSession();
    window.history.pushState({}, '', '/profile');
    setUpSwitcherAppHandlers();
    let resolveTrips: (() => void) | undefined;
    server.use(
      http.get(
        'http://localhost:8000/auth/trips',
        () =>
          new Promise<Response>(resolve => {
            resolveTrips = () =>
              resolve(HttpResponse.json({ trips: [SWITCH_TRIP_CURRENT, SWITCH_TRIP_OTHER] }));
          })
      )
    );

    render(<App />);

    await userEvent.click(await screen.findByRole('button', { name: /trocar de viagem/i }));

    expect(await screen.findByRole('status', { name: /carregando viagens/i })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /cancelar/i }));

    await screen.findByRole('heading', { name: 'My Profile' });
    expect(screen.queryByRole('status', { name: /carregando viagens/i })).not.toBeInTheDocument();

    // Let the in-flight request settle so it doesn't leak into another test.
    resolveTrips?.();
  });
});
