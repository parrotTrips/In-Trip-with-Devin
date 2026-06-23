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
    <button
      onClick={onBack}
      className="fixed bottom-24 left-4 z-50 inline-flex items-center gap-1.5 rounded-full bg-gray-900 px-3 py-2 text-xs font-semibold text-white shadow-lg shadow-gray-900/20 transition-colors hover:bg-gray-800 sm:bottom-6"
      title="Voltar ao staff"
      aria-label="Voltar ao staff"
    >
      <ArrowLeft size={14} />
      <span>Staff</span>
    </button>
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
