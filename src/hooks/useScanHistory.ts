import { useCallback, useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';

export interface ScanHistoryRow {
  id: string;
  created_at: string;
  is_diseased: boolean | null;
  label: string | null;
  confidence: number | null;
  notes: string | null;
  sprayed: boolean;
  grid_row: number | null;
  grid_col: number | null;
  qr_raw: string | null;
}

export interface ScanHistoryFilter {
  row?: number;
  col?: number;
}

const PAGE_LIMIT = 200;

export function useScanHistory(filter: ScanHistoryFilter = {}) {
  const [rows, setRows] = useState<ScanHistoryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { row, col } = filter;

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    let q = supabase
      .from('scan_results')
      .select(
        'id, created_at, is_diseased, label, confidence, notes, sprayed, grid_row, grid_col, qr_raw'
      )
      .order('created_at', { ascending: false })
      .limit(PAGE_LIMIT);
    if (row !== undefined) q = q.eq('grid_row', row);
    if (col !== undefined) q = q.eq('grid_col', col);

    const { data, error } = await q;
    if (error) {
      setError(error.message);
      setRows([]);
    } else {
      setRows((data ?? []) as ScanHistoryRow[]);
    }
    setLoading(false);
  }, [row, col]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { rows, loading, error, refresh };
}
