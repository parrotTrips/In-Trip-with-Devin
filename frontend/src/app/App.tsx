import '../App.css';
import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';

import LoginScreen from '../features/auth/pages/LoginScreen';
import StaffScreen from '../features/staff/pages/StaffScreen';
import DevUserSwitcher from '../features/dev/DevUserSwitcher';

import { AuthProvider } from './providers/AuthProvider';
import { TripProvider } from './providers/TripProvider';
import { useAuth } from './providers/auth-context';
import AppRouter from './router';

function TravelerPreviewExitButton({ onBack }: { onBack: () => void }) {
  return (
    <div className="fixed top-0 left-1/2 z-[70] flex h-14 w-full max-w-lg -translate-x-1/2 items-center justify-end px-4 pointer-events-none">
      <button
        onClick={onBack}
        className="pointer-events-auto inline-flex items-center gap-1.5 rounded-full bg-gray-900 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-gray-800"
        title="Voltar ao staff"
        aria-label="Voltar ao staff"
      >
        <ArrowLeft size={14} />
        <span>Staff</span>
      </button>
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
        <TravelerPreviewExitButton onBack={() => setViewingAsTraveler(false)} />
      )}
      <AppRouter />
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
