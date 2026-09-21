import { AuthProvider } from './auth/AuthProvider';
import LoginScreen from './auth/LoginScreen';

export default function App() {
  return (
    <AuthProvider>
      <LoginScreen />
    </AuthProvider>
  );
}
