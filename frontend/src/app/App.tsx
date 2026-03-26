import '../App.css';

import LoginScreen from '../features/auth/pages/LoginScreen';

import { AuthProvider, useAuth } from './providers/AuthProvider';
import AppRouter from './router';

function AppContent() {
  const { isLoggedIn } = useAuth();

  if (!isLoggedIn) {
    return <LoginScreen />;
  }

  return <AppRouter />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
