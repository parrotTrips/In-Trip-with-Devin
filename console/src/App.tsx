import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { AuthProvider } from './auth/AuthProvider';
import { useAuth } from './auth/auth-context';
import LoginScreen from './auth/LoginScreen';
import PhaseEditor from './pages/PhaseEditor';
import RoteiroScreen from './pages/RoteiroScreen';
import SectionScreen from './pages/SectionScreen';
import TripLayout from './pages/TripLayout';
import PhasesScreen from './pages/PhasesScreen';
import TripsScreen from './pages/TripsScreen';

function Routed() {
  const { isLoggedIn } = useAuth();
  if (!isLoggedIn) return <LoginScreen />;
  return (
    <Routes>
      <Route path="/" element={<TripsScreen />} />
      {/* O editor de fase fica fora do layout: é tela cheia de edição. */}
      <Route path="/trips/:tripUuid/fases/:phaseId" element={<PhaseEditor />} />
      <Route path="/trips/:tripUuid" element={<TripLayout />}>
        <Route index element={<Navigate to="fases" replace />} />
        <Route path="fases" element={<PhasesScreen />} />
        <Route path="roteiro" element={<RoteiroScreen />} />
        <Route path=":sectionKey" element={<SectionScreen />} />
      </Route>
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
