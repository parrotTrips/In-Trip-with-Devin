import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import { server } from '../../test/server';
import NotificationsScreen from './pages/NotificationsScreen';

function renderNotificationsScreen() {
  return render(
    <MemoryRouter>
      <NotificationsScreen />
    </MemoryRouter>
  );
}

describe('NotificationsScreen', () => {
  test('marks an unread announcement as read only when expanded', async () => {
    const markRead = vi.fn();

    server.use(
      http.get('http://localhost:8000/me/announcements', () => HttpResponse.json({
        unread_count: 1,
        announcements: [
          {
            id: 'ann-1',
            title: 'Pickup update',
            body: 'Meet at the lobby at 9 AM.',
            sent_by: 'Parrot Team',
            created_at: '2026-08-16T12:00:00Z',
            is_read: false,
          },
        ],
      })),
      http.post('http://localhost:8000/me/announcements/ann-1/read', () => {
        markRead();
        return HttpResponse.json({ status: 'read', announcement_id: 'ann-1' });
      })
    );

    renderNotificationsScreen();

    const announcementButton = await screen.findByRole('button', { name: /pickup update/i });
    expect(screen.getByLabelText(/unread notification/i)).toBeInTheDocument();
    expect(screen.queryByText('Meet at the lobby at 9 AM.')).not.toBeInTheDocument();
    expect(markRead).not.toHaveBeenCalled();

    await userEvent.click(announcementButton);

    expect(await screen.findByText('Meet at the lobby at 9 AM.')).toBeInTheDocument();
    await waitFor(() => expect(markRead).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.queryByLabelText(/unread notification/i)).not.toBeInTheDocument());
  });
});
