import { DPad } from '../components/DPad';
import { ScanButton } from '../components/ScanButton';
import { StatusIndicator } from '../components/StatusIndicator';
import { useRoverStatus } from '../hooks/useRoverStatus';
import { useScanResults } from '../hooks/useScanResults';

export default function RoverDashboard() {
  const { isOnline } = useRoverStatus();
  useScanResults();

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

      <main className="flex flex-1 items-center justify-center py-8">
        <DPad />
      </main>

      <footer>
        <ScanButton />
      </footer>
    </div>
  );
}
