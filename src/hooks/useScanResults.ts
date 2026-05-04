import { useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { supabase } from '../lib/supabase';

const POLL_MS = 3000;

interface ScanResult {
  id: string;
  created_at: string;
  is_diseased: boolean | null;
  label: string | null;
  confidence: number | null;
  notes: string | null;
  sprayed: boolean;
}

const DISEASE_NAMES: Record<string, string> = {
  brownspot: 'Brown spot',
  sheath_blight: 'Sheath blight',
  tungro: 'Tungro',
  rice_blast: 'Rice blast',
};

function showToast(row: ScanResult) {
  // ScanButton fires a `loading` toast with id 'scan'; replace it.
  toast.dismiss('scan');

  const conf = row.confidence != null ? `${Math.round(row.confidence * 100)}%` : '';

  if (row.label === 'error') {
    toast.warning('Scan failed', {
      description: row.notes ?? 'Unknown error on the rover',
    });
    return;
  }
  if (row.is_diseased === true) {
    const name = DISEASE_NAMES[row.label ?? ''] ?? row.label ?? 'Disease';
    const sprayNote = row.sprayed
      ? `Sprayer activated (${conf} confidence)`
      : `${conf} confidence — sprayer only triggers for brown spot`;
    toast.error(`🚨 ${name} detected`, { description: sprayNote });
    return;
  }
  if (row.is_diseased === false) {
    toast.success('✅ Healthy leaf', {
      description: conf ? `${conf} confidence` : undefined,
    });
    return;
  }
  toast.info('Scan inconclusive', {
    description: row.notes ?? 'Try again with a clearer view of the leaf',
  });
}

export function useScanResults() {
  const cursorRef = useRef<string>(new Date().toISOString());

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      const { data, error } = await supabase
        .from('scan_results')
        .select('id, created_at, is_diseased, label, confidence, notes, sprayed')
        .gt('created_at', cursorRef.current)
        .order('created_at', { ascending: true })
        .limit(20);
      if (cancelled) return;
      if (error) {
        console.error('[useScanResults] poll error', error);
        return;
      }
      for (const row of data ?? []) {
        showToast(row as ScanResult);
        if (row.created_at > cursorRef.current) {
          cursorRef.current = row.created_at;
        }
      }
    }

    const interval = window.setInterval(poll, POLL_MS);

    const channel = supabase
      .channel('scan_results_inserts')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'scan_results' },
        (payload) => {
          const row = payload.new as ScanResult;
          if (row.created_at > cursorRef.current) {
            cursorRef.current = row.created_at;
            showToast(row);
          }
        }
      )
      .subscribe((status) => {
        console.log('[useScanResults] realtime status:', status);
      });

    return () => {
      cancelled = true;
      window.clearInterval(interval);
      supabase.removeChannel(channel);
    };
  }, []);
}
