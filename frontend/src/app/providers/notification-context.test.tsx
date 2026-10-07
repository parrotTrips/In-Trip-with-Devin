import { act, render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterEach, vi } from 'vitest';

import { server } from '../../test/server';
import { NotificationProvider, useNotifications } from './notification-context';

function UnreadCount() {
  return <p data-testid="unread">{useNotifications().unreadCount}</p>;
}

let unread = 0;
let fail = false;

function serveAnnouncements() {
  server.use(
    http.get('http://localhost:8000/me/announcements', () =>
      fail
        ? HttpResponse.json({ detail: 'down' }, { status: 500 })
        : HttpResponse.json({ announcements: [], unread_count: unread })
    )
  );
}

async function flush() {
  await act(async () => {
    await new Promise(resolve => setTimeout(resolve, 0));
  });
}

describe('NotificationProvider', () => {
  beforeEach(() => {
    unread = 0;
    fail = false;
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'u1', phone: '+1', name: 'A', token: 'tok', role: 'traveler', tripId: 't1', activeTrip: null })
    );
    serveAnnouncements();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test('brings the dot back when a new message arrives while the app is open', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    render(<NotificationProvider><UnreadCount /></NotificationProvider>);
    await flush();
    expect(screen.getByTestId('unread')).toHaveTextContent('0');

    unread = 1;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(60_000);
    });

    expect(screen.getByTestId('unread')).toHaveTextContent('1');
  });

  test('refreshes when the traveler comes back to the app', async () => {
    render(<NotificationProvider><UnreadCount /></NotificationProvider>);
    await flush();

    unread = 2;
    await act(async () => {
      window.dispatchEvent(new Event('focus'));
    });
    await flush();

    expect(screen.getByTestId('unread')).toHaveTextContent('2');
  });

  test('keeps the last known count when a refresh fails', async () => {
    unread = 3;
    render(<NotificationProvider><UnreadCount /></NotificationProvider>);
    await flush();
    expect(screen.getByTestId('unread')).toHaveTextContent('3');

    fail = true;
    await act(async () => {
      window.dispatchEvent(new Event('focus'));
    });
    await flush();

    expect(screen.getByTestId('unread')).toHaveTextContent('3');
  });
});
