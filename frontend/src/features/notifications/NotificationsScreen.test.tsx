import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { server } from '../../test/server';
import NotificationsScreen from './pages/NotificationsScreen';

describe('NotificationsScreen', () => {
  test('loads notifications and marks one as read', async () => {
    const notifications = [
      {
        id: 1,
        title: 'Welcome',
        body: 'You have a new update',
        type: 'info',
        link: null,
        read: false,
        created_at: '2026-03-01T10:00:00+00:00',
      },
    ];

    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice' })
    );

    server.use(
      http.get('http://localhost:8000/notifications/1', () =>
        HttpResponse.json({
          notifications,
          unread_count: notifications.filter((item) => !item.read).length,
        })
      ),
      http.put('http://localhost:8000/notifications/1/read', () => {
        notifications[0].read = true;
        return HttpResponse.json({ message: 'Notification marked as read' });
      })
    );

    render(
      <MemoryRouter>
        <AuthProvider>
          <NotificationsScreen />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Welcome')).toBeInTheDocument();
    expect(screen.getByText('Unread (1)')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /welcome/i }));

    await waitFor(() => {
      expect(screen.getByText('Unread (0)')).toBeInTheDocument();
    });
  });
});
