import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL as string;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

export const supabase = createClient(url, anonKey);

export type RoverCommand =
  | 'forward'
  | 'backward'
  | 'left'
  | 'right'
  | 'stop'
  | 'scan';

export async function sendCommand(command: RoverCommand) {
  const { error } = await supabase.from('rover_commands').insert({ command });
  if (error) console.error('sendCommand error', command, error);
}
