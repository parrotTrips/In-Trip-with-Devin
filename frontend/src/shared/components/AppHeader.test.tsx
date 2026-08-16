import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import { NotificationContext } from '../../app/providers/notification-context';
import { AvatarContext } from '../../app/providers/avatar-context';
import AppHeader from './AppHeader';

function renderAppHeader(unreadCount: number) {
  return render(
    <MemoryRouter>
      <NotificationContext.Provider value={{
        unreadCount,
        setUnreadCount: () => {},
        decrementUnreadCount: () => {},
        refreshUnreadCount: async () => {},
      }}>
        <AvatarContext.Provider value={{ avatarUrl: null, setAvatarUrl: () => {} }}>
          <AppHeader title="Trip" />
        </AvatarContext.Provider>
      </NotificationContext.Provider>
    </MemoryRouter>
  );
}

describe('AppHeader', () => {
  test('shows an unread notifications badge when unread announcements exist', () => {
    renderAppHeader(1);

    expect(screen.getByLabelText(/unread notifications/i)).toBeInTheDocument();
  });

  test('hides the unread notifications badge when there are no unread announcements', () => {
    renderAppHeader(0);

    expect(screen.queryByLabelText(/unread notifications/i)).not.toBeInTheDocument();
  });
});
