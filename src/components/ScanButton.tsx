import { useState } from 'react';
import { Radar } from 'lucide-react';
import { Button } from './ui/button';
import { sendCommand } from '../lib/supabase';

export function ScanButton() {
  const [busy, setBusy] = useState(false);

  const handleClick = async () => {
    if (busy) return;
    setBusy(true);
    await sendCommand('scan');
    window.setTimeout(() => setBusy(false), 500);
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
