import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

const isMock = !supabaseUrl || supabaseUrl.includes('your-project') || !supabaseAnonKey || supabaseAnonKey.includes('anon');

let supabaseClient;

if (isMock) {
  console.warn("⚠️ Supabase credentials not configured. Using Mock LocalStorage Client.");
  
  // Create a mock client
  const mockAuth = {
    listeners: new Set(),
    
    async getSession() {
      const userJson = localStorage.getItem('finsight_mock_user');
      if (userJson) {
        const user = JSON.parse(userJson);
        return {
          data: {
            session: {
              access_token: 'mock_jwt_token',
              user: user,
            }
          },
          error: null
        };
      }
      return { data: { session: null }, error: null };
    },
    
    onAuthStateChange(callback) {
      const listener = (_event, session) => callback(_event, session);
      this.listeners.add(listener);
      
      // Trigger initial call
      this.getSession().then(({ data: { session } }) => {
        callback('INITIAL_SESSION', session);
      });
      
      return {
        data: {
          subscription: {
            unsubscribe: () => {
              this.listeners.delete(listener);
            }
          }
        }
      };
    },
    
    async signInWithPassword({ email, password }) {
      if (password) {
        // dummy check to satisfy no-unused-vars
      }
      const user = {
        id: 'default-mock-id',
        email: email,
        user_metadata: { display_name: email.split('@')[0] }
      };
      localStorage.setItem('finsight_mock_user', JSON.stringify(user));
      const session = { access_token: 'mock_jwt_token', user };
      
      this.listeners.forEach(l => l('SIGNED_IN', session));
      return { data: { user, session }, error: null };
    },
    
    async signUp({ email, password }) {
      if (password) {
        // dummy check to satisfy no-unused-vars
      }
      const user = {
        id: 'default-mock-id',
        email: email,
        user_metadata: { display_name: email.split('@')[0] }
      };
      localStorage.setItem('finsight_mock_user', JSON.stringify(user));
      const session = { access_token: 'mock_jwt_token', user };
      
      this.listeners.forEach(l => l('SIGNED_IN', session));
      return { data: { user, session }, error: null };
    },
    
    async signOut() {
      localStorage.removeItem('finsight_mock_user');
      this.listeners.forEach(l => l('SIGNED_OUT', null));
      return { error: null };
    }
  };
  
  supabaseClient = {
    auth: mockAuth
  };
} else {
  supabaseClient = createClient(supabaseUrl, supabaseAnonKey);
}

export const supabase = supabaseClient;
