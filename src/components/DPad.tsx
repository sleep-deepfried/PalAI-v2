import { useState } from 'react';
import {
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUpLeft,
  ArrowUpRight,
  ArrowDownLeft,
  ArrowDownRight,
  Square,
} from 'lucide-react';
import { useHoldCommand } from '../hooks/useHoldCommand';
import { sendDrive, type DriveCommand } from '../lib/supabase';
import { useSpeed } from '../hooks/useSpeed';
import { cn } from '../lib/utils';

const padBase =
  'flex items-center justify-center rounded-2xl border text-zinc-100 shadow-lg active:scale-95 transition-all select-none w-20 h-20 sm:w-24 sm:h-24 border-zinc-800 bg-zinc-900';

const padActive =
  'border-emerald-500/60 bg-emerald-900/60 text-emerald-100 scale-95';

interface HoldButtonProps {
  command: Exclude<DriveCommand, 'stop'>;
  label: string;
  active: boolean;
  bind: ReturnType<ReturnType<typeof useHoldCommand>['bind']> | null;
  bindFor: (cmd: DriveCommand) => ReturnType<ReturnType<typeof useHoldCommand>['bind']>;
  children: React.ReactNode;
}

function HoldButton({ command, label, active, bindFor, children }: HoldButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      data-active={active || undefined}
      className={cn(padBase, active && padActive)}
      {...bindFor(command)}
    >
      {children}
    </button>
  );
}

interface DPadProps {
  onActiveChange?: (cmd: DriveCommand | null) => void;
}

export function DPad({ onActiveChange }: DPadProps) {
  const [active, setActive] = useState<DriveCommand | null>(null);
  const { speed } = useSpeed();

  const { bind } = useHoldCommand({
    onActiveChange: (cmd) => {
      setActive(cmd);
      onActiveChange?.(cmd);
    },
  });

  const isActive = (cmd: DriveCommand) => active === cmd;

  return (
    <div
      className="grid grid-cols-3 grid-rows-3 gap-3"
      style={{ touchAction: 'none' }}
    >
      <HoldButton command="forward_left" label="Forward-left" active={isActive('forward_left')} bind={null} bindFor={bind}>
        <ArrowUpLeft className="h-7 w-7" />
      </HoldButton>
      <HoldButton command="forward" label="Forward" active={isActive('forward')} bind={null} bindFor={bind}>
        <ArrowUp className="h-8 w-8" />
      </HoldButton>
      <HoldButton command="forward_right" label="Forward-right" active={isActive('forward_right')} bind={null} bindFor={bind}>
        <ArrowUpRight className="h-7 w-7" />
      </HoldButton>

      <HoldButton command="left" label="Left" active={isActive('left')} bind={null} bindFor={bind}>
        <ArrowLeft className="h-8 w-8" />
      </HoldButton>
      <button
        type="button"
        aria-label="Stop"
        onClick={() => void sendDrive('stop', speed)}
        className={cn(
          padBase,
          'border-red-900/60 bg-red-950/60 text-red-200 hover:bg-red-900/60'
        )}
      >
        <Square className="h-7 w-7 fill-current" />
      </button>
      <HoldButton command="right" label="Right" active={isActive('right')} bind={null} bindFor={bind}>
        <ArrowRight className="h-8 w-8" />
      </HoldButton>

      <HoldButton command="backward_left" label="Backward-left" active={isActive('backward_left')} bind={null} bindFor={bind}>
        <ArrowDownLeft className="h-7 w-7" />
      </HoldButton>
      <HoldButton command="backward" label="Backward" active={isActive('backward')} bind={null} bindFor={bind}>
        <ArrowDown className="h-8 w-8" />
      </HoldButton>
      <HoldButton command="backward_right" label="Backward-right" active={isActive('backward_right')} bind={null} bindFor={bind}>
        <ArrowDownRight className="h-7 w-7" />
      </HoldButton>
    </div>
  );
}
