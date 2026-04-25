import { cn } from '../lib/utils';

interface Props {
  isOnline: boolean | null;
}

export function StatusIndicator({ isOnline }: Props) {
  const label =
    isOnline === null ? 'Connecting…' : isOnline ? 'Online' : 'Offline';
  const dotColor =
    isOnline === null
      ? 'bg-zinc-500'
      : isOnline
        ? 'bg-green-500'
        : 'bg-red-500';

  return (
    <div className="flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/60 px-4 py-2">
      <span
        className={cn(
          'h-2.5 w-2.5 rounded-full',
          dotColor,
          isOnline && 'animate-pulse'
        )}
      />
      <span className="text-sm font-medium tracking-wide text-zinc-200">
        Rover {label}
      </span>
    </div>
  );
}
