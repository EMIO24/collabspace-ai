import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import * as workspaceAPI from '../../api/workspaces';

// Load all workspaces
export const fetchWorkspaces = createAsyncThunk(
  'workspace/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const response = await workspaceAPI.getWorkspaces();
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Failed to load workspaces');
    }
  }
);

const workspaceSlice = createSlice({
  name: 'workspace',
  initialState: {
    list: [],
    current: null,
    loading: false,
    error: null,
  },
  reducers: {
    setCurrentWorkspace: (state, action) => {
      state.current = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchWorkspaces.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchWorkspaces.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload;
      })
      .addCase(fetchWorkspaces.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { setCurrentWorkspace } = workspaceSlice.actions;
export default workspaceSlice.reducer;
