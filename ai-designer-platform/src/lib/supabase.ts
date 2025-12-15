import { createClient, SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://ezipxfwailjdebaffbys.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV6aXB4ZndhaWxqZGViYWZmYnlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ4MDcxNzEsImV4cCI6MjA4MDM4MzE3MX0.ocOJKRJT2GuWKOOROJB82-rix8Ub8wdc7Q_lgyNvGf0'

// Check if Supabase is configured
export const isSupabaseConfigured = () => {
  return !!(supabaseUrl && supabaseAnonKey)
}

// Create a mock supabase client for demo mode
const createMockClient = () => {
  return {
    functions: {
      invoke: async () => ({ data: null, error: new Error('Demo mode - Supabase not configured') })
    },
    from: () => ({
      select: () => ({ data: null, error: new Error('Demo mode') }),
      insert: () => ({ data: null, error: new Error('Demo mode') }),
      update: () => ({ data: null, error: new Error('Demo mode') }),
      delete: () => ({ data: null, error: new Error('Demo mode') }),
    }),
    storage: {
      from: () => ({
        upload: async () => ({ data: null, error: new Error('Demo mode') }),
        download: async () => ({ data: null, error: new Error('Demo mode') }),
      })
    }
  } as unknown as SupabaseClient
}

// Only create real client if configured, otherwise use mock
export const supabase: SupabaseClient = isSupabaseConfigured() 
  ? (() => {
      console.log('Creating real Supabase client with URL:', supabaseUrl)
      return createClient(supabaseUrl, supabaseAnonKey)
    })()
  : createMockClient()
