import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { AuthProvider } from './auth/AuthProvider';
import { useAuth } from './auth/auth-context';
import LoginScreen from './auth/LoginScreen';
import PhaseEditor from './pages/PhaseEditor';
import PhasesScreen from './pages/PhasesScreen';
import TripsScreen from './pages/TripsScreen';

function Routed() {
  const { isLoggedIn } = useAuth();
  if (!isLoggedIn) return <LoginScreen />;
  return (
    <Routes>
      <Route path="/" element={<TripsScreen />} />
      <Route path="/trips/:tripUuid/phases" element={<PhasesScreen />} />
      <Route path="/trips/:tripUuid/phases/:phaseId" element={<PhaseEditor />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routed />
      </BrowserRouter>
    </AuthProvider>
  );
}
