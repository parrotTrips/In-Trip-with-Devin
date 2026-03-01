import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';
import BottomNav from './components/BottomNav';
import HomeScreen from './pages/HomeScreen';
import PhaseDetails from './pages/PhaseDetails';
import DayDetails from './pages/DayDetails';
import LoginScreen from './pages/LoginScreen';
import MissionsScreen from './pages/MissionsScreen';
import DocumentsScreen from './pages/DocumentsScreen';
import EmergencyContacts from './pages/EmergencyContacts';
import ProfileScreen from './pages/ProfileScreen';
import { AuthProvider, useAuth } from './services/AuthContext';

function AppContent() {
  const { isLoggedIn } = useAuth();

  if (!isLoggedIn) {
    return <LoginScreen />;
  }

  return (
    <BrowserRouter>
      <div className="max-w-lg mx-auto relative min-h-screen bg-white shadow-xl">
        <Routes>
          <Route path="/" element={<HomeScreen />} />
          <Route path="/phase/:phaseId" element={<PhaseDetails />} />
          <Route path="/day/:dayId" element={<DayDetails />} />
          <Route path="/missions" element={<MissionsScreen />} />
          <Route path="/documents" element={<DocumentsScreen />} />
          <Route path="/emergency" element={<EmergencyContacts />} />
          <Route path="/profile" element={<ProfileScreen />} />
        </Routes>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
