import { useState } from 'react';
import { Droplets } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { sendCommand } from '../lib/supabase';

export function SprayButton() {
  const [busy, setBusy] = useState(false);

  const handleClick = async () => {
    if (busy) return;
    setBusy(true);
    toast.info('💧 Spraying', {
      id: 'spray',
      description: 'Manual pump trigger',
      duration: 2000,
    });
    await sendCommand('spray');
    window.setTimeout(() => setBusy(false), 2500);
  };

  return (
    <Button
      size="lg"
      variant="secondary"
      onClick={handleClick}
      disabled={busy}
      className="w-full gap-2 text-base"
    >
      <Droplets className="h-5 w-5" />
      Spray
    </Button>
  );
}
