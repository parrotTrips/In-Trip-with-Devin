import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';

import { getMyAnnouncements } from '../../features/trip/services/trip-api';

interface NotificationContextType {
  unreadCount: number;
  setUnreadCount: (count: number) => void;
  decrementUnreadCount: () => void;
  refreshUnreadCount: () => Promise<void>;
}

export const NotificationContext = createContext<NotificationContextType>({
  unreadCount: 0,
  setUnreadCount: () => {},
  decrementUnreadCount: () => {},
  refreshUnreadCount: async () => {},
});

// New announcements must bring the dot back without a reload.
const REFRESH_INTERVAL_MS = 60_000;

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [unreadCount, setUnreadCount] = useState(0);

  const refreshUnreadCount = useCallback(async () => {
    try {
      const result = await getMyAnnouncements();
      setUnreadCount(result.unread_count);
    } catch {
      // Keep the last known count: a network blip must not hide unread messages.
    }
  }, []);

  useEffect(() => {
    refreshUnreadCount();
    const refreshIfVisible = () => {
      if (document.visibilityState !== 'hidden') void refreshUnreadCount();
    };
    const interval = window.setInterval(refreshIfVisible, REFRESH_INTERVAL_MS);
    window.addEventListener('focus', refreshIfVisible);
    document.addEventListener('visibilitychange', refreshIfVisible);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener('focus', refreshIfVisible);
      document.removeEventListener('visibilitychange', refreshIfVisible);
    };
  }, [refreshUnreadCount]);

  const decrementUnreadCount = useCallback(() => {
    setUnreadCount(current => Math.max(0, current - 1));
  }, []);

  return (
    <NotificationContext.Provider value={{ unreadCount, setUnreadCount, decrementUnreadCount, refreshUnreadCount }}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  return useContext(NotificationContext);
}
