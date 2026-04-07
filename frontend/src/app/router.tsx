import { BrowserRouter, Route, Routes } from 'react-router-dom';

import DayDetails from '../features/trip/pages/DayDetails';
import HomeScreen from '../features/trip/pages/HomeScreen';
import ProfileScreen from '../features/profile/pages/ProfileScreen';
import PhaseDetails from '../features/trip/pages/PhaseDetails';
import BottomNav from '../shared/components/BottomNav';

export default function AppRouter() {
  return (
    <BrowserRouter>
      <div className="max-w-lg mx-auto relative min-h-screen bg-white shadow-xl">
        <Routes>
          <Route path="/" element={<HomeScreen />} />
          <Route path="/phase/:phaseId" element={<PhaseDetails />} />
          <Route path="/day/:dayId" element={<DayDetails />} />
          <Route path="/profile" element={<ProfileScreen />} />
        </Routes>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}
