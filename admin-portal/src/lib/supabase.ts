import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Graceful degradation: 缺失 env vars 时不崩溃，仅 warn
let supabase: SupabaseClient | null = null;
if (supabaseUrl && supabaseAnonKey) {
  supabase = createClient(supabaseUrl, supabaseAnonKey);
} else {
  console.warn('[supabase] Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY — Supabase disabled');
}

export { supabase };

export interface AuditLog {
  id?: string;
  trace_id: string;
  patient_id: string;
  master_signer_id: string;
  secondary_signer_id: string;
  original_l5_output: string;
  approved_l6_output: string;
  risk_level: string;
  approved_at?: string;
  created_at?: string;
}

export const sendBehaviorEvent = async (logData: Omit<AuditLog, 'id' | 'created_at'>) => {
  if (!supabase) {
    console.warn('[supabase] Client not initialized, skipping audit log');
    return null;
  }

  const { data, error } = await supabase
    .from('behavior_audit_logs')
    .insert([logData])
    .select()
    .maybeSingle();

  if (error) {
    console.error(`[supabase] Failed to log audit event: ${error.message}`);
    return null;
  }

  return data;
};
