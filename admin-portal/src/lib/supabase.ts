import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

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
  const { data, error } = await supabase
    .from('behavior_audit_logs')
    .insert([logData])
    .select()
    .maybeSingle();

  if (error) {
    throw new Error(`Failed to log audit event: ${error.message}`);
  }

  return data;
};
