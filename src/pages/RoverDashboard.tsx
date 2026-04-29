import { useState } from 'react';
import { ActiveCommandBadge } from '../components/ActiveCommandBadge';
import { DPad } from '../components/DPad';
import { ScanButton } from '../components/ScanButton';
import { SpeedSlider } from '../components/SpeedSlider';
import { SprayButton } from '../components/SprayButton';
import { StatusIndicator } from '../components/StatusIndicator';
import { SpeedProvider } from '../hooks/useSpeed';
import { useRoverStatus } from '../hooks/useRoverStatus';
import { useScanResults } from '../hooks/useScanResults';
import type { DriveCommand } from '../lib/supabase';

function DashboardInner() {
  const { isOnline } = useRoverStatus();
  useScanResults();
  const [active, setActive] = useState<DriveCommand | null>(null);

  return (
    <div
      className="mx-auto flex min-h-dvh w-full max-w-md flex-col px-5 pt-6"
      style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 1.25rem)' }}
    >
      <header className="flex items-center justify-between">
        <h1 className="text-lg font-semibold tracking-tight text-zinc-100">
          Rover Control
        </h1>
        <StatusIndicator isOnline={isOnline} />
      </header>

      <main className="flex flex-1 flex-col items-center justify-center gap-4 py-6">
        <ActiveCommandBadge active={active} />
        <DPad onActiveChange={setActive} />
        <div className="w-full max-w-xs">
          <SpeedSlider />
        </div>
      </main>

      <footer className="flex flex-col gap-2">
        <ScanButton />
        <SprayButton />
      </footer>
    </div>
  );
}

export default function RoverDashboard() {
  return (
    <SpeedProvider>
      <DashboardInner />
    </SpeedProvider>
  );
}
