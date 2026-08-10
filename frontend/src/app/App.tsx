import '../App.css';
import { useEffect, useState } from 'react';

import LoginScreen from '../features/auth/pages/LoginScreen';
import StaffScreen from '../features/staff/pages/StaffScreen';
import DevUserSwitcher from '../features/dev/DevUserSwitcher';

import { AuthProvider } from './providers/AuthProvider';
import { TripProvider } from './providers/TripProvider';
import { useAuth } from './providers/auth-context';
import { StaffViewContext } from './providers/staff-view-context';
import { AvatarContext, loadStoredAvatar, persistAvatar } from './providers/avatar-context';
import AppRouter from './router';

function AppContent() {
  const { isLoggedIn, user } = useAuth();
  const [viewingAsTraveler, setViewingAsTraveler] = useState(false);
  const userId = user?.userId ?? '';
  const [avatarUrl, setAvatarUrl] = useState<string | null>(() =>
    userId ? loadStoredAvatar(userId) : null
  );

  useEffect(() => {
    if (userId) {
      setAvatarUrl(loadStoredAvatar(userId));
    } else {
      setAvatarUrl(null);
    }
  }, [userId]);

  const handleSetAvatarUrl = (url: string | null) => {
    if (userId) persistAvatar(userId, url);
    setAvatarUrl(url);
  };

  if (!isLoggedIn) {
    return <LoginScreen />;
  }

  if (user?.role === 'staff' && !viewingAsTraveler) {
    return <StaffScreen onSwitchToTravelerView={() => setViewingAsTraveler(true)} />;
  }

  return (
    <TripProvider>
      <StaffViewContext.Provider value={{
        onSwitchToStaffView: user?.role === 'staff' ? () => setViewingAsTraveler(false) : null,
      }}>
        <AvatarContext.Provider value={{ avatarUrl, setAvatarUrl: handleSetAvatarUrl }}>
          <AppRouter />
        </AvatarContext.Provider>
      </StaffViewContext.Provider>
    </TripProvider>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
      <DevUserSwitcher />
    </AuthProvider>
  );
}
