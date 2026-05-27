import '../App.css';

import LoginScreen from '../features/auth/pages/LoginScreen';
import StaffScreen from '../features/staff/pages/StaffScreen';
import DevUserSwitcher from '../features/dev/DevUserSwitcher';

import { AuthProvider } from './providers/AuthProvider';
import { TripProvider } from './providers/TripProvider';
import { useAuth } from './providers/auth-context';
import AppRouter from './router';

function AppContent() {
  const { isLoggedIn, user } = useAuth();

  if (!isLoggedIn) {
    return <LoginScreen />;
  }

  if (user?.role === 'staff') {
    return <StaffScreen />;
  }

  return (
    <TripProvider>
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
