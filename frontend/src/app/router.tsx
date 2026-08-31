import { useEffect, useMemo, useRef } from 'react';
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

const ACTIVE_SCREEN_IDLE_TIMEOUT_MS = 30_000;

function screenPayloadForPath(pathname: string) {
  const dayMatch = pathname.match(/^\/day\/([^/]+)\/?$/);
  if (dayMatch) return { tela: '/day', day_id: dayMatch[1] };

  const phaseMatch = pathname.match(/^\/phase\/([^/]+)\/?$/);
  if (phaseMatch) return { tela: '/phase', phase_id: phaseMatch[1] };

  return { tela: pathname };
}

function screenPayloadForRoute(pathname: string, viagemId?: string, modoViagem?: string) {
  return {
    ...screenPayloadForPath(pathname),
    ...(viagemId && modoViagem
      ? {
          viagem_id: viagemId,
          modo_viagem: modoViagem,
        }
      : {}),
  };
}

function pageIsVisibleAndFocused() {
  return document.visibilityState === 'visible' && (!document.hasFocus || document.hasFocus());
}

function RouteTracker() {
  const location = useLocation();
  const { tripInfo, loading } = useTripContext();
  const viagemId = tripInfo?.wetravel_trip_uuid;
  const modoViagem = tripInfo?.trip_mode;
  const payload = useMemo(
    () => screenPayloadForRoute(location.pathname, viagemId, modoViagem),
    [location.pathname, viagemId, modoViagem]
  );

  useEffect(() => {
    if (loading) return;

    posthog.capture('tela_visitada', payload);
  }, [loading, payload]);
  return null;
}

function ActiveScreenTimeTracker() {
  const location = useLocation();
  const { tripInfo, loading } = useTripContext();
  const viagemId = tripInfo?.wetravel_trip_uuid;
  const modoViagem = tripInfo?.trip_mode;
  const payload = useMemo(
    () => screenPayloadForRoute(location.pathname, viagemId, modoViagem),
    [location.pathname, viagemId, modoViagem]
  );
  const activeMsRef = useRef(0);
  const activeSegmentStartedAtRef = useRef<number | null>(null);
  const lastActivityAtRef = useRef(Date.now());

  useEffect(() => {
    if (loading) return;

    activeMsRef.current = 0;
    lastActivityAtRef.current = Date.now();
    activeSegmentStartedAtRef.current = pageIsVisibleAndFocused() ? Date.now() : null;

    const addActiveTimeUntilNow = () => {
      const segmentStartedAt = activeSegmentStartedAtRef.current;
      if (segmentStartedAt === null) return;

      const now = Date.now();
      const activeUntil = Math.min(now, lastActivityAtRef.current + ACTIVE_SCREEN_IDLE_TIMEOUT_MS);
      activeMsRef.current += Math.max(0, activeUntil - segmentStartedAt);
      activeSegmentStartedAtRef.current = null;
    };

    const resumeActiveTime = () => {
      if (!pageIsVisibleAndFocused() || activeSegmentStartedAtRef.current !== null) return;

      const now = Date.now();
      lastActivityAtRef.current = now;
      activeSegmentStartedAtRef.current = now;
    };

    const handleActivity = () => {
      addActiveTimeUntilNow();
      const now = Date.now();
      lastActivityAtRef.current = now;
      if (pageIsVisibleAndFocused()) {
        activeSegmentStartedAtRef.current = now;
      }
    };

    const handleVisibilityChange = () => {
      if (pageIsVisibleAndFocused()) {
        resumeActiveTime();
        return;
      }
      addActiveTimeUntilNow();
    };

    const flushActiveScreenTime = () => {
      addActiveTimeUntilNow();
      if (activeMsRef.current <= 0) return;

      posthog.capture('tela_tempo_ativo', {
        ...payload,
        tempo_ativo_ms: activeMsRef.current,
        idle_timeout_ms: ACTIVE_SCREEN_IDLE_TIMEOUT_MS,
      });
      activeMsRef.current = 0;
    };

    window.addEventListener('click', handleActivity);
    window.addEventListener('touchstart', handleActivity);
    window.addEventListener('keydown', handleActivity);
    window.addEventListener('scroll', handleActivity, true);
    window.addEventListener('focus', resumeActiveTime);
    window.addEventListener('blur', addActiveTimeUntilNow);
    window.addEventListener('pagehide', flushActiveScreenTime);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      flushActiveScreenTime();
      window.removeEventListener('click', handleActivity);
      window.removeEventListener('touchstart', handleActivity);
      window.removeEventListener('keydown', handleActivity);
      window.removeEventListener('scroll', handleActivity, true);
      window.removeEventListener('focus', resumeActiveTime);
      window.removeEventListener('blur', addActiveTimeUntilNow);
      window.removeEventListener('pagehide', flushActiveScreenTime);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [loading, payload]);

  return null;
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <RouteTracker />
      <ActiveScreenTimeTracker />
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
