/** Supabase browser client. Null when not configured — callers must
 * degrade honestly instead of pretending auth works.
 */
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let client: SupabaseClient | null | undefined;

export function getSupabase(): SupabaseClient | null {
  if (client !== undefined) return client;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  client = url && anon ? createClient(url, anon) : null;
  return client;
}

export function supabaseConfigured(): boolean {
  return getSupabase() !== null;
}
