import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import * as projectAPI from '../../api/projects';

export const fetchProjects = createAsyncThunk(
  'project/fetchAll',
  async ({ workspaceId, filters }, { rejectWithValue }) => {
    try {
      const response = await projectAPI.getProjects(workspaceId, filters);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Failed to load projects');
    }
  }
);

const projectSlice = createSlice({
  name: 'project',
  initialState: {
    list: [],
    current: null,
    filters: {},
    loading: false,
    error: null,
  },
  reducers: {
    setProjectFilters: (state, action) => {
      state.filters = action.payload;
    },
    setCurrentProject: (state, action) => {
      state.current = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchProjects.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchProjects.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload;
      })
      .addCase(fetchProjects.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { setProjectFilters, setCurrentProject } = projectSlice.actions;
export default projectSlice.reducer;
