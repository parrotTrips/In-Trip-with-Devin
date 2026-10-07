import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';

import { AuthProvider } from './auth/AuthProvider';
import { useAuth } from './auth/auth-context';
import LoginScreen from './auth/LoginScreen';
import { readConfig, type ConsoleConfig } from './config';
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
      <Route path="/trips/:tripUuid" element={<TripLayout />}>
        <Route index element={<Navigate to="fases" replace />} />
        <Route path="fases" element={<PhasesScreen />} />
        <Route path="fases/:phaseId" element={<PhaseEditor />} />
        <Route path="roteiro" element={<RoteiroScreen />} />
        <Route path="wrap-up" element={<PhasesScreen phaseType="post-trip" />} />
        <Route path=":sectionKey" element={<SectionScreen />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  const result = readConfig();
  if (!result.ok) {
    return (
      <main className="max-w-lg mx-auto p-6">
        <h1 className="text-xl font-bold">Console indisponível</h1>
        <p className="mt-2 text-red-700">{result.error}</p>
      </main>
    );
  }
  return <ConfiguredApp config={result.value} />;
}

function ConfiguredApp({ config }: { config: ConsoleConfig }) {
  const content = (
    <AuthProvider config={config}>
      <BrowserRouter>
        <Routed />
      </BrowserRouter>
    </AuthProvider>
  );
  if (config.localBypass) return content;
  return (
    <GoogleOAuthProvider clientId={config.googleClientId}>
      {content}
    </GoogleOAuthProvider>
  );
}
