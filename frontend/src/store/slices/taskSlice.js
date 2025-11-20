import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import * as taskAPI from '../../api/tasks';

export const fetchTasks = createAsyncThunk(
  'task/fetchAll',
  async ({ projectId, filters }, { rejectWithValue }) => {
    try {
      const response = await taskAPI.getTasks(projectId, filters);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Failed to load tasks');
    }
  }
);

const taskSlice = createSlice({
  name: 'task',
  initialState: {
    list: [],
    selected: null,
    loading: false,
    error: null,
  },
  reducers: {
    selectTask: (state, action) => {
      state.selected = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTasks.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchTasks.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload;
      })
      .addCase(fetchTasks.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { selectTask } = taskSlice.actions;
export default taskSlice.reducer;
