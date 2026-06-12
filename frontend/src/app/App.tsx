import '../App.css';
import { useState } from 'react';

import LoginScreen from '../features/auth/pages/LoginScreen';
import StaffScreen from '../features/staff/pages/StaffScreen';
import DevUserSwitcher from '../features/dev/DevUserSwitcher';

import { AuthProvider } from './providers/AuthProvider';
import { TripProvider } from './providers/TripProvider';
import { useAuth } from './providers/auth-context';
import AppRouter from './router';

function TravelerViewBanner({ onBack }: { onBack: () => void }) {
  return (
    <div className="fixed top-0 left-0 right-0 z-[100] bg-amber-500 text-white text-xs font-semibold flex items-center justify-between px-4 py-2 max-w-lg mx-auto">
      <span>👁 Viewing as traveler</span>
      <button onClick={onBack} className="underline hover:no-underline">Back to staff view</button>
    </div>
  );
}

function AppContent() {
  const { isLoggedIn, user } = useAuth();
  const [viewingAsTraveler, setViewingAsTraveler] = useState(false);

  if (!isLoggedIn) {
    return <LoginScreen />;
  }

  if (user?.role === 'staff' && !viewingAsTraveler) {
    return <StaffScreen onSwitchToTravelerView={() => setViewingAsTraveler(true)} />;
  }

  return (
    <TripProvider>
      {user?.role === 'staff' && viewingAsTraveler && (
        <TravelerViewBanner onBack={() => setViewingAsTraveler(false)} />
      )}
      <div className={user?.role === 'staff' && viewingAsTraveler ? 'pt-8' : ''}>
        <AppRouter />
      </div>
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
