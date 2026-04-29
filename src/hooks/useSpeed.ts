import { createContext, createElement, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';

const STORAGE_KEY = 'palai.speed';
const MIN = 0.3;
const MAX = 1.0;
const DEFAULT = 0.7;

const clamp = (n: number) => Math.min(MAX, Math.max(MIN, n));

interface SpeedCtx {
  speed: number;
  setSpeed: (n: number) => void;
}

const Ctx = createContext<SpeedCtx | null>(null);

export function SpeedProvider({ children }: { children: ReactNode }) {
  const [speed, setSpeedState] = useState<number>(() => {
    const raw = typeof window !== 'undefined' ? window.localStorage.getItem(STORAGE_KEY) : null;
    const parsed = raw ? Number(raw) : NaN;
    return Number.isFinite(parsed) ? clamp(parsed) : DEFAULT;
  });

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, String(speed));
  }, [speed]);

  const setSpeed = useCallback((n: number) => setSpeedState(clamp(n)), []);

  return createElement(Ctx.Provider, { value: { speed, setSpeed } }, children);
}

export function useSpeed(): SpeedCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error('useSpeed must be used inside <SpeedProvider>');
  return v;
}
