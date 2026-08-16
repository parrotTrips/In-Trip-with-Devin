import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import { NotificationContext } from '../../app/providers/notification-context';
import TopBar from './TopBar';

describe('TopBar', () => {
  const notificationValue = (unreadCount: number) => ({
    unreadCount,
    setUnreadCount: () => {},
    decrementUnreadCount: () => {},
    refreshUnreadCount: async () => {},
  });

  test('renders the provided title', () => {
    render(
      <MemoryRouter>
        <TopBar title="Trip" />
      </MemoryRouter>
    );

    expect(screen.getByText('Trip')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /menu/i })).not.toBeInTheDocument();
    expect(screen.queryByText('Local Recommendations')).not.toBeInTheDocument();
  });

  test('shows an unread notifications badge when unread announcements exist', () => {
    render(
      <MemoryRouter>
        <NotificationContext.Provider value={notificationValue(2)}>
          <TopBar title="Trip" />
        </NotificationContext.Provider>
      </MemoryRouter>
    );

    expect(screen.getByLabelText(/unread notifications/i)).toBeInTheDocument();
  });

  test('hides the unread notifications badge when there are no unread announcements', () => {
    render(
      <MemoryRouter>
        <NotificationContext.Provider value={notificationValue(0)}>
          <TopBar title="Trip" />
        </NotificationContext.Provider>
      </MemoryRouter>
    );

    expect(screen.queryByLabelText(/unread notifications/i)).not.toBeInTheDocument();
  });
});
