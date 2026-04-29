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

export type DriveCommand =
  | 'forward'
  | 'backward'
  | 'left'
  | 'right'
  | 'stop'
  | 'forward_left'
  | 'forward_right'
  | 'backward_left'
  | 'backward_right';

export type RoverCommand = DriveCommand | 'scan' | 'spray';

export async function sendDrive(command: DriveCommand, speed: number): Promise<void> {
  const { error } = await supabase
    .from('rover_commands')
    .insert({ command, speed });
  if (error) console.error('[sendDrive] error', command, error);
}

export async function sendCommand(command: 'scan' | 'spray'): Promise<void> {
  const { error } = await supabase.from('rover_commands').insert({ command });
  if (error) console.error('[sendCommand] error', command, error);
}
