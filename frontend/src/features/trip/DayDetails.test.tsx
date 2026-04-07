import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { AuthProvider } from '../../app/providers/AuthProvider';
import DayDetails from './pages/DayDetails';

describe('DayDetails', () => {
  test('renders the selected trip day itinerary and album', () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice' })
    );

    render(
      <MemoryRouter initialEntries={['/day/day1']}>
        <AuthProvider>
          <Routes>
            <Route path="/day/:dayId" element={<DayDetails />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText("Today's Itinerary")).toBeInTheDocument();
    expect(screen.getByText('Group Album')).toBeInTheDocument();
  });
});
