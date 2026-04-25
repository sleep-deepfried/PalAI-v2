import { Route, Routes } from 'react-router-dom';
import RoverDashboard from './pages/RoverDashboard';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RoverDashboard />} />
    </Routes>
  );
}
