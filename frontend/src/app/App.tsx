import '../App.css';

import LoginScreen from '../features/auth/pages/LoginScreen';

import { AuthProvider } from './providers/AuthProvider';
import { useAuth } from './providers/auth-context';
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
