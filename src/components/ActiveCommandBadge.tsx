import type { DriveCommand } from '../lib/supabase';
import { useSpeed } from '../hooks/useSpeed';
import { cn } from '../lib/utils';

const LABEL: Record<DriveCommand, string> = {
  forward: 'Forward',
  backward: 'Backward',
  left: 'Left',
  right: 'Right',
  stop: 'Stop',
  forward_left: 'Forward-Left',
  forward_right: 'Forward-Right',
  backward_left: 'Backward-Left',
  backward_right: 'Backward-Right',
};

export function ActiveCommandBadge({ active }: { active: DriveCommand | null }) {
  const { speed } = useSpeed();
  const pct = Math.round(speed * 100);
  const live = active && active !== 'stop';

  return (
    <div
      className={cn(
        'mx-auto rounded-full border px-3 py-1 text-xs font-medium tracking-wide transition-colors',
        live
          ? 'border-emerald-500/60 bg-emerald-900/40 text-emerald-200'
          : 'border-zinc-800 bg-zinc-900 text-zinc-500'
      )}
      role="status"
      aria-live="polite"
    >
      {live ? `${LABEL[active].toUpperCase()} · ${pct}%` : 'IDLE'}
    </div>
  );
}
