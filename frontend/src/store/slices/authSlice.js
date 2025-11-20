import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
// NOTE: Ensure '@api/axios' is correctly configured as an alias in your vite.config.js
import api from '@api/axios'; 

// --- Async Thunk for Login ---
/**
 * @name login
 * Handles the asynchronous login process.
 * - Sends user credentials to the backend.
 * - On success, returns user data and the auth token.
 * - On failure, uses rejectWithValue to pass the error to the state.
 */
export const login = createAsyncThunk(
  'auth/login',
  async (credentials, { rejectWithValue }) => {
    try {
      const res = await api.post('/auth/login/', credentials);
      // The backend should return { user: {...}, token: '...' }
      return res.data;
    } catch (err) {
      // Extract the error message from the response or use a default
      const errorPayload = err.response?.data || { message: 'Network or general login failed' };
      return rejectWithValue(errorPayload);
    }
  }
);

// --- Initial State ---
const initialState = {
  user: null, // Stores the authenticated user's object
  // Initialize token from localStorage for persistence across page reloads
  token: localStorage.getItem('token') || null, 
  status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null     // Stores error details on failure
};

// --- Auth Slice Definition ---
const authSlice = createSlice({
  name: 'auth',
  initialState,
  // Reducers for synchronous state updates
  reducers: {
    /** Clears user, token, and removes token from localStorage. */
    logout(state) {
      state.user = null;
      state.token = null;
      localStorage.removeItem('token');
    },
    /** Directly sets the user object (e.g., after fetching current user data). */
    setUser(state, action) {
      state.user = action.payload;
    }
  },
  // Extra Reducers for handling createAsyncThunk lifecycle actions (pending, fulfilled, rejected)
  extraReducers: (builder) => {
    builder
      // 1. Pending: Request started
      .addCase(login.pending, (state) => { 
        state.status = 'loading'; 
        state.error = null; // Clear previous errors
      })
      // 2. Fulfilled: Request successful
      .addCase(login.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.user = action.payload.user;
        state.token = action.payload.token;
        // Persist the token in localStorage
        localStorage.setItem('token', action.payload.token); 
      })
      // 3. Rejected: Request failed
      .addCase(login.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload; // Error object from rejectWithValue
      });
  }
});

// Export synchronous actions for use in components
export const { logout, setUser } = authSlice.actions;

// Export the reducer to be combined in the store
export default authSlice.reducer;