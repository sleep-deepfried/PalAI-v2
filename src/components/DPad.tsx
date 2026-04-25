import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Square } from 'lucide-react';
import { useHoldCommand } from '../hooks/useHoldCommand';
import { sendCommand, type RoverCommand } from '../lib/supabase';
import { cn } from '../lib/utils';

const padBase =
  'flex items-center justify-center rounded-2xl border border-zinc-800 bg-zinc-900 text-zinc-100 shadow-lg active:scale-95 active:bg-zinc-800 transition-transform select-none w-20 h-20 sm:w-24 sm:h-24';

interface HoldButtonProps {
  command: Exclude<RoverCommand, 'stop' | 'scan'>;
  label: string;
  className?: string;
  children: React.ReactNode;
}

function HoldButton({ command, label, className, children }: HoldButtonProps) {
  const { bind } = useHoldCommand();
  return (
    <button
      type="button"
      aria-label={label}
      className={cn(padBase, className)}
      {...bind(command)}
    >
      {children}
    </button>
  );
}

export function DPad() {
  return (
    <div
      className="grid grid-cols-3 grid-rows-3 gap-3"
      style={{ touchAction: 'none' }}
    >
      <div />
      <HoldButton command="forward" label="Forward">
        <ArrowUp className="h-8 w-8" />
      </HoldButton>
      <div />

      <HoldButton command="left" label="Left">
        <ArrowLeft className="h-8 w-8" />
      </HoldButton>
      <button
        type="button"
        aria-label="Stop"
        onClick={() => void sendCommand('stop')}
        className={cn(
          padBase,
          'border-red-900/60 bg-red-950/60 text-red-200 hover:bg-red-900/60'
        )}
      >
        <Square className="h-7 w-7 fill-current" />
      </button>
      <HoldButton command="right" label="Right">
        <ArrowRight className="h-8 w-8" />
      </HoldButton>

      <div />
      <HoldButton command="backward" label="Backward">
        <ArrowDown className="h-8 w-8" />
      </HoldButton>
      <div />
    </div>
  );
}
