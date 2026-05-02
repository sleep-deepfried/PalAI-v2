import { Route, Routes } from 'react-router-dom';
import RoverDashboard from './pages/RoverDashboard';
import ScanHistory from './pages/ScanHistory';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RoverDashboard />} />
      <Route path="/history" element={<ScanHistory />} />
    </Routes>
  );
}
