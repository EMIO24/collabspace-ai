import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import * as chatAPI from '../../api/chat';

export const fetchChannels = createAsyncThunk(
  'chat/fetchChannels',
  async (workspaceId, { rejectWithValue }) => {
    try {
      const response = await chatAPI.getChannels(workspaceId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Failed to load channels');
    }
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    channels: [],
    messages: {},
    activeChannel: null,
    loading: false,
    error: null,
  },
  reducers: {
    setActiveChannel: (state, action) => {
      state.activeChannel = action.payload;
    },
    addMessage: (state, action) => {
      const { channelId, message } = action.payload;
      if (!state.messages[channelId]) state.messages[channelId] = [];
      state.messages[channelId].push(message);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchChannels.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchChannels.fulfilled, (state, action) => {
        state.loading = false;
        state.channels = action.payload;
      })
      .addCase(fetchChannels.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { setActiveChannel, addMessage } = chatSlice.actions;
export default chatSlice.reducer;
