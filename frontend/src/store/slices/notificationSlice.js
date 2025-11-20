import { createSlice } from '@reduxjs/toolkit';

const notificationSlice = createSlice({
  name: 'notification',
  initialState: {
    list: [],
  },
  reducers: {
    pushNotification: (state, action) => {
      state.list.push(action.payload);
    },
    removeNotification: (state, action) => {
      state.list = state.list.filter((n) => n.id !== action.payload);
    },
  },
});

export const { pushNotification, removeNotification } = notificationSlice.actions;
export default notificationSlice.reducer;
