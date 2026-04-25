import { useCallback, useEffect, useRef } from 'react';
import { sendCommand, type RoverCommand } from '../lib/supabase';

const REPEAT_MS = 300;

export function useHoldCommand() {
  const intervalRef = useRef<number | null>(null);
  const activeRef = useRef<RoverCommand | null>(null);

  const stop = useCallback(() => {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (activeRef.current !== null) {
      activeRef.current = null;
      void sendCommand('stop');
    }
  }, []);

  const start = useCallback(
    (command: RoverCommand) => {
      if (activeRef.current === command) return;
      stop();
      activeRef.current = command;
      void sendCommand(command);
      intervalRef.current = window.setInterval(() => {
        void sendCommand(command);
      }, REPEAT_MS);
    },
    [stop]
  );

  useEffect(() => () => stop(), [stop]);

  const bind = useCallback(
    (command: RoverCommand) => ({
      onPointerDown: (e: React.PointerEvent) => {
        e.preventDefault();
        (e.target as Element).setPointerCapture?.(e.pointerId);
        start(command);
      },
      onPointerUp: (e: React.PointerEvent) => {
        (e.target as Element).releasePointerCapture?.(e.pointerId);
        stop();
      },
      onPointerCancel: () => stop(),
      onPointerLeave: () => stop(),
      onContextMenu: (e: React.MouseEvent) => e.preventDefault(),
      style: { touchAction: 'none' as const },
    }),
    [start, stop]
  );

  return { bind };
}
