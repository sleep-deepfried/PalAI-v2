import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';

export function useRoverStatus() {
  const [isOnline, setIsOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;

    supabase
      .from('rover_status')
      .select('is_online')
      .eq('id', 1)
      .single()
      .then(({ data, error }) => {
        if (cancelled) return;
        if (error) {
          console.error('rover_status fetch error', error);
          return;
        }
        setIsOnline(Boolean(data?.is_online));
      });

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
      .subscribe();

    return () => {
      cancelled = true;
      supabase.removeChannel(channel);
    };
  }, []);

  return { isOnline };
}
