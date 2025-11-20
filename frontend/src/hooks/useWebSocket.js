import { useEffect } from 'react';
import { useSelector } from 'react-redux';
import websocketManager from '../utils/websocket';

export function useWebSocket() {
  const { user } = useSelector((state) => state.auth);
  const { currentWorkspace } = useSelector((state) => state.workspace);

  useEffect(() => {
    if (user && currentWorkspace) {
      const token = localStorage.getItem('access_token');

      websocketManager.connect(currentWorkspace.id, token);

      return () => websocketManager.disconnect();
    }
  }, [user, currentWorkspace]);

  return websocketManager;
}
