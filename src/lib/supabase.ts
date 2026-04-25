import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

if (!url || !anonKey) {
  // Visible in browser console — no silent failure on Vercel.
  console.error(
    '[supabase] Missing env vars. ' +
      'Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your Vercel project ' +
      'and redeploy. Got:',
    { url, anonKey: anonKey ? '<set>' : '<missing>' }
  );
}

export const supabase = createClient(url ?? '', anonKey ?? '');

export type RoverCommand =
  | 'forward'
  | 'backward'
  | 'left'
  | 'right'
  | 'stop'
  | 'scan';

export async function sendCommand(command: RoverCommand) {
  const { error } = await supabase.from('rover_commands').insert({ command });
  if (error) console.error('[sendCommand] error', command, error);
}
