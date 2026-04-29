import { useCallback, useEffect, useRef } from 'react';
import { sendDrive, type DriveCommand } from '../lib/supabase';
import { useSpeed } from './useSpeed';

const REPEAT_MS = 300;

interface Options {
  onActiveChange?: (cmd: DriveCommand | null) => void;
}

export function useHoldCommand({ onActiveChange }: Options = {}) {
  const intervalRef = useRef<number | null>(null);
  const activeRef = useRef<DriveCommand | null>(null);
  const speedRef = useRef(0.7);

  const { speed } = useSpeed();
  speedRef.current = speed;

  const stop = useCallback(() => {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (activeRef.current !== null) {
      activeRef.current = null;
      onActiveChange?.(null);
      void sendDrive('stop', speedRef.current);
    }
  }, [onActiveChange]);

  const start = useCallback(
    (command: DriveCommand) => {
      if (activeRef.current === command) return;
      stop();
      activeRef.current = command;
      onActiveChange?.(command);
      void sendDrive(command, speedRef.current);
      intervalRef.current = window.setInterval(() => {
        void sendDrive(command, speedRef.current);
      }, REPEAT_MS);
    },
    [stop, onActiveChange]
  );

  useEffect(() => () => stop(), [stop]);

  const bind = useCallback(
    (command: DriveCommand) => ({
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
