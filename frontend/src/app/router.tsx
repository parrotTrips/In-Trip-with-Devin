import { useEffect } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import posthog from 'posthog-js';

import { useTripContext } from './providers/trip-context';
import DayDetails from '../features/trip/pages/DayDetails';
import HomeScreen from '../features/trip/pages/HomeScreen';
import ProfileScreen from '../features/profile/pages/ProfileScreen';
import PhaseDetails from '../features/trip/pages/PhaseDetails';
import NotificationsScreen from '../features/notifications/pages/NotificationsScreen';
import InformationScreen from '../features/team/pages/InformationScreen';
import RecommendationsScreen from '../features/recommendations/pages/RecommendationsScreen';
import BottomNav from '../shared/components/BottomNav';

function screenPayloadForPath(pathname: string) {
  const [, route, id] = pathname.split('/');
  if (route === 'day' && id) return { tela: '/day', day_id: id };
  if (route === 'phase' && id) return { tela: '/phase', phase_id: id };
  return { tela: pathname };
}

function RouteTracker() {
  const location = useLocation();
  const { tripInfo, loading } = useTripContext();
  const viagemId = tripInfo?.wetravel_trip_uuid;
  const modoViagem = tripInfo?.trip_mode;

  useEffect(() => {
    if (loading) return;

    const payload = {
      ...screenPayloadForPath(location.pathname),
      ...(viagemId && modoViagem
        ? {
            viagem_id: viagemId,
            modo_viagem: modoViagem,
          }
        : {}),
    };

    posthog.capture('tela_visitada', payload);
  }, [location.pathname, loading, viagemId, modoViagem]);
  return null;
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <RouteTracker />
      <div className="max-w-lg mx-auto relative min-h-screen bg-white shadow-xl">
        <Routes>
          <Route path="/" element={<HomeScreen />} />
          <Route path="/notifications" element={<NotificationsScreen />} />
          <Route path="/phase/:phaseId" element={<PhaseDetails />} />
          <Route path="/day/:dayId" element={<DayDetails />} />
          <Route path="/profile" element={<ProfileScreen />} />
          <Route path="/information" element={<InformationScreen />} />
          <Route path="/recommendations" element={<RecommendationsScreen />} />
          <Route path="/team" element={<Navigate to="/information" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}
