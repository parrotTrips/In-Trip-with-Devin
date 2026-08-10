import { useEffect } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import posthog from 'posthog-js';

import DayDetails from '../features/trip/pages/DayDetails';
import HomeScreen from '../features/trip/pages/HomeScreen';
import ProfileScreen from '../features/profile/pages/ProfileScreen';
import PhaseDetails from '../features/trip/pages/PhaseDetails';
import NotificationsScreen from '../features/notifications/pages/NotificationsScreen';
import InformationScreen from '../features/team/pages/InformationScreen';
import RecommendationsScreen from '../features/recommendations/pages/RecommendationsScreen';
import BottomNav from '../shared/components/BottomNav';

function RouteTracker() {
  const location = useLocation();
  useEffect(() => {
    posthog.capture('tela_visitada', { tela: location.pathname });
  }, [location.pathname]);
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
