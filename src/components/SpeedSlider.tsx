import { Gauge } from 'lucide-react';
import { useSpeed } from '../hooks/useSpeed';

export function SpeedSlider() {
  const { speed, setSpeed } = useSpeed();
  const pct = Math.round(speed * 100);

  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3">
      <div className="flex items-center justify-between text-xs text-zinc-400">
        <span className="flex items-center gap-1.5">
          <Gauge className="h-3.5 w-3.5" />
          Speed
        </span>
        <span className="font-mono text-sm font-semibold text-zinc-100">{pct}%</span>
      </div>
      <input
        type="range"
        min={0.3}
        max={1.0}
        step={0.05}
        value={speed}
        onChange={(e) => setSpeed(Number(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-full bg-zinc-800 accent-emerald-500"
        aria-label="Motor speed"
      />
    </div>
  );
}
