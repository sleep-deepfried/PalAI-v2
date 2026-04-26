import { useState } from 'react';
import { Radar } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { sendCommand } from '../lib/supabase';

export function ScanButton() {
  const [busy, setBusy] = useState(false);

  const handleClick = async () => {
    if (busy) return;
    setBusy(true);
    // Loading toast is replaced by useScanResults on the next scan_results row.
    toast.loading('Scanning…', {
      id: 'scan',
      description: 'Rover is capturing and analyzing',
    });
    await sendCommand('scan');
    window.setTimeout(() => setBusy(false), 1500);
  };

  return (
    <Button
      size="lg"
      variant="secondary"
      onClick={handleClick}
      disabled={busy}
      className="w-full gap-2 text-base"
    >
      <Radar className="h-5 w-5" />
      Scan
    </Button>
  );
}
