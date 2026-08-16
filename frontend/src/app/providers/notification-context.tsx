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

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [unreadCount, setUnreadCount] = useState(0);

  const refreshUnreadCount = useCallback(async () => {
    try {
      const result = await getMyAnnouncements();
      setUnreadCount(result.unread_count);
    } catch {
      setUnreadCount(0);
    }
  }, []);

  useEffect(() => {
    refreshUnreadCount();
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
