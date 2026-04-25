import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';

const POLL_MS = 3000;

export function useRoverStatus() {
  const [isOnline, setIsOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchStatus() {
      const { data, error } = await supabase
        .from('rover_status')
        .select('is_online')
        .eq('id', 1)
        .maybeSingle();
      if (cancelled) return;
      if (error) {
        console.error('[useRoverStatus] fetch error', error);
        return;
      }
      if (data) {
        setIsOnline(Boolean(data.is_online));
      } else {
        console.warn('[useRoverStatus] no row with id=1 in rover_status');
      }
    }

    void fetchStatus();
    const interval = window.setInterval(fetchStatus, POLL_MS);

    const channel = supabase
      .channel('rover_status_changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'rover_status',
          filter: 'id=eq.1',
        },
        (payload) => {
          const row = payload.new as { is_online?: boolean } | null;
          if (row && typeof row.is_online === 'boolean') {
            setIsOnline(row.is_online);
          }
        }
      )
      .subscribe((status) => {
        console.log('[useRoverStatus] realtime status:', status);
      });

    return () => {
      cancelled = true;
      window.clearInterval(interval);
      supabase.removeChannel(channel);
    };
  }, []);

  return { isOnline };
}
