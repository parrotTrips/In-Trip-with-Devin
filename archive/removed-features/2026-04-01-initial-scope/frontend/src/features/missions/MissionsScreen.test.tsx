import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { server } from '../../test/server';
import MissionsScreen from './pages/MissionsScreen';

describe('MissionsScreen', () => {
  test('loads missions and toggles completion', async () => {
    let missionCompleted = false;

    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice' })
    );

    server.use(
      http.get('http://localhost:8000/missions/ross26', ({ request }) => {
        const userId = new URL(request.url).searchParams.get('user_id');
        if (!userId) {
          return HttpResponse.json({ trip_id: 'ross26', missions: [] });
        }

        return HttpResponse.json({
          trip_id: 'ross26',
          missions: [
            {
              id: 1,
              title: 'First Photo!',
              description: 'Upload your first photo to the group album',
              points: 50,
              icon: '📸',
              category: 'social',
              completed: missionCompleted,
            },
          ],
        });
      }),
      http.get('http://localhost:8000/notifications/:userId/count', () =>
        HttpResponse.json({ unread_count: 0 })
      ),
      http.get('http://localhost:8000/missions/ross26/leaderboard', () =>
        HttpResponse.json({
          trip_id: 'ross26',
          leaderboard: [{ user_id: 1, name: 'Alice', total_points: 50, missions_completed: 1 }],
        })
      ),
      http.post('http://localhost:8000/missions/ross26/complete', async () => {
        missionCompleted = true;
        return HttpResponse.json({
          message: 'Mission completed!',
          points_earned: 50,
          already_completed: false,
        });
      })
    );

    render(
      <MemoryRouter>
        <AuthProvider>
          <MissionsScreen />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('First Photo!')).toBeInTheDocument();
    expect(screen.getByText('0/1 completed')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /first photo!/i }));

    await waitFor(() => {
      expect(screen.getByText('1/1 completed')).toBeInTheDocument();
    });
  });
});
