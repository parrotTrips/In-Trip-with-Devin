import { BrowserRouter, Route, Routes } from 'react-router-dom';

import DayDetails from '../features/trip/pages/DayDetails';
import DocumentsScreen from '../features/documents/pages/DocumentsScreen';
import EmergencyContacts from '../features/emergency/pages/EmergencyContacts';
import HomeScreen from '../features/trip/pages/HomeScreen';
import MissionsScreen from '../features/missions/pages/MissionsScreen';
import NotificationsScreen from '../features/notifications/pages/NotificationsScreen';
import ProfileScreen from '../features/profile/pages/ProfileScreen';
import PhaseDetails from '../features/trip/pages/PhaseDetails';
import RecommendationsScreen from '../features/recommendations/pages/RecommendationsScreen';
import SharingXPScreen from '../features/sharing/pages/SharingXPScreen';
import BottomNav from '../shared/components/BottomNav';

export default function AppRouter() {
  return (
    <BrowserRouter>
      <div className="max-w-lg mx-auto relative min-h-screen bg-white shadow-xl">
        <Routes>
          <Route path="/" element={<HomeScreen />} />
          <Route path="/phase/:phaseId" element={<PhaseDetails />} />
          <Route path="/day/:dayId" element={<DayDetails />} />
          <Route path="/missions" element={<MissionsScreen />} />
          <Route path="/documents" element={<DocumentsScreen />} />
          <Route path="/sharing-xp" element={<SharingXPScreen />} />
          <Route path="/emergency" element={<EmergencyContacts />} />
          <Route path="/profile" element={<ProfileScreen />} />
          <Route path="/recommendations" element={<RecommendationsScreen />} />
          <Route path="/notifications" element={<NotificationsScreen />} />
        </Routes>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}
